/* Scroll-triggered photo reveal; visible without JavaScript and in reduced-motion mode. */
(() => {
  const init = () => {
    const photos = [...document.querySelectorAll('#career .career-photo[data-career-reveal]')];
    const show = element => element.classList.add('is-visible');
    for (const figure of photos) {
      const img = figure.querySelector('img');
      if (!img) continue;
      const markFailure = () => figure.querySelector('.career-photo__frame')?.classList.add('image-load-failed');
      img.addEventListener('error', markFailure, { once: true });
      if (img.complete && img.naturalWidth === 0) markFailure();
    }
    if (!('IntersectionObserver' in window)) { photos.forEach(show); return; }
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) if (entry.isIntersecting) {
        show(entry.target);
        observer.unobserve(entry.target);
      }
    }, { threshold: 0.1, rootMargin: '0px 0px -6% 0px' });
    photos.forEach(figure => observer.observe(figure));
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
