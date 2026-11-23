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


/* 2026-11-23 | Reader-first editorial guide.
 * Keeps all eleven approved research chapters and every source/chart untouched.
 * Focus mode is opt-in, inline (no modal), reversible and print-safe.
 */
(() => {
  "use strict";
  if (!document.body?.classList.contains("page-trend")) return;

  function initReader() {
    const main = document.querySelector("main.trend-main");
    if (!main || main.querySelector(".reader-guide")) return;
    const sections = [...main.querySelectorAll(":scope > section[id]")];
    const names = {
      market: "市場判讀", competition: "品牌競爭", consumer: "消費心理",
      location: "商圈研究", digital: "數位轉型", people: "人才管理",
      experience: "經驗連結", strategy: "改善方針", roadmap: "90 天計畫",
      metrics: "成效追蹤", sources: "資料來源"
    };
    if (sections.length !== 11 || sections.some(s => !names[s.id])) return;
    const ids = sections.map(s => s.id);
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    const guide = document.createElement("aside");
    guide.className = "reader-guide";
    guide.setAttribute("aria-label", "專題閱讀導覽");
    const eyebrow = document.createElement("p");
    eyebrow.className = "reader-guide__eyebrow";
    eyebrow.textContent = "THE READING MAP  /  專題閱讀地圖";
    const title = document.createElement("h2");
    title.className = "reader-guide__title";
    title.textContent = "先選主題，再深入閱讀";
    const intro = document.createElement("p");
    intro.className = "reader-guide__intro";
    intro.textContent = "完整研究仍在原頁面。你可以自由跳章，或啟用單章閱讀，減少一次出現的資訊量。";
    const landmarks = document.createElement("nav");
    landmarks.className = "reader-guide__landmarks";
    landmarks.setAttribute("aria-label", "專題快速路徑");
    const groups = [
      ["#market", "01", "看市場與消費", "MARKET & PEOPLE"],
      ["#experience", "02", "看管理與改善", "ACTION & PRACTICE"],
      ["#metrics", "03", "看成效與來源", "EVIDENCE & LIMITS"]
    ];
    groups.forEach(([href,number,label,english]) => {
      const a = document.createElement("a");
      a.className = "reader-guide__route";
      a.href = href;
      const n = document.createElement("span");
      n.className = "reader-guide__route-number";
      n.textContent = number;
      const copy = document.createElement("span");
      const zh = document.createElement("strong");
      zh.textContent = label;
      const en = document.createElement("small");
      en.textContent = english;
      copy.append(zh, en);
      const arrow = document.createElement("span");
      arrow.className = "reader-guide__route-arrow";
      arrow.setAttribute("aria-hidden", "true");
      arrow.textContent = "↗";
      a.append(n,copy,arrow);
      landmarks.append(a);
    });

    const toolbar = document.createElement("div");
    toolbar.className = "reader-guide__toolbar";
    const label = document.createElement("label");
    label.className = "reader-guide__select-label";
    const labelText = document.createElement("span");
    labelText.textContent = "跳至章節";
    const select = document.createElement("select");
    select.className = "reader-guide__select";
    select.setAttribute("aria-label", "選擇研究章節");
    sections.forEach((section,index) => {
      const option = document.createElement("option");
      option.value = section.id;
      option.textContent = String(index + 1).padStart(2,"0") + "  " + names[section.id];
      select.append(option);
    });
    label.append(labelText,select);
    const focusButton = document.createElement("button");
    focusButton.className = "reader-guide__mode";
    focusButton.type = "button";
    focusButton.textContent = "切換單章閱讀";
    focusButton.setAttribute("aria-pressed", "false");
    focusButton.setAttribute("aria-label", "啟用單章閱讀模式");
    const prev = document.createElement("button");
    prev.type = "button";
    prev.className = "reader-guide__step";
    prev.textContent = "← 上一章";
    prev.hidden = true;
    const next = document.createElement("button");
    next.type = "button";
    next.className = "reader-guide__step";
    next.textContent = "下一章 →";
    next.hidden = true;
    toolbar.append(label,focusButton,prev,next);

    const progress = document.createElement("div");
    progress.className = "reader-guide__progress";
    const now = document.createElement("p");
    now.className = "reader-guide__now";
    const track = document.createElement("div");
    track.className = "reader-guide__track";
    track.setAttribute("aria-hidden", "true");
    const fill = document.createElement("span");
    fill.className = "reader-guide__fill";
    track.append(fill);
    progress.append(now,track);
    guide.append(eyebrow,title,intro,landmarks,toolbar,progress);
    main.insertBefore(guide,sections[0]);

    let currentIndex = 0;
    let focusMode = false;
    let scheduled = false;

    function hashChapter() {
      const raw = window.location.hash.slice(1);
      let id;
      try { id = decodeURIComponent(raw); } catch (_) { return null; }
      const target = document.getElementById(id);
      const section = target?.closest("section[id]");
      return section && ids.includes(section.id) ? ids.indexOf(section.id) : null;
    }

    function selectCurrent(index) {
      currentIndex = Math.max(0,Math.min(sections.length-1,index));
      select.value = ids[currentIndex];
      now.textContent =
        "閱讀進度  " + String(currentIndex + 1).padStart(2,"0") +
        " / 11  ·  " + names[ids[currentIndex]];
      fill.style.width = ((currentIndex + 1) / sections.length * 100) + "%";
      sections.forEach((section,i) =>
        section.classList.toggle("reader-current",i === currentIndex));
      prev.disabled = currentIndex === 0;
      next.disabled = currentIndex === sections.length - 1;
    }

    function goTo(index,writeHash=true) {
      selectCurrent(index);
      if (focusMode) {
        sections.forEach((section,i) => {
          section.classList.toggle("reader-focus-active",i === currentIndex);
        });
      }
      if (writeHash) {
        try {
          const url = new URL(window.location.href);
          url.hash = ids[currentIndex];
          window.history.replaceState(null,"",url.pathname+url.search+url.hash);
        } catch (_) {}
      }
      const target = sections[currentIndex];
      // Native anchor positioning is preserved; no modal or content cloning.
      target.scrollIntoView({
        behavior: reduced?.matches ? "auto" : "smooth",
        block: "start"
      });
    }

    function setMode(active) {
      focusMode = active;
      main.classList.toggle("reader-focus-mode",active);
      focusButton.setAttribute("aria-pressed",String(active));
      focusButton.setAttribute(
        "aria-label",active ? "關閉單章閱讀，顯示完整研究" : "啟用單章閱讀模式");
      focusButton.textContent = active ? "展開全部章節" : "切換單章閱讀";
      prev.hidden = !active;
      next.hidden = !active;
      sections.forEach((section,i) =>
        section.classList.toggle("reader-focus-active",active && i === currentIndex));
    }

    select.addEventListener("change",() => goTo(ids.indexOf(select.value)));
    focusButton.addEventListener("click",() => {
      const selected = currentIndex;
      setMode(!focusMode);
      if (focusMode) goTo(selected,false);
    });
    prev.addEventListener("click",() => goTo(currentIndex - 1));
    next.addEventListener("click",() => goTo(currentIndex + 1));

    // When focus mode is on, opening a chapter from the original chapter nav
    // must reveal it before scrolling. Normal anchor clicks remain native.
    document.addEventListener("click",event => {
      if (!focusMode || event.defaultPrevented || event.button !== 0 ||
          event.metaKey || event.ctrlKey || event.altKey || event.shiftKey) return;
      const link = event.target.closest?.('a[href^="#"]');
      if (!link) return;
      let id;
      try { id=decodeURIComponent(link.hash.slice(1)); } catch (_) { return; }
      const target = document.getElementById(id);
      const section = target?.closest("section[id]");
      if (!section || !ids.includes(section.id)) return;
      event.preventDefault();
      goTo(ids.indexOf(section.id));
      if (target !== section) target.scrollIntoView({block:"start"});
    });

    function onScroll() {
      scheduled = false;
      if (focusMode) return;
      let selected = 0;
      const line = Math.min(window.innerHeight * .35,300);
      for (let index=0;index<sections.length;index++) {
        if (sections[index].getBoundingClientRect().top <= line) selected=index;
        else break;
      }
      // Before reaching the article itself, prefer the first chapter.
      selectCurrent(selected);
    }
    function schedule() {
      if (scheduled) return;
      scheduled=true;
      window.requestAnimationFrame(onScroll);
    }
    window.addEventListener("scroll",schedule,{passive:true});
    window.addEventListener("resize",schedule,{passive:true});
    window.addEventListener("hashchange",() => {
      const index=hashChapter();
      if (index !== null) {
        if (focusMode) goTo(index,false);
        else selectCurrent(index);
      }
    });
    window.addEventListener("beforeprint",() => setMode(false));
    const initial = hashChapter();
    selectCurrent(initial ?? 0);
    schedule();
  }

  if (document.readyState==="loading")
    document.addEventListener("DOMContentLoaded",initReader,{once:true});
  else initReader();
})();
