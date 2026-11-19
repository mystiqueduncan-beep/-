"""Real-browser acceptance for the compact, translucent chapter banners.

Use --baseline to capture unchanged source without asserting the new design.
--url checks the same four paths on an already deployed site. No source files
or remote application state are changed by this audit.
"""
import argparse
import functools
import http.server
import json
import math
import os
import threading
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

WIDTHS = (390, 430, 768, 1024, 1440, 1920)
PAGES = ("index.html", "trend.html", "mobile.html", "mobile-trend.html")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
parser.add_argument("--out", required=True)
parser.add_argument("--baseline", action="store_true")
parser.add_argument("--url", help="Deployed site base URL, including its project path")
args = parser.parse_args()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


server = None
if args.url:
    base = args.url.rstrip("/") + "/"
else:
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", 0), functools.partial(Handler, directory=args.root)
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}/"

MEASURE = """() => {
 const nav=document.querySelector('[data-keycap-marquee]');
 const viewport=nav.querySelector('.keycap-marquee__viewport');
 const belt=nav.querySelector('.keycap-marquee__belt');
 const group=nav.querySelector('.keycap-marquee__group');
 const sticky=nav.closest('nav');
 const rect=e=>{const r=e.getBoundingClientRect();return {
   x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}};
 const style=e=>{const s=getComputedStyle(e);return {
   background:s.backgroundColor,image:s.backgroundImage,opacity:s.opacity,
   blur:s.backdropFilter,borderRadius:s.borderRadius,position:s.position,
   fontSize:s.fontSize,outline:s.outlineStyle,outlineWidth:s.outlineWidth}};
 const ornament=p=>{const s=getComputedStyle(belt,p);return {
   content:s.content,display:s.display,align:s.justifyContent,
   paddingLeft:s.paddingLeft,paddingRight:s.paddingRight,
   letterSpacing:s.letterSpacing,height:s.height,background:s.backgroundColor}};
 const wrappers=[...nav.parentElement.closest('nav').querySelectorAll(':scope > .container')];
 const app=document.querySelector('.mobile-app-wrapper');
 const header=document.querySelector('.mobile-top-bar');
 return {nav:rect(nav),navStyle:style(nav),sticky:rect(sticky),stickyStyle:style(sticky),
   viewport:rect(viewport),viewportStyle:style(viewport),
   beltStyle:style(belt),groupStyle:style(group),
   containers:wrappers.map(e=>({rect:rect(e),style:style(e)})),
   app:app?rect(app):null,header:header?rect(header):null,
   groupWidth:group.getBoundingClientRect().width,
   links:[...group.querySelectorAll('a')].map(e=>({
     href:e.getAttribute('href'),rect:rect(e),style:style(e),
     textFits:e.scrollWidth<=e.clientWidth+1,
     ancestorOpacity:[e,group,belt,viewport,nav,sticky].every(x=>getComputedStyle(x).opacity==='1')})),
   before:ornament('::before'),after:ornament('::after'),
   start:parseFloat(belt.style.getPropertyValue('--keycap-start'))||0,
   interlude:parseFloat(belt.style.getPropertyValue('--keycap-interlude-width'))||0,
   scrollLeft:viewport.scrollLeft,clientWidth:viewport.clientWidth,
   scrollWidth:viewport.scrollWidth,overflow:document.documentElement.scrollWidth-innerWidth,
   current:[...group.querySelectorAll('[aria-current="location"]')].map(a=>a.getAttribute('href')),
   chapterWidth:document.querySelector(group.querySelector('a').getAttribute('href')).getBoundingClientRect().width,
   reading:nav.classList.contains('is-reading-section'),
   scrollY,enhanced:nav.classList.contains('is-enhanced')};
}"""


def alpha(color):
    if color == "transparent":
        return 0
    return float(color.rsplit(",", 1)[-1].rstrip(") ")) if color.startswith("rgba") else 1


def verify(condition, message, detail=None):
    if not condition:
        raise AssertionError((message, detail))


def scroll_value(viewport):
    return viewport.evaluate("e=>e.scrollLeft")


def leave_banner(page):
    page.mouse.move(1, 820)


