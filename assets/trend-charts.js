/* Animate the research chart only after its content area has entered view.
   Original HTML remains readable without scripting and with reduced motion. */
(() => {
  'use strict';
  const chart = document.querySelector('.channel-study');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (!chart || reduced.matches || !('IntersectionObserver' in window)) return;

  const fullyEntered = () => {
    const rect = chart.getBoundingClientRect();
    const viewport = document.documentElement.clientHeight || window.innerHeight;
    const bottom = viewport - Math.min(48, Math.max(20, viewport * 0.06));
    if (!rect.height || !rect.width) return false;
    if (rect.height <= bottom) return rect.top >= -1 && rect.bottom <= bottom + 1;
    const visible = Math.max(0, Math.min(rect.bottom, bottom) - Math.max(rect.top, 0));
    return visible >= bottom * 0.8;
  };

  let observer;
  let entered = false;
  let queued = false;
  const stopWatching = () => {
    observer?.disconnect();
    window.removeEventListener('scroll', scheduleCheck);
    window.removeEventListener('resize', scheduleCheck);
  };
  const finish = () => {
    stopWatching();
    chart.classList.remove('is-entering');
  };
  const check = () => {
    if (entered || !fullyEntered()) return;
    entered = true;
    stopWatching();
    chart.classList.add('is-entering');
    window.setTimeout(finish, 1750);
  };
  function scheduleCheck() {
    if (queued || entered) return;
    queued = true;
    window.requestAnimationFrame(() => {
      queued = false;
      check();
    });
  }
  try {
    observer = new IntersectionObserver(scheduleCheck, { threshold: 0 });
    observer.observe(chart);
    window.addEventListener('scroll', scheduleCheck, { passive: true });
    window.addEventListener('resize', scheduleCheck);
    scheduleCheck();
  } catch (_) { finish(); }
  reduced.addEventListener?.('change', event => { if (event.matches) finish(); });
  window.addEventListener('beforeprint', finish, { once: true });
})();
