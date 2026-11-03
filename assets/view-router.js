/* Shared early device routing for the six portfolio pages.
 * Canonical desktop URLs stay unchanged; ?view=desktop or ?view=mobile
 * explicitly selects a version and saves the visitor's preference.
 * ?view=auto clears that choice and restores device detection.
 */
(() => {
  "use strict";
  const variants = {
    "index.html": ["index.html", "mobile.html"],
    "mobile.html": ["index.html", "mobile.html"],
    "trend.html": ["trend.html", "mobile-trend.html"],
    "mobile-trend.html": ["trend.html", "mobile-trend.html"],
    "contact.html": ["contact.html", "mobile-contact.html"],
    "mobile-contact.html": ["contact.html", "mobile-contact.html"]
  };
  const current = window.location.pathname.split("/").pop() || "index.html";
  const pages = variants[current];
  if (!pages) return;

  const key = "portfolioPreferredView";
  const query = new URLSearchParams(window.location.search);
  const requested = query.get("view");
  let preferred = null;
  if (requested === "desktop" || requested === "mobile") {
    preferred = requested;
    try { window.localStorage.setItem(key, preferred); } catch (_) {}
  } else if (requested === "auto") {
    try { window.localStorage.removeItem(key); } catch (_) {}
  } else {
    try {
      const saved = window.localStorage.getItem(key);
      if (saved === "desktop" || saved === "mobile") preferred = saved;
    } catch (_) {}
  }

  const ua = window.navigator.userAgent || "";
  const phone = /iPhone|iPod|Android.*Mobile|Windows Phone|webOS|BlackBerry/i.test(ua)
    || Boolean(window.navigator.userAgentData && window.navigator.userAgentData.mobile)
    || (typeof window.matchMedia === "function"
        && window.matchMedia("(max-width: 767px) and (pointer: coarse)").matches);
  const destination = preferred === "mobile" || (!preferred && phone) ? pages[1] : pages[0];
  if (destination === current) return;

  const next = new URL(destination, window.location.href);
  next.search = window.location.search;
  next.hash = window.location.hash;
  if (requested === "auto") next.searchParams.delete("view");
  window.location.replace(next.href);
})();
