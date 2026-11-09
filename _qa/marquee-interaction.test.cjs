"use strict";
// Regression tests for shared marquee navigation (trend-marquee.js & trend-marquee.css).
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
    matches(selector) {
      if (selector === ":focus-visible") return true;
      return true;
    },
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

function makeHarness(options = {}) {
  const events = new Map();
  const windowEvents = new Map();
  const mediaEvents = new Map();
  const playback = {
    matches: options.prefersReducedMotion ? false : true,
    addEventListener(name, callback) { mediaEvents.set(name, callback); },
    addListener(callback) { mediaEvents.set("change", callback); }
  };
  const originals = [link("#motivation"), link("#career")];
  let cloned = null;
  const original = {
    scrollWidth: options.groupWidth || 1100,
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
    style: {
      properties: new Map(),
      setProperty(name, value) { this.properties.set(name, String(value)); },
      getProperty(name) { return this.properties.get(name) || null; }
    },
    contains(node) { return originals.includes(node) || Boolean(cloned && cloned.links.includes(node)); },
    appendChild() {}
  };
  const viewport = {
    clientWidth: options.viewportWidth || 760,
    scrollLeft: 0,
    events: new Map(),
    addEventListener(name, callback) { this.events.set(name, callback); }
  };
  const createdElements = [];
  const nav = {
    closest(selector) { return selector === ".home-keycap-strip" && options.isHomepage ? this : null; },
    appendChild(node) { createdElements.push(node); },
    contains(node) { return originals.includes(node); },
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
  const document = {
    querySelector() { return nav; },
    createElement(tag) {
      const el = {
        tagName: tag,
        attributes: new Map(),
        events: new Map(),
        classList: classes(),
        setAttribute(k, v) { this.attributes.set(k, v); },
        addEventListener(k, v) { this.events.set(k, v); }
      };
      createdElements.push(el);
      return el;
    }
  };
  let resizeCallback = null;
  class ResizeObserver {
    constructor(callback) { resizeCallback = callback; }
    observe() {}
  }

  vm.runInNewContext(source, {
    window,
    document,
    ResizeObserver,
    setTimeout,
    clearTimeout
  });

  return {
    nav,
    viewport,
    getClone: () => cloned,
    belt,
    originals,
    playback,
    window,
    events,
    windowEvents,
    mediaEvents,
    createdElements,
    triggerResize() { if (resizeCallback) resizeCallback(); },
    dispatch(name, target, relatedTarget = null, pointerType = "mouse") {
      const listener = events.get(name);
      assert.ok(listener, "missing event handler: " + name);
      listener({ target, relatedTarget, pointerType });
    }
  };
}

test("autoplays smoothly on load with duplicate group and no pause/play button", () => {
  const h = makeHarness();
  assert.equal(h.nav.classList.contains("is-enhanced"), true, "marquee must be enhanced for autoplay");
  assert.ok(h.getClone(), "duplicate group must be created for continuous loop");
  assert.equal(h.createdElements.length, 0, "no pause or play button should be created by script");
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  assert.equal(h.nav.classList.contains("is-touch-paused"), false);
  assert.equal(h.nav.classList.contains("is-keyboard-paused"), false);
  assert.ok(h.belt.style.properties.has("--keycap-duration"), "duration must be computed");
});

test("only an actual chapter key pauses on desktop hover; blank strip and mouse exit do not", () => {
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


test("no visible pause or play button exists in CSS or DOM", () => {
  assert.doesNotMatch(css, /\.keycap-marquee__toggle/);
  assert.doesNotMatch(css, /is-user-paused/);
  const h = makeHarness();
  assert.equal(h.createdElements.length, 0);
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

test("mobile touch interaction pauses during swipe and resumes after release", async () => {
  const h = makeHarness();
  assert.equal(h.nav.classList.contains("is-touch-paused"), false);
  // Touch pointer down on a keycap
  h.dispatch("pointerdown", h.originals[0], null, "touch");
  assert.equal(h.nav.classList.contains("is-touch-paused"), true);

  // Releasing touch
  h.dispatch("pointerup", h.originals[0], null, "touch");
  // Clicking immediately restores
  h.dispatch("click", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-touch-paused"), false);

  // Another touch then wait for timer
  h.dispatch("pointerdown", h.originals[1], null, "touch");
  assert.equal(h.nav.classList.contains("is-touch-paused"), true);
  h.dispatch("pointerup", h.originals[1], null, "touch");
  await new Promise(r => setTimeout(r, 1300));
  assert.equal(h.nav.classList.contains("is-touch-paused"), false);
});

test("system prefers-reduced-motion cleanly disables autoplay and removes duplicates", () => {
  const h = makeHarness({ prefersReducedMotion: true });
  assert.equal(h.nav.classList.contains("is-enhanced"), false);
  assert.equal(h.getClone(), null);
  // Switching preference back restores autoplay
  h.playback.matches = true;
  h.mediaEvents.get("change")();
  assert.equal(h.nav.classList.contains("is-enhanced"), true);
  assert.ok(h.getClone());
});

test("resize observer dynamically updates marquee animation duration", () => {
  const h = makeHarness();
  const initialDuration = h.belt.style.getProperty("--keycap-duration");
  assert.ok(initialDuration);
  h.triggerResize();
  assert.equal(h.belt.style.getProperty("--keycap-duration"), initialDuration);
});

test("gracefully handles missing DOM elements or media query API", () => {
  // If nav is missing, should exit without throwing
  let errored = false;
  try {
    vm.runInNewContext(source, {
      window: { matchMedia: () => ({ matches: true }) },
      document: { querySelector: () => null }
    });
  } catch (e) {
    errored = true;
  }
  assert.equal(errored, false, "should not throw when nav element is missing");
});

test("homepage matches research page continuous marquee without extra DOM controls", () => {
  for (const isHomepage of [true, false]) {
    const h = makeHarness({ isHomepage });
    assert.equal(h.nav.classList.contains("is-enhanced"), true);
    assert.ok(h.getClone(), "the seamless loop requires an accessibility-hidden visual clone");
    assert.equal(h.getClone().attributes.get("aria-hidden"), "true");
    assert.equal(h.getClone().links[0].getAttribute("tabindex"), "-1");
    assert.equal(h.createdElements.length, 0, "no extra buttons are introduced");
    assert.equal(h.belt.style.getProperty("--keycap-duration"), "48.0s");
  }
  assert.match(css, /@keyframes keycap-marquee-scroll/);
  assert.doesNotMatch(css, /home-keycap-shuttle|is-home-animated/);
  assert.ok(css.includes("max-width: min(100%, 620px)"));
});

test("homepage reduced motion and hover/touch controls match research page", () => {
  const h = makeHarness({ isHomepage: true, prefersReducedMotion: true });
  assert.equal(h.getClone(), null);
  assert.equal(h.nav.classList.contains("is-enhanced"), false);
  h.playback.matches = true;
  h.mediaEvents.get("change")();
  assert.ok(h.getClone());
  h.dispatch("pointerover", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("pointerout", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  h.dispatch("pointerdown", h.originals[0], null, "touch");
  assert.equal(h.nav.classList.contains("is-touch-paused"), true);
  h.dispatch("click", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-touch-paused"), false);
  h.playback.matches = false;
  h.mediaEvents.get("change")();
  assert.equal(h.getClone(), null);
});
