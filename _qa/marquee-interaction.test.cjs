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
      getProperty(name) { return this.properties.get(name) || null; },
      getPropertyValue(name) { return this.properties.get(name) || ""; }
    },
    contains(node) { return originals.includes(node) || Boolean(cloned && cloned.links.includes(node)); },
    appendChild() {}
  };
  const viewport = {
    clientWidth: options.viewportWidth || 760,
    scrollLeft: 0,
    scrollWidth: options.scrollWidth || 2800,
    events: new Map(),
    capturedPointer: null,
    querySelectorAll() { return originals; },
    setPointerCapture(pointerId) { this.capturedPointer = pointerId; },
    hasPointerCapture(pointerId) { return this.capturedPointer === pointerId; },
    releasePointerCapture() { this.capturedPointer = null; },
    addEventListener(name, callback) { this.events.set(name, callback); }
  };
  const createdElements = [];
  const nav = {
    closest(selector) { return selector === ".home-keycap-strip" && options.isHomepage ? this : null; },
    appendChild(node) { createdElements.push(node); },
    contains(node) { return originals.includes(node); },
    classList: classes(),
    matches(selector) { return selector === ":hover" ? Boolean(this.hovering) : false; },
    hovering: false,
    capturedPointer: null,
    setPointerCapture(id) { this.capturedPointer = id; },
    hasPointerCapture(id) { return this.capturedPointer === id; },
    releasePointerCapture() { this.capturedPointer = null; },
    querySelector(selector) {
      if (selector === ".keycap-marquee__viewport") return viewport;
      if (selector === ".keycap-marquee__belt") return belt;
      if (selector === ".keycap-marquee__group") return original;
      return null;
    },
    querySelectorAll() { return originals.concat(cloned ? cloned.links : []); },
    addEventListener(name, callback) { events.set(name, callback); }
  };
  let frameCallback = null;
  const window = {
    location: { hash: "" },
    requestAnimationFrame(callback) { frameCallback = callback; },
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
    advanceFrame(time) { assert.ok(frameCallback); frameCallback(time); },
    dispatch(name, target, relatedTarget = null, pointerType = "mouse") {
      const listener = events.get(name);
      assert.ok(listener, "missing event handler: " + name);
      if (name === "pointerover" || name === "pointerenter") nav.hovering = true;
      if (name === "pointerleave" || (name === "pointerout" && !nav.contains(relatedTarget))) nav.hovering = false;
      listener({ target, relatedTarget, pointerType });
    }
  };
}

test("autoplays one chapter group followed by decorative blank space", () => {
  const h = makeHarness();
  assert.equal(h.nav.classList.contains("is-enhanced"), true, "marquee must be enhanced for autoplay");
  assert.equal(h.getClone(), null, "no duplicate chapter buttons are allowed");
  assert.ok(h.belt.style.properties.has("--keycap-interlude-width"));
  assert.equal(h.createdElements.length, 0, "no pause or play button should be created by script");
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  assert.equal(h.nav.classList.contains("is-touch-paused"), false);
  assert.equal(h.nav.classList.contains("is-keyboard-paused"), false);
  assert.ok(h.belt.style.properties.has("--keycap-start"), "decorative width must be measured");
});

