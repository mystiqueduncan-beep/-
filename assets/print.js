/* Print the complete report, then restore the reader's interactive state. */
(() => {
  let closed = [];
  let hidden = [];
  window.addEventListener('beforeprint', () => {
    closed = [...document.querySelectorAll('details:not([open])')];
    hidden = [...document.querySelectorAll('[data-owner][hidden]')];
    closed.forEach(el => { el.open = true; });
    hidden.forEach(el => { el.hidden = false; });
  });
  window.addEventListener('afterprint', () => {
    closed.forEach(el => { el.open = false; });
    hidden.forEach(el => { el.hidden = true; });
    closed = []; hidden = [];
  });
})();
