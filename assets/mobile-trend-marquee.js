(() => {
  const nav = document.querySelector('[data-mobile-keycap-marquee]');
  if (!nav) return;
  const belt = nav.querySelector('.mobile-keycap-belt');
  const group = nav.querySelector('.mobile-keycap-group');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  if (!belt || !group || reduce.matches) return;
  const copy = group.cloneNode(true);
  copy.setAttribute('aria-hidden', 'true');
  copy.setAttribute('inert', '');
  copy.classList.add('mobile-keycap-group--duplicate');
  copy.querySelectorAll('a').forEach(a => a.tabIndex = -1);
  belt.appendChild(copy);
  nav.classList.add('is-mobile-auto');
  const stop = () => {
    nav.classList.remove('is-mobile-auto');
    copy.remove();
  };
  nav.addEventListener('pointerdown', stop, {once:true, passive:true});
  nav.addEventListener('touchstart', stop, {once:true, passive:true});
  nav.addEventListener('wheel', stop, {once:true, passive:true});
  nav.addEventListener('keydown', stop, {once:true});
  reduce.addEventListener?.('change', stop);
})();