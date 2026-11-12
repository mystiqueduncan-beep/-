/* Progressive enhancement: original chapter links remain functional without JS. */
(() => {
  "use strict";
  const nav = document.querySelector("[data-keycap-marquee]");
  if (!nav || typeof window.matchMedia !== "function") return;

  const belt = nav.querySelector(".keycap-marquee__belt");
  const original = nav.querySelector(".keycap-marquee__group");
  if (!belt || !original) return;

  // Respect user preference for reduced motion across desktop, tablet and mobile.
  const playback = window.matchMedia("(prefers-reduced-motion: no-preference)");
  const viewport = nav.querySelector(".keycap-marquee__viewport");

  // Show the original list so every keyboard target remains visible.
  nav.addEventListener("focusin", (event) => {
    const link = chapterLink(event.target);
    if (link && link.matches(":focus-visible")) {
      nav.classList.add("is-keyboard-paused");
      link.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  });
  nav.addEventListener("focusout", (event) => {
    if (!nav.contains(event.relatedTarget)) {
      nav.classList.remove("is-keyboard-paused");
    }
  });

  // A finger stays in control until release. Never let touch auto-play
  // while the user is examining a key or dragging the surrounding strip.
  let touchResumeTimer = null;
  function setTouchPaused(paused) {
    if (touchResumeTimer !== null) {
      clearTimeout(touchResumeTimer);
      touchResumeTimer = null;
    }
    nav.classList.toggle("is-touch-paused", Boolean(paused) && playback.matches);
  }
  function resumeTouchSoon() {
    if (touchResumeTimer !== null) clearTimeout(touchResumeTimer);
    touchResumeTimer = setTimeout(() => {
      nav.classList.remove("is-touch-paused");
      touchResumeTimer = null;
    }, 350);
  }

  // Pointer position, not link focus or hash navigation, owns hover pause.
  // Pointerout can fire when a moving key slides beneath a stationary cursor:
  // only leaving the entire strip should resume playback.
  let hovering = false;
  const mousePointer = event => event.pointerType === "mouse" || event.pointerType === "pen";

  function chapterLink(node) {
    if (!node || typeof node.closest !== "function") return null;
    const link = node.closest(".keycap-marquee__group a");
    return link && belt.contains(link) ? link : null;
  }

  function setHoverPaused(shouldPause) {
    hovering = Boolean(shouldPause);
    nav.classList.toggle("is-hover-paused", hovering && playback.matches);
  }

  nav.addEventListener("pointerenter", event => {
    if (mousePointer(event)) setHoverPaused(true);
  });
  nav.addEventListener("pointerover", event => {
    if (mousePointer(event)) setHoverPaused(true);
  });
  nav.addEventListener("pointerout", event => {
    if (!mousePointer(event) || nav.contains(event.relatedTarget)) return;
    // During a key transition the browser may report relatedTarget=null even
    // though the mouse is still hovering over the surrounding navigation.
    if (typeof nav.matches === "function" && nav.matches(":hover")) return;
    setHoverPaused(false);
  });
  nav.addEventListener("pointerleave", event => {
    if (mousePointer(event)) setHoverPaused(false);
  });

  function updateCurrent() {
    const active = window.location.hash || "#summary";
    nav.querySelectorAll('.keycap-marquee__group a[href^="#"]').forEach((link) => {
      const selected = link.getAttribute("href") === active;
      link.classList.toggle("is-current", selected);
      if (selected) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  }

  // Entire decorated marquee (not merely the buttons/viewport) is a drag
  // surface. A short, stationary pointer click still follows its real link.
  // A horizontal gesture may NEVER activate a chapter link.
  let drag = null;
  let suppressNextClick = false;
  let suppressionTimer = null;
  let layoutInitialized = false;
  const pixelsPerSecond = 32;
  // Content follows the very first horizontal pixel. This tolerance is only
  // for deciding whether a release is a click, never for delaying movement.
  const clickTolerance = 4;
  const verticalTolerance = 6;

  if (viewport) {
    viewport.querySelectorAll?.("a")?.forEach(link => link.setAttribute("draggable", "false"));
    nav.addEventListener("dragstart", event => event.preventDefault());
    nav.addEventListener("selectstart", event => {
      if (drag?.moved) event.preventDefault();
    });

    nav.addEventListener("pointerdown", event => {
      if (event.pointerType !== "touch" && event.button !== 0) return;
      if (drag) return;
      if (suppressionTimer !== null) {
        clearTimeout(suppressionTimer);
        suppressionTimer = null;
      }
      suppressNextClick = false;
      nav.classList.remove("is-keyboard-paused");
      drag = {
        pointerId: event.pointerId,
        type: event.pointerType,
        x: event.clientX,
        y: event.clientY || 0,
        scrollLeft: viewport.scrollLeft,
        moved: false,
        vertical: false
      };
      // Pause immediately at first contact, including the decorative interval.
      nav.classList.add("is-drag-paused");
      if (event.pointerType === "touch") setTouchPaused(true);
      else if (mousePointer(event)) setHoverPaused(true);
    });

    nav.addEventListener("pointermove", event => {
      if (!drag || drag.pointerId !== event.pointerId) return;
      if (drag.type !== "touch" && typeof event.buttons === "number" && event.buttons === 0) return;
      if (drag.vertical) return;

      const dx = event.clientX - drag.x;
      const dy = (event.clientY || 0) - drag.y;
      const horizontal = Math.abs(dx);
      const vertical = Math.abs(dy);

      // Do not hijack vertical scrolling on touchscreens. This check does not
      // postpone horizontal motion: even a 1px horizontal move scrolls.
      if (drag.type === "touch" && !drag.moved &&
          vertical >= verticalTolerance && vertical > horizontal) {
        drag.vertical = true;
        viewport.scrollLeft = drag.scrollLeft;
        return;
      }

      // From the first pixel, track the finger/mouse without any activation
      // threshold. Click suppression and pointer capture are independent.
      if (horizontal > 0 && horizontal >= vertical) {
        viewport.scrollLeft = drag.scrollLeft - dx;
      }
      if (!drag.moved && horizontal > clickTolerance &&
          horizontal >= vertical) {
        drag.moved = true;
        nav.classList.add("is-scrubbing");
        // Capture after a real gesture, not on pointerdown: true taps must
        // still dispatch their click to the original chapter anchor.
        try { nav.setPointerCapture?.(event.pointerId); } catch (_) {}
      }
      if (drag.moved && event.cancelable !== false) event.preventDefault();
    });

    function finishDrag(event) {
      if (!drag || drag.pointerId !== event.pointerId) return;
      const wasDragged = drag.moved;
      const wasTouch = drag.type === "touch";
      drag = null;
      nav.classList.remove("is-drag-paused");
      nav.classList.remove("is-scrubbing");
      if (wasTouch) resumeTouchSoon();
      try {
        if (nav.hasPointerCapture?.(event.pointerId)) nav.releasePointerCapture(event.pointerId);
      } catch (_) {}
      if (wasDragged) {
        suppressNextClick = true;
        if (suppressionTimer !== null) clearTimeout(suppressionTimer);
        // Safari can synthesize click in a later task after pointerup.
        suppressionTimer = setTimeout(() => {
          suppressNextClick = false;
          suppressionTimer = null;
        }, 650);
      }
    }
    nav.addEventListener("pointerup", finishDrag);
    nav.addEventListener("pointercancel", finishDrag);
    // A touch can change its implicit pointer-capture target mid-swipe.
    // lostpointercapture is NOT a release; never end the gesture on that event.
    // The window fallback catches releases outside the marquee instead.
    window.addEventListener("pointerup", finishDrag);
    window.addEventListener("pointercancel", finishDrag);

    // Capture before a click can reach any button or a delegated page handler.
    // Keyboard/assistive-tech activations (detail=0) must remain available.
    nav.addEventListener("click", event => {
      if (suppressNextClick && event.detail !== 0) {
        event.preventDefault();
        event.stopImmediatePropagation();
        suppressNextClick = false;
        if (suppressionTimer !== null) clearTimeout(suppressionTimer);
        suppressionTimer = null;
        return;
      }
      if (chapterLink(event.target)) setTouchPaused(false);
    }, true);

    window.addEventListener("blur", () => {
      if (!drag) return;
      const wasTouch = drag.type === "touch";
      drag = null;
      nav.classList.remove("is-drag-paused");
      nav.classList.remove("is-scrubbing");
      if (wasTouch) setTouchPaused(false);
    });

    viewport.addEventListener("keydown", event => {
      if (event.target !== viewport) return;
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      event.preventDefault();
      nav.classList.add("is-keyboard-paused");
      viewport.scrollLeft += event.key === "ArrowRight" ? 135 : -135;
    });
  }

  // Keep subpixel progress between frames: some Safari/Chromium modes
  // round scrollLeft to whole pixels and would otherwise never advance at 32px/s.
  let fractionalScroll = null;
  // Browser-driven scroll instead of CSS transform keeps the visible track
  // stationary while paused and makes mouse/touch dragging directly responsive.
  function autoScroll(timestamp) {
    if (!viewport || !playback.matches || !nav.classList.contains("is-enhanced")) return;
    if (!autoScroll.last) { autoScroll.last = timestamp; return; }
    const elapsed = Math.min(60, Math.max(0, timestamp - autoScroll.last));
    autoScroll.last = timestamp;
    if (nav.classList.contains("is-hover-paused") ||
        nav.classList.contains("is-keyboard-paused") ||
        nav.classList.contains("is-touch-paused") ||
        nav.classList.contains("is-drag-paused") ||
        document.hidden) {
      fractionalScroll = viewport.scrollLeft;
      return;
    }
    const limit = Math.max(0, viewport.scrollWidth - viewport.clientWidth);
    if (fractionalScroll === null || Math.abs(fractionalScroll - viewport.scrollLeft) > 2) {
      fractionalScroll = viewport.scrollLeft;
    }
    fractionalScroll += pixelsPerSecond * elapsed / 1000;
    if (limit > 0 && fractionalScroll >= limit - 1) {
      fractionalScroll = 0;
    }
    viewport.scrollLeft = fractionalScroll;
  }
  if (typeof window.requestAnimationFrame === "function" && viewport) {
    let lastFrame = 0;
    const tick = timestamp => {
      if (lastFrame) autoScroll(timestamp);
      else autoScroll.last = timestamp;
      lastFrame = timestamp;
      window.requestAnimationFrame(tick);
    };
    window.requestAnimationFrame(tick);
  }

  // A single original set of chapter buttons passes once, followed by a
  // decorated empty interval. Start/end are entirely offscreen so the loop
  // never exposes another copy of the same button or visibly jumps.
  function updateDuration() {
    const viewportWidth = Math.max(1, viewport?.clientWidth || 620);
    const interludeWidth = Math.max(390, Math.ceil(viewportWidth * 1.12));
    const previousStart = Number.parseFloat(belt.style.getPropertyValue?.("--keycap-start") || 0) || 0;
    belt.style.setProperty("--keycap-start", viewportWidth + "px");
    if (viewport && !layoutInitialized) {
      // Start with the first original chapter in view rather than an empty screen.
      viewport.scrollLeft = viewportWidth + 14;
      layoutInitialized = true;
    } else if (viewport && previousStart && previousStart !== viewportWidth) {
      // Changing the leading decorative width must not move the current key.
      viewport.scrollLeft += viewportWidth - previousStart;
    }
    belt.style.setProperty("--keycap-interlude-width", interludeWidth + "px");
  }

  function syncMode() {
    if (playback.matches) {
      nav.classList.add("is-enhanced");
      updateDuration();
      nav.classList.toggle("is-hover-paused", hovering);
    } else {
      nav.classList.remove("is-enhanced");
      nav.classList.remove("is-hover-paused");
      setTouchPaused(false);
    }
    updateCurrent();
  }

  window.addEventListener("hashchange", updateCurrent);
  if (typeof playback.addEventListener === "function") {
    playback.addEventListener("change", syncMode);
  } else if (typeof playback.addListener === "function") {
    playback.addListener(syncMode);
  }
  if (typeof ResizeObserver !== "undefined") {
    new ResizeObserver(() => {
      if (playback.matches) updateDuration();
    }).observe(original);
  }
  window.addEventListener("resize", () => {
    if (playback.matches) updateDuration();
  });
  syncMode();
})();
