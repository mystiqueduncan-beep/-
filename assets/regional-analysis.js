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
