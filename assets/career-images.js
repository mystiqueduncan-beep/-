/* Progressive enhancement: never conceal photos until observation succeeds. */
(() => {
  'use strict';
  const init = () => {
    const photos = [...document.querySelectorAll('#career .career-photo[data-career-reveal]')];
    const show = figure => {
      figure.classList.remove('is-pending');
      figure.classList.add('is-visible');
    };
    let observer;
    const showAll = () => {
      observer?.disconnect();
      photos.forEach(show);
    };
    try {
      for (const figure of photos) {
        const img = figure.querySelector('img');
        if (!img) continue;
        const fail = () => figure.querySelector('.career-photo__frame')?.classList.add('image-load-failed');
        img.addEventListener('error', fail, { once: true });
        img.addEventListener('load', () => figure.querySelector('.career-photo__frame')?.classList.remove('image-load-failed'), { once: true });
        if (img.complete && img.naturalWidth === 0) fail();
      }
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
      if (!('IntersectionObserver' in window) || reduced.matches) { showAll(); return; }
      observer = new IntersectionObserver(entries => {
        try {
          for (const entry of entries) if (entry.isIntersecting && entry.intersectionRatio >= 0.15) {
            show(entry.target);
            observer.unobserve(entry.target);
          }
        } catch (_) { showAll(); }
      }, { threshold: 0.15 });
      // Read all positions before marking or observing any photo. Alternating
      // dataset/class writes and rectangle reads forces repeated synchronous layout.
      const initialPositions = [];
      const fold = window.innerHeight;
      for (const figure of photos) {
        if (figure.dataset.revealInitialized) continue;
        initialPositions.push({ figure, belowFold: figure.getBoundingClientRect().top >= fold });
      }
      for (const { figure, belowFold } of initialPositions) {
        figure.dataset.revealInitialized = 'true';
        if (belowFold) figure.classList.add('is-pending');
        else show(figure);
      }
      for (const { figure } of initialPositions) observer.observe(figure);
      document.addEventListener('focusin', event => {
        const figure = event.target.closest('.career-photo');
        if (figure) { show(figure); observer.unobserve(figure); }
      });
      reduced.addEventListener('change', event => { if (event.matches) showAll(); });
      window.addEventListener('beforeprint', showAll);
      window.addEventListener('pagehide', showAll, { once: true });
    } catch (_) { showAll(); }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
