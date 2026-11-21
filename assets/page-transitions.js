/* Progressive enhancement: smooth site-wide page transitions between internal pages.
 * Supports native View Transitions (Chrome/Edge) and provides lightweight fallback (Safari/Firefox).
 * Strictly preserves reduced-motion, bfcache, and internal anchor navigation.
 */
(() => {
  "use strict";

  // Check reduced motion preference
  const reducedMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reducedMotion && reducedMotion.matches) {
    return;
  }

  // If native cross-document view transitions are supported by the browser,
  // the browser engine natively runs @view-transition in CSS.
  // We only enable JS click interception fallback on browsers lacking native cross-document transitions.
  const hasNativeCrossDocVT = ("onpageswap" in window) && ("onpagereveal" in window);
  if (hasNativeCrossDocVT) {
    return;
  }

  // Enable fallback styling on <html>
  document.documentElement.classList.add("page-trans-fallback");

  // Safeguard: always clear exiting state on pageshow (e.g. bfcache, back/forward)
  window.addEventListener("pageshow", () => {
    document.body.classList.remove("is-page-exiting");
  });

  window.addEventListener("pagehide", () => {
    document.body.classList.remove("is-page-exiting");
  });

  function isSamePageAnchor(targetUrl) {
    const curPath = window.location.pathname.replace(/\/index\.html$/, "/");
    const tgtPath = targetUrl.pathname.replace(/\/index\.html$/, "/");
    return curPath === tgtPath && targetUrl.search === window.location.search;
  }

  document.addEventListener("click", (event) => {
    if (event.defaultPrevented) return;
    if (event.button !== 0) return; // Only primary (left) click
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return; // Allow new tab/window

    const link = event.target.closest("a");
    if (!link || !link.href) return;

    // Do not intercept links configured to open in new tab/window
    if (link.target && link.target !== "_self") return;

    // Do not intercept file downloads
    if (link.hasAttribute("download")) return;

    let targetUrl;
    try {
      targetUrl = new URL(link.href, window.location.href);
    } catch (_) {
      return;
    }

    // Only handle http and https
    if (targetUrl.protocol !== "http:" && targetUrl.protocol !== "https:") return;

    // Must be same origin
    if (targetUrl.origin !== window.location.origin) return;

    // In-page hash anchors (e.g. #career, #contact) must NOT trigger page transition!
    if (isSamePageAnchor(targetUrl)) return;

    // Perform smooth fade-out and navigate
    event.preventDefault();
    document.body.classList.add("is-page-exiting");

    const destination = targetUrl.href;
    let navigated = false;
    const navigate = () => {
      if (!navigated) {
        navigated = true;
        window.location.href = destination;
      }
    };

    // 380ms matches the fade-out duration
    setTimeout(navigate, 380);

    // Fallback safety timeout: restore if navigation did not proceed
    setTimeout(() => {
      document.body.classList.remove("is-page-exiting");
    }, 2000);
  });
})();



/* Shared trilingual editorial headlines (six portfolio pages).
 * Progressive enhancement: the original HTML remains readable without JS.
 * All mappings translate the existing Chinese heading, never resume facts.
 * Existing marquee, reveal, link routing and print/PDF handlers stay untouched.
 */
