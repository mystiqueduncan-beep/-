/* Visibility is the default; initialize the observer before hiding photos. */
(() => {
  const init = () => {
    const photos = [...document.querySelectorAll('#career .career-photo[data-career-reveal]')];
    const show = element => { element.classList.add('is-visible'); element.classList.remove('is-pending'); };
    for (const figure of photos) {
      const img = figure.querySelector('img');
      if (!img) continue;
      const frame = figure.querySelector('.career-photo__frame');
      const markFailure = () => frame?.classList.add('image-load-failed');
      img.addEventListener('error', markFailure, { once: true });
      img.addEventListener('load', () => frame?.classList.remove('image-load-failed'), { once: true });
      if (img.complete && img.naturalWidth === 0) markFailure();
    }
    if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let observer;
    try {
      observer = new IntersectionObserver(entries => {
        for (const entry of entries) if (entry.isIntersecting) {
          show(entry.target);
          observer.unobserve(entry.target);
        }
      }, { threshold: 0.1 });
      for (const figure of photos) {
        observer.observe(figure);
        figure.classList.add('is-pending');
      }
    } catch (_) {
      observer?.disconnect();
      photos.forEach(show);
    }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();

