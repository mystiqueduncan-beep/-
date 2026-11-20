/* Calm editorial chapter navigation.
   Desktop: stationary wrapping list; mobile: user-controlled horizontal scroll.
   No autoplay, duplicate links, simulated drag, hidden spacer or timed motion.
   The current chapter keeps a non-moving, accessible visual indicator. */
(() => {
  "use strict";

  function init() {
    const nav = document.querySelector("[data-keycap-marquee]");
    if (!nav) return;
    const viewport = nav.querySelector(".keycap-marquee__viewport");
    const list = nav.querySelector(".keycap-marquee__group");
    if (!viewport || !list) return;

    const links = [...list.querySelectorAll('a[href^="#"]')];
    const entries = links.map(link => {
      const id = decodeURIComponent(link.getAttribute("href").slice(1));
      const section = document.getElementById(id);
      return section ? {link, section, hash:"#" + id} : null;
    }).filter(Boolean);
    if (!entries.length) return;

    // The original anchor list is always visible without scripting. Do not
    // duplicate nodes or auto-scroll the navigation to the selected link.
    nav.classList.remove(
      "is-enhanced", "is-hover-paused", "is-keyboard-paused",
      "is-touch-paused", "is-drag-paused", "is-chapter-paused", "is-scrubbing"
    );
    nav.classList.add("is-static-nav");
    const mobile = document.body.classList.contains("page-mobile");
    const navName = document.body.classList.contains("page-trend") ? "專題章節導覽" : "履歷章節導覽";
    const shell = nav.closest("nav");
    if (shell?.getAttribute("aria-label")?.includes("跑馬燈")) {
      shell.setAttribute("aria-label",navName);
    }
    function syncViewportSemantics() {
      const manual = mobile || window.innerWidth <= 720;
      if (manual) {
        viewport.setAttribute("tabindex","0");
        viewport.setAttribute("aria-label",navName+"，可用手指或鍵盤左右滑動");
      } else {
        // A stationary, non-focusable desktop wrapper is purely structural.
        // Never leave aria-label on a generic div without a supported role.
        viewport.removeAttribute("tabindex");
        viewport.removeAttribute("aria-label");
      }
    }
    syncViewportSemantics();
    window.addEventListener("resize",syncViewportSemantics,{passive:true});

    function currentChapter() {
      const shell = nav.closest(".mag-subnav-strip,.bilingual-mobile-strip,.trend-subnav-strip");
      const bottom = shell?.getBoundingClientRect().bottom || 0;
      const readingLine = Math.max(bottom + 20, Math.min(window.innerHeight * .32, 330));
      let index = 0;
      for (let i = 0; i < entries.length; i++) {
        if (entries[i].section.getBoundingClientRect().top <= readingLine) index = i;
        else break;
      }
      const first = entries[0].section.getBoundingClientRect();
      const last = entries[entries.length - 1].section.getBoundingClientRect();
      const reading = first.top <= readingLine && last.bottom > readingLine;
      nav.classList.toggle("is-reading-section", reading);
      return entries[index].hash;
    }

    let requested = false;
    function updateCurrent() {
      requested = false;
      const current = currentChapter();
      for (const item of entries) {
        const selected = item.hash === current;
        item.link.classList.toggle("is-current",selected);
        if (selected) item.link.setAttribute("aria-current","location");
        else item.link.removeAttribute("aria-current");
      }
      // Intentionally no scrollIntoView/scrollLeft: the user controls the strip.
    }
    function schedule() {
      if (requested) return;
      requested = true;
      requestAnimationFrame(updateCurrent);
    }

    window.addEventListener("scroll", schedule, {passive:true});
    window.addEventListener("resize", schedule, {passive:true});
    window.addEventListener("hashchange", schedule);
    // A click follows the native real link; only the active highlight changes.
    list.addEventListener("click", schedule);
    viewport.addEventListener("keydown", event => {
      if (event.target !== viewport || !["ArrowLeft","ArrowRight"].includes(event.key)) return;
      if (viewport.scrollWidth <= viewport.clientWidth) return;
      event.preventDefault();
      viewport.scrollLeft += event.key === "ArrowRight" ? 150 : -150;
    });
    updateCurrent();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, {once:true});
  } else {
    init();
  }
})();
