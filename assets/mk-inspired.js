/* Portfolio interaction enhancements: shared across desktop and mobile.
 * No portfolio facts or chart values are recreated here; original DOM content is moved intact.
 */
(() => {
  "use strict";
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  let seq = 0;

  function disclosure(card, body, anchor, label) {
    if (!card || card.dataset.portfolioDisclosure || !anchor || !body.length) return;
    const nodes = body.filter(node => node && node.parentNode);
    if (!nodes.length || nodes.some(node => node.parentNode !== nodes[0].parentNode)) return;
    const parent = nodes[0].parentNode;
    const panel = document.createElement("div");
    panel.className = "portfolio-disclosure-panel";
    panel.id = "portfolio-detail-" + (++seq);
    panel.setAttribute("aria-hidden", "true");
    panel.setAttribute("inert", "");
    const inner = document.createElement("div");
    inner.className = "portfolio-panel-inner";
    panel.append(inner);
    parent.insertBefore(panel, nodes[0]);
    nodes.forEach(node => inner.append(node));

    const button = document.createElement("button");
    button.type = "button";
    button.className = "portfolio-disclosure-toggle";
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", panel.id);
    button.setAttribute("aria-label", "展開「" + label + "」的詳細內容");
    button.innerHTML = '<span class="portfolio-toggle-text">展開詳細內容</span><span class="portfolio-toggle-chevron" aria-hidden="true">⌄</span>';
    anchor.insertAdjacentElement("afterend", button);
    card.dataset.portfolioDisclosure = "true";
    card.classList.add("portfolio-disclosure-card");

    function setOpen(open) {
      card.classList.toggle("portfolio-is-open", open);
      button.setAttribute("aria-expanded", String(open));
      button.setAttribute("aria-label", (open ? "收合" : "展開") + "「" + label + "」的詳細內容");
      $(".portfolio-toggle-text", button).textContent = open ? "收合詳細內容" : "展開詳細內容";
      panel.setAttribute("aria-hidden", String(!open));
      if (open) panel.removeAttribute("inert");
      else panel.setAttribute("inert", "");
    }
    button.addEventListener("click", () => setOpen(!card.classList.contains("portfolio-is-open")));
    card.portfolioSetOpen = setOpen;
  }

  function initDisclosures() {
    // Introductory summaries and credentials remain visible; only details are collapsed.
    $$("#competencies .editorial-card").forEach(card =>
      disclosure(card, [$(".task-bullet-list", card)], $(".card-body-text", card),
        $(".card-heading", card)?.textContent.trim() || "核心管理能力"));
    $$("#competencies .adv-dim-card").forEach(card =>
      disclosure(card, [$(".adv-task-list", card)], $(".adv-dim-desc", card),
        $(".adv-dim-title", card)?.textContent.trim() || "核心管理能力"));

    $$("#cases .wide-star-case").forEach(card =>
      disclosure(card, [$(".star-fields-grid", card)], $(".card-heading", card),
        $(".card-heading", card)?.textContent.trim() || "營運改善構想"));
    $$("#cases .mobile-case-box").forEach(card => {
      const heading = $(".mobile-case-title", card);
      if (heading) disclosure(card, [...card.children].slice([...card.children].indexOf(heading) + 1),
        heading, heading.textContent.trim());
    });

    // Career details stay in the original reading order and document flow.
    // Keep the existing photo/text layout, but never collapse work experience.
    $$("#career .career-entry-card, #career .timeline-job-card").forEach(card => {
      const spread = $(".career-spread", card);
      if (!spread || $(".portfolio-career-copy", spread)) return;
      const list = $(".duty-bullet-list, .duty-list", spread);
      if (!list || list.parentElement !== spread) return;
      const intro = [...spread.children].find(node => node.tagName === "P");
      const copy = document.createElement("div");
      copy.className = "portfolio-career-copy";
      spread.insertBefore(copy, intro || list);
      if (intro) copy.append(intro);
      copy.append(list);
    });

    $$("#proposal .stage-card").forEach(card => {
      const title = $(".stage-title", card);
      disclosure(card, [$(".stage-content", card), $(".stage-meta-box", card)],
        title, title?.textContent.trim() || "到任工作構想");
    });
    $$("#proposal .stage-card-mini").forEach(card => {
      const title = $("h3", card);
      disclosure(card, [...card.children].filter(el => title && el.compareDocumentPosition(title) & Node.DOCUMENT_POSITION_PRECEDING),
        title, title?.textContent.trim() || "到任工作構想");
    });

    // Research is read by ordinary page scrolling, not card accordions.
    // All original strategy, consumer, location, digital, people and brand
    // details remain in the original DOM/reading order, always visible.
    // Homepage disclosures above are intentionally unchanged.

    // Deep links and print should never leave a requested detail inaccessible.
    const openHash = () => {
      let hash;
      try { hash = decodeURIComponent(location.hash.slice(1)); }
      catch (_) { return; }
      if (!hash) return;
      const target = document.getElementById(hash);
      target?.closest(".portfolio-disclosure-card")?.portfolioSetOpen?.(true);
    };
    window.addEventListener("hashchange", openHash);
    openHash();
  }

  function initBarCharts() {
    const groups = [];
    const homeBars = $$("#research .data-bar-fill");
    if (homeBars.length) {
      const parent = homeBars[0].closest(".data-bars-container") || homeBars[0].parentElement?.parentElement?.parentElement;
      groups.push({ host: parent, bars: homeBars });
    }
    for (const section of ["#market", "#consumer"]) {
      const trendBars = $$(section + " .animated-bar");
      if (trendBars.length) {
        const parent = trendBars[0].closest(".feature-card") || trendBars[0].parentElement;
        groups.push({ host: parent, bars: trendBars });
      }
    }
    for (const group of groups) {
      const { host, bars } = group;
      if (!host || host.dataset.portfolioChart) continue;
      host.dataset.portfolioChart = "true";
      host.classList.add("portfolio-chart");
      bars.forEach((bar, index) => {
        bar.classList.add("portfolio-bar");
        bar.style.setProperty("--portfolio-bar-delay", index * 110 + "ms");
        // Preserve the original width/percentage written in the HTML.
      });

      function play() {
        if (reduce.matches) return;
        host.classList.remove("portfolio-chart-active");
        // Flush the prepared zero pose before restarting the fill transition.
        void host.offsetWidth;
        window.requestAnimationFrame(() => {
          window.requestAnimationFrame(() => host.classList.add("portfolio-chart-active"));
        });
      }
      if (reduce.matches) continue;
      host.classList.add("portfolio-chart-ready");
      const isVisibleEnough = () => {
        const box = host.getBoundingClientRect();
        const h = window.innerHeight || document.documentElement.clientHeight;
        const visible = Math.max(0, Math.min(box.bottom, h - 28) - Math.max(0, box.top));
        return visible >= Math.min(box.height * .4, h * .36) && visible >= Math.min(50, box.height);
      };
      let played = false;
      let observer = null;
      const onPosition = () => {
        if (played || !isVisibleEnough()) return;
        played = true;
        observer?.disconnect();
        window.removeEventListener("scroll", onPosition);
        window.removeEventListener("resize", onPosition);
        play();
      };
      if ("IntersectionObserver" in window) {
        observer = new IntersectionObserver(onPosition, { threshold: [0, .1, .25, .4] });
        observer.observe(host);
      }
      window.addEventListener("scroll", onPosition, { passive: true });
      window.addEventListener("resize", onPosition);
      window.requestAnimationFrame(onPosition);
    }
    reduce.addEventListener?.("change", event => {
      $$(".portfolio-chart").forEach(host => {
        if (event.matches) {
          host.classList.remove("portfolio-chart-ready", "portfolio-chart-active");

        } else {
          host.classList.add("portfolio-chart-ready", "portfolio-chart-active");

        }
      });
    });
  }

  if (!document.body)
    document.addEventListener("DOMContentLoaded", () => { initDisclosures(); initBarCharts(); }, { once: true });
  else { initDisclosures(); initBarCharts(); }
})();

