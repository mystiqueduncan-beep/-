/* Progressive enhancement: original nine chapter links remain functional without JS. */
(() => {
  "use strict";
  const nav = document.querySelector("[data-keycap-marquee]");
  if (!nav || typeof window.matchMedia !== "function") return;

  const belt = nav.querySelector(".keycap-marquee__belt");
  const original = nav.querySelector(".keycap-marquee__group");
  if (!belt || !original) return;

  // Avoid playing under reduced motion, on small screens and with touch pointers.
  const playback = window.matchMedia(
    "(min-width: 769px) and (hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)"
  );
  let duplicate = null;

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

  function syncMode() {
    if (playback.matches) {
      if (!duplicate) {
        duplicate = original.cloneNode(true);
        duplicate.classList.add("keycap-marquee__group--duplicate");
        duplicate.setAttribute("aria-hidden", "true");
        duplicate.setAttribute("inert", "");
        duplicate.querySelectorAll("a").forEach((link) => {
          link.setAttribute("tabindex", "-1");
          link.removeAttribute("aria-current");
        });
        belt.appendChild(duplicate);
      }
      const distance = original.getBoundingClientRect().width + 14;
      belt.style.setProperty("--keycap-duration", Math.max(38, Math.min(90, distance / 38)).toFixed(1) + "s");
      nav.classList.add("is-enhanced");
    } else {
      if (duplicate) {
        duplicate.remove();
        duplicate = null;
      }
      nav.classList.remove("is-enhanced");
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
      if (playback.matches) {
        const distance = original.getBoundingClientRect().width + 14;
        belt.style.setProperty("--keycap-duration", Math.max(38, Math.min(90, distance / 38)).toFixed(1) + "s");
      }
    }).observe(original);
  }
  syncMode();
})();
