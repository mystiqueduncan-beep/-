// Tests for the user-approved nonmoving editorial chapter navigation.
// Browser tests separately cover actual pointer/touch swipes and layout.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const src = fs.readFileSync(path.join(root, "assets/trend-marquee.js"), "utf8");
const css = fs.readFileSync(path.join(root, "assets/portfolio-polish.css"), "utf8");

function classes(initial = []) {
  const values = new Set(initial);
  return {
    add(...names) { names.forEach(name => values.add(name)); },
    remove(...names) { names.forEach(name => values.delete(name)); },
    toggle(name, yes) { if (yes) values.add(name); else values.delete(name); },
    contains(name) { return values.has(name); },
  };
}
function createHarness(mobile = false) {
  const handlers = {};
  const viewHandlers = {};
  const itemHandlers = {};
  const sectionTop = [150,700,1300,1900,2500,3100];
  const anchorState = [];
  const links = sectionTop.map((_,i) => {
    const attrs = new Map([["href","#chapter-"+i]]);
    const link = {
      classList:classes(),
      getAttribute(key) { return attrs.get(key) ?? null; },
      setAttribute(key,value) { attrs.set(key,value); },
      removeAttribute(key) { attrs.delete(key); },
    };
    anchorState.push({link,attrs});
    return link;
  });
  const list = {
    querySelectorAll(selector) {
      assert.equal(selector,'a[href^="#"]');
      return links;
    },
    addEventListener(type,fn) { itemHandlers[type]=fn; },
  };
  const viewport = {
    scrollLeft:0, scrollWidth:1200,clientWidth:400,
    attrs:new Map([["tabindex","0"]]),
    setAttribute(k,v) {this.attrs.set(k,v);},
    removeAttribute(k) {this.attrs.delete(k);},
    addEventListener(type,fn) {viewHandlers[type]=fn;},
  };
  const shell = {
    attrs:new Map([["aria-label","履歷章節跑馬燈"]]),
    getAttribute(k) {return this.attrs.get(k)||null;},
    setAttribute(k,v) {this.attrs.set(k,v);},
    getBoundingClientRect(){return {bottom:90};},
  };
  const nav = {
    classList:classes(["is-enhanced","is-chapter-paused","is-hover-paused"]),
    querySelector(query) {
      return query === ".keycap-marquee__viewport" ? viewport :
        query === ".keycap-marquee__group" ? list : null;
    },
    closest() {return shell;},
  };
  const sections=sectionTop.map((_,i)=>({
    getBoundingClientRect(){return {top:sectionTop[i],bottom:sectionTop[i]+500};}
  }));
  let frames=[];
  const win={
    innerHeight:844,innerWidth:mobile?390:1440,
    addEventListener(k,fn) {handlers[k]=fn;},
  };
  const doc={
    readyState:"complete",
    body:{classList:{contains:k => k === (mobile?"page-mobile":"page-desktop") || k==="page-home"}},
    querySelector(query){return query==="[data-keycap-marquee]"?nav:null;},
    getElementById(id){const m=/^chapter-(\d+)$/.exec(id);return m?sections[+m[1]]:null;},
  };
  vm.runInNewContext(src,{
    document:doc,window:win,
    requestAnimationFrame: fn=>{frames.push(fn);return frames.length;},
    decodeURIComponent,
  });
  function frame(){let q=frames;frames=[];q.forEach(fn=>fn());}
  return {handlers,viewHandlers,itemHandlers,nav,links,anchorState,sections,sectionTop,
          viewport,shell,frame};
}
test("one stationary shortcut per chapter and no repeating animation loop",()=>{
  assert.doesNotMatch(src,/setInterval\(|setTimeout\(/);
  assert.doesNotMatch(src,/function autoScroll|function tick|setPointerCapture|--keycap-start/);
  assert.match(src,/aria-current/);
  assert.match(src,/is-static-nav/);
  for(const [page,count] of [["index.html",6],["mobile.html",6],
                             ["trend.html",11],["mobile-trend.html",11]]){
    const html=fs.readFileSync(path.join(root,page),"utf8");
    const nav=html.match(/<[^>]+data-keycap-marquee[\s\S]*?<\/nav>/i);
    assert.ok(nav, page+" navigation missing");
    const targets=[...nav[0].matchAll(/<a href="#([^"]+)" class="nav-btn-mk"/g)].map(x=>x[1]);
    assert.equal(targets.length,count,page);
    assert.equal(new Set(targets).size,count,page+" duplicates");
    targets.forEach(id=>assert.ok(html.includes('id="'+id+'"'),page+" missing target "+id));
  }
});
test("desktop headings stay visible, while mobile uses native swipe",()=>{
  assert.match(css,/Calm static section navigation \/ 2026-11-20/);
  assert.match(css,/flex-flow:row wrap !important/);
  assert.match(css,/scroll-snap-type:x proximity !important/);
  assert.match(css,/touch-action:pan-x pan-y !important/);
  assert.match(css,/\.bilingual-nav-jp\s*\{\s*display:none !important/);
});
test("highlight follows content without moving the list or autoplay",()=>{
  const h=createHarness(false);
  assert.equal(h.nav.classList.contains("is-enhanced"),false);
  assert.equal(h.nav.classList.contains("is-static-nav"),true);
  assert.equal(h.viewport.scrollLeft,0);
  assert.equal(h.links.filter(x=>x.getAttribute("aria-current")==="location").length,1);
  assert.equal(h.links[0].getAttribute("aria-current"),"location");
  assert.equal(h.viewport.attrs.has("tabindex"),false);
  h.sectionTop[0]=-700;h.sectionTop[1]=120;
  h.handlers.scroll();
  h.frame();
  assert.equal(h.links[1].getAttribute("aria-current"),"location");
  assert.equal(h.links[0].getAttribute("aria-current"),null);
  assert.equal(h.viewport.scrollLeft,0,"active chapter must never reposition nav");
  h.handlers.scroll();h.frame();
  assert.equal(h.viewport.scrollLeft,0,"stationary even after repeated scroll");
});
test("mobile arrow-key motion is user controlled; it never auto-resets",()=>{
  const h=createHarness(true);
  assert.equal(h.viewport.attrs.get("tabindex"),"0");
  assert.equal(h.viewport.scrollLeft,0);
  h.viewHandlers.keydown({target:h.viewport,key:"ArrowRight",preventDefault(){}});
  assert.equal(h.viewport.scrollLeft,150);
  h.handlers.scroll();h.frame();
  assert.equal(h.viewport.scrollLeft,150);
  h.viewHandlers.keydown({target:h.viewport,key:"ArrowLeft",preventDefault(){}});
  assert.equal(h.viewport.scrollLeft,0);
});