/* Legacy one-time markers: only subordinate content may be registered.
   Contact/hero buttons keep their one-time pop. Reduced-motion/print/no-JS are safe. */
(() => {
  "use strict";
  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  if (!("IntersectionObserver" in window) || (reduced && reduced.matches)) return;

  const selectors = [
    ".key-pillar-card",
    ".hero-action-card",
    "main .star-field-box",
    "main .stage-meta-box",
    "main .candidate-info-box",
    "main .candidate-specs-box",
    "main .timeline-job-card",
    "main .mobile-case-box",
    "main .pillar-mini-card",
    "main .editorial-card",
    "main .wide-star-case",
    "main .career-entry-card",
    "main #career .duty-bullet-list > li",
    "main #career .duty-list > li",
    "main .edu-dedicated-card",
    "main .stage-card",
    "main .contact-action-panel",
    "main .feature-card",
    "main .metric-tile",
    "main .case-box",
    "main .content-article-box",
    "main .mobile-subcard",
    "main .adv-dim-card",
    "main .stage-card-mini"
  ];
  const targets = [...new Set(document.querySelectorAll(selectors.join(",")))];
  const contactMethods = [...document.querySelectorAll("main .contact-methods-stack > .method-card, main > section .method-card")];
  // Pop-in is reserved for action controls, not narrative content.
  // Hero controls are immediately present; only hover and focus feedback remain.
  // Move only headline units: full sections and narrative cards fade in place.
  // Contact/hero actions retain their one-time pop.
  const chapterSelector = ".mag-header > .container, main .section-editorial-header, main .mobile-card-title, main #career > div > h2, main .education-profile > h2";
  // Phase cards use the dedicated interactive roadmap animation. Do not attach
  // one-time scroll reveal to panels that can be intentionally hidden.
  const allTargets = [...new Set([...targets, ...contactMethods])]
    .filter(el => !el.matches("#roadmap [data-phase-card]"));
  if (!allTargets.length) return;

  // Reveal as soon as about 15% of a unit is visible; do not wait for an
  // entire section to enter. A 32px minimum avoids triggering on a tiny peek.
  // Anything scrolled past is permanently exposed for easy reverse reading.
  const hasEnteredEnough = el => {
    const rect = el.getBoundingClientRect();
    const viewportHeight = document.documentElement.clientHeight || window.innerHeight;
    const visibleBottom = viewportHeight - Math.min(48, Math.max(20, viewportHeight * 0.06));
    if (!rect.width || !rect.height || visibleBottom <= 0) return false;
    if (rect.bottom <= 0) return true;
    const visibleHeight = Math.max(0, Math.min(rect.bottom, visibleBottom) - Math.max(rect.top, 0));
    const requiredHeight = Math.min(rect.height, Math.max(32, Math.min(rect.height, visibleBottom) * 0.15));
    return visibleHeight >= requiredHeight;
  };
  const pending = new Set();
  let observer;
  let scheduled = false;
  let listening = false;
  const detachChecks = () => {
    if (!listening) return;
    listening = false;
    window.removeEventListener("scroll", scheduleCheck);
    window.removeEventListener("resize", scheduleCheck);
    window.removeEventListener("pageshow", scheduleCheck);
  };
  const reveal = el => {
    // Stagger only career duty rows already entering the viewport together.
    // Keep their full space reserved; never delay access to focused/printed content.
    if (el.matches("#career .duty-bullet-list > li, #career .duty-list > li")) {
      const row = [...el.parentElement.children].indexOf(el);
      el.style.setProperty("transition-delay", Math.min(row * 80, 240) + "ms", "important");
    }
    el.classList.remove("mk-motion-pending", "mk-pop-pending");
    el.classList.add(el.classList.contains("mk-pop-item") ? "mk-pop-in" : "mk-motion-in");
    pending.delete(el);
    observer?.unobserve?.(el);
    if (!pending.size) detachChecks();
  };
  const checkPending = () => {
    // Read all positions first; write classes afterwards to avoid layout thrashing.
    const ready = [...pending].filter(hasEnteredEnough);
    ready.forEach(reveal);
  };
  function scheduleCheck() {
    if (scheduled || !pending.size) return;
    scheduled = true;
    window.requestAnimationFrame(() => {
      scheduled = false;
      checkPending();
    });
  }

  try {
    observer = new IntersectionObserver(() => scheduleCheck(), { threshold: 0 });
  } catch (_) { return; }

  // Establish the pending pose before starting any observation.
  const toObserve = allTargets.filter(el => {
    if (el.closest('[hidden], [aria-hidden="true"]')) return false;
    const box = el.getBoundingClientRect();
    return box.width > 0 && box.height > 0;
  });
  for (const el of toObserve) {
    const isPopItem = contactMethods.includes(el);
    el.classList.add(isPopItem ? "mk-pop-item" : "mk-motion-item");
    // A fade remains part of the same one-time observer/focus/anchor lifecycle.
    // This prevents nested elements from sliding repeatedly inside a chapter.
    if (!isPopItem && !el.matches(chapterSelector)) el.classList.add("mk-fade-item");
    el.classList.add(isPopItem ? "mk-pop-pending" : "mk-motion-pending");
    pending.add(el);
  }
  try {
    for (const el of toObserve) observer.observe(el);
  } catch (_) {
    observer.disconnect();
    allTargets.forEach(reveal);
    return;
  }

  // Scroll checks allow early one-time reveal even when the observer callback
  // fires before the 15% entrance threshold is reached.
  if (pending.size) {
    window.addEventListener("scroll", scheduleCheck, { passive: true });
    window.addEventListener("resize", scheduleCheck, { passive: true });
    window.addEventListener("pageshow", scheduleCheck);
    listening = true;
    scheduleCheck();
  }

  const revealEverything = () => {
    observer.disconnect();
    allTargets.forEach(reveal);
    detachChecks();
  };

  // Reveal the focused item and any hidden ancestors so keyboard users never
  // land inside content that is still visually concealed.
  const revealFocusedAncestors = target => {
    let pending = target.closest(".mk-motion-pending, .mk-pop-pending");
    while (pending) {
      reveal(pending);
      observer.unobserve(pending);
      pending = target.parentElement?.closest(".mk-motion-pending, .mk-pop-pending") || null;
    }
  };
  document.addEventListener("focusin", event => {
    revealFocusedAncestors(event.target);
  });
  const revealHashTarget = () => {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); }
    catch (_) { return; }
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    revealFocusedAncestors(target);
  };
  window.addEventListener("hashchange", revealHashTarget);
  revealHashTarget();
  window.addEventListener("beforeprint", revealEverything, { once: true });
  window.addEventListener("pagehide", revealEverything, { once: true });
  if (reduced) {
    if (reduced.addEventListener) reduced.addEventListener("change", event => {
      if (event.matches) revealEverything();
    });
    else if (reduced.addListener) reduced.addListener(event => {
      if (event.matches) revealEverything();
    });
  }
})();


