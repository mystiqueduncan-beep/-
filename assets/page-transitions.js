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
    ["應徵動機", ["MOTIVATION FOR APPLYING", "志望動機"]],
    ["核心管理能力", ["CORE MANAGEMENT COMPETENCIES", "主なマネジメント能力"]],
    ["門市營運改善構想", ["STORE OPERATIONS IMPROVEMENT PROPOSALS", "店舗運営の改善案"]],
    ["工作經歷", ["WORK EXPERIENCE", "職務経歴"]],
    ["到任後工作構想", ["POST-HIRE OPERATIONS PLAN", "入社後の業務計画"]],
    ["實體通路趨勢研究摘要", ["PHYSICAL RETAIL TRENDS: RESEARCH SUMMARY", "実店舗の市場動向調査概要"]],
  ]);

  const research = new Map([
    ["市場訊號，如何轉成營運決策？", ["FROM MARKET SIGNALS TO OPERATIONAL DECISIONS", "市場動向を運営判断につなげる"]],
    ["把既有經驗，轉成跨店管理方法", ["APPLYING EXPERIENCE TO MULTI-STORE MANAGEMENT", "現場経験を複数店舗の管理に生かす"]],
    ["六項改善方針，明確分工執行", ["SIX IMPROVEMENT PRIORITIES & CLEAR RESPONSIBILITIES", "六つの改善方針と明確な役割分担"]],
    ["90 天區域營運推進計畫", ["90-DAY REGIONAL OPERATIONS ROADMAP", "90日間のエリア運営推進計画"]],
    ["不只看業績，也看改善的代價", ["BEYOND SALES: ASSESSING IMPROVEMENT COSTS", "売上だけでなく改善コストも評価する"]],
    ["資料來源與提案邊界", ["SOURCES & PROPOSAL SCOPE", "情報源と提案の適用範囲"]],
  ]);

  const mobile = new Map([
    ["應徵者專訪特輯", ["APPLICANT FEATURE", "応募者紹介特集"]],
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

  function createLine(zh, en, ja, row) {
    row.classList.add("tri-type-line");
    zh.classList.add("trilingual-zh");
    if (!zh.lang) zh.lang = "zh-Hant";
    localized(en, en.textContent, "en", "trilingual-en");
    localized(ja, ja.textContent, "ja", "trilingual-ja");
    row.append(zh, en, ja);
    return row;
  }

  function desktopSections() {
    document.querySelectorAll(".section-editorial-header").forEach((header) => {
      const wrapper = header.querySelector(".sec-title-wrap");
      const zh = wrapper?.querySelector("h2.sec-title-main");
      if (!wrapper || !zh) return;

      const lookup = document.body.classList.contains("page-trend") ? research : desktop;
      const term = normalize(zh.textContent);
      const translation = lookup.get(term);
      const en = wrapper.querySelector(".sec-title-sub") || header.querySelector(".sec-en-badge");
      const ja = wrapper.querySelector(".sec-title-jp");
      if (!translation || !en || !ja) return;

      localized(en, translation[0], "en", "trilingual-en");
      localized(ja, translation[1], "ja", "trilingual-ja");
      const line = document.createElement("span");
      wrapper.insertBefore(line, zh);
      createLine(zh, en, ja, line);
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

  function mobileSections() {
    document.querySelectorAll("h2.mobile-card-title").forEach((heading) => {
      const line = heading.querySelector(":scope > span:first-child");
      const ja = line?.querySelector(".mobile-section-jp");
      const en = heading.querySelector(":scope > .mobile-badge");
      if (!line || !ja || !en) return;

      const chinese = wrapChineseText(line);
      const translation = chinese && mobile.get(chinese.value);
      if (!translation) return;

      localized(en, translation[0], "en", "trilingual-en");
      localized(ja, translation[1], "ja", "trilingual-ja");
      line.classList.add("tri-type-line");
      line.insertBefore(en, ja);
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
        careerHeading.classList.add("tri-type-line");
        careerHeading.insertBefore(careerEnglish, careerJa);
      }
    }

    const researchJa = document.querySelector("#research .mobile-section-jp, #research-summary .mobile-section-jp");
    // The actual short research summary is also on the mobile homepage; it
    // has a stand-alone h3 and a following Japanese caption.
    const summaryTitle = [...document.querySelectorAll("h3")].find((heading) =>
      mobile.has(normalize(heading.textContent))
    );
    if (summaryTitle) {
      const followingJa = summaryTitle.nextElementSibling;
      if (followingJa?.classList.contains("mobile-section-jp")) {
        const [enText, jaText] = mobile.get(normalize(summaryTitle.textContent));
        const english = document.createElement("span");
        localized(english, enText, "en", "trilingual-en");
        localized(followingJa, jaText, "ja", "trilingual-ja");
        summaryTitle.classList.add("tri-type-line");
        summaryTitle.append(english, followingJa);
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
    heading.classList.add("tri-type-line", "tri-education-line");
    labels.remove();
    heading.append(en, ja);
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
    line.append(en, ja);
  }

  function animateOnce() {
    const lines = [...document.querySelectorAll(".tri-type-line")];
    if (!lines.length || reducedMotion.matches) return;

    const durations = new Map();
    const pending = new Set(lines);
    let observer = null;

    function finish(target) {
      target.classList.remove("tri-type-pending", "tri-type-active");
      target.classList.add("tri-type-done");
    }

    function activate(target) {
      if (!pending.has(target)) return;
      pending.delete(target);
      observer?.unobserve(target);
      target.classList.remove("tri-type-pending");
      target.classList.add("tri-type-active");
      target.addEventListener("animationend", (event) => {
        if (event.target === target) finish(target);
      }, { once: true });
      // The heading must never stay hidden if an effect is interrupted by
      // another reveal, a browser visibility change, or a stylesheet override.
      window.setTimeout(() => finish(target), durations.get(target) + 300);
    }

    function checkVisible() {
      pending.forEach((line) => {
        const rect = line.getBoundingClientRect();
        if (rect.height > 0 && rect.top < window.innerHeight * .96 && rect.bottom > 0) {
          activate(line);
        }
      });
    }

    lines.forEach((line) => {
      const text = normalize(line.textContent);
      const length = (window.Intl?.Segmenter)
        ? [...new Intl.Segmenter("ja", { granularity: "grapheme" }).segment(text)].length
        : [...text].length;
      const duration = Math.min(2.1, Math.max(1.05, length * .032));
      durations.set(line, duration * 1000);
      line.style.setProperty("--tri-steps", String(Math.min(78, Math.max(18, length))));
      line.style.setProperty("--tri-duration", duration.toFixed(2) + "s");
      line.classList.add("tri-type-pending");
    });

    if ("IntersectionObserver" in window) {
      observer = new IntersectionObserver((entries) => {
        entries.forEach(({ target, isIntersecting }) => {
          if (isIntersecting) activate(target);
        });
      }, { rootMargin: "0px 0px -4% 0px", threshold: .08 });
      lines.forEach((line) => observer.observe(line));
    }
    // Scroll fallback also covers observers stubbed by tests or temporarily
    // unavailable during page transitions; no perpetual hidden headings.
    window.addEventListener("scroll", checkVisible, { passive: true });
    window.addEventListener("resize", checkVisible, { passive: true });
    window.requestAnimationFrame(checkVisible);

    reducedMotion.addEventListener?.("change", (event) => {
      if (!event.matches) return;
      observer?.disconnect();
      pending.clear();
      lines.forEach(finish);
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
    animateOnce();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
