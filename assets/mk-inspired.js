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

    $$("#career .career-entry-card").forEach(card => {
      const spread = $(".career-spread", card);
      const list = $(".duty-bullet-list", spread || card);
      if (!spread || !list || !list.firstElementChild) return;
      // Original first duty becomes the always-visible synopsis, not duplicated.
      const copy = document.createElement("div");
      copy.className = "portfolio-career-copy";
      spread.insertBefore(copy, list);
      copy.append(list);
      const preview = document.createElement("ul");
      preview.className = "duty-bullet-list portfolio-career-preview";
      preview.append(list.firstElementChild);
      copy.insertBefore(preview, list);
      disclosure(card, [list], preview, $(".company-title", card)?.textContent.trim() || "工作經歷");
    });
    $$("#career .timeline-job-card").forEach(card => {
      const spread = $(".career-spread", card);
      const list = $(".duty-list", spread || card);
      if (!spread || !list) return;
      const preview = [...spread.children].find(node => node.tagName === "P");
      if (!preview) return;
      const copy = document.createElement("div");
      copy.className = "portfolio-career-copy";
      spread.insertBefore(copy, preview);
      copy.append(preview, list);
      disclosure(card, [list], preview, $(".job-title", card)?.textContent.trim() || "工作經歷");
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

    $$("#strategy .strategy.feature-card").forEach(card => {
      const title = $(".feature-card-title", card);
      if (!title) return;
      const after = [...card.children].slice([...card.children].indexOf(title) + 1);
      disclosure(card, after, title, title.textContent.trim());
    });

    // Research uses the same disclosure controls as the homepage. Keep the
    // introductory description, charts and source citations visible; reveal
    // the proposed actions using the shared accessible control.
    $("#competition .cards-2x2-grid > .feature-card, #consumer .cards-2x2-grid > .feature-card, #location .cards-2x2-grid > .feature-card, #digital .cards-2x2-grid > .feature-card, #people .cards-2x2-grid > .feature-card").forEach(card => {
      const title = $(".feature-card-title", card);
      const synopsis = $(".feature-card-text", card);
      const data = $(".feature-card-data", card);
      if (!title || !synopsis || !data) return;
      // Citations remain available even while detailed actions are folded.
      [...data.querySelectorAll(".research-inline-source")].forEach(source => card.append(source));
      disclosure(card, [data], synopsis, title.textContent.trim());
    });

    // Deep links and print should never leave a requested detail inaccessible.
    const openHash = () => {
      const hash = decodeURIComponent(location.hash.slice(1));
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
      const trendBars = $(section + " .animated-bar");
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
        bar.style.setProperty("--portfolio-bar-delay", index * 250 + "ms");
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

/* One-time editorial motion: major chapters slide in, inner cards simply fade in.
   Contact/hero buttons keep their one-time pop. Reduced-motion/print/no-JS are safe. */
(() => {
  "use strict";
  const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  if (!("IntersectionObserver" in window) || (reduced && reduced.matches)) return;

  const selectors = [
    ".mag-header > .container",
    ".source-verification",
    "main section",
    ".key-pillar-card",
    ".hero-action-card",
    "main .star-field-box",
    "main .stage-meta-box",
    "main .candidate-info-box",
    "main .candidate-specs-box",
    "main .timeline-job-card",
    "main .mobile-case-box",
    "main .pillar-mini-card",
    "main .contact-card-outer",
    "main .section-editorial-header",
    "main .mobile-card-title",
    "main #career > div > h2",
    "main .education-profile > h2",
    "main .editorial-card",
    "main .wide-star-case",
    "main .career-entry-card",
    "main .edu-dedicated-card",
    "main .stage-card",
    "main .research-summary-panel",
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
  const heroActions = [...document.querySelectorAll(".hero-cta-group > .mag-btn, .mobile-hero-actions > a, .mobile-hero-actions > button")];
  // Move only headline units: full sections and narrative cards fade in place.
  // Contact/hero actions retain their one-time pop.
  const chapterSelector = ".mag-header > .container, main .section-editorial-header, main .mobile-card-title, main #career > div > h2, main .education-profile > h2";
  // Phase cards use the dedicated interactive roadmap animation. Do not attach
  // one-time scroll reveal to panels that can be intentionally hidden.
  const allTargets = [...new Set([...targets, ...contactMethods, ...heroActions])]
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
    const heroIndex = heroActions.indexOf(el);
    const isPopItem = contactMethods.includes(el) || heroIndex !== -1;
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
