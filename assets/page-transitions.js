/* Progressive enhancement: smooth site-wide page transitions between internal pages.
 * Supports native View Transitions (Chrome/Edge) and provides lightweight fallback (Safari/Firefox).
 * Strictly preserves reduced-motion, bfcache, and internal anchor navigation.
 */
(() => {
  "use strict";

  // Check reduced motion preference
  const reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reducedMotion && reducedMotion.matches) {
    return;
  }

  // If native cross-document view transitions are supported by the browser,
  // the browser engine natively runs @view-transition in CSS.
  // We only enable JS click interception fallback on browsers lacking native cross-document transitions.
  const hasNativeCrossDocVT = ("onpageswap" in window) && ("onpagereveal" in window);
  if (hasNativeCrossDocVT) {
    return;
  }

  // Enable fallback styling on <html>
  document.documentElement.classList.add("page-trans-fallback");

  // Safeguard: always clear exiting state on pageshow (e.g. bfcache, back/forward)
  window.addEventListener("pageshow", () => {
    document.body.classList.remove("is-page-exiting");
  });

  window.addEventListener("pagehide", () => {
    document.body.classList.remove("is-page-exiting");
  });

  function isSamePageAnchor(targetUrl) {
    const curPath = window.location.pathname.replace(/\/index\.html$/, "/");
    const tgtPath = targetUrl.pathname.replace(/\/index\.html$/, "/");
    return curPath === tgtPath && targetUrl.search === window.location.search;
  }

  document.addEventListener("click", (event) => {
    if (event.defaultPrevented) return;
    if (event.button !== 0) return; // Only primary (left) click
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return; // Allow new tab/window

    const link = event.target.closest("a");
    if (!link || !link.href) return;

    // Do not intercept links configured to open in new tab/window
    if (link.target && link.target !== "_self") return;

    // Do not intercept file downloads
    if (link.hasAttribute("download")) return;

    let targetUrl;
    try {
      targetUrl = new URL(link.href, window.location.href);
    } catch (_) {
      return;
    }

    // Only handle http and https
    if (targetUrl.protocol !== "http:" && targetUrl.protocol !== "https:") return;

    // Must be same origin
    if (targetUrl.origin !== window.location.origin) return;

    // In-page hash anchors (e.g. #career, #contact) must NOT trigger page transition!
    if (isSamePageAnchor(targetUrl)) return;

    // Perform smooth fade-out and navigate
    event.preventDefault();
    document.body.classList.add("is-page-exiting");

    const destination = targetUrl.href;
    let navigated = false;
    const navigate = () => {
      if (!navigated) {
        navigated = true;
        window.location.href = destination;
      }
    };

    // 400ms matches the fade-out duration
    setTimeout(navigate, 400);

    // Fallback safety timeout: restore if navigation did not proceed
    setTimeout(() => {
      document.body.classList.remove("is-page-exiting");
    }, 2000);
  });
})();
