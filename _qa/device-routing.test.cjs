"use strict";
const {test} = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname, "../assets/view-router.js"), "utf8");
const domain = "https://mystiqueduncan-beep.github.io";
const iphone = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Mobile/15E148";
const desktop = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0";
function browser(address, options = {}) {
  const location = new URL(address, domain);
  const calls = [];
  const saved = options.saved || new Map();
  location.replace = value => calls.push(value);
  const storage = options.brokenStorage
    ? {getItem() {throw Error("disabled");}, setItem() {throw Error("disabled");}, removeItem() {throw Error("disabled");}}
    : {getItem(key) {return saved.has(key) ? saved.get(key) : null;},
       setItem(key, value) {saved.set(key, value);},
       removeItem(key) {saved.delete(key);}};
  const window = {
    location,
    localStorage: storage,
    navigator: {userAgent: options.ua || desktop, userAgentData: {mobile: Boolean(options.uaMobile)}},
    matchMedia() {return {matches: Boolean(options.coarse)};}
  };
  vm.runInNewContext(source, {window, URL, URLSearchParams, Boolean});
  return {calls, saved};
}
test("canonical desktop homepage stays desktop for desktop visitors", () => {
  assert.equal(browser("/-/").calls.length, 0);
  assert.equal(browser("/-/index.html").calls.length, 0);
});
test("single homepage entry chooses mobile on iPhone and small touch devices", () => {
  assert.deepEqual(browser("/-/", {ua:iphone}).calls, [domain+"/-/mobile.html"]);
  assert.deepEqual(browser("/-/index.html", {coarse:true}).calls, [domain+"/-/mobile.html"]);
});
test("research and contact use corresponding mobile pages while preserving anchors", () => {
  assert.deepEqual(browser("/-/trend.html?source=link#strategy", {ua:iphone}).calls,
    [domain+"/-/mobile-trend.html?source=link#strategy"]);
  assert.deepEqual(browser("/-/contact.html", {ua:iphone}).calls, [domain+"/-/mobile-contact.html"]);
});
test("mobile URLs return to desktop counterparts on computers without manual override", () => {
  assert.deepEqual(browser("/-/mobile.html").calls, [domain+"/-/index.html"]);
  assert.deepEqual(browser("/-/mobile-trend.html").calls, [domain+"/-/trend.html"]);
  assert.deepEqual(browser("/-/mobile-contact.html").calls, [domain+"/-/contact.html"]);
});
test("manual desktop switch on mobile persists across internal pages without loops", () => {
  const saved = new Map();
  assert.deepEqual(browser("/-/index.html?view=desktop", {ua:iphone,saved}).calls, []);
  assert.equal(saved.get("portfolioPreferredView"), "desktop");
  assert.deepEqual(browser("/-/trend.html", {ua:iphone,saved}).calls, []);
  assert.deepEqual(browser("/-/mobile-contact.html", {ua:iphone,saved}).calls, [domain+"/-/contact.html"]);
});
test("manual mobile switch on desktop persists across tabs and pages", () => {
  const saved = new Map();
  assert.deepEqual(browser("/-/mobile.html?view=mobile", {saved}).calls, []);
  assert.equal(saved.get("portfolioPreferredView"), "mobile");
  assert.deepEqual(browser("/-/", {saved}).calls, [domain+"/-/mobile.html"]);
  assert.deepEqual(browser("/-/trend.html", {saved}).calls, [domain+"/-/mobile-trend.html"]);
});
test("explicit view parameter overrides saved preference and preserves unrelated query", () => {
  const saved = new Map([["portfolioPreferredView","mobile"]]);
  assert.deepEqual(browser("/-/mobile-trend.html?origin=qr&view=desktop#market", {ua:iphone,saved}).calls,
    [domain+"/-/trend.html?origin=qr&view=desktop#market"]);
  assert.equal(saved.get("portfolioPreferredView"), "desktop");
});
test("auto restores default selection and removes view override from redirect", () => {
  const saved = new Map([["portfolioPreferredView","desktop"]]);
  assert.deepEqual(browser("/-/index.html?view=auto&topic=demo#career", {ua:iphone,saved}).calls,
    [domain+"/-/mobile.html?topic=demo#career"]);
  assert.equal(saved.has("portfolioPreferredView"), false);
});
test("tablet can retain desktop layout, independent of narrow desktop windows", () => {
  assert.deepEqual(browser("/-/", {ua:"Mozilla/5.0 (iPad; CPU OS 17_0)",coarse:false}).calls, []);
});
test("storage restrictions and unrelated files do not break page load", () => {
  assert.deepEqual(browser("/-/index.html", {ua:iphone,brokenStorage:true}).calls, [domain+"/-/mobile.html"]);
  assert.deepEqual(browser("/-/robots.txt", {ua:iphone}).calls, []);
});
