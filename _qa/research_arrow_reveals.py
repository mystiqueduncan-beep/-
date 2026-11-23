"""Regression suite for three directional research arrows and their source content.

Only source-preserving progressive enhancements are allowed. Tests cover
keyboard, mouse, touch, responsive layouts, reduced motion, print and no JS.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import os

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def run(browser, base, filename, width):
    mobile=filename.startswith("mobile-")
    page=browser.new_page(viewport={"width":width,"height":900},
                          is_mobile=mobile,has_touch=mobile)
    page.route("https://**/*",lambda route:route.abort())
    page.goto(f"{base}/{filename}?view="+("mobile" if mobile else "desktop"),
              wait_until="load")
    page.locator("#experience .exp-arrow-ready").first.wait_for()
    page.locator("#strategy .measure-flow-interactive").wait_for()
    page.locator("#strategy .arrow-flow-grid").wait_for()

    experience=page.locator("#experience .exp-arrow-ready")
    assert experience.count()==3
    actions=experience.locator(".exp-arrow-button")
    assert actions.count()==3
    original=[
        "將巡店缺失、尖峰排班與補貨問題整理成每週行動清單",
        "觀摩 → 演練 → 陪同操作 → 獨立確認",
        "以需求詢問、商品比較與陳列維護為服務帶訓內容",
    ]
    for i in range(3):
        assert original[i] in experience.nth(i).text_content()  # collapsed visually, never deleted
        assert actions.nth(i).get_attribute("aria-expanded")=="false"
        expect(experience.nth(i).locator(".exp-method-reveal")).to_be_hidden()
    actions.first.click()
    assert actions.first.get_attribute("aria-expanded")=="true"
    expect(experience.first.locator(".exp-method-reveal")).to_be_visible()
    actions.nth(1).click()
    assert actions.first.get_attribute("aria-expanded")=="false"
    assert actions.nth(1).get_attribute("aria-expanded")=="true"
    expect(experience.first.locator(".exp-method-reveal")).to_be_hidden()
    actions.nth(1).press("Enter")
    assert actions.nth(1).get_attribute("aria-expanded")=="false"

    # Six action-to-indicator arrows: clicking one pins its source-grounded
    # indicator, while all guardrails remain unchanged and printable.
    rows=page.locator("#strategy .measure-flow-interactive .measure-flow-row")
    assert rows.count()==6
    controls=rows.locator(".measure-reveal-trigger")
    for i in range(6):
        assert controls.nth(i).get_attribute("aria-expanded")=="false"
        expect(rows.nth(i).locator(".editorial-measure-map__measures")).to_be_hidden()
    controls.first.click()
    assert controls.first.get_attribute("aria-expanded")=="true"
    expect(rows.first.locator(".editorial-measure-map__measures")).to_be_visible()
    assert "缺貨率、庫存準確率、報損成本" in rows.first.inner_text()
    controls.nth(4).click()
    assert controls.first.get_attribute("aria-expanded")=="false"
    assert controls.nth(4).get_attribute("aria-expanded")=="true"
    assert "會員回購率、取貨準時率、退訂率" in rows.nth(4).inner_text()
    controls.nth(4).press(" ")
    assert controls.nth(4).get_attribute("aria-expanded")=="false"
    # Source ownership filter still works, including the derived diagram.
    page.locator("#strategy [data-filter='hq']").click()
    assert rows.nth(0).is_hidden()
    assert rows.nth(4).is_visible()
    page.locator("#strategy [data-filter='all']").click()
    assert rows.nth(0).is_visible()

    # Static swimlane: original four phase headings and twelve owner cells.
    # No selectable stages, additional mobile controls or animated highlights.
    grid=page.locator("#strategy .swim-grid")
    assert grid.count()==1
    assert grid.locator(":scope > .lane-stage").count()==4
    assert grid.locator(":scope > .lane-task").count()==12
    assert grid.locator(".arrow-flow-stage,.flow-follow,.flow-current").count()==0
    assert not grid.evaluate("(el)=>el.classList.contains('arrow-flow-grid') or el.classList.contains('mag-lane-focus')")
    assert page.locator("#strategy .arrow-flow-mobile-controls").count()==0
    assert grid.locator(".lane-stage").all_text_contents()==[
        "01 發現問題","02 選擇措施","03 試行追蹤","04 檢討擴大"
    ]
    # Check document-level overflow: the existing 720px swimlane may scroll
    # within its own accessible container but never stretch the whole page.
    overflow=page.evaluate("document.documentElement.scrollWidth - innerWidth")
    assert overflow<=2,(filename,width,"document overflow",overflow)

    page.emulate_media(media="print")
    for i in range(3):
        assert experience.nth(i).locator(".exp-method-reveal").is_visible(),\
            (filename,"print experience",i)
    for i in range(6):
        assert rows.nth(i).locator(".editorial-measure-map__measures").evaluate(
            "el=>getComputedStyle(el).visibility==='visible'"),\
            (filename,"print measure",i)
    assert page.locator("#strategy .arrow-flow-mobile-controls").count()==0
    page.emulate_media(media="screen",reduced_motion="reduce")
    expect(experience.first.locator(".exp-method-reveal")).to_be_hidden()
    expect(rows.first.locator(".editorial-measure-map__measures")).to_be_hidden()
    actions.first.click()
    expect(experience.first.locator(".exp-method-reveal")).to_be_visible()
    assert experience.first.locator(".exp-method-reveal").evaluate(
        "el=>getComputedStyle(el).transitionDuration.split(',').every(x=>parseFloat(x)===0)")

    page.close()

    # The source content must always survive disabled JavaScript.
    context=browser.new_context(viewport={"width":width,"height":900},
                                java_script_enabled=False)
    static=context.new_page()
    static.goto(f"{base}/{filename}",wait_until="load")
    assert static.locator("#experience .exp-application:visible").count()==3
    assert static.locator("#strategy .strategy .action-measure:visible").count()==6
    assert static.locator("#strategy .swim-grid .lane-task:visible").count()==12
    context.close()
    print(f"{filename}@{width}: arrow direction, toggles, guardrails, "
          "keyboard, static swimlane, print, reduced motion, no JS: PASS")


def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),
                               partial(Quiet,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(
                executable_path=os.environ.get("CHROME_PATH"),
                args=["--no-sandbox"]
            )
            base=f"http://127.0.0.1:{server.server_port}"
            for name,width in (
                ("trend.html",1440),("trend.html",1024),
                ("mobile-trend.html",390),("mobile-trend.html",640)
            ):
                run(browser,base,name,width)
            browser.close()
    finally:
        server.shutdown()


if __name__=="__main__":
    main()
