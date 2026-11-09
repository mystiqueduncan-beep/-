'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const source = fs.readFileSync(require('node:path').join(__dirname, '../assets/trend-charts.js'), 'utf8');

function run({ reduce = false, fail = false, missing = false } = {}) {
  const classes = new Set();
  let callback, change, timer;
  let disconnected = 0;
  const rect = { top: 820, bottom: 1140, width: 400, height: 320 };
  const chart = {
    classList: { add: c => classes.add(c), remove: c => classes.delete(c) },
    getBoundingClientRect: () => rect
  };
  const window = {
    innerHeight: 844,
    matchMedia: () => ({ matches: reduce, addEventListener: (_, cb) => change = cb }),
    addEventListener() {},
    removeEventListener() {},
    requestAnimationFrame: cb => cb(),
    setTimeout: cb => timer = cb
  };
  class Observer {
    constructor(cb) { if (fail) throw Error('unsupported'); callback = cb; }
    observe() {}
    disconnect() { disconnected++; }
  }
  if (!missing) window.IntersectionObserver = Observer;
  vm.runInNewContext(source, { window, document: {
    querySelector: () => chart,
    documentElement: { clientHeight: 844 }
  }, IntersectionObserver: Observer });
  return {
    classes,
    enter: () => callback([{ isIntersecting: true }]),
    move: (top, height = 320) => { rect.top = top; rect.height = height; rect.bottom = top + height; },
    reduce: () => change({ matches: true }),
    finish: () => timer?.(),
    get disconnected() { return disconnected; }
  };
}
test('reduced motion and missing/failed observers leave static content complete', () => {
  for (const opts of [{ reduce: true }, { fail: true }, { missing: true }]) {
    assert.equal(run(opts).classes.size, 0);
  }
});
test('first pixel of a chart does not trigger animation; full entry does', () => {
  const h = run();
  h.enter();
  assert.equal(h.classes.has('is-entering'), false);
  h.move(240);
  h.enter();
  assert.equal(h.classes.has('is-entering'), true);
  assert.equal(h.disconnected, 1);
  h.finish();
  assert.equal(h.classes.size, 0);
});
test('changing to reduced motion immediately finishes an active entrance', () => {
  const h = run();
  h.move(240);
  h.enter();
  h.reduce();
  assert.equal(h.classes.size, 0);
});
