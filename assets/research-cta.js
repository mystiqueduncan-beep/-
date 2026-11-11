/* Research link pop: once when visible, followed by gentle perpetual rose glow.
   Progressive enhancement: links remain usable without JS/IntersectionObserver.
   Navigation, hrefs and existing section/marquee animations remain untouched. */
(() => {
  "use strict";
  const selector = 'a[href="trend.html"], a[href="mobile-trend.html"]';
  const links = [...document.querySelectorAll(selector)].filter(link =>
    !link.closest('[hidden], [aria-hidden="true"]')
  );
  if (!links.length) return;
  for (const link of links) {
    if (!link.querySelector(".research-meteor")) {
      const meteor = document.createElement("span");
      meteor.className = "research-meteor";
      meteor.setAttribute("aria-hidden", "true");
      link.appendChild(meteor);
    }
  }
  const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)");
  if (!("IntersectionObserver" in window) || reduced?.matches) return;

  const pending = new Set();
  let observer;
  const reveal = link => {
    link.classList.remove("research-pop-wait");
    link.classList.add("research-pop-in");
    pending.delete(link);
    observer?.unobserve(link);
  };
  try {
    observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting) reveal(entry.target);
      }
    }, { threshold: 0.2, rootMargin: "0px 0px -5% 0px" });
    for (const link of links) {
      link.classList.add("research-pop-wait");
      pending.add(link);
      observer.observe(link);
    }
  } catch (_) {
    observer?.disconnect();
    links.forEach(reveal);
    return;
  }
  // Keep keyboard and accessibility actions operable even before scroll entry.
  document.addEventListener("focusin", event => {
    const link = event.target.closest?.(selector);
    if (link && pending.has(link)) reveal(link);
  });
  const revealAll = () => {
    links.forEach(reveal);
    observer?.disconnect();
  };
  window.addEventListener("beforeprint", revealAll);
  if (reduced) {
    const onChange = event => { if (event.matches) revealAll(); };
    if (reduced.addEventListener) reduced.addEventListener("change", onChange);
    else reduced.addListener?.(onChange);
  }
})();