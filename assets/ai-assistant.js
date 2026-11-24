/* Portfolio AI guide: entirely local, knowledge-based demo for GitHub Pages.
 * No external service, API key, analytics, storage or user-message transmission.
 * Answers are limited to verified facts already published in this portfolio.
 */
(() => {
  "use strict";

  const home = { desktop: "index.html", mobile: "mobile.html" };
  const pages = {
    trend: { desktop: "trend.html", mobile: "mobile-trend.html" },
    contact: { desktop: "contact.html", mobile: "mobile-contact.html" }
  };
  const reduceMotion = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const currentPage = window.location.pathname.split("/").pop() || "index.html";
  const mobileVariant = currentPage === "mobile.html" || currentPage.indexOf("mobile-") === 0;
  const mode = mobileVariant ? "mobile" : "desktop";

  function destination(target, section) {
    const route = target === "home" ? home[mode] :
      target === "resume" ? "resume.html" : pages[target] && pages[target][mode];
    return route ? route + (section ? "#" + section : "") : home[mode];
  }

  // Text is drawn from the site's published work experience, skills, study
  // dates and proposal; proposals are never presented as achieved results.
  const knowledge = {
    introduction: {
      answer: "黃博詩的作品集聚焦門市營運管理與區域營運改善。職涯經歷包含 Tomod's 日系藥妝、築心動物醫院及 Levi's；目前研讀萬能科技大學企業管理系。這份作品集以應徵台灣松本清區域營運經理為目標。",
      links: [["查看工作經歷", "home", "career"], ["了解應徵動機", "home", "motivation"]]
    },
    experience: {
      answer: "工作經歷包含：Tomod's 日系藥妝約 6 年（其中門市店長約 3 年）；築心動物醫院 4 年，擔任櫃台助理兼新人帶訓；Levi's 連鎖服飾 2 年，從事門市銷售、陳列和庫存工作。各段經歷的實際職責可在作品集中查看。",
      links: [["查看完整工作經歷", "home", "career"]]
    },
    tomods: {
      answer: "在 Tomod's，從門市正職走向門市店長。作品集記載的工作包括賣場營運、日常排班、人員帶訓、營收與成本檢視、商品研習，以及主持門市例會、參與總部月會。藥妝工作經歷約 6 年，其中店長約 3 年。",
      links: [["查看 Tomod's 經歷", "home", "career"]]
    },
    levis: {
      answer: "在 Levi's 任職約 2 年，負責主動銷售、依身型與穿搭需求提供建議，也參與陳列、商品整燙、補貨與庫存清點。這是服飾門市的工作經歷，不是區域經理職務。",
      links: [["查看 Levi's 經歷", "home", "career"]]
    },
    zhuxin: {
      answer: "在築心動物醫院任職約 4 年，擔任櫃台助理兼新人帶訓。工作涉及門診預約掛號、收費、飼主溝通、就診引導，以及新人的實務操作帶訓。",
      links: [["查看築心工作經歷", "home", "career"]]
    },
    skills: {
      answer: "作品集列出四項核心管理能力：① 門市標準化營運與日常排班；② 人員實務帶訓與工作指導；③ 顧客需求了解與客訴應對；④ 總部方針布達與門市例會協調。這些能力主要來自既有門市實務。",
      links: [["閱讀核心管理能力", "home", "competencies"]]
    },
    research: {
      answer: "藥妝產業研究從市場與競爭、消費者行為、商圈展店、數位轉型及人才管理切入，延伸提出六項門市改善方針、90 天區域營運推進計畫與衡量指標。它是研究與改善提案，不代表已實施或獲得企業驗證的成果。",
      links: [["閱讀完整產業研究", "trend", "market"], ["查看六項改善方針", "trend", "strategy"]]
    },
    strategy: {
      answer: "改善提案的六個方向是：熱銷缺貨與即期庫存、尖峰排班與現場服務、商品諮詢與新人帶訓、體驗陳列與特色商品、會員回購與跨通路承接、數位工具與作業成本。90 天計畫依序建立基準、選店試行、比較成效。這些是待評估的方案，不是已完成的績效。",
      links: [["查看六項改善方針", "trend", "strategy"], ["查看 90 天計畫", "trend", "roadmap"]]
    },
    education: {
      answer: "目前就讀萬能科技大學企業管理系，2026 年 10 月入學，預計 2030 年 6 月畢業。網站明確標示為研讀中，並非已畢業。",
      links: [["查看教育背景", "contact", "education"]]
    },
    motivation: {
      answer: "作品集以台灣松本清區域營運經理為應徵目標，說明希望將既有的單店管理、帶訓與營運協調經驗，延伸到跨店營運改善的思考。相關措施是到任後構想，而非已任職或已完成的成果。",
      links: [["閱讀應徵動機", "home", "motivation"], ["查看到任後構想", "home", "proposal"]]
    },
    resume: {
      answer: "網站有精簡 A4 個人簡歷頁，提供列印與 PDF 下載操作。若想查看工作經歷的完整敘述，也可以閱讀作品集首頁。",
      links: [["開啟 A4 個人簡歷", "resume", ""], ["查看工作經歷", "home", "career"]]
    },
    contact: {
      answer: "聯絡方式包含 Email、電話與 LINE，請點下方按鈕查看。",
      links: [["前往聯絡資訊", "contact", ""]]
    },
    greeting: {
      answer: "您好！想了解黃博詩的工作經歷、核心管理能力、藥妝產業研究，或取得聯絡方式嗎？可以點選上方的快捷問題，也可以直接輸入問題。",
      links: []
    },
    fallback: {
      answer: "這個版本是依作品集內容運作的本機問答導覽，無法回答網站未提供的資訊。可以改問「Tomod's 的工作內容」、「90 天改善計畫」、「核心管理能力」或「如何聯絡」，我會帶你找到相應內容。",
      links: [["瀏覽作品集", "home", ""], ["閱讀產業專題", "trend", ""]]
    }
  };

  const patterns = [
    ["contact", ["如何聯絡", "聯絡", "聯繫", "連絡", "聯絡方式", "聯絡資訊", "電子郵件", "信箱", "email", "mail", "電話", "line", "怎麼找你"]],
    ["resume", ["簡歷", "履歷表", "履歷pdf", "下載履歷", "列印履歷", "列印簡歷", "下載pdf", "a4", "pdf"]],
    ["education", ["學歷", "學校", "萬能", "企管系", "大學", "畢業", "就學", "讀什麼", "入學", "就讀", "學系"]],
    ["levis", ["levis", "牛仔", "服飾工作"]],
    ["zhuxin", ["築心", "動物醫院", "獸醫院"]],
    ["tomods", ["tomods", "tomods工作", "藥妝店長", "三友藥妝"]],
    ["strategy", ["90天", "九十天", "kpi", "績效指標", "改善方針", "改善策略", "改善計畫", "改善方案", "營運改善", "執行計畫", "管理提案", "六項", "6項"]],
    ["research", ["產業分析", "產業研究", "分析專題", "分析專案", "產業專題", "藥妝專題", "研究專題", "專題", "市場趨勢", "藥妝產業", "商圈", "數位轉型", "消費者行為", "專案", "競爭分析"]],
    ["skills", ["核心能力", "核心管理", "核心專長", "核心優勢", "企管核心", "管理能力", "專長", "優勢", "技能", "擅長", "強項", "帶訓", "排班"]],
    ["experience", ["工作經歷", "工作經驗", "過往經歷", "經歷", "資歷", "做過哪些工作", "任職", "履歷", "店長經驗"]],
    ["motivation", ["應徵動機", "應徵", "松本清", "求職", "為什麼選擇", "到任後"]],
    ["introduction", ["自我介紹", "介紹自己", "你是誰", "你叫什麼", "黃博詩", "博詩是誰", "關於你"]],
    ["greeting", ["你好", "您好", "嗨", "哈囉", "hello", "hi", "謝謝"]]
  ];

  function normalize(value) {
    return String(value).toLocaleLowerCase().normalize("NFKC").replace(/[^\p{L}\p{N}]/gu, "");
  }

  // Keep Latin terms as words: "online" must not match LINE, and "this"
  // must not match the greeting "hi". Chinese phrases can match naturally.
  function matches(question, word) {
    if (/^[a-z0-9]+$/i.test(word)) {
      const latin = String(question).normalize("NFKC").toLowerCase().replace(/['’]/g, "");
      return new RegExp("(^|[^a-z0-9])" + word.toLowerCase() + "(?=$|[^a-z0-9])").test(latin);
    }
    return normalize(question).includes(normalize(word));
  }

  function answerFor(question) {
    const value = normalize(question);
    const found = patterns.filter(([key, words]) =>
      key !== "greeting" && words.some(word => matches(question, word))
    ).map(([key]) => key);
    // A company-specific question usually needs only that company's answer.
    // Retain an explicitly requested general career overview, however.
    const companies = ["tomods", "levis", "zhuxin"];
    const broadCareer = /工作經歷|工作經驗|所有經歷|完整經歷|全部經歷|做過哪些工作/.test(value);
    const topics = found.filter(key =>
      !(key === "experience" && found.some(item => companies.includes(item)) && !broadCareer)
    );
    if (!topics.length) {
      const greeting = patterns.find(([key]) => key === "greeting");
      return greeting[1].some(word => value === normalize(word)) ? knowledge.greeting : knowledge.fallback;
    }
    if (topics.length === 1) return knowledge[topics[0]];
    const answers = topics.map(key => knowledge[key]);
    const links = [];
    const seen = new Set();
    answers.forEach(item => item.links.forEach(link => {
      const id = link[1] + "#" + link[2];
      if (!seen.has(id)) { seen.add(id); links.push(link); }
    }));
    return { answer: answers.map(item => item.answer).join("\n\n"), links };
  }

  function element(tag, className, textValue) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (textValue != null) node.textContent = textValue;
    return node;
  }

  function mount() {
    if (document.getElementById("bs-ai-root")) return;
    const root = element("div", "bs-ai-root");
    root.id = "bs-ai-root";
    if (document.querySelector(".mobile-bottom-bar")) {
      root.classList.add("bs-ai-root--bottom-nav");
    }

    const panel = element("section", "bs-ai-panel");
    panel.id = "bs-ai-panel";
    panel.setAttribute("aria-label", "黃博詩的 AI 履歷導覽");
    panel.setAttribute("role", "region");
    panel.hidden = true;

    const header = element("div", "bs-ai-header");
    const headerIcon = element("span", "bs-ai-header-icon", "✦");
    headerIcon.setAttribute("aria-hidden", "true");
    const titleBlock = element("div", "bs-ai-title-block");
    titleBlock.append(
      element("strong", "bs-ai-title", "博詩的 AI 數位分身"),
      element("span", "bs-ai-kicker", "PORTFOLIO GUIDE / 作品集導覽")
    );
    const close = element("button", "bs-ai-close", "×");
    close.type = "button";
    close.setAttribute("aria-label", "關閉履歷 AI 導覽");
    header.append(headerIcon, titleBlock, close);

    const messages = element("div", "bs-ai-messages");
    messages.id = "bs-ai-messages";
    messages.setAttribute("role", "log");
    messages.setAttribute("aria-label", "履歷導覽對話紀錄");
    messages.setAttribute("aria-live", "polite");
    messages.setAttribute("aria-relevant", "additions");

    const promptLabel = element("p", "bs-ai-chips-label", "QUICK QUESTIONS / 快速提問");
    const chips = element("div", "bs-ai-chips");
    const quick = [
      ["請自我介紹", "請自我介紹"],
      ["產業分析專題", "介紹你的產業分析專題"],
      ["企管核心專長", "你的企管核心專長"],
      ["如何聯絡你", "如何聯絡你"]
    ];

    const form = element("form", "bs-ai-form");
    const input = element("input", "bs-ai-input");
    input.type = "text";
    input.placeholder = "輸入想了解的問題…";
    input.autocomplete = "off";
    input.maxLength = 200;
    input.setAttribute("aria-label", "輸入作品集相關問題");
    const send = element("button", "bs-ai-send", "➤");
    send.type = "submit";
    send.setAttribute("aria-label", "送出問題");
    form.append(input, send);

    const note = element("p", "bs-ai-disclaimer",
      "本機知識庫示範｜回答以本站公開資料為準，不連線外部 AI。");
    panel.append(header, messages, promptLabel, chips, form, note);

    const launcher = element("button", "bs-ai-launcher");
    launcher.type = "button";
    launcher.setAttribute("aria-label", "開啟履歷 AI 導覽");
    launcher.setAttribute("aria-expanded", "false");
    launcher.setAttribute("aria-controls", "bs-ai-panel");
    const emblem = element("span", "bs-ai-launcher-emblem", "✦");
    emblem.setAttribute("aria-hidden", "true");
    launcher.append(emblem, element("span", "bs-ai-launcher-label", "問問 AI"));
    root.append(panel, launcher);
    document.body.append(root);

    let openedOnce = false;
    let busy = false;
    let composing = false;

    function scrollToLatest() {
      messages.scrollTop = messages.scrollHeight;
    }

    function message(sender, textValue, links) {
      const line = element("div", "bs-ai-message bs-ai-message--" + sender);
      const bubble = element("div", "bs-ai-bubble");
      bubble.append(element("p", "bs-ai-message-text", textValue));
      if (links && links.length) {
        const actions = element("div", "bs-ai-actions");
        links.forEach(data => {
          const a = element("a", "bs-ai-action-link", data[0] + " ↗");
          a.href = destination(data[1], data[2]);
          actions.append(a);
        });
        bubble.append(actions);
      }
      line.append(bubble);
      messages.append(line);
      scrollToLatest();
      return line;
    }

    function setOpen(open) {
      panel.hidden = !open;
      root.classList.toggle("bs-ai-root--open", open);
      launcher.setAttribute("aria-expanded", String(open));
      launcher.setAttribute("aria-label", open ? "收合履歷 AI 導覽" : "開啟履歷 AI 導覽");
      if (open) {
        if (!openedOnce) {
          message("bot",
            "您好！我是黃博詩的 AI 數位分身，專門介紹他的工作經歷、核心能力與藥妝產業分析專題。想先了解哪個部分？",
            []);
          openedOnce = true;
        }
        input.focus({ preventScroll: true });
      } else {
        launcher.focus({ preventScroll: true });
      }
    }

    function setBusy(value) {
      busy = value;
      input.disabled = value;
      send.disabled = value;
      chips.querySelectorAll("button").forEach(button => { button.disabled = value; });
    }

    function submitQuestion(rawQuestion) {
      const question = String(rawQuestion).trim().slice(0, 200);
      if (!question || busy) return;
      message("user", question, []);
      input.value = "";
      setBusy(true);
      const typing = element("div", "bs-ai-message bs-ai-message--bot");
      typing.setAttribute("aria-label", "正在整理作品集回答");
      const dots = element("div", "bs-ai-bubble bs-ai-typing");
      dots.setAttribute("aria-hidden", "true");
      for (let index = 0; index < 3; index += 1) {
        dots.append(element("i", "bs-ai-dot"));
      }
      typing.append(dots);
      messages.append(typing);
      scrollToLatest();

      window.setTimeout(() => {
        typing.remove();
        const response = answerFor(question);
        message("bot", response.answer, response.links);
        setBusy(false);
        if (!panel.hidden) input.focus({ preventScroll: true });
      }, reduceMotion ? 0 : Math.min(780, 320 + question.length * 17));
    }

    quick.forEach(item => {
      const button = element("button", "bs-ai-chip", item[0]);
      button.type = "button";
      button.addEventListener("click", () => submitQuestion(item[1]));
      chips.append(button);
    });

    launcher.addEventListener("click", () => setOpen(panel.hidden));
    close.addEventListener("click", () => setOpen(false));
    form.addEventListener("submit", event => {
      event.preventDefault();
      if (!composing) submitQuestion(input.value);
    });
    input.addEventListener("compositionstart", () => { composing = true; });
    input.addEventListener("compositionend", () => { composing = false; });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && !panel.hidden) setOpen(false);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount, { once: true });
  } else {
    mount();
  }
})();