(() => {
  "use strict";

  const desktop = new Map([
    ["應徵動機", ["APPLICATION MOTIVATION", "応募動機"]],
    ["核心管理能力", ["CORE OPERATIONAL COMPETENCIES", "主なマネジメント能力"]],
    ["門市營運改善構想", ["STORE OPERATIONS IMPROVEMENT", "店舗運営の改善提案"]],
    ["工作經歷", ["WORK EXPERIENCE", "職務経歴"]],
    ["到任後工作構想", ["POST-HIRE OPERATIONS PLAN", "入社後の業務構想"]],
    ["實體通路趨勢研究摘要", ["RETAIL RESEARCH", "実店舗の市場動向リサーチ"]],
  ]);

  const research = new Map([
    ["品牌競爭與市場定位", ["COMPETITIVE STRATEGY & MARKET POSITIONING", "ブランド競争と市場ポジショニング"]],
    ["消費者行為與購物心理", ["CONSUMER BEHAVIOR & SHOPPING PSYCHOLOGY", "消費者行動と購買心理"]],
    ["商圈研究與展店策略", ["TRADE AREA & STORE NETWORK", "商圏分析と出店戦略"]],
    ["零售數位轉型與虛實整合", ["DIGITAL RETAIL & OMNICHANNEL", "小売のデジタル化とオムニチャネル"]],
    ["組織行為與人才管理", ["ORGANIZATIONAL BEHAVIOR & TALENT MANAGEMENT", "組織行動と人材育成"]],
    ["市場訊號，如何轉成營運決策？", ["FROM MARKET SIGNALS TO OPERATIONAL DECISIONS", "市場動向を運営判断につなげる"]],
    ["把既有經驗，轉成跨店管理方法", ["APPLYING EXPERIENCE TO MULTI-STORE MANAGEMENT", "現場経験を複数店舗の管理に生かす"]],
    ["六項改善方針，明確分工執行", ["SIX IMPROVEMENT PRIORITIES & CLEAR RESPONSIBILITIES", "六つの改善方針と明確な役割分担"]],
    ["90 天區域營運推進計畫", ["90-DAY REGIONAL OPERATIONS ROADMAP", "90日間のエリア運営推進計画"]],
    ["不只看業績，也看改善的代價", ["BEYOND SALES: ASSESSING IMPROVEMENT COSTS", "売上だけでなく改善コストも評価する"]],
    ["資料來源與提案邊界", ["SOURCES & PROPOSAL SCOPE", "情報源と提案の適用範囲"]],
  ]);

  const mobile = new Map([
    ["個人作品集", ["PERSONAL PORTFOLIO", "個人ポートフォリオ"]],
    ["應徵動機與志向", ["MOTIVATION & CAREER GOALS", "志望動機と今後の目標"]],
    ["四大核心管理能力", ["FOUR CORE MANAGEMENT COMPETENCIES", "四つの主要なマネジメント能力"]],
    ["門市營運實務與改善構想", ["STORE OPERATIONS & IMPROVEMENT PROPOSALS", "店舗運営の実務と改善提案"]],
    ["工作經歷", ["WORK EXPERIENCE", "職務経歴"]],
    ["到任後工作構想", ["POST-HIRE OPERATIONS PLAN", "入社後の業務計画"]],
    ["美妝實體通路未來優勢、挑戰與轉型策略", ["BEAUTY RETAIL: OPPORTUNITIES, CHALLENGES & TRANSFORMATION", "実店舗型美容小売の強み・課題と変革戦略"]],
  ]);

  const normalize = (value) => value.replace(/\s+/g, " ").trim();
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  function localized(node, text, lang, className) {
    node.textContent = text;
    node.lang = lang;
    node.classList.add(className);
    return node;
  }

  // One editorial unit: prominent Chinese heading, then a compact linked
  // English/Japanese line. The two subtitle languages never become
  // independent flex items that drift to opposite sides of the page.
  function createSubtitle(en, ja) {
    const caption = document.createElement("span");
    caption.className = "tri-subtitle-line";
    const separator = document.createElement("span");
    separator.className = "tri-subtitle-divider";
    separator.textContent = "／";
    separator.setAttribute("aria-hidden", "true");
    caption.append(en, separator, ja);
    return caption;
  }

  function createHeadingGroup(zh, number) {
    const group = document.createElement("span");
    group.className = "tri-heading-primary";
    if (number) group.append(number);
    zh.classList.add("trilingual-zh");
    if (!zh.lang) zh.lang = "zh-Hant";
    group.append(zh);
    return group;
  }

  function createLine(zh, en, ja, row, number) {
    row.classList.add("tri-type-line", "tri-editorial-line");
    localized(en, en.textContent, "en", "trilingual-en");
    localized(ja, ja.textContent, "ja", "trilingual-ja");
    row.append(createHeadingGroup(zh, number), createSubtitle(en, ja));
    return row;
  }

  function desktopSections() {
    const onResearch = document.body.classList.contains("page-trend");
    document.querySelectorAll(".section-editorial-header").forEach((header) => {
      const wrapper = header.querySelector(".sec-title-wrap");
      const zh = wrapper?.querySelector("h2.sec-title-main");
      if (!wrapper || !zh) return;

      const term = normalize(zh.textContent);
      const translation = (onResearch ? research : desktop).get(term);
      const en = wrapper.querySelector(".sec-title-sub") || header.querySelector(".sec-en-badge");
      const ja = wrapper.querySelector(".sec-title-jp");
      if (!en || !ja) return;
      // New research chapters with existing source translations use the same renderer.
      const locales = translation || [normalize(en.textContent), normalize(ja.textContent)];
      if (!locales[0] || !locales[1]) return;
      localized(en, locales[0], "en", "trilingual-en");
      localized(ja, locales[1], "ja", "trilingual-ja");
      const line = document.createElement("span");
      const number = wrapper.querySelector(".sec-number");
      wrapper.prepend(line);
      createLine(zh, en, ja, line, number);
      // The approved bilingual homepage uses a presentational wrapper.
      // The nodes have moved into the shared editorial line; remove empty wrappers.
      wrapper.querySelector(".bilingual-heading-text")?.remove();
      // The five requested home chapters share exactly the research-page
      // heading system. The summary chapter uses the same stable component
      // to avoid introducing a sixth inconsistent layout.
      header.classList.add("tri-editorial-header");
    });
  }

  // Move the existing mobile English badge inline, after Chinese and before
  // Japanese. Do not rewrite the Chinese text, numbering, or heading levels.
  function wrapChineseText(host) {
    const node = [...host.childNodes].find((part) =>
      part.nodeType === Node.TEXT_NODE && normalize(part.textContent)
    );
    if (!node) return null;
    const value = normalize(node.textContent);
    const span = document.createElement("span");
    span.className = "trilingual-zh";
    span.lang = "zh-Hant";
    span.textContent = value;
    node.replaceWith(span);
    return { value, span };
  }

  function chapterNumber(value) {
    const number = document.createElement("span");
    number.className = "sec-number";
    number.textContent = value;
    number.setAttribute("aria-hidden", "true");
    return number;
  }

  function mobileSections() {
    const numbers = { motivation:"01", competencies:"02", cases:"03", career:"04", proposal:"05", research:"06" };
    // The approved homepage's six identical bilingual chapter headings.
    // Reuse the existing one-time editorial typing lifecycle and semantic H2s.
    document.querySelectorAll("h2.bilingual-mobile-heading").forEach((heading) => {
      const chinese = heading.querySelector(".bilingual-mobile-cn");
      const en = heading.querySelector(".bilingual-mobile-en");
      const ja = heading.querySelector(".bilingual-mobile-jp");
      if (!chinese || !en || !ja) return;
      const row = document.createElement("span");
      row.className = "bilingual-mobile-title";
      const sectionId = heading.closest("section[id]")?.id;
      const number = numbers[sectionId] ? chapterNumber(numbers[sectionId]) : null;
      chinese.classList.add("sec-title-main");
      const line = createLine(chinese, en, ja, row, number);
      heading.classList.add("tri-editorial-header");
      heading.replaceChildren(line);
    });
    document.querySelectorAll("h2.mobile-card-title:not(.bilingual-mobile-heading)").forEach((heading) => {
      // The cover is an editorial label; the candidate name must be the first
      // announced heading, without rewriting protected source HTML.
      if (heading.closest("#profile")) heading.setAttribute("role", "presentation");
      const line = heading.querySelector(":scope > span:first-child");
      const ja = line?.querySelector(".mobile-section-jp");
      const en = heading.querySelector(":scope > .mobile-badge");
      if (!line || !ja || !en) return;

      const chinese = wrapChineseText(line);
      const translation = chinese && mobile.get(chinese.value);
      if (!translation) return;
      localized(en, translation[0], "en", "trilingual-en");
      localized(ja, translation[1], "ja", "trilingual-ja");
      const number = line.querySelector(".ui-code");
      line.classList.add("tri-type-line", "tri-editorial-line");
      line.replaceChildren(createHeadingGroup(chinese.span, number), createSubtitle(en, ja));
    });

    const career = document.querySelector("#career > div");
    const careerHeading = career?.querySelector("h2");
    const careerJa = careerHeading?.querySelector(".mobile-section-jp");
    const careerEnglish = career?.querySelector(":scope > span");
    if (careerHeading && careerJa && careerEnglish) {
      const chinese = wrapChineseText(careerHeading);
      const translation = chinese && mobile.get(chinese.value);
      if (translation) {
        localized(careerEnglish, translation[0], "en", "trilingual-en");
        localized(careerJa, translation[1], "ja", "trilingual-ja");
        const number = careerHeading.querySelector(".ui-code");
        careerHeading.classList.add("tri-type-line", "tri-editorial-line");
        careerHeading.replaceChildren(
          createHeadingGroup(chinese.span, number), createSubtitle(careerEnglish, careerJa)
        );
      }
    }

    const summaryTitle = document.querySelector("#research h2.bilingual-mobile-heading")
      ? null
      : [...document.querySelectorAll("h3")].find((heading) =>
          mobile.has(normalize(heading.textContent))
        );
    if (summaryTitle) {
      const followingJa = summaryTitle.nextElementSibling;
      if (followingJa?.classList.contains("mobile-section-jp")) {
        const chinese = normalize(summaryTitle.textContent);
        const [enText, jaText] = mobile.get(chinese);
        const en = localized(document.createElement("span"), enText, "en", "trilingual-en");
        localized(followingJa, jaText, "ja", "trilingual-ja");
        const zh = document.createElement("span");
        zh.textContent = chinese;
        summaryTitle.classList.add("tri-type-line", "tri-editorial-line");
        summaryTitle.replaceChildren(createHeadingGroup(zh), createSubtitle(en, followingJa));
      }
    }
  }

  function education() {
    const heading = document.querySelector("#education-title");
    const labels = heading?.nextElementSibling;
    if (!heading || !labels?.classList.contains("section-locale-line")) return;
    const en = labels.querySelector('[lang="en"]');
    const ja = labels.querySelector('[lang="ja"]');
    if (!en || !ja) return;
    localized(en, "EDUCATION", "en", "trilingual-en");
    localized(ja, "学歴", "ja", "trilingual-ja");
    const zh = document.createElement("span");
    zh.textContent = heading.textContent;
    heading.classList.add("tri-type-line", "tri-editorial-line", "tri-education-line");
    zh.classList.add("sec-title-main");
    heading.replaceChildren(createHeadingGroup(zh, chapterNumber("01")), createSubtitle(en, ja));
    labels.remove();
  }

  function nameHero() {
    const heading = document.querySelector("h1.candidate-name, h1.candidate-name-huge, #profile .candidate-info-box h1");
    if (!heading) return;
    const scope = heading.parentElement;
    const label = scope?.querySelector(".candidate-en-name, .candidate-furigana, .en-name");
    if (!label || label.querySelector(".tri-subtitle-line")) return;
    const original = normalize(label.textContent);
    const match = original.match(/^(HUANG BO-SHIH)\s*\(([^)]+)\)$|^([^✦]+)\s*✦\s*(HUANG BO-SHIH)$/i);
    if (!match) return;
    const en = localized(document.createElement("span"), match[1] || match[4], "en", "trilingual-en");
    const ja = localized(document.createElement("span"), (match[2] || match[3]).trim(), "ja", "trilingual-ja");
    const row = document.createElement("span");
    row.className = "tri-type-line tri-hero-line tri-name-locale";
    row.append(createSubtitle(en, ja));
    label.replaceWith(row);
    heading.insertAdjacentElement("afterend", row);
  }

  function researchHero() {
    const en = document.querySelector(".report-title-jp");
    const ja = document.querySelector(".report-title-ja");
    if (!en || !ja) return;
    localized(en, "DRUGSTORE INDUSTRY TRENDS & REGIONAL OPERATIONS PROPOSAL", "en", "trilingual-en");
    localized(ja, "ドラッグストア業界の動向調査とエリア運営改善提案", "ja", "trilingual-ja");
    const line = document.createElement("div");
    line.className = "tri-hero-line tri-type-line";
    en.parentNode.insertBefore(line, en);
    line.append(createSubtitle(en, ja));
  }

  function animateOnce() {
    const lines = [...document.querySelectorAll(".tri-type-line")];
    if (!lines.length || reducedMotion.matches) return;
    const states = new Map();
    let observer = null, scheduled = false;

    // Keep the complete original text in the DOM throughout the effect.
    // Reserve every character's space so narrow/mobile headings never reflow.
    function segment(text) {
      return window.Intl?.Segmenter
        ? [...new Intl.Segmenter("zh-Hant", { granularity: "grapheme" }).segment(text)].map(x => x.segment)
        : Array.from(text);
    }
    function primaryOf(line) {
      const chapter = line.querySelector(".tri-heading-primary .trilingual-zh");
      if (chapter) return chapter;
      if (line.classList.contains("tri-hero-line")) {
        const preceding = line.previousElementSibling;
        if (preceding?.matches("h1")) return preceding;
        return line.closest(".trend-hero,.hero-name-row,.name-title-wrap,.candidate-info-box")?.querySelector("h1") || null;
      }
      return null;
    }
    function preparePrimary(state) {
      const root = state.primary;
      if (!root) return;
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) if (walker.currentNode.textContent.trim()) nodes.push(walker.currentNode);
      for (const node of nodes) {
        const fragment = document.createDocumentFragment();
        const chars = segment(node.textContent).map(character => {
          const glyph = document.createElement("span");
          glyph.className = "tri-primary-char";
          glyph.textContent = character;
          fragment.append(glyph);
          return glyph;
        });
        if (!chars.length) continue;
        state.records.push({ node, chars });
        state.glyphs.push(...chars);
        node.replaceWith(fragment);
      }
      root.classList.add("tri-primary-typing");
    }
    function finish(state) {
      if (state.done) return;
      state.done = true;
      observer?.unobserve(state.line);
      if (state.timer !== null) window.clearTimeout(state.timer);
      state.primary?.classList.remove("tri-primary-typing");
      for (const { node, chars } of state.records) {
        if (chars[0]?.parentNode) {
          chars[0].replaceWith(node);
          chars.slice(1).forEach(glyph => glyph.remove());
        }
      }
      state.caption?.classList.remove("tri-typing");
      state.caption?.querySelector(".tri-typed-visual")?.remove();
      state.line.classList.remove("tri-type-pending", "tri-type-active");
      state.line.classList.add("tri-type-done");
      if ([...states.values()].every(item => item.done)) {
        observer?.disconnect();
        window.removeEventListener("scroll", schedule);
        window.removeEventListener("resize", schedule);
        document.removeEventListener("transitionend", schedule, true);
      }
    }
    function activate(state) {
      if (state.started || state.done) return;
      state.started = true;
      observer?.unobserve(state.line);
      const { line, caption, en, ja, glyphs } = state;
      const zhDelay = 90, enDelay = 30, jaDelay = 50, gap = 80, dividerDelay = 30;
      const zhDuration = glyphs.length * zhDelay;
      const subtitleStart = zhDuration + (glyphs.length ? gap : 0);
      const enChars = segment(en?.textContent || "");
      const jaChars = segment(ja?.textContent || "");
      const enDuration = enChars.length * enDelay;
      const totalDuration = subtitleStart + enDuration + dividerDelay + jaChars.length * jaDelay;
      let visualEn, visualDivider, visualJa;
      if (caption && en && ja) {
        const visual = document.createElement("span");
        visual.className = "tri-typed-visual";
        visual.setAttribute("aria-hidden", "true");
        visualEn = document.createElement("span");
        visualEn.className = "tri-typed-en";
        visualDivider = document.createElement("span");
        visualDivider.className = "tri-typed-divider";
        visualJa = document.createElement("span");
        visualJa.className = "tri-typed-ja";
        visual.append(visualEn, visualDivider, visualJa);
        caption.append(visual);
        caption.classList.add("tri-typing");
      }
      line.classList.remove("tri-type-pending");
      line.classList.add("tri-type-active");
      const startedAt = performance.now();
      let visibleCount = 0;
      const tick = now => {
        if (state.done) return;
        if (reducedMotion.matches || document.hidden) { finish(state); return; }
        const elapsed = Math.max(0, now - startedAt);
        const count = Math.min(glyphs.length, Math.floor(elapsed / zhDelay));
        while (visibleCount < count) glyphs[visibleCount++].classList.add("is-typed");
        const subElapsed = Math.max(0, elapsed - subtitleStart);
        if (visualEn) {
          visualEn.textContent = enChars.slice(0, Math.floor(subElapsed / enDelay)).join("");
          visualDivider.textContent = elapsed >= subtitleStart + enDuration ? "／" : "";
          visualJa.textContent = jaChars.slice(0, Math.max(0, Math.floor((subElapsed - enDuration - dividerDelay) / jaDelay))).join("");
        }
        if (elapsed >= totalDuration) { finish(state); return; }
        window.requestAnimationFrame(tick);
      };
      state.timer = window.setTimeout(() => finish(state), totalDuration + 900);
      window.requestAnimationFrame(tick);
    }
    function checkVisible() {
      const height = window.innerHeight || document.documentElement.clientHeight;
      let top = 0;
      document.querySelectorAll(".mag-subnav-strip,.bilingual-mobile-strip,.trend-subnav-strip,.mobile-top-bar").forEach(nav => {
        const style = window.getComputedStyle(nav);
        const rect = nav.getBoundingClientRect();
        const offset = Number.parseFloat(style.top);
        // A nav still in its normal document position cannot obscure the hero.
        if (["sticky","fixed"].includes(style.position) && Number.isFinite(offset) && rect.top <= offset + 2 && rect.bottom > 0) top = Math.max(top, rect.bottom);
      });
      for (const state of states.values()) {
        if (state.started || state.done) continue;
        const target = state.primary || state.line;
        const box = target.getBoundingClientRect();
        if (!box.width || !box.height) continue;
        if (target.closest(".mk-motion-pending,.mk-pop-pending")) continue;
        const visible = Math.min(box.bottom, height - 12) - Math.max(box.top, top);
        if (visible >= Math.min(24, box.height * .55)) activate(state);
      }
    }
    function schedule() {
      if (scheduled) return;
      scheduled = true;
      window.requestAnimationFrame(() => { scheduled = false; checkVisible(); });
    }
    const finishAll = () => { observer?.disconnect(); states.forEach(finish); };
    try {
      lines.forEach(line => {
        const caption = line.querySelector(".tri-subtitle-line");
        const state = {
          line, primary: primaryOf(line), caption,
          en: caption?.querySelector(".trilingual-en"),
          ja: caption?.querySelector(".trilingual-ja"),
          records: [], glyphs: [], timer: null, done: false, started: false
        };
        states.set(line, state);
        preparePrimary(state);
        line.classList.add("tri-type-pending");
      });
      if ("IntersectionObserver" in window) {
        try {
          observer = new IntersectionObserver(schedule, { threshold: [0,.08,.35,.6] });
          lines.forEach(line => observer.observe(line));
          states.forEach(state => { if (state.primary) observer.observe(state.primary); });
        } catch (_) { observer?.disconnect(); observer = null; }
      }
      // The common slide-in controller may remove its pending class after
      // this observer's first callback; transitionend catches that reveal.
      window.addEventListener("scroll", schedule, { passive: true });
      window.addEventListener("resize", schedule, { passive: true });
      document.addEventListener("transitionend", schedule, true);
      document.addEventListener("focusin", event => {
        const line = event.target.closest?.(".tri-type-line");
        if (line && states.has(line)) finish(states.get(line));
      });
      window.addEventListener("beforeprint", finishAll);
      window.addEventListener("pagehide", finishAll, { once: true });
      const motionChanged = event => { if (event.matches) finishAll(); };
      if (reducedMotion.addEventListener) reducedMotion.addEventListener("change", motionChanged);
      else reducedMotion.addListener?.(motionChanged);
      // When returning from a hidden tab do not leave a partially typed title.
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) states.forEach(state => { if (state.started) finish(state); });
        else schedule();
      });
      schedule();
    } catch (_) { finishAll(); }
  }

  // Only captions that truly overflow become keyboard-focusable scroll
  // regions. Avoid adding unnecessary tab stops on wide screens. This
  // directly resolves axe "scrollable-region-focusable" for narrow displays.
  function refreshScrollableCaptions() {
    document.querySelectorAll(".tri-subtitle-line").forEach((caption) => {
      const overflowing = caption.scrollWidth > caption.clientWidth + 1;
      if (overflowing) {
        caption.tabIndex = 0;
        caption.setAttribute("role", "group");
        caption.setAttribute("aria-label", "英文與日文副標題，可左右捲動");
      } else {
        caption.removeAttribute("tabindex");
        caption.removeAttribute("role");
        caption.removeAttribute("aria-label");
      }
    });
  }


  function init() {
    if (!document.body?.matches(".page-home,.page-trend,.page-contact")) return;
    if (document.body.classList.contains("page-home")) {
      if (document.body.classList.contains("page-mobile")) mobileSections();
      else desktopSections();
    }
    if (document.body.classList.contains("page-trend")) {
      desktopSections();
      researchHero();
    }
    if (document.body.classList.contains("page-contact")) education();
    if (document.body.matches(".page-home,.page-contact")) nameHero();
    refreshScrollableCaptions();
    window.requestAnimationFrame(refreshScrollableCaptions);
    window.addEventListener("resize", refreshScrollableCaptions, { passive: true });
    document.fonts?.ready?.then(refreshScrollableCaptions);
    animateOnce();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();


/* Japanese magazine entrance choreography: once-only sections and a factual
   training-process diagram. No source wording, values or links are changed. */
(() => {
  "use strict";
  function init() {
    if (!document.body?.matches(".page-home,.page-trend,.page-contact")) return;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)");

    // An illustrated restatement of the original case, not an invented result.
    let flow = null;
    if (document.body.classList.contains("page-home")) {
      const heading = document.querySelector(
        ".page-desktop #cases .wide-star-case .card-heading," +
        ".page-mobile #cases .mobile-case-box .mobile-case-title"
      );
      if (heading && !heading.parentElement.querySelector(".magazine-training-flow")) {
        flow = document.createElement("figure");
        flow.className = "magazine-training-flow";
        const caption = document.createElement("figcaption");
        caption.textContent = "TRAINING STEPS / 新人帶訓方法圖解";
        const steps = document.createElement("ol");
        steps.className = "magazine-training-steps";
        ["重點觀摩", "步驟演練", "陪同操作"].forEach((label, index) => {
          const item = document.createElement("li");
          item.textContent = label;
          item.style.setProperty("--magazine-step", String(index));
          steps.append(item);
        });
        flow.append(caption, steps);
        heading.insertAdjacentElement("afterend", flow);
      }
    }

    if (!("IntersectionObserver" in window) || reduce?.matches) return;
    const primary = [...document.querySelectorAll(
      "body.page-home.page-desktop main.mag-main > section.section-block," +
      "body.page-home.page-mobile main.mobile-content > section.mobile-card:not(.mobile-cover)," +
      "body.page-home.page-mobile main.mobile-content > section#career," +
      "body.page-trend .trend-main > section[id]," +
      "body.page-contact .contact-card-outer," +
      "body.page-contact.page-mobile main.mobile-content > section.mobile-card"
    )];
    const details = [...document.querySelectorAll(
      "body.page-home #competencies :is(.grid-2x2 > .editorial-card,.adv-dim-card)," +
      "body.page-home #cases :is(.wide-star-case,.mobile-case-box)," +
      "body.page-home #proposal :is(.stage-card,.stage-card-mini)," +
      "body.page-trend #competition > .cards-2x2-grid > .feature-card," +
      "body.page-trend :is(.swimlane-panel,.decision-map,.timeline-control)," +
      "body.page-trend #metrics .metric-grid > .metric-tile," +
      "body.page-contact .method-card"
    )];
    const targets = [...new Set([...primary, ...details])].filter(el => el.isConnected);
    if (!targets.length) return;
    let observer;
    const pending = new Set();
    const reveal = el => {
      if (!el) return;
      pending.delete(el);
      el.classList.remove("magazine-slide-pending");
      el.classList.add("magazine-slide-in");
      observer?.unobserve(el);
    };
    const revealAll = () => {
      observer?.disconnect();
      [...pending].forEach(reveal);
      flow?.classList.add("magazine-flow-played");
    };
    const alreadyInView = el => {
      const rect = el.getBoundingClientRect();
      const height = window.innerHeight || document.documentElement.clientHeight;
      return rect.top <= height * .89 && rect.bottom > 0;
    };
    try {
      observer = new IntersectionObserver(entries => {
        entries.forEach(entry => { if (entry.isIntersecting) reveal(entry.target); });
      }, {threshold:.08, rootMargin:"0px 0px -7% 0px"});
      targets.forEach((el, index) => {
        el.classList.add("magazine-slide");
        const detail = details.includes(el);
        el.style.setProperty("--magazine-slide-x", detail ? "0px" : (index % 2 ? "22px" : "-22px"));
        if (detail) {
          const siblings = [...el.parentElement.children].filter(child => details.includes(child));
          const step = siblings.indexOf(el);
          el.style.setProperty("--magazine-delay", String(Math.min(Math.max(step,0),3)*65)+"ms");
        }
        if (alreadyInView(el)) el.classList.add("magazine-slide-in");
        else {
          pending.add(el);
          el.classList.add("magazine-slide-pending");
          observer.observe(el);
        }
      });
      // Never conceal content when scripting or observers are unavailable.
      document.documentElement.classList.add("magazine-motion-ready");

      document.addEventListener("focusin", event => {
        let current = event.target?.closest?.(".magazine-slide");
        while (current) { reveal(current); current = current.parentElement?.closest?.(".magazine-slide"); }
      });
      const revealHash = () => {
        let id;
        try { id = decodeURIComponent(window.location.hash.slice(1)); }
        catch (_) { return; }
        if (!id) return;
        const target = document.getElementById(id);
        let parent = target?.closest(".magazine-slide");
        while (parent) { reveal(parent); parent = parent.parentElement?.closest?.(".magazine-slide"); }
      };
      window.addEventListener("hashchange", revealHash);
      revealHash();
      window.addEventListener("beforeprint", revealAll);
      window.addEventListener("pagehide", revealAll, {once:true});
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) revealAll();
      });
      reduce?.addEventListener?.("change", event => { if (event.matches) revealAll(); });

      if (flow) {
        if (alreadyInView(flow)) flow.classList.add("magazine-flow-played");
        else {
          const flowObserver = new IntersectionObserver(entries => {
            if (!entries.some(entry => entry.isIntersecting)) return;
            flow.classList.add("magazine-flow-played");
            flowObserver.disconnect();
          }, {threshold:.1});
          flowObserver.observe(flow);
          window.addEventListener("beforeprint", () => flowObserver.disconnect(), {once:true});
        }
      }
    } catch (_) {
      document.documentElement.classList.remove("magazine-motion-ready");
      revealAll();
    }
  }
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", init, {once:true});
  else init();
})();
