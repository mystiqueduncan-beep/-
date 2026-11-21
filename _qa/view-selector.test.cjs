"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname, "../assets/view-mode-switch.js"), "utf8");

function makeElement(tagName) {
  const classes = new Set();
  const attrs = new Map();
  const node = {
    tagName, children: [], textContent: "", className: "",
    classList: {
      add(...names) { names.forEach(name => classes.add(name)); },
      contains(name) { return classes.has(name) || node.className.split(/\s+/).includes(name); }
    },
    append(...children) {
      for (const child of children) { child.parentElement = node; node.children.push(child); }
    },
    appendChild(child) { node.append(child); },
    setAttribute(name, value) { attrs.set(name, value); },
    removeAttribute(name) { attrs.delete(name); },
    getAttribute(name) { return attrs.get(name) || null; }
  };
  return node;
}

function render(mobile, savedPreference = null) {
  const body = makeElement("body");
  body.classList.add(mobile ? "page-mobile" : "page-desktop");
  body.querySelector = () => null;
  body.insertBefore = function(child) { this.append(child); };
  const counterpart = makeElement("a");
  counterpart.className = mobile ? "btn-switch-desktop" : "top-switch-link";
  const parent = makeElement("div");
  parent.textContent = "existing switch";
  counterpart.parentElement = parent;
  const document = {
    body,
    createElement: tag => makeElement(tag),
    querySelector: () => counterpart
  };
  const basename = mobile ? "mobile.html" : "index.html";
  const window = {
    location: { pathname: "/-/" + basename, hash: "#career" },
    localStorage: { getItem: () => savedPreference }
  };
  vm.runInNewContext(source, { document, window });
  const nav = body.children[0];
  const options = nav.children[0].children[1];
  return { nav, options, children: options.children };
}

test("selector contains manual desktop, manual mobile and automatic modes", () => {
  for (const mobile of [false, true]) {
    const { nav, children } = render(mobile, "desktop");
    assert.equal(nav.getAttribute("aria-label"), "瀏覽版本切換");
    assert.equal(children.length, 3);
    assert.deepEqual(children.map(x => x.textContent), mobile
      ? ["電腦版", "手機版", "自動"]
      : ["電腦版", "手機版", "自動"]);
    assert.equal(children[2].href, (mobile ? "mobile.html" : "index.html") + "?view=auto#career");
    assert.equal(children[2].getAttribute("aria-label"), "恢復依裝置自動切換版本");
    assert.equal(children[0].classList.contains("is-current"), !mobile);
    assert.equal(children[1].classList.contains("is-current"), mobile);
  }
});

test("automatic selection reflects cleared preference without changing current page", () => {
  const { children } = render(true);
  assert.equal(children[2].getAttribute("aria-label"), "目前依裝置自動切換版本");
  assert.equal(children[2].classList.contains("is-auto-current"), true);
  assert.equal(children[1].getAttribute("aria-current"), "page");
});

test("mobile cover keeps approved source markup and decorates its accessible role", () => {
  const html = fs.readFileSync(path.join(__dirname, "../mobile.html"), "utf8");
  assert.match(html, /<h2 class="mobile-card-title">\s*<span> 個人作品集/);
  const transitions = fs.readFileSync(path.join(__dirname, "../assets/page-transitions.js"), "utf8");
  assert.match(transitions, /heading\.closest\("#profile"\).*?setAttribute\("role", "presentation"\)/);
});
