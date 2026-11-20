/* Site-consistent, reduced-motion-aware analysis interactions. */
(() => {
 "use strict";
 const filters=[...document.querySelectorAll("[data-filter]")];
 const cards=[...document.querySelectorAll("[data-owner]")];
 filters.forEach(b=>b.addEventListener("click",()=>{
  filters.forEach(x=>x.setAttribute("aria-pressed",String(x===b)));
  cards.forEach(x=>{x.hidden=b.dataset.filter!=="all"&&x.dataset.owner!==b.dataset.filter;});
 }));
 const summaries=[
 "第一階段：先建立可比較的門市基準，確認改善問題。",
 "第二階段：聚焦 1–2 項措施，選店試行並記錄每週回饋。",
 "第三階段：比較成果與執行代價，決定擴大、調整或停止。"];
 const roadmap=document.querySelector("#roadmap");
 if(roadmap){
  const phases=[...roadmap.querySelectorAll("[data-phase]")];
  const panels=[...roadmap.querySelectorAll("[data-phase-card]")];
  const summary=roadmap.querySelector(".timeline-summary");
  const prev=roadmap.querySelector("[data-phase-prev]");
  const next=roadmap.querySelector("[data-phase-next]");
  const count=roadmap.querySelector("[data-phase-count]");
  if(phases.length===3&&panels.length===3&&summary&&prev&&next&&count){
   let selected=0;
   const selectPhase=(index,focusTab=false)=>{
    if(index<0||index>=phases.length)return;
    selected=index;
    phases.forEach((tab,i)=>{
     const active=i===selected;
     tab.classList.toggle("active",active);
     tab.setAttribute("aria-pressed",String(active));
    });
    panels.forEach((panel,i)=>{
     const active=i===selected;
     panel.hidden=!active;
     panel.classList.toggle("phase-current",active);
    });
    summary.textContent=summaries[selected];
    count.textContent=String(selected+1).padStart(2,"0")+" / 03";
    prev.disabled=selected===0;
    next.disabled=selected===phases.length-1;
    roadmap.style.setProperty("--roadmap-progress",selected===0?"0%":selected===1?"34%":"68%");
    if(focusTab)phases[selected].focus();
   };
   phases.forEach((tab,i)=>{
    tab.addEventListener("click",()=>selectPhase(i));
    tab.addEventListener("keydown",event=>{
     let target;
     if(event.key==="ArrowRight")target=Math.min(i+1,phases.length-1);
     else if(event.key==="ArrowLeft")target=Math.max(i-1,0);
     else if(event.key==="Home")target=0;
     else if(event.key==="End")target=phases.length-1;
     else return;
     event.preventDefault();
     selectPhase(target,true);
    });
   });
   prev.addEventListener("click",()=>selectPhase(selected-1,true));
   next.addEventListener("click",()=>selectPhase(selected+1,true));
   // Until JS is initialized, all three original cards remain visible.
   // Hidden inactive cards are removed from reading and focus order.
   selectPhase(0);
   roadmap.classList.add("roadmap-ready");
  }
 }
 const reduced=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)");
 if(!("IntersectionObserver" in window)||(reduced&&reduced.matches))return;
 // The shared site observer already manages mk-motion-item cards; never
 // attach a second entrance observer to them, which would replay reveals.
 const items=[...document.querySelectorAll(".viz-comparison,.swimlane-panel,.metric-tile,.decision-map,.timeline-control,.stats,.split .box")]
  .filter(el=>!el.matches(".mk-motion-item, .mk-pop-item"));
 if(!items.length)return;
 let observer;
 try{
  observer=new IntersectionObserver(entries=>entries.forEach(e=>{
   if(e.isIntersecting){e.target.classList.add("is-visible");observer.unobserve(e.target);}
  }),{threshold:.08});
  items.forEach(x=>{x.classList.add("viz-reveal");observer.observe(x);});
  document.documentElement.classList.add("motion-ready");
 }catch(_){
  if(observer)observer.disconnect();
  document.documentElement.classList.remove("motion-ready");
 }
 if(reduced&&typeof reduced.addEventListener==="function")reduced.addEventListener("change",e=>{
  if(e.matches){
   document.documentElement.classList.remove("motion-ready");
   items.forEach(x=>x.classList.add("is-visible"));
   if(observer)observer.disconnect();
  }
 });
})();


/* Research experience: the "可延伸方法" panels descend gently once after
   entering view. The source text stays in the HTML and is always readable
   without JS, IntersectionObserver, or under reduced-motion/print. */
