/* One-time editorial motion: major chapters slide in, inner cards simply fade in.
   Contact/hero buttons keep their one-time pop. Reduced-motion/print/no-JS are safe. */
(() => {
  "use strict";
  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  if (!("IntersectionObserver" in window) || (reduced && reduced.matches)) return;

  const selectors = [
    ".mag-header > .container",
    ".source-verification",
    "main section",
    ".key-pillar-card",
    ".hero-action-card",
    "main .star-field-box",
    "main .stage-meta-box",
    "main .candidate-info-box",
    "main .candidate-specs-box",
    "main .timeline-job-card",
    "main .mobile-case-box",
    "main .pillar-mini-card",
    "main .contact-card-outer",
    "main .section-editorial-header",
    "main .mobile-card-title",
    "main #career > div > h2",
    "main .education-profile > h2",
    "main .editorial-card",
    "main .wide-star-case",
    "main .career-entry-card",
    "main .edu-dedicated-card",
    "main .stage-card",
    "main .research-summary-panel",
    "main .contact-action-panel",
    "main .feature-card",
    "main .metric-tile",
    "main .case-box",
    "main .content-article-box",
    "main .mobile-subcard",
    "main .adv-dim-card",
    "main .stage-card-mini"
  ];
  const targets = [...new Set(document.querySelectorAll(selectors.join(",")))];
  const contactMethods = [...document.querySelectorAll("main .contact-methods-stack > .method-card, main > section .method-card")];
  // Pop-in is reserved for action controls, not narrative content.
  const heroActions = [...document.querySelectorAll(".hero-cta-group > .mag-btn, .mobile-hero-actions > a, .mobile-hero-actions > button")];
  // Move only headline units: full sections and narrative cards fade in place.
  // Contact/hero actions retain their one-time pop.
  const chapterSelector = ".mag-header > .container, main .section-editorial-header, main .mobile-card-title, main #career > div > h2, main .education-profile > h2";
  const allTargets = [...new Set([...targets, ...contactMethods, ...heroActions])];
  if (!allTargets.length) return;

  // Reveal as soon as about 15% of a unit is visible; do not wait for an
  // entire section to enter. A 32px minimum avoids triggering on a tiny peek.
  // Anything scrolled past is permanently exposed for easy reverse reading.
  const hasEnteredEnough = el => {
    const rect = el.getBoundingClientRect();
    const viewportHeight = document.documentElement.clientHeight || window.innerHeight;
    const visibleBottom = viewportHeight - Math.min(48, Math.max(20, viewportHeight * 0.06));
    if (!rect.width || !rect.height || visibleBottom <= 0) return false;
    if (rect.bottom <= 0) return true;
    const visibleHeight = Math.max(0, Math.min(rect.bottom, visibleBottom) - Math.max(rect.top, 0));
    const requiredHeight = Math.min(rect.height, Math.max(32, Math.min(rect.height, visibleBottom) * 0.15));
    return visibleHeight >= requiredHeight;
  };
  const pending = new Set();
  let observer;
  let scheduled = false;
  let listening = false;
  const detachChecks = () => {
    if (!listening) return;
    listening = false;
    window.removeEventListener("scroll", scheduleCheck);
    window.removeEventListener("resize", scheduleCheck);
    window.removeEventListener("pageshow", scheduleCheck);
  };
  const reveal = el => {
    el.classList.remove("mk-motion-pending", "mk-pop-pending");
    el.classList.add(el.classList.contains("mk-pop-item") ? "mk-pop-in" : "mk-motion-in");
    pending.delete(el);
    observer?.unobserve?.(el);
    if (!pending.size) detachChecks();
  };
  const checkPending = () => {
    // Read all positions first; write classes afterwards to avoid layout thrashing.
    const ready = [...pending].filter(hasEnteredEnough);
    ready.forEach(reveal);
  };
  function scheduleCheck() {
    if (scheduled || !pending.size) return;
    scheduled = true;
    window.requestAnimationFrame(() => {
      scheduled = false;
      checkPending();
    });
  }

  try {
    observer = new IntersectionObserver(() => scheduleCheck(), { threshold: 0 });
  } catch (_) { return; }

  // Establish the pending pose before starting any observation.
  const toObserve = allTargets.filter(el => {
    if (el.closest('[hidden], [aria-hidden="true"]')) return false;
    const box = el.getBoundingClientRect();
    return box.width > 0 && box.height > 0;
  });
  for (const el of toObserve) {
    const heroIndex = heroActions.indexOf(el);
    const isPopItem = contactMethods.includes(el) || heroIndex !== -1;
    el.classList.add(isPopItem ? "mk-pop-item" : "mk-motion-item");
    // A fade remains part of the same one-time observer/focus/anchor lifecycle.
    // This prevents nested elements from sliding repeatedly inside a chapter.
    if (!isPopItem && !el.matches(chapterSelector)) el.classList.add("mk-fade-item");
    el.classList.add(isPopItem ? "mk-pop-pending" : "mk-motion-pending");
    pending.add(el);
  }
  try {
    for (const el of toObserve) observer.observe(el);
  } catch (_) {
    observer.disconnect();
    allTargets.forEach(reveal);
    return;
  }

  // Scroll checks allow early one-time reveal even when the observer callback
  // fires before the 15% entrance threshold is reached.
  if (pending.size) {
    window.addEventListener("scroll", scheduleCheck, { passive: true });
    window.addEventListener("resize", scheduleCheck, { passive: true });
    window.addEventListener("pageshow", scheduleCheck);
    listening = true;
    scheduleCheck();
  }

  const revealEverything = () => {
    observer.disconnect();
    allTargets.forEach(reveal);
    detachChecks();
  };

  // Reveal the focused item and any hidden ancestors so keyboard users never
  // land inside content that is still visually concealed.
  const revealFocusedAncestors = target => {
    let pending = target.closest(".mk-motion-pending, .mk-pop-pending");
    while (pending) {
      reveal(pending);
      observer.unobserve(pending);
      pending = target.parentElement?.closest(".mk-motion-pending, .mk-pop-pending") || null;
    }
  };
  document.addEventListener("focusin", event => {
    revealFocusedAncestors(event.target);
  });
  const revealHashTarget = () => {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); }
    catch (_) { return; }
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    revealFocusedAncestors(target);
  };
  window.addEventListener("hashchange", revealHashTarget);
  revealHashTarget();
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
