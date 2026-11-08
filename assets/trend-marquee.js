/* Progressive enhancement: original chapter links remain functional without JS. */
(() => {
  "use strict";
  const nav = document.querySelector("[data-keycap-marquee]");
  if (!nav || typeof window.matchMedia !== "function") return;

  const belt = nav.querySelector(".keycap-marquee__belt");
  const original = nav.querySelector(".keycap-marquee__group");
  if (!belt || !original) return;
  const isHomepage = typeof nav.closest === "function" && Boolean(nav.closest(".home-keycap-strip"));

  // Respect user preference for reduced motion across desktop, tablet and mobile.
  const playback = window.matchMedia("(prefers-reduced-motion: no-preference)");
  let duplicate = null;
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
      if (viewport) viewport.scrollLeft = 0;
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
    // Duplicates accept pointer clicks without becoming hidden focus targets.
    if (link && link.closest('[aria-hidden="true"]')) event.preventDefault();
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

  if (viewport) {
    viewport.addEventListener("scroll", () => {
      if (touchResumeTimer) clearTimeout(touchResumeTimer);
      touchResumeTimer = setTimeout(() => {
        setTouchPaused(false);
      }, 1200);
    }, { passive: true });
  }

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

  // Only hovering an actual chapter key pauses. Blank space in the strip does not.
  nav.addEventListener("pointerover", (event) => {
    if (mousePointer(event) && chapterLink(event.target)) setHoverPaused(true);
  });
  nav.addEventListener("pointerout", (event) => {
    if (mousePointer(event) && chapterLink(event.target) && !chapterLink(event.relatedTarget)) {
      setHoverPaused(false);
    }
  });
  nav.addEventListener("pointerleave", () => {
    resumeAfterNavigation = false;
    setHoverPaused(false);
  });
  nav.addEventListener("pointermove", (event) => {
    if (!mousePointer(event) || !resumeAfterNavigation) return;
    resumeAfterNavigation = false;
    setHoverPaused(Boolean(chapterLink(event.target)));
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
      if (link.closest('[aria-hidden="true"]')) {
        link.removeAttribute("aria-current");
      } else if (selected) {
        link.setAttribute("aria-current", "location");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  }

  // The homepage deliberately uses one group of links. It moves out and back
  // rather than cloning links for a seamless one-way loop.
  // Other pages retain their existing, independently verified marquee behavior.
  function updateTravel() {
    if (isHomepage) {
      const travel = viewport ? Math.max(0, Math.ceil(original.scrollWidth - viewport.clientWidth)) : 0;
      belt.style.setProperty("--keycap-home-offset", "-" + travel + "px");
      belt.style.setProperty("--keycap-duration", Math.max(14, Math.min(45, travel / 22)).toFixed(1) + "s");
      nav.classList.toggle("is-home-animated", travel > 1);
    } else {
      const distance = original.getBoundingClientRect().width + 14;
      belt.style.setProperty("--keycap-duration", Math.max(48, Math.min(115, distance / 30)).toFixed(1) + "s");
    }
  }

  function syncMode() {
    if (playback.matches) {
      if (!isHomepage && !duplicate) {
        duplicate = original.cloneNode(true);
        duplicate.classList.add("keycap-marquee__group--duplicate");
        duplicate.setAttribute("aria-hidden", "true");
        duplicate.querySelectorAll("a").forEach((link) => {
          link.setAttribute("tabindex", "-1");
          link.removeAttribute("aria-current");
        });
        belt.appendChild(duplicate);
      }
      updateTravel();
      nav.classList.add("is-enhanced");
    } else {
      if (duplicate) {
        duplicate.remove();
        duplicate = null;
      }
      nav.classList.remove("is-enhanced", "is-home-animated");
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
    const observer = new ResizeObserver(() => {
      if (playback.matches) updateTravel();
    });
    observer.observe(original);
    if (isHomepage && viewport) observer.observe(viewport);
  }
  syncMode();
})();