def assert_design(row, mobile, trend, width):
    verify(row["overflow"] <= 1, "page horizontal overflow", row["overflow"])
    verify(row["navStyle"]["background"] == ("rgba(255, 249, 247, 0.2)" if row["reading"] else "rgba(255, 249, 247, 0.96)"),
           "visible banner cream background / alpha", row["navStyle"])
    verify(alpha(row["stickyStyle"]["background"]) == 0,
           "outer sticky must be transparent", row["stickyStyle"])
    verify(row["stickyStyle"]["blur"] == "none", "outer sticky must not blur the whole row")
    verify(row["stickyStyle"]["position"] == "sticky", "sticky positioning retained")
    verify(row["navStyle"]["blur"] == "none",
           "visible banner has no blur under current design", row["navStyle"])
    verify(22 <= float(row["navStyle"]["borderRadius"].split()[0].rstrip("px")) <= 28,
           "banner corner radius", row["navStyle"])
    for name in ("viewportStyle", "beltStyle", "groupStyle"):
        verify(alpha(row[name]["background"]) == 0 and row[name]["image"] == "none",
               "moving track / viewport must be transparent", {name: row[name]})
    for item in row["containers"]:
        verify(alpha(item["style"]["background"]) == 0, "layout container transparent", item)
    verify(abs(row["nav"]["x"] + row["nav"]["width"] / 2 - width / 2) <= 2,
           "visible banner horizontally centered", row["nav"])
    verify(row["nav"]["x"] >= 11 and row["nav"]["right"] <= width - 11,
           "banner stays within screen with side margins", row["nav"])
    verify(abs(row["nav"]["width"] - min(row["chapterWidth"], width - 24)) <= 2,
           "banner matches primary chapter width", row["nav"])
    verify(len(row["links"]) == (11 if trend else 6), "exact chapter link count for each page")
    for link in row["links"]:
        verify(alpha(link["style"]["background"]) == 1 and link["ancestorOpacity"],
               "buttons remain fully opaque", link)
        verify(link["rect"]["height"] >= (49 if mobile or width <= 768 else 57) - 1,
               "existing touch target height retained", link)
        verify(link["textFits"], "no clipping inside chapter button", link)
        verify(link["rect"]["y"] >= row["viewport"]["y"] - 1 and
               link["rect"]["bottom"] <= row["viewport"]["bottom"] - 2,
               "button and its shadow have vertical space", link)
    for key, alignment, padding in (("before", "flex-end", "paddingRight"),
                                    ("after", "flex-start", "paddingLeft")):
        ornament = row[key]
        verify("♡" in ornament["content"] and "✦" in ornament["content"],
               "original stars and hearts retained", ornament)
        verify(ornament["align"] == alignment and ornament[padding] == "20px" and
               ornament["letterSpacing"] == "6px", "original ornament spacing retained", ornament)
        verify(float(ornament["height"].rstrip("px")) >= 20,
               "ornaments have vertical room", ornament)
    verify(row["enhanced"] and row["scrollWidth"] > row["clientWidth"],
           "native scrolling is usable", row)
    verify(row["start"] == row["clientWidth"] and
           row["interlude"] == max(390, math.ceil(row["clientWidth"] * 1.12)),
           "run-in and run-out measured from actual viewport", row)
    verify(any(link["rect"]["right"] > row["viewport"]["x"] + 20 and
               link["rect"]["x"] < row["viewport"]["right"] - 20 for link in row["links"]),
           "initial chapter content is visible", row)


