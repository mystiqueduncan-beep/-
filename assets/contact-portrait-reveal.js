/* Start the contact portrait fade only after the photograph enters view.
   Reveal once, never reset on scrolling; image stays visible when motion is reduced. */
(() => {
  "use strict";
  const image = document.querySelector("body.page-contact .photo-frame img.contact-portrait-photo");
  if (!image) {
    document.documentElement.classList.remove("portrait-reveal-js");
    return;
  }
  window.__portraitObserverInitialized = true;
  let shown = false;
  let observer = null;
  const reveal = () => {
    if (shown) return;
    shown = true;
    image.classList.add("portrait-in-view");
    if (observer) observer.disconnect();
  };
  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reduced && reduced.matches) {
    reveal();
    return;
  }
  const start = () => {
    if (image.complete && image.naturalWidth > 0) { reveal(); return; }
    if (typeof image.decode === "function") {
      try { image.decode().then(reveal).catch(reveal); }
      catch (_) { reveal(); }
    } else if (image.complete) {
      reveal();
    } else {
      image.addEventListener("load",reveal,{once:true});
      image.addEventListener("error",reveal,{once:true});
    }
  };
  if (!("IntersectionObserver" in window)) {
    start();
    return;
  }
  try {
    observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) start();
    }, {threshold:0.1,rootMargin:"0px 0px -24px 0px"});
    observer.observe(image);
  } catch (_) { start(); }
  if (reduced) {
    const change = event => { if (event.matches) reveal(); };
    if (typeof reduced.addEventListener === "function") reduced.addEventListener("change",change);
    else if (typeof reduced.addListener === "function") reduced.addListener(change);
  }
  window.addEventListener("beforeprint",reveal,{once:true});
})();
