/* Put the two viewport choices in one consistent top-of-page bar.
   Existing source links remain functional if JavaScript is unavailable. */
(() => {
  "use strict";
  const body = document.body;
  if (!body || !body.classList.contains("page-desktop") && !body.classList.contains("page-mobile")) return;
  const mobile = body.classList.contains("page-mobile");
  const counterpart = document.querySelector(mobile ? "a.btn-switch-desktop" : "a.top-switch-link, a[href*='?view=mobile']");
  if (!counterpart) return;

  const label = mobile ? "電腦版" : "手機版";
  const current = mobile ? "手機版" : "電腦版";
  const currentHref = (window.location.pathname.split("/").pop() || "index.html")
    + (mobile ? "?view=mobile" : "?view=desktop");

  const nav = document.createElement("nav");
  nav.className = "view-mode-switch";
  nav.setAttribute("aria-label","瀏覽版本切換");
  const inner = document.createElement("div");
  inner.className = "view-mode-switch__inner";
  const cue = document.createElement("span");
  cue.className = "view-mode-switch__label";
  cue.textContent = "VIEW MODE · 瀏覽版本";
  const options = document.createElement("div");
  options.className = "view-mode-switch__options";
  const selected = document.createElement("a");
  selected.className = "view-mode-switch__option is-current";
  selected.href = currentHref;
  selected.textContent = current;
  selected.setAttribute("aria-current","page");

  const oldParent = counterpart.parentElement;
  counterpart.classList.add("view-mode-switch__option");
  counterpart.textContent = label;
  counterpart.removeAttribute("style");
  counterpart.removeAttribute("title");
  if (mobile) {
    options.append(counterpart,selected);
  } else {
    options.append(selected,counterpart);
  }
  inner.append(cue,options);
  nav.append(inner);
  const skip = body.querySelector(":scope > .skip-link");
  body.insertBefore(nav,skip ? skip.nextSibling : body.firstChild);

  // The research page formerly placed its version switch after its hero.
  const nowEmpty = oldParent && oldParent.textContent.trim() === "";
  if (nowEmpty && oldParent.classList.contains("analysis-switch-bar")) oldParent.remove();
  if (nowEmpty && oldParent.parentElement?.classList.contains("ticker-inner")) oldParent.remove();
})();
