"use strict";
// Zero-dependency regression for both desktop pages sharing trend-marquee.js.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const source = fs.readFileSync(path.join(root, "assets/trend-marquee.js"), "utf8");
const css = fs.readFileSync(path.join(root, "assets/trend-marquee.css"), "utf8");

function classes() {
  const set = new Set();
  return {
    add(value) { set.add(value); },
    remove(value) { set.delete(value); },
    toggle(value, enabled) {
      if (enabled === undefined) enabled = !set.has(value);
      enabled ? set.add(value) : set.delete(value);
      return Boolean(enabled);
    },
    contains(value) { return set.has(value); }
  };
}
function link(href, duplicated = false) {
  const attributes = new Map([["href", href]]);
  return {
    classList: classes(),
    matches() { return true; },
    scrollIntoView() { this.scrolled = true; },
    getAttribute(name) { return attributes.get(name) || null; },
    setAttribute(name, value) { attributes.set(name, String(value)); },
    removeAttribute(name) { attributes.delete(name); },
    closest(selector) {
      if (selector === ".keycap-marquee__group a") return this;
      if (selector === '[aria-hidden="true"]') return duplicated ? { hidden: true } : null;
      return null;
    }
  };
}
function makeHarness() {
  const events = new Map();
  const windowEvents = new Map();
  const mediaEvents = new Map();
  const playback = {
    matches: true,
    addEventListener(name, callback) { mediaEvents.set(name, callback); }
  };
  const originals = [link("#motivation"), link("#career")];
  let cloned = null;
  const original = {
    getBoundingClientRect() { return { width: 700 }; },
    cloneNode() {
      cloned = {
        links: [link("#motivation", true), link("#career", true)],
        classList: classes(),
        attributes: new Map(),
        setAttribute(name, value) { this.attributes.set(name, value); },
        querySelectorAll() { return this.links; },
        remove() { cloned = null; }
      };
      return cloned;
    }
  };
  const belt = {
    style: { setProperty() {} },
    contains(node) { return originals.includes(node) || Boolean(cloned && cloned.links.includes(node)); },
    appendChild() {}
  };
  const viewport = { scrollLeft: 0 };
  const toggle = { attributes: new Map(), events: new Map(), setAttribute(k,v) { this.attributes.set(k,v); }, addEventListener(k,v) { this.events.set(k,v); } };
  const nav = {
    appendChild() {},
    contains(node) { return originals.includes(node) || node === toggle; },
    classList: classes(),
    querySelector(selector) {
      if (selector === ".keycap-marquee__viewport") return viewport;
      if (selector === ".keycap-marquee__belt") return belt;
      if (selector === ".keycap-marquee__group") return original;
      return null;
    },
    querySelectorAll() { return originals.concat(cloned ? cloned.links : []); },
    addEventListener(name, callback) { events.set(name, callback); }
  };
  const window = {
    location: { hash: "" },
    matchMedia() { return playback; },
    addEventListener(name, callback) { windowEvents.set(name, callback); }
  };
  const document = { querySelector() { return nav; }, createElement() { return toggle; } };
  class ResizeObserver { observe() {} }

  vm.runInNewContext(source, { window, document, ResizeObserver });
  return {
    nav, toggle, viewport, getClone: () => cloned, belt, originals, playback, window, events, windowEvents, mediaEvents,
    dispatch(name, target, relatedTarget = null) {
      const listener = events.get(name);
      assert.ok(listener, "missing event handler: " + name);
      listener({ target, relatedTarget, pointerType: "mouse" });
    }
  };
}

test("only an actual chapter key pauses; blank strip and mouse exit do not", () => {
  const h = makeHarness();
  assert.equal(h.nav.classList.contains("is-enhanced"), true);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  h.dispatch("pointerover", { closest() { return null; } });
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  h.dispatch("pointerover", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("pointerout", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  h.dispatch("pointerover", h.originals[1]);
  h.dispatch("pointerleave", h.originals[1]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
});

test("clicking a key resumes even with retained focus and hash navigation", () => {
  const h = makeHarness();
  const a = h.originals[0];
  h.dispatch("pointerover", a);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("click", a);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  h.window.location.hash = "#motivation";
  h.windowEvents.get("hashchange")();
  assert.equal(a.getAttribute("aria-current"), "location");
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  // A motionless cursor can hover over another scrolling key; it must not re-freeze.
  h.dispatch("pointerover", h.originals[1]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  // No scroll or hash location should disable the animation after navigation.
  assert.equal(h.nav.classList.contains("is-enhanced"), true);
  h.dispatch("pointermove", h.originals[1]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("pointerleave", h.originals[1]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
});

test("duplicated keys are not keyboard navigable and responsive mode restores playback", () => {
  const h = makeHarness();
  h.dispatch("pointerover", h.originals[0]);
  h.playback.matches = false;
  h.mediaEvents.get("change")();
  assert.equal(h.nav.classList.contains("is-enhanced"), false);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  h.playback.matches = true;
  h.mediaEvents.get("change")();
  assert.equal(h.nav.classList.contains("is-enhanced"), true);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
});

test("CSS has no whole-strip hover or focus-within pause selector", () => {
  assert.match(css, /\.keycap-marquee\.is-enhanced\.is-hover-paused\s+\.keycap-marquee__belt\s*\{/);
  assert.doesNotMatch(css, /\.keycap-marquee\.is-enhanced:hover\s+\.keycap-marquee__belt/);
  assert.doesNotMatch(css, /\.keycap-marquee__viewport:(?:hover|focus-within)\s+\.keycap-marquee__belt/);
});


test("explicit pause survives pointer exit, navigation and responsive changes", () => {
  const h = makeHarness();
  h.toggle.events.get("click")();
  assert.equal(h.toggle.attributes.get("aria-pressed"), "true");
  h.dispatch("pointerleave", h.originals[0]);
  h.windowEvents.get("hashchange")();
  h.playback.matches = false; h.mediaEvents.get("change")();
  assert.equal(h.toggle.hidden, true);
  h.playback.matches = true; h.mediaEvents.get("change")();
  assert.equal(h.toggle.hidden, false);
  assert.equal(h.nav.classList.contains("is-user-paused"), true);
  h.toggle.events.get("click")();
  assert.equal(h.nav.classList.contains("is-user-paused"), false);
});

test("keyboard focus exposes original links and leaving nav restores motion", () => {
  const h = makeHarness();
  h.dispatch("focusin", h.originals[1]);
  assert.equal(h.nav.classList.contains("is-keyboard-paused"), true);
  assert.equal(h.originals[1].scrolled, true);
  h.dispatch("focusout", h.originals[1], h.originals[0]);
  assert.equal(h.nav.classList.contains("is-keyboard-paused"), true);
  h.dispatch("focusout", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-keyboard-paused"), false);
});

test("duplicates remain pointer-operable but never acquire pointer focus", () => {
  const h = makeHarness(); const clone = h.getClone();
  assert.equal(clone.attributes.has("inert"), false);
  assert.equal(clone.attributes.get("aria-hidden"), "true");
  assert.equal(clone.links[0].getAttribute("tabindex"), "-1");
  let prevented = false;
  h.events.get("pointerdown")({ target: clone.links[0], preventDefault() { prevented = true; } });
  assert.equal(prevented, true);
  h.dispatch("pointerover", clone.links[0]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("click", clone.links[0]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
});
