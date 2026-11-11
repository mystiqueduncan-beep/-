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
    const link = chapterLink(event.target);
  });
  nav.addEventListener("pointerup", (event) => {
    if (event.pointerType === "touch") {
      if (touchResumeTimer) clearTimeout(touchResumeTimer);
      touchResumeTimer = setTimeout(() => {
        setTouchPaused(false);
      }, 1200);
    }
  });
  nav.addEventListener("pointercancel", (event) => {
    if (event.pointerType === "touch") {
      if (touchResumeTimer) clearTimeout(touchResumeTimer);
      touchResumeTimer = setTimeout(() => {
        setTouchPaused(false);
      }, 1200);
    }
  });

  // A clicked anchor retains focus after hash navigation. That focus must not
  // permanently pause the animation; require an actual new pointer movement.
  let resumeAfterNavigation = false;
  const mousePointer = (event) => event.pointerType === "mouse" || event.pointerType === "pen";

  function chapterLink(node) {
    if (!node || typeof node.closest !== "function") return null;
    const link = node.closest(".keycap-marquee__group a");
    return link && belt.contains(link) ? link : null;
  }

  function setHoverPaused(shouldPause) {
    nav.classList.toggle("is-hover-paused", Boolean(shouldPause) && playback.matches && !resumeAfterNavigation);
  }

  // Hover pauses over keys AND the decorated interval so the whole strip can be scrubbed.
  nav.addEventListener("pointerover", (event) => {
    if (mousePointer(event)) setHoverPaused(true);
  });
  nav.addEventListener("pointerout", (event) => {
    if (mousePointer(event) && !nav.contains(event.relatedTarget)) setHoverPaused(false);
  });
  nav.addEventListener("pointerleave", () => {
    resumeAfterNavigation = false;
    setHoverPaused(false);
  });
  nav.addEventListener("pointermove", (event) => {
    if (!mousePointer(event) || !resumeAfterNavigation) return;
    resumeAfterNavigation = false;
    setHoverPaused(true);
  });

  // Resume immediately on click, including while the page scrolls to an anchor.
  // Do not re-pause beneath a stationary cursor until the user moves it again.
  nav.addEventListener("click", (event) => {
    if (!chapterLink(event.target)) return;
    resumeAfterNavigation = true;
    setHoverPaused(false);
    setTouchPaused(false);
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
  let layoutInitialized = false;
  const pixelsPerSecond = 32;
  if (viewport) {
    viewport.querySelectorAll?.("a")?.forEach(link => link.setAttribute("draggable", "false"));
    viewport.addEventListener("dragstart", event => event.preventDefault());
    viewport.addEventListener("pointerdown", event => {
      if (event.pointerType !== "touch" && event.button !== 0) return;
      if (drag) return;
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
      // A subsequent independent click must never be blocked.
      if (suppressNextClick) setTimeout(() => { suppressNextClick = false; }, 0);
    }
    viewport.addEventListener("pointerup", finishDrag);
    viewport.addEventListener("pointercancel", finishDrag);
    viewport.addEventListener("click", event => {
      if (!suppressNextClick) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      suppressNextClick = false;
    }, true);
    viewport.addEventListener("keydown", event => {
      if (event.target !== viewport) return;
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      event.preventDefault();
      nav.classList.add("is-keyboard-paused");
      viewport.scrollLeft += event.key === "ArrowRight" ? 135 : -135;
    });
  }

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
        document.hidden) return;
    const limit = Math.max(0, viewport.scrollWidth - viewport.clientWidth);
    viewport.scrollLeft += pixelsPerSecond * elapsed / 1000;
    if (limit > 0 && viewport.scrollLeft >= limit - 1) {
      viewport.scrollLeft = 0;
    }
  }
  if (typeof window.requestAnimationFrame === "function" && viewport) {
    let lastFrame = 0;
    const tick = timestamp => {
      if (lastFrame) autoScroll(timestamp);
      else autoScroll.last = timestamp;
      lastFrame = timestamp;
      window.__marqueeDebug = {
        frames: (window.__marqueeDebug?.frames || 0) + 1,
        timestamp,
        scrollLeft: viewport.scrollLeft,
        matches: playback.matches,
        paused: ["is-hover-paused","is-touch-paused","is-keyboard-paused","is-drag-paused"].filter(c=>nav.classList.contains(c))
      };
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
    belt.style.setProperty("--keycap-start", viewportWidth + "px");
    if (!layoutInitialized && viewport) {
      // Start with the first original chapter in view rather than an empty screen.
      viewport.scrollLeft = viewportWidth + 14;
      layoutInitialized = true;
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
    } else {
      nav.classList.remove("is-enhanced");
      resumeAfterNavigation = false;
      setHoverPaused(false);
      setTouchPaused(false);
    }
    updateCurrent();
  }

  window.addEventListener("hashchange", () => {
    resumeAfterNavigation = true;
    setHoverPaused(false);
    setTouchPaused(false);
    updateCurrent();
  });
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
