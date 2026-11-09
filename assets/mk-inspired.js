/* One-time left-to-right section reveals after a content unit fully enters the viewport.
   Content stays visible if this script fails, JavaScript is disabled, or reduced motion is preferred. */
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
  const allTargets = [...new Set([...targets, ...contactMethods])];
  if (!allTargets.length) return;

  // A brief glimpse at the bottom of the screen must not trigger the entrance.
  // Compact blocks wait until their entire height is in the visible viewport.
  // Sections taller than a screen cannot fit fully; reveal after they cover 80%
  // of the usable screen height, on both desktop and mobile.
  const hasFullyEntered = el => {
    const rect = el.getBoundingClientRect();
    const viewportHeight = document.documentElement.clientHeight || window.innerHeight;
    const visibleBottom = viewportHeight - Math.min(48, Math.max(20, viewportHeight * 0.06));
    const usableHeight = visibleBottom;
    if (!rect.width || !rect.height || usableHeight <= 0) return false;
    if (rect.height <= usableHeight) {
      return rect.top >= -1 && rect.bottom <= visibleBottom + 1;
    }
    const visibleHeight = Math.max(0, Math.min(rect.bottom, visibleBottom) - Math.max(rect.top, 0));
    return visibleHeight >= usableHeight * 0.8;
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
    observer?.unobserve(el);
    if (!pending.size) detachChecks();
  };
  const checkPending = () => {
    // Read all positions first; write classes afterwards to avoid layout thrashing.
    const ready = [...pending].filter(hasFullyEntered);
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
    const isContactMethod = contactMethods.includes(el);
    el.classList.add(isContactMethod ? "mk-pop-item" : "mk-motion-item");
    el.classList.add(isContactMethod ? "mk-pop-pending" : "mk-motion-pending");
    pending.add(el);
  }
  try {
    for (const el of toObserve) observer.observe(el);
  } catch (_) {
    observer.disconnect();
    allTargets.forEach(reveal);
    return;
  }

  // Scroll checks are essential: intersection alone fires too early, and does
  // not fire again as a partially visible block becomes fully visible.
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
