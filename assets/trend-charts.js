/* Animate visible content once. Static HTML remains complete if enhancement fails. */
(() => {
  'use strict';
  const chart = document.querySelector('.channel-study');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (!chart || reduced.matches || !('IntersectionObserver' in window)) return;
  let observer;
  const finish = () => {
    observer?.disconnect();
    chart.classList.remove('is-entering');
  };
  try {
    observer = new IntersectionObserver(entries => {
      if (!entries.some(entry => entry.isIntersecting)) return;
      observer.disconnect();
      // Keep section reveals intact; animate only this chart's child elements.
      chart.classList.add('is-entering');
      window.setTimeout(finish, 800);
    }, { threshold: 0, rootMargin: '0px 0px -24px 0px' });
    observer.observe(chart);
  } catch (_) { finish(); }
  reduced.addEventListener?.('change', event => { if (event.matches) finish(); });
  window.addEventListener('beforeprint', finish, { once: true });
})();
