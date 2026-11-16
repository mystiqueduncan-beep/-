/* Shared chapter status for the approved pastel bilingual desktop/mobile navigation. */
(() => {
  'use strict';
  const nav = document.querySelector('[data-bilingual-nav]');
  if (!nav) return;
  const links = Array.from(nav.querySelectorAll('a[data-chapter]'));
  const chapters = links.map(link => ({link, section:document.getElementById(link.dataset.chapter)}))
    .filter(item => item.section);
  if (!chapters.length) return;
  const number = nav.querySelector('[data-bilingual-number]');
  const title = nav.querySelector('[data-bilingual-title]');
  const en = nav.querySelector('[data-bilingual-en]');
  const jp = nav.querySelector('[data-bilingual-jp]');
  let selected = '';
  function update(id) {
    if (selected === id) return;
    const found = chapters.find(item => item.link.dataset.chapter === id);
    if (!found) return;
    selected = id;
    const link = found.link;
    if (number) number.textContent = link.dataset.number || '';
    if (title) title.textContent = link.dataset.cn || '';
    if (en) en.textContent = link.dataset.en || '';
    if (jp) jp.textContent = link.dataset.jp || '';
    links.forEach(item => {
      const active = item === link;
      item.classList.toggle('is-current', active);
      if (active) item.setAttribute('aria-current','location');
      else item.removeAttribute('aria-current');
    });
  }
  function sync() {
    const edge = Math.max(100, nav.getBoundingClientRect().bottom + 25);
    let active = chapters[0];
    for (const chapter of chapters) {
      if (chapter.section.getBoundingClientRect().top <= edge) active = chapter;
      else break;
    }
    update(active.link.dataset.chapter);
  }
  let scheduled = false;
  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {scheduled = false;sync();});
  }
  nav.addEventListener('click', event => {
    const a = event.target.closest('a[data-chapter]');
    if (a && nav.contains(a)) update(a.dataset.chapter);
  });
  window.addEventListener('scroll',schedule,{passive:true});
  window.addEventListener('resize',schedule,{passive:true});
  window.addEventListener('hashchange',schedule);
  window.addEventListener('pageshow',schedule);
  schedule();
})();