def interactions(page, row, width, mobile):
    nav = page.locator("[data-keycap-marquee]")
    viewport = nav.locator(".keycap-marquee__viewport")
    belt = nav.locator(".keycap-marquee__belt")
    group = nav.locator(".keycap-marquee__group")
    result = {}
    start = scroll_value(viewport)
    page.wait_for_timeout(220)
    verify(scroll_value(viewport) > start + 2, "autoplay advances")
    box = nav.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(60)
    paused = scroll_value(viewport)
    page.wait_for_timeout(200)
    verify(abs(scroll_value(viewport) - paused) <= 1, "real pointer hover pauses")
    leave_banner(page)
    page.wait_for_timeout(220)
    verify(scroll_value(viewport) > paused + 2, "pointer leave resumes")
    result["autoplay_hover"] = "passed"

    page.mouse.move(box["x"] + box["width"] * .7, box["y"] + box["height"] / 2)
    viewport.evaluate("e=>e.scrollLeft=parseFloat(e.querySelector('.keycap-marquee__belt').style.getPropertyValue('--keycap-start'))+20")
    before = scroll_value(viewport)
    old_hash = page.evaluate("location.hash")
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * .7 - 80, box["y"] + box["height"] / 2, steps=8)
    page.mouse.up()
    verify(scroll_value(viewport) >= before + 65, "real mouse drag scrolls")
    verify(page.evaluate("location.hash") == old_hash, "drag does not activate chapter")
    leave_banner(page)
    result["mouse_drag"] = "passed"

    cdp = page.context.new_cdp_session(page)
    x, y = box["x"] + box["width"] * .7, box["y"] + box["height"] / 2
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]})
    before = scroll_value(viewport)
    for delta in (12, 28, 48, 68, 88):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x - delta, "y": y}]})
    verify(scroll_value(viewport) >= before + 65, "real CDP touch swipe scrolls")
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    cdp.detach()
    page.wait_for_timeout(420)
    verify(not nav.evaluate("e=>e.classList.contains('is-touch-paused')||e.classList.contains('is-drag-paused')"),
           "touch release resumes engine")
    result["touch_swipe"] = "passed"

    # Let the deliberate post-drag click suppression expire, then perform a
    # real stationary click on an original key rather than dispatching a DOM event.
    page.wait_for_timeout(700)
    first_link = group.locator("a").first
    first_link.click()
    page.wait_for_timeout(250)
    verify(page.evaluate("location.hash") == first_link.get_attribute("href"),
           "real pointer click follows original chapter link")
    leave_banner(page)
    result["chapter_click"] = "passed"

    # Test the loop at its native scroll boundary without changing its geometry.
    leave_banner(page)
    viewport.evaluate("e=>e.scrollLeft=e.scrollWidth-e.clientWidth-2")
    page.wait_for_timeout(220)
    verify(scroll_value(viewport) < 24, "native-scroll loop wraps and continues")
    loop_start = scroll_value(viewport)
    page.wait_for_timeout(220)
    verify(scroll_value(viewport) > loop_start + 2, "loop cannot remain stuck on blank run-in")
    result["loop"] = "passed"

    # Keyboard pause survives native pointer hover re-evaluation on resize.
    # Measure relative to the viewport, excluding the banner's centering shift.
    box = nav.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    verify(nav.evaluate("e=>e.classList.contains('is-hover-paused')"),
           "resize measurement starts with real hover pause", box)
    viewport.focus()
    page.keyboard.press("ArrowRight")
    viewport.evaluate("e=>e.scrollLeft=parseFloat(e.querySelector('.keycap-marquee__belt').style.getPropertyValue('--keycap-start'))+5")
    relative = group.evaluate("e=>e.getBoundingClientRect().x-e.closest('.keycap-marquee__viewport').getBoundingClientRect().x")
    page.set_viewport_size({"width": width + 47, "height": 844})
    page.wait_for_timeout(150)
    resized = page.evaluate(MEASURE)
    verify(resized["start"] == resized["clientWidth"], "resize uses new actual viewport width", resized)
    relative_after = group.evaluate("e=>e.getBoundingClientRect().x-e.closest('.keycap-marquee__viewport').getBoundingClientRect().x")
    verify(abs(relative_after - relative) <= 2, "resize preserves visible chapter position", (relative, relative_after))
    page.set_viewport_size({"width": width, "height": 844})
    page.wait_for_timeout(100)
    page.evaluate("() => document.activeElement?.blur()")
    leave_banner(page)
    result["resize"] = "passed"

    viewport.focus()
    before = scroll_value(viewport)
    page.keyboard.press("ArrowRight")
    verify(scroll_value(viewport) >= before + 130, "keyboard arrow scrolls viewport")
    verify(nav.evaluate("e=>e.classList.contains('is-keyboard-paused')"), "keyboard pauses autoplay")
    first = group.locator("a").first
    first.focus()
    page.keyboard.press("Tab")
    focused = page.locator(":focus")
    verify(focused.evaluate("e=>e.matches('.keycap-marquee__group a:focus-visible')"),
           "keyboard chapter focus is discoverable")
    verify(focused.evaluate("e=>getComputedStyle(e).outlineStyle") != "none", "chapter focus outline retained")
    href = focused.get_attribute("href")
    page.keyboard.press("Enter")
    page.wait_for_timeout(300)
    verify(page.evaluate("location.hash") == href, "keyboard activation follows original chapter link")
    result["keyboard"] = "passed"

    target = "experience" if "trend" in page.url else "competencies"
    page.locator("#" + target).evaluate("e=>e.scrollIntoView({behavior:'instant',block:'start'})")
    page.wait_for_timeout(220)
    selected = group.locator('[aria-current="location"]')
    verify(selected.count() == 1 and selected.get_attribute("href") == "#" + target,
           "active chapter follows scroll")
    verify(selected.evaluate("e=>getComputedStyle(e).backgroundColor") == "rgb(223, 173, 193)",
           "active chapter retains stronger rose color")
    page.wait_for_function("""() => {const n=document.querySelector("[data-keycap-marquee]");return n.classList.contains("is-reading-section") && getComputedStyle(n).backgroundColor==="rgba(255, 249, 247, 0.2)"}""")
    after_scroll = page.evaluate(MEASURE)
    verify(abs(after_scroll["nav"]["width"] - row["nav"]["width"]) <= 1,
           "chapter changes cannot resize banner")
    top = after_scroll["header"]["bottom"] if mobile and after_scroll["header"] else 0
    verify(abs(after_scroll["sticky"]["y"] - top) <= 9, "sticky stays below existing header", after_scroll)
    section_top = page.locator("#" + target).bounding_box()["y"]
    verify(section_top >= after_scroll["sticky"]["bottom"] - 5, "chapter heading is not obscured")
    result["scroll_highlight_sticky"] = "passed"

    page.emulate_media(reduced_motion="reduce")
    page.wait_for_function("() => !document.querySelector('[data-keycap-marquee]').classList.contains('is-enhanced')")
    page.evaluate("() => document.activeElement?.blur()")
    leave_banner(page)
    before = scroll_value(viewport)
    page.wait_for_timeout(250)
    verify(abs(scroll_value(viewport) - before) <= 1 and
           not nav.evaluate("e=>e.classList.contains('is-enhanced')"), "reduced motion stops autoplay")
    verify(belt.evaluate("e=>getComputedStyle(e,'::before').display") == "none", "reduced-motion ornaments hidden")
    viewport.focus()
    viewport.evaluate("e=>e.scrollLeft=0")
    before = scroll_value(viewport)
    reduced_scroll_range = viewport.evaluate("e=>e.scrollWidth-e.clientWidth")
    page.keyboard.press("ArrowRight")
    verify(reduced_scroll_range <= 1 or scroll_value(viewport) > before,
           "manual keyboard scrolling works whenever reduced-motion content overflows")
    result["reduced_motion"] = "passed"
    page.evaluate("() => document.activeElement?.blur()")
    leave_banner(page)
    page.emulate_media(reduced_motion="no-preference")
    page.wait_for_function("() => document.querySelector('[data-keycap-marquee]').classList.contains('is-enhanced')")
    restored = page.evaluate(MEASURE)
    verify(any(link["rect"]["right"] > restored["viewport"]["x"] + 20 and
               link["rect"]["x"] < restored["viewport"]["right"] - 20 for link in restored["links"]),
           "restoring normal motion immediately shows original chapters", restored)
    before = scroll_value(viewport)
    page.wait_for_timeout(220)
    verify(scroll_value(viewport) > before + 2, "autoplay resumes after motion preference restoration")
    result["motion_preference_restoration"] = "passed"
    return result


