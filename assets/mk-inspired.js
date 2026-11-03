/* Section entrances for the personal portfolio, inspired by storefront editorial pacing.
   No copy/images modified. Nothing is hidden if this script fails or JS is disabled. */
(() => {
  "use strict";
  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  if (!("IntersectionObserver" in window) || (reduced && reduced.matches)) return;

  const selectors = [
    "main .section-editorial-header",
    "main .editorial-card",
    "main .wide-star-case",
    "main .career-entry-card",
    "main .edu-dedicated-card",
    "main .stage-card",
    "main .research-summary-panel",
    "main .contact-action-panel",
    "main .feature-card",
    "main .case-box",
    "main .content-article-box",
    "main .contact-card-outer",
    "main .method-card",
    "main.mobile-content > .mobile-card",
    "main.mobile-content > .timeline-job-card",
    "main.mobile-content > .mobile-trend-banner",
    "main.mobile-content > .edu-card-mobile",
    "main.mobile-content > .mobile-case-box"
  ];
  const targets = [...document.querySelectorAll(selectors.join(","))];
  if (!targets.length) return;

  const reveal = (el) => {
    el.classList.remove("mk-motion-pending");
    el.classList.add("mk-motion-in");
  };

  const observer = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        reveal(entry.target);
        observer.unobserve(entry.target);
      }
    }
  }, { threshold: 0.04, rootMargin: "0px 0px -35px 0px" });

  let pending = 0;
  for (const el of targets) {
    if (el.closest('[hidden], [aria-hidden="true"]')) continue;
    const box = el.getBoundingClientRect();
    if (box.width === 0 || box.height === 0) continue;
    // Never conceal the first screen, focused elements, or anchor-linked content.
    if (box.top < window.innerHeight * 0.87 ||
        el.matches(":target") || el.contains(document.activeElement)) continue;
    el.classList.add("mk-motion-item", "mk-motion-pending");
    observer.observe(el);
    pending++;
  }
  if (!pending) return;

  const revealEverything = () => {
    observer.disconnect();
    targets.forEach(reveal);
  };

  // Keyboard users should never navigate to visually concealed content.
  document.addEventListener("focusin", event => {
    const target = event.target.closest(".mk-motion-pending");
    if (target) {
      reveal(target);
      observer.unobserve(target);
    }
  });
  window.addEventListener("hashchange", () => {
    const id = decodeURIComponent(location.hash.slice(1));
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    const parent = target.closest(".mk-motion-pending");
    if (parent) {
      reveal(parent);
      observer.unobserve(parent);
    }
    if (target.classList.contains("mk-motion-pending")) {
      reveal(target);
      observer.unobserve(target);
    }
  });
  window.addEventListener("beforeprint", revealEverything, { once: true });
  window.addEventListener("pagehide", revealEverything, { once: true });
  if (reduced) {
    if (reduced.addEventListener) reduced.addEventListener("change", event => {
      if (event.matches) revealEverything();
    });
    else if (reduced.addListener) reduced.addListener(event => {
      if (event.matches) revealEverything();
    });
  }
})();