test("hovering the whole strip pauses, including decorated empty space", () => {
  const h = makeHarness();
  assert.equal(h.nav.classList.contains("is-enhanced"), true);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  h.dispatch("pointerover", { closest() { return null; } });
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("pointerleave", h.originals[0]);
  h.dispatch("pointerover", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("pointerout", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  h.dispatch("pointerover", h.originals[1]);
  h.dispatch("pointerleave", h.originals[1]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
});

test("click and hash navigation never override pause while the pointer is inside", () => {
  const h = makeHarness();
  const a = h.originals[0];
  h.dispatch("pointerover", a);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("click", a);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.window.location.hash = "#motivation";
  h.windowEvents.get("hashchange")();
  assert.equal(a.getAttribute("aria-current"), "location");
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("pointerover", h.originals[1]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  assert.equal(h.nav.classList.contains("is-enhanced"), true);
  h.dispatch("pointerleave", h.originals[1]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
});

test("moving content under a stationary cursor cannot cancel the strip hover", () => {
  const h = makeHarness();
  h.dispatch("pointerenter", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  // Pointerout with null relatedTarget can be generated by a moving child.
  h.events.get("pointerout")({ pointerType: "mouse", relatedTarget: null });
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("pointerout", h.originals[0], h.originals[1]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("pointerleave", h.originals[0]);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
});

test("single buttons preserve keyboard access and responsive playback", () => {
  const h = makeHarness();
  h.dispatch("pointerover", h.originals[0]);
  h.playback.matches = false;
  h.mediaEvents.get("change")();
  assert.equal(h.nav.classList.contains("is-enhanced"), false);
  assert.equal(h.nav.classList.contains("is-hover-paused"), false);
  h.playback.matches = true;
  h.mediaEvents.get("change")();
  assert.equal(h.nav.classList.contains("is-enhanced"), true);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
});

test("only the native scroll engine moves the belt; CSS cannot restart it", () => {
  assert.doesNotMatch(css, /@keyframes keycap-marquee-scroll/);
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

test("empty marquee spacing cannot add duplicate links or keyboard targets", () => {
  const h = makeHarness();
  assert.equal(h.getClone(), null);
  assert.equal(h.originals.length, 2);
  assert.equal(h.createdElements.length, 0);
  assert.match(css, /content: "✦.*♡.*✧"/);
  const other = { closest() { return null; } };
  h.dispatch("pointerover", other);
  assert.equal(h.nav.classList.contains("is-hover-paused"), true);
  h.dispatch("pointerleave", other);
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
  await new Promise(r => setTimeout(r, 420));
  assert.equal(h.nav.classList.contains("is-touch-paused"), false);
});

test("system reduced motion disables single-pass autoplay", () => {
  const h = makeHarness({ prefersReducedMotion: true });
  assert.equal(h.nav.classList.contains("is-enhanced"), false);
  assert.equal(h.getClone(), null);
  // Switching preference back restores autoplay
  h.playback.matches = true;
  h.mediaEvents.get("change")();
  assert.equal(h.nav.classList.contains("is-enhanced"), true);
  assert.equal(h.getClone(), null);
});

test("resize observer preserves the visible keycap instead of jumping", () => {
  const h = makeHarness();
  assert.equal(h.belt.style.getProperty("--keycap-start"), "760px");
  const initialPosition = h.viewport.scrollLeft;
  h.viewport.clientWidth = 840;
  h.triggerResize();
  assert.equal(h.belt.style.getProperty("--keycap-start"), "840px");
  assert.equal(h.viewport.scrollLeft, initialPosition + 80);
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

test("homepage and research page show each chapter once with a decorative interlude", () => {
  for (const isHomepage of [true, false]) {
    const h = makeHarness({ isHomepage });
    assert.equal(h.nav.classList.contains("is-enhanced"), true);
    assert.equal(h.getClone(), null, "no repeated chapter buttons");
    assert.equal(h.createdElements.length, 0, "no extra links or controls");
    assert.equal(h.belt.style.getProperty("--keycap-start"), "760px");
    assert.equal(h.belt.style.getProperty("--keycap-interlude-width"), "852px");
    assert.equal(h.viewport.scrollLeft, 774);
  }
  assert.doesNotMatch(css, /@keyframes keycap-marquee-scroll/);
  assert.match(css, /\.keycap-marquee\.is-enhanced \.keycap-marquee__belt::after/);
  assert.ok(css.includes("max-width: min(100%, 620px)"));
});

test("homepage reduced motion and hover/touch controls match research page", () => {
  const h = makeHarness({ isHomepage: true, prefersReducedMotion: true });
  assert.equal(h.getClone(), null);
  assert.equal(h.nav.classList.contains("is-enhanced"), false);
  h.playback.matches = true;
  h.mediaEvents.get("change")();
  assert.equal(h.getClone(), null);
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

test("automatic native scrolling pauses and can be dragged both ways", () => {
  const h=makeHarness();
  const view=h.viewport;
  const initial=view.scrollLeft;
  h.advanceFrame(1000);
  h.advanceFrame(1400);
  assert.ok(view.scrollLeft>initial, "auto scrolling must move scrollLeft");
  h.dispatch("pointerover",h.originals[0]);
  const paused=view.scrollLeft;
  h.advanceFrame(1900);
  assert.equal(view.scrollLeft,paused, "pointer hovering pauses scroll");
  const event=(x)=>({
    pointerType:"mouse",pointerId:11,button:0,clientX:x,
    preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;}
  });
  h.events.get("pointerdown")(event(220));
  h.events.get("pointermove")(event(298));
  const earlier=view.scrollLeft;
  assert.ok(earlier<paused-70,"rightward drag reveals previous chapters");
  h.events.get("pointermove")(event(155));
  const later=view.scrollLeft;
  assert.ok(later>earlier+130,"leftward drag reveals later chapters");
  h.events.get("pointerup")(event(155));
  assert.equal(h.nav.classList.contains("is-drag-paused"),false);
  h.advanceFrame(2400);
  assert.equal(view.scrollLeft,later,"hover pause remains after drag");
  h.dispatch("pointerleave",h.originals[0]);
  h.advanceFrame(2800);
  assert.ok(view.scrollLeft>later,"resumes where it stopped, no transform jump");
  assert.match(css,/touch-action:\s*pan-y/);
  assert.match(css,/keycap-marquee__belt::before/);
});
test("a dragged chapter does not trigger unwanted link navigation", () => {
  const h=makeHarness(), v=h.viewport;
  const evt=(x)=>({pointerId:7,pointerType:"mouse",button:0,clientX:x,preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;}});
  h.events.get("pointerdown")(evt(100));
  h.events.get("pointermove")(evt(40));
  h.events.get("pointerup")(evt(40));
  const click=evt(40);
  h.events.get("click")(click);
  assert.equal(click.prevented,true);
  assert.equal(click.stopped,true);
});

test("a new pointer gesture is never blocked by an earlier drag", () => {
  const h = makeHarness();
  const view = h.viewport;
  const evt = x => ({
    pointerId: 16, pointerType: "mouse", button: 0, clientX: x,
    preventDefault() { this.prevented = true; },
    stopImmediatePropagation() { this.stopped = true; }
  });
  h.events.get("pointerdown")(evt(220));
  h.events.get("pointermove")(evt(120));
  h.events.get("pointerup")(evt(120));
  const next = evt(100);
  h.events.get("pointerdown")(next);
  h.events.get("pointerup")(next);
  h.events.get("click")(next);
  assert.equal(Boolean(next.prevented), false);
  assert.equal(Boolean(next.stopped), false);
});

test("window blur during a drag clears capture-based pause", () => {
  const h = makeHarness();
  const evt = (x) => ({ pointerId: 3, pointerType: "mouse", button: 0, clientX: x, preventDefault() {} });
  h.events.get("pointerdown")(evt(100));
  h.events.get("pointermove")(evt(80));
  assert.equal(h.nav.classList.contains("is-drag-paused"), true);
  h.windowEvents.get("blur")();
  assert.equal(h.nav.classList.contains("is-drag-paused"), false);
});

test("mouse contact pauses even on decorative space; a short click does not drag", () => {
  const h = makeHarness(), view = h.viewport;
  h.advanceFrame(1000);
  h.advanceFrame(1300);
  const started = view.scrollLeft;
  const event = (name,x) => ({
    target: name === "click" ? h.originals[0] : { closest() { return null; } },
    pointerType:"mouse", pointerId:25, button:0, clientX:x, clientY:90,
    detail:1, preventDefault() { this.prevented=true; },
    stopImmediatePropagation() { this.stopped=true; }
  });
  h.events.get("pointerdown")(event("down",100));
  assert.equal(h.nav.classList.contains("is-drag-paused"), true);
  h.advanceFrame(1600);
  assert.equal(view.scrollLeft, started);
  // Even a 2px motion follows immediately, but does not yet suppress a tap.
  h.events.get("pointermove")(event("move",98));
  assert.ok(Math.abs(view.scrollLeft - (started + 2)) < 0.1, "no activation delay on initial mouse move");
  assert.equal(h.nav.classList.contains("is-scrubbing"), false);
  h.events.get("pointerup")(event("up",98));
  const click=event("click",98);
  h.events.get("click")(click);
  assert.equal(Boolean(click.prevented), false, "a stationary click must remain usable");
  assert.equal(h.nav.classList.contains("is-drag-paused"), false);
});

test("touch swiping anywhere drags but suppresses synthetic chapter click", () => {
  const h=makeHarness(), view=h.viewport, start=view.scrollLeft;
  const touch=(x,y=50)=>({
    target:h.originals[0], pointerType:"touch", pointerId:77,button:0,
    clientX:x,clientY:y,detail:1,
    preventDefault(){this.prevented=true;},
    stopImmediatePropagation(){this.stopped=true;}
  });
  h.events.get("pointerdown")(touch(180));
  assert.equal(h.nav.classList.contains("is-touch-paused"),true);
  h.events.get("pointermove")(touch(178));
  assert.ok(Math.abs(view.scrollLeft - (start + 2)) < 0.1, "touch must track initial 2px");
  assert.equal(h.nav.classList.contains("is-scrubbing"),false);
  h.events.get("pointermove")(touch(120));
  assert.ok(view.scrollLeft > start+50, "touch must move the entire native scroll strip");
  assert.equal(h.nav.classList.contains("is-scrubbing"),true);
  assert.equal(h.nav.capturedPointer,77);
  h.events.get("pointerup")(touch(120));
  const synthetic=touch(120);
  h.events.get("click")(synthetic);
  assert.equal(synthetic.prevented,true,"dragged chapter must not navigate");
  assert.equal(synthetic.stopped,true);
  const fresh=touch(120);
  h.events.get("pointerdown")(fresh);
  h.events.get("pointerup")(fresh);
  const tap=touch(120);
  h.events.get("click")(tap);
  assert.equal(Boolean(tap.prevented),false,"next independent tap should navigate");
});

test("vertical touch swipe is left to the browser and not classified as a drag", () => {
  const h=makeHarness(), start=h.viewport.scrollLeft;
  const touch=(x,y)=>({
    target:h.originals[0],pointerType:"touch",pointerId:99,button:0,
    clientX:x,clientY:y,detail:1,
    preventDefault(){this.prevented=true;},
    stopImmediatePropagation(){this.stopped=true;}
  });
  h.events.get("pointerdown")(touch(100,100));
  const move=touch(104,160);
  h.events.get("pointermove")(move);
  assert.equal(Boolean(move.prevented),false);
  assert.equal(h.viewport.scrollLeft,start);
  h.events.get("pointerup")(touch(104,160));
  const click=touch(104,160);
  h.events.get("click")(click);
  assert.equal(Boolean(click.prevented),false);
  assert.equal(h.nav.classList.contains("is-scrubbing"),false);
});

test("touch capture handoff never ends the user's horizontal swipe early", () => {
  const h=makeHarness(), initial=h.viewport.scrollLeft;
  const evt=x=>({ pointerId:42,pointerType:"touch",button:0,clientX:x,clientY:90,preventDefault(){} });
  h.events.get("pointerdown")(evt(250));
  h.events.get("pointermove")(evt(225));
  const first=h.viewport.scrollLeft;
  assert.ok(first>initial);
  // iOS and Chromium can emit lostpointercapture on a former target
  // while the same finger is still moving; it must not close the gesture.
  assert.equal(h.events.has("lostpointercapture"),false);
  h.events.get("pointermove")(evt(190));
  assert.ok(h.viewport.scrollLeft>=first+30);
  assert.equal(h.nav.classList.contains("is-drag-paused"),true);
  h.events.get("pointerup")(evt(190));
  assert.equal(h.nav.classList.contains("is-drag-paused"),false);
});

test("a 5px gesture suppresses click without waiting 8px for movement", () => {
  const h=makeHarness(), start=h.viewport.scrollLeft;
  const mouse=x=>({pointerId:15,pointerType:"mouse",button:0,clientX:x,clientY:20,detail:1,
    preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;}});
  h.events.get("pointerdown")(mouse(200));
  h.events.get("pointermove")(mouse(195));
  assert.ok(Math.abs(h.viewport.scrollLeft-(start+5))<0.1);
  assert.equal(h.nav.classList.contains("is-scrubbing"),true);
  h.events.get("pointerup")(mouse(195));
  const click=mouse(195);
  h.events.get("click")(click);
  assert.equal(click.prevented,true);
  assert.equal(click.stopped,true);
  assert.match(css,/\-webkit-touch-callout:\s*none/);
});