/* Research magazine contents + compact reading navigation.
 * Original chapter IDs, full article, source links and all existing motion stay intact.
 * The legacy desktop chapter strip remains a no-JS fallback. */
(() => {
  "use strict";
  if (!document.body?.classList.contains("page-trend")) return;
  function initReader() {
    const main = document.querySelector("main.trend-main");
    if (!main || main.querySelector(".reader-guide")) return;
    const sections = [...main.querySelectorAll(":scope > section[id]")];
    const groups = [
      ["市場與消費","MARKET & PEOPLE",[
        ["market","市場判讀"],["competition","品牌競爭"],["consumer","消費心理"],["location","商圈研究"]]],
      ["管理與改善","ACTION & PRACTICE",[
        ["digital","數位轉型"],["people","人才管理"],["experience","經驗連結"],["strategy","改善方針"],["roadmap","90天計畫"]]],
      ["成效與來源","EVIDENCE & LIMITS",[
        ["metrics","成效追蹤"],["sources","研究來源"]]]
    ];
    const entries=groups.flatMap(group=>group[2]);
    if(sections.length!==entries.length || sections.some((s,i)=>s.id!==entries[i][0])) return;
    const create=(tag,cls,copy)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(copy!==undefined)e.textContent=copy;return e;};
    const number=i=>String(i+1).padStart(2,"0");
    const reduced=window.matchMedia("(prefers-reduced-motion: reduce)");
    const guide=create("aside","reader-guide");
    guide.id="research-index";
    guide.setAttribute("aria-labelledby","research-index-title");
    guide.tabIndex=-1;
    const eyebrow=create("p","reader-guide__eyebrow","CONTENTS / 目次");
    const title=create("h2","reader-guide__title","研究章節一覽");
    title.id="research-index-title";
    const intro=create("p","reader-guide__intro","可以自由選章節閱讀");
    const grid=create("nav","reader-index-grid");
    grid.setAttribute("aria-label","研究章節目次");
    const links=[];
    groups.forEach(([name,en,items],gi)=>{
      const group=create("div","reader-index-group");
      const heading=create("h3","reader-index-heading");
      heading.append(create("span","reader-index-number",number(gi)),create("span","reader-index-name",name));
      const english=create("p","reader-index-english",en);
      english.lang="en";
      const list=create("ul","reader-index-list");
      items.forEach(([id,label])=>{
        const i=entries.findIndex(entry=>entry[0]===id);
        const li=create("li");
        const a=create("a","reader-index-link");
        a.href="#"+id;
        const n=create("span","reader-index-link-number",number(i));
        n.setAttribute("aria-hidden","true");
        const arrow=create("span","reader-index-arrow","›");
        arrow.setAttribute("aria-hidden","true");
        a.append(n,create("span","reader-index-link-name",label),arrow);
        li.append(a);list.append(li);links.push(a);
      });
      group.append(heading,english,list);grid.append(group);
    });
    guide.append(eyebrow,title,intro,grid);
    const compact=create("nav","reader-compact");
    compact.setAttribute("aria-label","目前研究章節與切換");
    compact.hidden=true;
    const status=create("div","reader-compact-status");
    const counter=create("span","reader-compact-count");
    const name=create("strong","reader-compact-name");
    status.append(counter,name);
    const indexLink=create("a","reader-compact-index");
    indexLink.href="#research-index";
    indexLink.setAttribute("aria-label","研究目次");
    const indexIcon=create("span","reader-compact-icon","☰");
    indexIcon.setAttribute("aria-hidden","true");
    indexLink.append(indexIcon,create("span","reader-compact-index-label","研究目次"));
    const prev=create("button","reader-compact-step","‹");
    const next=create("button","reader-compact-step","›");
    prev.type=next.type="button";
    const track=create("div","reader-compact-track");
    track.setAttribute("role","progressbar");
    track.setAttribute("aria-label","目前閱讀章節");
    track.setAttribute("aria-valuemin","1");
    track.setAttribute("aria-valuemax",String(entries.length));
    const fill=create("span","reader-compact-fill");
    track.append(fill);
    compact.append(prev,status,next,indexLink,track);
    main.insertBefore(guide,sections[0]);
    main.insertBefore(compact,sections[0]);
    document.body.classList.add("reader-index-ready");
    let current=-1,scheduled=false;
    function setCurrent(index){
      if(index===current)return;
      current=index;
      counter.textContent=number(index)+" / "+entries.length;
      name.textContent=entries[index][1];
      track.setAttribute("aria-valuenow",String(index+1));
      track.setAttribute("aria-valuetext",number(index)+" / "+entries.length+" "+entries[index][1]);
      fill.style.width=((index+1)/entries.length*100)+"%";
      links.forEach((link,i)=>{
        if(i===index)link.setAttribute("aria-current","location");
        else link.removeAttribute("aria-current");
      });
      sections.forEach((s,i)=>s.classList.toggle("reader-current",i===index));
      prev.disabled=index===0;next.disabled=index===entries.length-1;
      prev.title=index>0?"上一章："+entries[index-1][1]:"已是第一章";
      next.title=index<entries.length-1?"下一章："+entries[index+1][1]:"已是最後一章";
      prev.setAttribute("aria-label",index>0?"上一章："+entries[index-1][1]:"上一章");
      next.setAttribute("aria-label",index<entries.length-1?"下一章："+entries[index+1][1]:"下一章");
    }
    function hashChapter(){
      try{
        const target=document.getElementById(decodeURIComponent(location.hash.slice(1)));
        const section=target?.closest("section[id]");
        return sections.indexOf(section);
      }catch(_){return -1;}
    }
    // Keep the compact navigation fixed throughout the article. Only the
    // full contents area supersedes it; scroll direction never hides it.
    function update(){
      scheduled=false;
      const y=Math.max(0,window.scrollY);
      compact.hidden=guide.getBoundingClientRect().bottom>80;
      let index=0;
      const line=Math.max(90,Math.min(innerHeight*.23,160));
      sections.forEach((section,i)=>{if(section.getBoundingClientRect().top<=line)index=i;});
      if(y+innerHeight>=document.documentElement.scrollHeight-3)index=sections.length-1;
      setCurrent(index);
    }
    function schedule(){if(!scheduled){scheduled=true;requestAnimationFrame(update);}}
    function goTo(index){
      if(index<0||index>=sections.length)return;
      const hash="#"+entries[index][0];
      if(location.hash!==hash)location.hash=hash;
      else sections[index].scrollIntoView({behavior:reduced.matches?"instant":"smooth",block:"start"});
      schedule();
    }
    prev.addEventListener("click",()=>goTo(current-1));
    next.addEventListener("click",()=>goTo(current+1));
    indexLink.addEventListener("click",()=>guide.focus({preventScroll:true}));
    window.addEventListener("scroll",schedule,{passive:true});
    window.addEventListener("resize",schedule,{passive:true});
    window.addEventListener("hashchange",schedule);
    window.addEventListener("pageshow",schedule);
    const initial=hashChapter();
    setCurrent(initial>=0?initial:0);
    schedule();
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",initReader,{once:true});
  else initReader();
})();
