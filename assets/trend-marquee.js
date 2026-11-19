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
  // Cache between change events; frame/layout reads must not consume a
  // pending media change before its listener synchronizes the scroll geometry.
  let playbackAllowed = playback.matches;
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
      scheduleCurrent();
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
    nav.classList.toggle("is-touch-paused", Boolean(paused) && playbackAllowed);
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
    nav.classList.toggle("is-hover-paused", hovering && playbackAllowed);
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

  // The highlighted key follows the section being read, not only the URL hash.
  // The same original six links power both desktop and mobile marquees.
  const chapterTargets = [];
  if (typeof document.getElementById === "function") {
    nav.querySelectorAll('.keycap-marquee__group a[href^="#"]').forEach(link => {
      const hash = link.getAttribute("href");
      const section = document.getElementById(hash.slice(1));
      if (section) chapterTargets.push({ hash, section, link });
    });
  }

  let lockedChapter = null;
  let positionedChapter = null;
  function activeChapterState() {
    if (!chapterTargets.length) return { active: window.location.hash || null, reading: false };
    const sticky = nav.closest(".mag-subnav-strip,.bilingual-mobile-strip,.trend-subnav-strip");
    const stickyBottom = sticky ? sticky.getBoundingClientRect().bottom : 0;
    // A new chapter becomes current when its heading reaches the reading line,
    // below the sticky header, rather than after its whole section is scrolled.
    const readingLine = Math.max(stickyBottom + 20, Math.min(window.innerHeight * .32, 330));
    let active = chapterTargets[0].hash;
    for (const entry of chapterTargets) {
      if (entry.section.getBoundingClientRect().top <= readingLine) active = entry.hash;
      else break;
    }
    const first = chapterTargets[0].section.getBoundingClientRect();
    const last = chapterTargets[chapterTargets.length - 1].section.getBoundingClientRect();
    const reading = stickyBottom >= 0 && stickyBottom < window.innerHeight &&
      first.top <= readingLine && last.bottom > readingLine;
    return { active, reading };
  }

  // The frame fades only when the sticky bar overlaps the chapter content.
  // Reading ends when the final chapter passes above the sticky bar.
  function updateReadingBackground() {
    if (!chapterTargets.length) return;
    const frame = nav.getBoundingClientRect();
    const first = chapterTargets[0].section.getBoundingClientRect();
    const last = chapterTargets[chapterTargets.length - 1].section.getBoundingClientRect();
    nav.classList.toggle("is-reading-section",
      first.top <= frame.bottom + 1 && last.bottom > frame.top);
  }

  function updateCurrent() {
    // Read chapter geometry before writing any visual or accessibility state.
    const { active, reading } = activeChapterState();
    updateReadingBackground();
    const nextLock = reading ? active : null;
    if (nextLock !== lockedChapter) {
      lockedChapter = nextLock;
      positionedChapter = null;
    }
    nav.classList.toggle("is-chapter-paused", Boolean(lockedChapter));
    if (!lockedChapter) belt.style.removeProperty?.("padding-inline-end");
    nav.querySelectorAll('.keycap-marquee__group a[href^="#"]').forEach(link => {
      const selected = link.getAttribute("href") === active;
      link.classList.toggle("is-current", selected);
      const current = link.getAttribute("aria-current");
      if (selected && current !== "location") link.setAttribute("aria-current", "location");
      else if (!selected && current !== null) link.removeAttribute("aria-current");
    });
    alignLockedChapter();
  }

  // Align once on each chapter entry. A manual drag remains exactly where
  // the reader left it until entering a different chapter. Never fight input.
  function alignLockedChapter() {
    if (!viewport || !lockedChapter || lockedChapter === positionedChapter || drag) return;
    const link = chapterTargets.find(entry => entry.hash === lockedChapter)?.link;
    if (!link) return;
    if (nav.classList.contains("is-keyboard-paused") && document.activeElement &&
        document.activeElement !== link && nav.contains(document.activeElement)) return;
    // Reduced motion suppresses the decorative trailing interval. Reserve
    // sufficient blank scroll range so the final key can also align fully.
    if (!playbackAllowed || nav.classList.contains("is-keyboard-paused")) {
      belt.style.setProperty("padding-inline-end", viewport.clientWidth + "px");
    }
    const inset = Math.max(14, Math.ceil(viewport.clientWidth * .035) + 4);
    const left = link.getBoundingClientRect().left - viewport.getBoundingClientRect().left;
    viewport.scrollLeft = Math.max(0, viewport.scrollLeft + left - inset);
    positionedChapter = lockedChapter;
    fractionalScroll = viewport.scrollLeft;
  }

  let currentRaf = 0;
  function scheduleCurrent() {
    if (currentRaf) return;
    currentRaf = window.requestAnimationFrame(() => {
      currentRaf = 0;
      updateCurrent();
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
      scheduleCurrent();
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
      scheduleCurrent();
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
    if (!viewport || !playbackAllowed || !nav.classList.contains("is-enhanced")) return;
    if (!autoScroll.last) { autoScroll.last = timestamp; return; }
    const elapsed = Math.min(60, Math.max(0, timestamp - autoScroll.last));
    autoScroll.last = timestamp;
    if (nav.classList.contains("is-chapter-paused") ||
        nav.classList.contains("is-hover-paused") ||
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
  function updateFrameWidth() {
    // Match the primary chapter's actual outer width, independent of key count.
    const chapter = chapterTargets[0]?.section;
    const width = chapter?.getBoundingClientRect().width;
    if (Number.isFinite(width) && width > 0) {
      const value = Math.floor(width * 100) / 100 + "px";
      nav.style.setProperty("--portfolio-chapter-width", value);
      nav.style.setProperty("--keycap-content-width", value);
    } else {
      nav.style.setProperty("--keycap-content-width", Math.ceil(original.getBoundingClientRect().width + 24) + "px");
    }
  }

  function updateDuration() {
    updateFrameWidth();
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

  function updateLayout() {
    if (playbackAllowed && nav.classList.contains("is-enhanced")) updateDuration();
    else updateFrameWidth();
  }

  function syncMode() {
    positionedChapter = null;
    belt.style.removeProperty?.("padding-inline-end");
    if (playbackAllowed) {
      nav.classList.add("is-enhanced");
      layoutInitialized = false;
      fractionalScroll = null;
      updateDuration();
      nav.classList.toggle("is-hover-paused", hovering);
    } else {
      nav.classList.remove("is-enhanced");
      nav.classList.remove("is-hover-paused");
      setTouchPaused(false);
      layoutInitialized = false;
      fractionalScroll = null;
      updateFrameWidth();
    }
    updateCurrent();
  }

  window.addEventListener("hashchange", () => { updateCurrent(); scheduleCurrent(); });
  window.addEventListener("scroll", scheduleCurrent, { passive: true });
  window.addEventListener("resize", scheduleCurrent);
  function syncPlayback() {
    playbackAllowed = playback.matches;
    syncMode();
  }
  if (typeof playback.addEventListener === "function") {
    playback.addEventListener("change", syncPlayback);
  } else if (typeof playback.addListener === "function") {
    playback.addListener(syncPlayback);
  }
  if (typeof ResizeObserver !== "undefined") {
    const resizeObserver = new ResizeObserver(updateLayout);
    resizeObserver.observe(original);
    if (viewport) resizeObserver.observe(viewport);
    if (chapterTargets[0]?.section) resizeObserver.observe(chapterTargets[0].section);
  }
  window.addEventListener("resize", updateLayout);
  syncMode();
})();