results = []
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ.get("CHROME_PATH"),
            args=["--no-sandbox"],
        )
        for name in PAGES:
            for width in WIDTHS:
                mobile = name.startswith("mobile")
                row = {"page": name, "width": width, "baseline": args.baseline}
                page = browser.new_page(viewport={"width": width, "height": 844},
                                        has_touch=True, is_mobile=mobile,
                                        reduced_motion="no-preference")
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                try:
                    page.goto(urljoin(base, name) + "?view=" + ("mobile" if mobile else "desktop"),
                              wait_until="load", timeout=45000)
                    page.evaluate("() => Promise.race([document.fonts.ready,new Promise(r=>setTimeout(r,8000))])")
                    nav = page.locator("[data-keycap-marquee]")
                    nav.evaluate("e=>scrollTo({top:scrollY+e.closest('nav').getBoundingClientRect().top-" +
                                 ("53" if mobile else "0") + ",behavior:'instant'})")
                    leave_banner(page)
                    page.wait_for_timeout(250)
                    row["measurement"] = page.evaluate(MEASURE)
                    if not args.baseline:
                        assert_design(row["measurement"], mobile, "trend" in name, width)
                    # Pause only for a stable screenshot; moving-track visuals
                    # and all later interaction checks use the real engine.
                    box = nav.bounding_box()
                    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                    page.screenshot(path=str(out / f"{Path(name).stem}-{width}.png"))
                    leave_banner(page)
                    if not args.baseline:
                        row["interactions"] = interactions(page, row["measurement"], width, mobile)
                        verify(not errors, "page has no JavaScript exceptions", errors)
                    row["status"] = "captured" if args.baseline else "passed"
                except Exception as error:
                    row["status"] = "failed"
                    row["error"] = str(error)
                    page.screenshot(path=str(out / f"{Path(name).stem}-{width}-failure.png"))
                row["pageErrors"] = errors
                results.append(row)
                print(json.dumps({k: row[k] for k in ("page", "width", "status", "error") if k in row}), flush=True)
                page.close()
        browser.close()
finally:
    if server:
        server.shutdown()
    (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

assert len(results) == len(PAGES) * len(WIDTHS) and all(r["status"] != "failed" for r in results), \
    f"Banner acceptance failed; inspect {out / 'results.json'}"
print(f"PASS: {len(results)} real-browser banner {'baseline captures' if args.baseline else 'acceptance cases'}", flush=True)
