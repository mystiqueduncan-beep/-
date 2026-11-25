/* Portfolio AI guide: entirely local, knowledge-based demo for GitHub Pages.
 * No external service, API key, analytics or user-message transmission. Only
 * reminder timing and phrase history use tab-local session storage.
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
      answer: "您好，我是黃博詩，目前就讀萬能科技大學企業管理系，並以台灣松本清的區域營運經理為職涯發展目標。\n\n我具備 6 年 Tomod’s 日系藥妝經驗，其中 3 年擔任門市店長，負責門市營運、人力調度、商品庫存、營收與成本檢視，以及總部方針與門市之間的協調。\n\n此外，我曾在築心動物醫院任職 4 年，期間兼任新人帶訓，並具備 2 年 Levi’s 服飾零售經驗。不同產業的服務經歷，讓我更加重視顧客需求、標準作業流程、人員培育與團隊合作。\n\n我希望將既有的單店管理經驗與企業管理知識，延伸至跨店協調、巡店及店長輔導。因此，我也整理了藥妝產業趨勢研究，提出六項營運改善方針與 90 天推進構想，作為未來區域營運管理的思考基礎。",
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
      answer: "作品集列出四項核心管理能力：① 門市營運與人力調度；② 新人帶訓與工作指導；③ 顧客服務與客訴處理；④ 總部方針與營運協調。這些能力主要來自既有門市實務。",
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
      answer: "目前就讀萬能科技大學企業管理系，2026 年 10 月入學，預計 2030 年 6 月畢業。網站明確標示為就讀中，並非已畢業。",
      links: [["查看教育背景", "contact", "education"]]
    },
    motivation: {
      answer: "作品集以台灣松本清區域營運經理為應徵目標，說明希望將既有的單店管理、帶訓與營運協調經驗，延伸到跨店營運改善的思考。相關措施是到任後構想，而非已任職或已完成的成果。",
      links: [["閱讀應徵動機", "home", "motivation"], ["查看到任後構想", "home", "proposal"]]
    },
    resume: {
      answer: "可於個人聯絡資訊頁找到原有個人簡歷入口，並使用該頁的 A4 列印與 PDF 功能。",
      links: [["前往個人聯絡資訊", "contact", ""]]
    },
    contact: {
      answer: "您可以透過行動電話、Email 或 LINE 與我聯絡。個人聯絡資訊頁提供直接撥打電話、開啟郵件、LINE 及複製資訊的功能。",
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

  Object.assign(knowledge, {"cases":{"answer":"改善構想包含新人帶訓流程標準化、尖峰排班與補貨調度、總部方針與門市例會，以過往實務延伸為區域巡店管理的構想。具體細節與成效於面談確認。","links":[["查看門市營運改善構想","home","cases"]]},"proposal":{"answer":"到任後先熟悉規範及商圈特性，再與主管和店長確認優先改善重點，經核可後選店試行、記錄回饋及檢討成效。實際安排依公司制度與主管指示調整。","links":[["查看到任後工作構想","home","proposal"]]},"market":{"answer":"研究由市場趨勢及商品結構切入，作為門市資源配置與營運決策的起點。","links":[["查看市場趨勢與營運決策","trend","market"]]},"competition":{"answer":"研究討論特色商品、電子會員、專業照護、在地選品、門市取貨與虛實通路等競爭面向。","links":[["查看品牌競爭與市場定位","trend","competition"]]},"consumer":{"answer":"研究探討美妝保養品購買管道、價格與成分考量，以及價值感知、體驗及信任。","links":[["查看消費者行為與購物心理","trend","consumer"]]},"location":{"answer":"研究以商圈資料及實地查核、投資效益與風險作為展店策略的考量。","links":[["查看商圈研究與展店策略","trend","location"]]},"digital":{"answer":"研究涵蓋庫存與效期管理、AI 輔助補貨、電子標籤與掃碼、會員與門市承接。","links":[["查看零售數位轉型","trend","digital"]]},"people":{"answer":"專題提出清楚的工作標準、分階段新人帶訓、具體行為回饋，並兼顧人效與工作負荷。","links":[["查看人才管理","trend","people"]]},"roadmap":{"answer":"90 天計畫分三階段：建立基準及確認優先問題、選店試行及每週追蹤、比較成效並決定是否擴大。這是推進構想，不是已實施的成果。","links":[["查看90 天推進計畫","trend","roadmap"]]},"metrics":{"answer":"評估面向包含同店營收、毛利額與毛利率、抽查缺貨率、報損成本率、人時營業額及會員回購率，屬於評估構想。","links":[["查看營運成效與成本評估","trend","metrics"]]},"sources":{"answer":"專題末尾列出資料來源及研究限制，可前往查閱原始研究依據。","links":[["查看資料來源","trend","sources"]]},"region":{"answer":"應徵職位為區域營運經理，志願區域為桃竹苗及大台北；到職與排班安排於面談確認。","links":[["查看應徵資訊","contact",""]]}});
  const patterns = [
    ["region", ["志願區域","區域任職","任職區域","希望在哪些區域","到職與排班"]],
    ["roadmap", ["90天","九十天","推進計畫"]],
    ["metrics", ["評估改善成效","評估指標","績效指標","毛利率","缺貨率","人時營業額","kpi"]],
    ["sources", ["研究來源","研究依據","資料來源"]],
    ["cases", ["如何改善門市營運","門市營運改善構想","改善構想"]],
    ["proposal", ["到任後會怎麼規劃","到任後工作構想"]],
    ["market", ["市場研究","商品結構"]],
    ["competition", ["品牌競爭","品牌如何競爭"]],
    ["consumer", ["顧客重視","消費者行為","購物心理"]],
    ["location", ["展店","商圈研究"]],
    ["digital", ["數位工具","數位轉型"]],
    ["people", ["人才管理","培育門市人才"]],
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

  function answerFor(question, previous = "") {
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
      const key = greeting[1].some(word => value === normalize(word)) ? "greeting" : previous && /^(請|可以|能不能|再|說|講|更|一些|多|一點|詳細|具體|更多|介紹|呢|嗎|一下)+$/.test(value) ? previous : "fallback";
      return {...knowledge[key],topics:[key]};
    }
    if (topics.length === 1) return {...knowledge[topics[0]],topics};
    const answers = topics.map(key => knowledge[key]);
    const links = [];
    const seen = new Set();
    answers.forEach(item => item.links.forEach(link => {
      const id = link[1] + "#" + link[2];
      if (!seen.has(id)) { seen.add(id); links.push(link); }
    }));
    return { answer: answers.map(item => item.answer).join("\n\n"), links, topics };
  }

  function element(tag, className, textValue) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (textValue != null) node.textContent = textValue;
    return node;
  }

  const cards = {"introduction":["請自我介紹","認識職涯與管理理念"],"contact":["如何聯絡","了解聯絡管道"],"motivation":["為何應徵區域經理？","理解職涯方向"],"experience":["有哪些實務經驗？","比較三段職涯"],"tomods":["店長負責哪些工作？","深入藥妝管理"],"skills":["具備哪些管理能力？","四項核心專長"],"cases":["如何改善門市營運？","了解改善構想"],"proposal":["到任後會怎麼規劃？","工作構想"],"research":["研究的核心是什麼？","掌握專題重點"],"market":["市場研究看什麼？","市場與商品結構"],"competition":["品牌如何競爭？","比較競爭面向"],"consumer":["顧客重視什麼？","理解消費需求"],"location":["展店要考慮什麼？","商圈與投資風險"],"digital":["數位工具能做什麼？","理解虛實整合"],"people":["如何培育門市人才？","人才管理與帶訓"],"strategy":["有哪六項改善方針？","拆解改善方案"],"roadmap":["90 天如何執行？","三階段推進計畫"],"metrics":["如何評估改善成效？","營運與成本指標"],"sources":["研究依據在哪裡？","查閱原始資料"],"education":["目前的學歷是什麼？","了解教育背景"],"region":["希望在哪些區域任職？","了解求職條件"],"levis":["Levi’s 工作內容？","服飾零售實務"],"zhuxin":["築心的帶訓經驗？","了解服務與帶訓"]};
  const facts = {"introduction":[["6 年","藥妝經驗"],["3 年","店長經驗"]],"experience":[["6 年","Tomod’s"],["4 年","築心"],["2 年","Levi’s"]],"tomods":[["6 年","藥妝經驗"],["3 年","店長經驗"]],"research":[["6 項","改善方針"],["90 天","推進構想"]],"roadmap":[["90 天","推進計畫"],["3 階段","執行構想"]]};
  const followTopics = {"introduction":["tomods","skills","motivation"],"experience":["tomods","skills","research"],"tomods":["skills","cases","people"],"skills":["tomods","cases","people"],"research":["strategy","roadmap","metrics"],"strategy":["roadmap","metrics"],"roadmap":["metrics","strategy"],"contact":["region","education"],"education":["introduction","motivation"],"region":["motivation","contact"],"motivation":["tomods","skills","proposal"],"cases":["strategy","roadmap"],"proposal":["roadmap","metrics"],"market":["competition","consumer","strategy"],"competition":["consumer","digital"],"consumer":["competition","strategy"],"location":["market","metrics"],"digital":["strategy","metrics"],"people":["skills","tomods"],"metrics":["roadmap","strategy"],"sources":["research","metrics"],"levis":["experience","skills"],"zhuxin":["people","skills"]};
  const pageKind = /trend|data-visualization/.test(currentPage) ? "trend" : /contact/.test(currentPage) ? "contact" : "home";
  const menus = {
    home:["motivation","experience","tomods","skills","cases","introduction"],
    trend:["research","market","strategy","roadmap","metrics","sources"],
    contact:["education","contact","region","motivation","experience","introduction"]
  };
  const sectionDefs = {
    home:[["#profile,.mag-hero-grid","profile","introduction","想先認識我嗎？"],["#motivation","motivation","motivation","想了解應徵動機嗎？"],["#competencies","competencies","skills","想了解管理能力嗎？"],["#cases","cases","cases","想了解改善構想嗎？"],["#career","career","experience","想了解工作經歷嗎？"],["#proposal","proposal","proposal","想了解工作構想嗎？"],["#research","research","research","想看看產業研究嗎？"]],
    trend:[["#market","market","market","想了解市場趨勢嗎？"],["#competition","competition","competition","想了解品牌競爭嗎？"],["#consumer","consumer","consumer","想了解消費者行為嗎？"],["#location","location","location","想了解展店策略嗎？"],["#digital","digital","digital","想了解數位轉型嗎？"],["#people","people","people","想了解人才管理嗎？"],["#experience","experience","tomods","想了解跨店管理嗎？"],["#strategy","strategy","strategy","想了解改善方針嗎？"],["#roadmap","roadmap","roadmap","想了解執行計畫嗎？"],["#metrics","metrics","metrics","想了解評估指標嗎？"],["#sources","sources","sources","想查看研究來源嗎？"]],
    contact:[[".candidate-specs-box","profile","region","想了解應徵方向嗎？"],["#education","education","education","想了解教育背景嗎？"],[".personal-resume-link","resume","region","想了解應徵方向嗎？"],["#phoneText,#emailText,#lineIdText","contact","contact","想找聯絡方式嗎？"]]
  };
  const highlightKey = "bs-reading-target";
  function revealTarget(section, scroll) {
    const target = document.getElementById(section);
    if (!target) return;
    if (scroll) target.scrollIntoView({block:"start",behavior:reduceMotion?"instant":"smooth"});
    target.classList.remove("bs-reading-highlight");
    requestAnimationFrame(()=>target.classList.add("bs-reading-highlight"));
    setTimeout(()=>target.classList.remove("bs-reading-highlight"),2600);
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
    panel.setAttribute("aria-label", "黃博詩的閱讀小助手");
    panel.setAttribute("role", "region");
    panel.hidden = true;

    const header = element("div", "bs-ai-header");
    const headerIcon = element("span", "bs-ai-header-icon", "✦");
    headerIcon.setAttribute("aria-hidden", "true");
    const titleBlock = element("div", "bs-ai-title-block");
    titleBlock.append(
      element("strong", "bs-ai-title", "閱讀小助手"),
      element("span", "bs-ai-kicker", "PORTFOLIO GUIDE / 作品集導覽")
    );
    const close = element("button", "bs-ai-close", "×");
    close.type = "button";
    close.setAttribute("aria-label", "關閉閱讀小助手");
    const reset = element("button", "bs-ai-reset", "↺ 重新開始對話");
    reset.type = "button";
    header.append(headerIcon, titleBlock, reset, close);
    const contextLabel = element("p","bs-ai-context");

    const messages = element("div", "bs-ai-messages");
    messages.id = "bs-ai-messages";
    messages.setAttribute("role", "log");
    messages.setAttribute("aria-label", "履歷導覽對話紀錄");
    messages.setAttribute("aria-live", "polite");
    messages.setAttribute("aria-relevant", "additions");

    const promptLabel = element("p", "bs-ai-chips-label", "QUICK QUESTIONS / 快速提問");
    const chips = element("div", "bs-ai-chips");


    const form = element("form", "bs-ai-form");
    const input = element("input", "bs-ai-input");
    input.type = "text";
    input.placeholder = "例如：如何聯絡？";
    input.autocomplete = "off";
    input.maxLength = 200;
    input.setAttribute("aria-label", "輸入作品集相關問題");
    const send = element("button", "bs-ai-send", "➤");
    send.type = "submit";
    send.setAttribute("aria-label", "送出問題");
    form.append(input, send);

    const note = element("p", "bs-ai-disclaimer",
      "本機知識庫示範｜回答以本站公開資料為準，不連線外部 AI。");
    panel.append(header, contextLabel, messages, promptLabel, chips, form, note);

    const launcher = element("button", "bs-ai-launcher");
    launcher.type = "button";
    launcher.setAttribute("aria-label", "開啟閱讀小助手");
    launcher.setAttribute("aria-expanded", "false");
    launcher.setAttribute("aria-controls", "bs-ai-panel");
    const face = element("span", "bs-ai-launcher-face");
    const emblem = element("span", "bs-ai-launcher-emblem", "♥");
    emblem.setAttribute("aria-hidden", "true");
    const starOne = element("span", "bs-ai-launcher-star bs-ai-launcher-star--one", "✧");
    const starTwo = element("span", "bs-ai-launcher-star bs-ai-launcher-star--two", "✦");
    starOne.setAttribute("aria-hidden", "true");
    starTwo.setAttribute("aria-hidden", "true");
    const label = element("span", "bs-ai-launcher-copy");
    label.append(element("strong", "bs-ai-launcher-label", "閱讀小助手"),
      element("small", "bs-ai-launcher-caption", "找資料・直達章節"));
    face.append(emblem, label, starOne, starTwo);
    launcher.append(face);
    const hint = element("button", "bs-ai-guide-hint");
    hint.type = "button";
    hint.tabIndex = -1;
    hint.setAttribute("aria-label", "開啟閱讀小助手");
    hint.setAttribute("aria-hidden", "true");
    const hintText = element("span", "bs-ai-guide-hint-text");
    hintText.setAttribute("aria-hidden", "true");
    const cursor = element("span", "bs-ai-guide-cursor");
    cursor.setAttribute("aria-hidden", "true");
    cursor.hidden = true;
    const hintFace = element("span", "bs-ai-guide-face");
    hintFace.append(hintText, cursor);
    hint.append(hintFace);
    const dock = element("div","bs-ai-dock");
    dock.append(launcher,hint);
    root.append(panel, dock);
    document.body.append(root);

    let openedOnce = false;
    let busy = false;
    let composing = false, previousTopic = "", replyTimer = 0, typingLine = null, menuMode = true;
    const sections = sectionDefs[pageKind].flatMap(d=>Array.from(document.querySelectorAll(d[0])).map(node=>({node,id:d[1],topic:d[2],phrase:d[3]})));
    function visibleSection() {
      const y = innerHeight * .32;
      const candidates = sections.map(s=>({...s,box:s.node.getBoundingClientRect()})).filter(s=>s.box.height>0);
      const inside = candidates.filter(s=>s.box.top<=y && s.box.bottom>=y).sort((a,b)=>b.box.top-a.box.top);
      if (inside.length) return inside[0];
      return candidates.filter(s=>s.box.top<=y).sort((a,b)=>b.box.top-a.box.top)[0] || candidates[0] || {id:"overview",topic:menus[pageKind][0],phrase:"想先看看重點嗎？"};
    }
    let active = visibleSection(), pendingSection = false, sectionTimer = 0;
    let afterClose = 0;
    function updateContext() {
      contextLabel.textContent = "正在閱讀："+(cards[active.topic]?.[1] || "作品集");
    }

    // Contextual prompts: all approved copy, no tracking or question storage.
    const common = ["想找什麼嗎？", "需要我帶路嗎？", "有什麼想了解的嗎？",
      "想先看看重點嗎？", "不知道從哪裡看起嗎？",
      "有需要我幫忙的嗎？", "想讓我為你介紹嗎？"];
    const contextual = currentPage.includes("trend") || currentPage === "data-visualization.html"
      ? ["想看看產業研究嗎？", "想了解管理能力嗎？"]
      : currentPage.includes("contact")
        ? ["想找聯絡方式嗎？", "想了解教育背景嗎？"]
        : ["想了解工作經歷嗎？", "想了解管理能力嗎？", "想了解應徵動機嗎？"];
    const key = "bs-ai-guide-timing-v1";
    const timing = { first:2000, enter:400, char:140, hold:10000, fade:600, gap:20000, idle:2000 };
    let state = { seen:false, nextAt:Date.now()+timing.first, last:"", used:[] };
    try {
      const saved = JSON.parse(sessionStorage.getItem(key) || "null");
      if (saved && typeof saved.seen === "boolean" && Number.isFinite(saved.nextAt)
        && typeof saved.last === "string" && Array.isArray(saved.used)) {
        state = { seen:saved.seen, nextAt:saved.nextAt, last:saved.last, used:saved.used.slice(-12) };
      }
    } catch (_) { /* Storage can be denied; reminders still work within the page. */ }
    const save = () => { try { sessionStorage.setItem(key, JSON.stringify(state)); } catch (_) {} };
    save();
    let timer = 0, lastScroll = -Infinity, hintVisible = false;
    function clearHintTimer() { window.clearTimeout(timer); timer = 0; }
    function hideHint() {
      hintVisible = false;
      hint.classList.remove("is-visible");
      hint.tabIndex = -1;
      hint.setAttribute("aria-hidden", "true");
      cursor.hidden = true;
    }
    function pickPhrase() {
      if (!state.seen) return common[0];
      const specificPool = [...new Set([active.phrase,...contextual])];
      if (pendingSection) {
        pendingSection=false;
        const options=specificPool.filter(s=>s!==state.last);
        return options[Math.floor(Math.random()*options.length)];
      }
      const pool = common.concat(specificPool);
      let available = pool.filter(s => s !== state.last && !state.used.includes(s));
      if (!available.length) {
        state.used = [];
        available = pool.filter(s => s !== state.last);
      }
      const general = available.filter(s => common.includes(s));
      const specific = available.filter(s => specificPool.includes(s));
      const group = general.length && specific.length
        ? (Math.random() < .65 ? general : specific)
        : available;
      return group[Math.floor(Math.random()*group.length)];
    }
    function scheduleHint() {
      clearHintTimer();
      if (!panel.hidden || document.hidden) return;
      const delay = Math.max(0, state.nextAt-Date.now(), lastScroll+timing.idle-Date.now());
      timer = window.setTimeout(() => {
        if (!panel.hidden || document.hidden) return;
        if (Date.now()-lastScroll < timing.idle || Date.now() < state.nextAt) { scheduleHint(); return; }
        showHint();
      }, delay);
    }
    function showHint() {
      const phrase = pickPhrase();
      pendingSection = false;
      const letters = Array.from(phrase);
      const duration = reduceMotion ? 0 : timing.enter+letters.length*timing.char;
      state.seen = true;
      state.last = phrase;
      state.used = state.used.concat(phrase).slice(-12);
      state.nextAt = Date.now()+duration+timing.hold+(reduceMotion ? 0 : timing.fade)+timing.gap;
      save();
      hintVisible = true;
      hintText.textContent = reduceMotion ? phrase : "";
      cursor.hidden = reduceMotion;
      hint.classList.add("is-visible");
      hint.tabIndex = 0;
      hint.removeAttribute("aria-hidden");
      const finish = () => {
        cursor.hidden = true;
        timer = window.setTimeout(endHint, timing.hold);
      };
      let i = 0;
      const type = () => {
        if (!hintVisible) return;
        hintText.textContent = letters.slice(0, ++i).join("");
        if (i < letters.length) timer = window.setTimeout(type, timing.char);
        else finish();
      };
      if (reduceMotion) finish();
      else timer = window.setTimeout(type, timing.enter+timing.char);
    }
    function endHint() {
      // Do not remove a focused control underneath keyboard users.
      if (document.activeElement === hint) {
        timer = window.setTimeout(endHint, 1000);
        return;
      }
      hideHint();
      state.nextAt = Date.now()+(reduceMotion ? 0 : timing.fade)+(pendingSection ? 0 : timing.gap);
      save();
      scheduleHint();
    }
    function stopHint() { clearHintTimer(); hideHint(); }
    function restartHint() {
      stopHint();
      state.nextAt = Date.now()+timing.gap;
      save();
      scheduleHint();
    }
    function detectSection() {
      const next = visibleSection();
      if (next.id === active.id) return;
      active = next;
      updateContext();
      if (!panel.hidden) { if(menuMode && !busy) renderMenu(); return; }
      if (!state.seen || document.hidden) return;
      pendingSection = true;
      if (!hintVisible) {
        state.nextAt = Math.max(Date.now(), afterClose);
        save();
        scheduleHint();
      }
    }
    window.addEventListener("scroll", () => {
      lastScroll = Date.now();
      clearTimeout(sectionTimer);
      sectionTimer = setTimeout(detectSection,timing.idle);
    }, { passive:true });
    window.addEventListener("resize",()=>{clearTimeout(sectionTimer);sectionTimer=setTimeout(detectSection,timing.idle);},{passive:true});
    try {
      const pending=JSON.parse(sessionStorage.getItem(highlightKey)||"null");
      if(pending && pending.page===currentPage && Date.now()-pending.at<30000) {
        sessionStorage.removeItem(highlightKey);
        setTimeout(()=>revealTarget(pending.section,true),350);
      }
    } catch (_) {}
    updateContext();
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) stopHint();
      else scheduleHint();
    });
    window.addEventListener("pagehide", stopHint);
    window.addEventListener("pageshow", () => { if (!hintVisible) scheduleHint(); });
    scheduleHint();

    function scrollToLatest() {
      messages.scrollTop = messages.scrollHeight;
    }

    function message(sender, textValue, links, topics = []) {
      const line = element("div", "bs-ai-message bs-ai-message--" + sender);
      const bubble = element("div", "bs-ai-bubble");
      bubble.append(element("p", "bs-ai-message-text", textValue));
      const data = facts[topics[0]];
      if (data && sender==="bot") {
        const grid=element("div","bs-ai-facts");
        data.forEach(([v,l])=>{const card=element("div","bs-ai-fact");card.append(element("strong","",v),element("span","",l));grid.append(card);});
        bubble.append(grid);
      }
      if (links && links.length) {
        const actions = element("div", "bs-ai-actions");
        links.forEach(data => {
          const a = element("a", "bs-ai-action-link", data[0] + " ↗");
          a.href = destination(data[1], data[2]);
          a.addEventListener("click",event=>{
            if (event.metaKey||event.ctrlKey||event.shiftKey||event.altKey||!data[2]) return;
            const url = new URL(a.href,location.href);
            const same = url.pathname===location.pathname;
            if (same && document.getElementById(data[2])) {
              event.preventDefault();
              history.pushState(null,"",url.hash);
              setOpen(false);
              revealTarget(data[2],true);
            } else {
              try {sessionStorage.setItem(highlightKey,JSON.stringify({page:url.pathname.split("/").pop(),section:data[2],at:Date.now()}));} catch (_) {}
            }
          });
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
      launcher.setAttribute("aria-label", open ? "收合閱讀小助手" : "開啟閱讀小助手");
      pendingSection=false;
      if (!open) afterClose=Date.now()+timing.gap;
      restartHint();
      if (open) {
        active=visibleSection(); updateContext();
        if (!openedOnce) {
          message("bot",
            "您好！我是黃博詩的 AI 數位分身。想了解哪一部分呢？選擇下方主題，或直接輸入問題，我會提供內容摘要及對應章節。",
            []);
          openedOnce = true;
          renderMenu();
        } else if(menuMode&&!busy) renderMenu();
        if(!mobileVariant) input.focus({ preventScroll: true });
        else reset.focus({preventScroll:true});
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

    function submitQuestion(rawQuestion, key = "") {
      const question = String(rawQuestion).trim().slice(0, 200);
      if (!question || busy) return;
      menuMode=false;
      message("user", question, []);
      input.value = "";
      setBusy(true);
      const typing = element("div", "bs-ai-message bs-ai-message--bot");
      typingLine=typing;
      typing.setAttribute("aria-label", "正在整理作品集回答");
      const dots = element("div", "bs-ai-bubble bs-ai-typing");
      dots.setAttribute("aria-hidden", "true");
      for (let index = 0; index < 3; index += 1) {
        dots.append(element("i", "bs-ai-dot"));
      }
      typing.append(dots);
      messages.append(typing);
      scrollToLatest();

      replyTimer=window.setTimeout(() => {
        typing.remove(); typingLine=null;
        const response = key ? {...knowledge[key],topics:[key]} : answerFor(question,previousTopic);
        const topics=response.topics||[];
        if(topics[0] && !["greeting","fallback","resume"].includes(topics[0])) previousTopic=topics[0];
        const line=message("bot", response.answer, response.links, topics);
        setBusy(false);
        renderFollow(topics[0]);
        if (!panel.hidden && document.activeElement===document.body) input.focus({ preventScroll: true });
        if(topics[0]==="introduction") messages.scrollTop=line.offsetTop-messages.offsetTop;
      }, reduceMotion ? 0 : Math.min(780, 320 + question.length * 17));
    }

    function makeCard(k,fixed=false,short=false) {
      const b=element("button","bs-ai-chip"+(fixed?" bs-ai-chip--fixed":""));
      b.type="button";b.dataset.topic=k;
      const title=mobileVariant&&k==="introduction"?"快速認識":mobileVariant&&k==="contact"?"有哪些聯絡方式？":cards[k][0];
      b.setAttribute("aria-label",title);
      b.append(element("strong","",title));
      if(!short)b.append(element("small","",cards[k][1]));
      b.addEventListener("click",()=>submitQuestion(title,k));
      return b;
    }
    function renderMenu() {
      menuMode=true;
      chips.classList.remove("bs-ai-chips--follow");
      promptLabel.textContent="QUICK QUESTIONS / 快速提問";
      chips.replaceChildren();
      const all=[...new Set([active.topic,...menus[pageKind],...menus.home])];
      const fixed=mobileVariant?[]:["introduction","contact"];
      const choices=all.filter(k=>cards[k]&&!fixed.includes(k));
      [...fixed,...choices.slice(0,6-fixed.length)].forEach(k=>chips.append(makeCard(k,fixed.includes(k))));
    }
    function renderFollow(k) {
      menuMode=false;
      chips.classList.add("bs-ai-chips--follow");
      promptLabel.textContent="接下來想了解什麼呢？";
      chips.replaceChildren();
      const options=[...new Set([...(followTopics[k]||menus[pageKind].slice(0,3)),...(!mobileVariant?["contact"]:[])])];
      options.filter(x=>cards[x]&&x!==k).slice(0,4).forEach(x=>chips.append(makeCard(x,false,true)));
      const back=element("button","bs-ai-chip bs-ai-back","返回主選單");
      back.type="button";back.addEventListener("click",()=>{renderMenu();chips.querySelector("button")?.focus({preventScroll:true});});chips.append(back);
    }
    reset.addEventListener("click",()=>{
      clearTimeout(replyTimer);typingLine?.remove();typingLine=null;
      setBusy(false);previousTopic="";input.value="";
      messages.replaceChildren();
      message("bot","您好！我是黃博詩的 AI 數位分身。想了解哪一部分呢？選擇下方主題，或直接輸入問題，我會提供內容摘要及對應章節。",[]);
      renderMenu();
      reset.focus({preventScroll:true});
    });
    renderMenu();

    launcher.addEventListener("click", () => setOpen(panel.hidden));
    hint.addEventListener("click", () => setOpen(true));
    close.addEventListener("click", () => setOpen(false));
    form.addEventListener("submit", event => {
      event.preventDefault();
      if (!composing) submitQuestion(input.value);
    });
    input.addEventListener("compositionstart", () => { composing = true; });
    input.addEventListener("compositionend", () => { composing = false; });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && !panel.hidden) setOpen(false);
      else if (event.key === "Escape" && hintVisible) {
        if (document.activeElement === hint) launcher.focus({ preventScroll:true });
        restartHint();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount, { once: true });
  } else {
    mount();
  }
})();
