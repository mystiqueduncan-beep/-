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
 const phases=[...document.querySelectorAll("[data-phase]")];
 phases.forEach(b=>b.addEventListener("click",()=>{
  phases.forEach(x=>{x.classList.toggle("active",x===b);x.setAttribute("aria-pressed",String(x===b));});
  document.querySelectorAll("[data-phase-card]").forEach(x=>x.classList.toggle("phase-current",x.dataset.phaseCard===b.dataset.phase));
  const summary=document.querySelector(".timeline-summary");
  if(summary)summary.textContent=summaries[Number(b.dataset.phase)]||summaries[0];
 }));
 const reduced=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)");
 if(!("IntersectionObserver" in window)||(reduced&&reduced.matches))return;
 const items=[...document.querySelectorAll(".viz-comparison,.swimlane-panel,.metric-tile,.decision-map,.timeline-control,.stats,.split .box")];
 if(!items.length)return;
 let observer;
 try{
  observer=new IntersectionObserver(entries=>entries.forEach(e=>{
   if(e.isIntersecting){e.target.classList.add("is-visible");observer.unobserve(e.target);}
  }),{threshold:.08});
  items.forEach(x=>observer.observe(x));
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
