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

  // Touch handling for mobile & tablet: pause during touch swiping and resume after release.
  let touchResumeTimer = null;
  function setTouchPaused(shouldPause) {
    if (touchResumeTimer) {
      clearTimeout(touchResumeTimer);
      touchResumeTimer = null;
    }
    nav.classList.toggle("is-touch-paused", Boolean(shouldPause) && playback.matches);
  }

  nav.addEventListener("pointerdown", (event) => {
    nav.classList.remove("is-keyboard-paused");
    if (event.pointerType === "touch") {
      setTouchPaused(true);
    }
  });
  nav.addEventListener("pointerup", (event) => {
    if (event.pointerType === "touch") {
      if (touchResumeTimer) clearTimeout(touchResumeTimer);
      touchResumeTimer = setTimeout(() => {
        setTouchPaused(false);
      }, 180);
    }
  });
  nav.addEventListener("pointercancel", (event) => {
    if (event.pointerType === "touch") {
      if (touchResumeTimer) clearTimeout(touchResumeTimer);
      touchResumeTimer = setTimeout(() => {
        setTouchPaused(false);
      }, 180);
    }
  });

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

  // Clicking changes only the location, never the pointer's hover state.
  // The clicked link may retain focus; that must not suppress hover detection.
  nav.addEventListener("click", event => {
    if (chapterLink(event.target)) setTouchPaused(false);
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

  // Dragging maps 1:1 to native horizontal scroll. No duplicate links, no
  // transform jump between pause and drag, and no invisible fake buttons.
  let drag = null;
  let suppressNextClick = false;
  let suppressionTimer = null;
  let layoutInitialized = false;
  const pixelsPerSecond = 32;
  if (viewport) {
    viewport.querySelectorAll?.("a")?.forEach(link => link.setAttribute("draggable", "false"));
    viewport.addEventListener("dragstart", event => event.preventDefault());
    viewport.addEventListener("pointerdown", event => {
      if (event.pointerType !== "touch" && event.button !== 0) return;
      if (drag) return;
      // An independent pointer gesture must not inherit click suppression.
      suppressNextClick = false;
      if (suppressionTimer) clearTimeout(suppressionTimer);
      nav.classList.remove("is-keyboard-paused");
      drag = {
        pointerId: event.pointerId,
        x: event.clientX,
        scrollLeft: viewport.scrollLeft,
        moved: false
      };
      nav.classList.add("is-drag-paused");
      if (event.pointerType === "touch") setTouchPaused(true);
    });
    viewport.addEventListener("pointermove", event => {
      if (!drag || drag.pointerId !== event.pointerId) return;
      const distance = event.clientX - drag.x;
      if (Math.abs(distance) > 6 && !drag.moved) {
        drag.moved = true;
        try { viewport.setPointerCapture?.(event.pointerId); } catch (_) {}
      }
      if (drag.moved) {
        viewport.scrollLeft = drag.scrollLeft - distance;
        event.preventDefault();
      }
    });
    function finishDrag(event) {
      if (!drag || event.pointerId !== drag.pointerId) return;
      suppressNextClick = drag.moved;
      drag = null;
      nav.classList.remove("is-drag-paused");
      if (event.pointerType === "touch") {
        setTouchPaused(true);
        if (touchResumeTimer) clearTimeout(touchResumeTimer);
        touchResumeTimer = setTimeout(() => setTouchPaused(false), 1200);
      }
      try {
        if (viewport.hasPointerCapture?.(event.pointerId)) viewport.releasePointerCapture(event.pointerId);
      } catch (_) {}
      // Keep suppression through the synthetic click after pointerup (which
      // Safari can dispatch after a task boundary), but not future gestures.
      if (suppressNextClick) {
        if (suppressionTimer) clearTimeout(suppressionTimer);
        suppressionTimer = setTimeout(() => {
          suppressNextClick = false;
          suppressionTimer = null;
        }, 450);
      }
    }
    viewport.addEventListener("pointerup", finishDrag);
    viewport.addEventListener("pointercancel", finishDrag);
    viewport.addEventListener("click", event => {
      if (!suppressNextClick) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      suppressNextClick = false;
      if (suppressionTimer) {
        clearTimeout(suppressionTimer);
        suppressionTimer = null;
      }
    }, true);
    window.addEventListener("blur", () => {
      // Releasing the browser window mid-gesture must never freeze playback.
      if (!drag) return;
      drag = null;
      nav.classList.remove("is-drag-paused");
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
    const groupWidth = original.getBoundingClientRect().width;
    const interludeWidth = Math.max(390, Math.ceil(viewportWidth * 1.12));
    const speed = 32; // pixels/second; calm editorial motion.
    const end = groupWidth + 14 + interludeWidth;
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
    belt.style.setProperty("--keycap-end", end + "px");
    belt.style.setProperty("--keycap-interlude-width", interludeWidth + "px");
    belt.style.setProperty("--keycap-duration", Math.max(40, (viewportWidth + end) / speed).toFixed(1) + "s");
    belt.style.setProperty("--keycap-delay", (-viewportWidth / speed).toFixed(2) + "s");
  }

  function syncMode() {
    if (playback.matches) {
      nav.classList.add("is-enhanced");
      updateDuration();
      nav.classList.toggle("is-hover-paused", hovering);
    } else {
      nav.classList.remove("is-enhanced", "is-hover-paused");
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