(() => {
  "use strict";
  const methods = [...document.querySelectorAll("#experience .exp .exp-application")];
  if (!methods.length || !("IntersectionObserver" in window)) return;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reduced.matches) return;

  let observer;
  try {
    observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("exp-method-in");
        observer.unobserve(entry.target);
      });
    }, { threshold: .22, rootMargin: "0px 0px -4% 0px" });

    methods.forEach((method, index) => {
      method.style.setProperty("--exp-method-delay", index * 100 + "ms");
      method.classList.add("exp-method-pending");
      observer.observe(method);
    });
    if (typeof reduced.addEventListener === "function") reduced.addEventListener("change", event => {
      if (!event.matches) return;
      observer.disconnect();
      methods.forEach(method => method.classList.add("exp-method-in"));
    });
  } catch (_) {
    observer?.disconnect();
    methods.forEach(method => method.classList.remove("exp-method-pending"));
  }
})();

/* One-shot KPI count-up: the canonical HTML remains intact and readable
   to assistive technology. Only an aria-hidden visual copy is animated. */
(() => {
  "use strict";
  if (!document.body.classList.contains("page-trend") ||
      !("IntersectionObserver" in window) || !window.matchMedia) return;
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reduced.matches) return;
  const items = [...document.querySelectorAll("#market .stats .stat strong")];
  const active = new Map();
  let observer;
  const finish = (el) => {
    const state = active.get(el);
    if (!state) return;
    cancelAnimationFrame(state.frame);
    state.copy.remove();
    el.classList.remove("research-counting");
    active.delete(el);
  };
  const stop = () => {
    if (observer) observer.disconnect();
    [...active.keys()].forEach(finish);
  };
  const start = (el) => {
    if (reduced.matches || document.hidden) return;
    const original = el.firstChild;
    if (!original || original.nodeType !== 3) return;
    const match = original.nodeValue.match(/^([+]?)([0-9,]+(?:\.[0-9]+)?)(%?)$/);
    if (!match) return;
    const [, prefix, digits, suffix] = match;
    const target = Number(digits.replace(/,/g, ""));
    const decimals = (digits.split(".")[1] || "").length;
    if (!Number.isFinite(target)) return;
    const formatter = new Intl.NumberFormat("en-US", {
      useGrouping: digits.includes(","), minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
    const copy = document.createElement("span");
    copy.className = "research-count-copy";
    copy.setAttribute("aria-hidden", "true");
    copy.textContent = prefix + formatter.format(0) + suffix;
    [...el.children].forEach(child => copy.appendChild(child.cloneNode(true)));
    const number = copy.firstChild;
    const state = {copy, frame:0};
    el.appendChild(copy);
    el.classList.add("research-counting");
    active.set(el, state);
    let begin;
    const tick = (now) => {
      if (!active.has(el)) return;
      if (reduced.matches || document.hidden) {finish(el);return;}
      if (begin === undefined) begin = now;
      const fraction = Math.min(1,(now-begin)/850);
      if (fraction >= 1) {finish(el);return;}
      number.nodeValue = prefix + formatter.format(target*(1-Math.pow(1-fraction,3))) + suffix;
      state.frame = requestAnimationFrame(tick);
    };
    state.frame = requestAnimationFrame(tick);
  };
  try {
    observer = new IntersectionObserver(entries => entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      observer.unobserve(entry.target);
      start(entry.target);
    }), {threshold:.25});
    items.forEach(el => observer.observe(el));
    if (typeof reduced.addEventListener === "function") reduced.addEventListener("change", e => {if(e.matches) stop();});
    window.addEventListener("beforeprint",stop);
    document.addEventListener("visibilitychange",()=>{if(document.hidden) [...active.keys()].forEach(finish);});
  } catch (_) {stop();}
})();


/* User-approved first-entrance fill for the four existing channel survey bars.
   The original numbers and the 0–50% chart width contract stay in HTML. */
(() => {
  "use strict";
  const host = document.querySelector("body.page-trend .inline-research-viz--channels");
  const bars = host ? [...host.querySelectorAll(".inline-research-viz__track > i")] : [];
  const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)");
  if (!host || bars.length !== 4 || reduce?.matches || !("IntersectionObserver" in window)) return;

  bars.forEach((bar, index) => bar.style.setProperty("--progress-delay", (index * 110) + "ms"));
  let played = false;
  let observer = null;
  const complete = () => {
    if (played) return;
    played = true;
    observer?.disconnect();
    // Two frames ensure the hidden 0%-fill state is committed before motion.
    window.requestAnimationFrame(() =>
      window.requestAnimationFrame(() => host.classList.add("inline-progress-played")));
  };
  try {
    observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) complete();
    }, {threshold:0.18,rootMargin:"0px 0px -4% 0px"});
    host.classList.add("inline-progress-ready");
    observer.observe(host);
  } catch (_) {
    observer?.disconnect();
    host.classList.remove("inline-progress-ready");
  }
  const showFullBars = () => {
    observer?.disconnect();
    host.classList.remove("inline-progress-ready");
    played = true;
  };
  reduce?.addEventListener?.("change", event => {if (event.matches) showFullBars();});
  window.addEventListener("beforeprint", showFullBars);
})();
