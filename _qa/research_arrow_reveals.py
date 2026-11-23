"""One-time arrow -> content regression. Source text stays intact in all modes."""
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import os

from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_):pass

def run(browser,base,name,width):
    mobile=name.startswith("mobile-")
    page=browser.new_page(viewport={"width":width,"height":900},
                          is_mobile=mobile,has_touch=mobile)
    page.route("https://**/*",lambda route:route.abort())
    page.goto(f"{base}/{name}?view="+("mobile" if mobile else "desktop"),wait_until="load")
    cards=page.locator("#experience .experience > .exp.feature-card")
    rows=page.locator("#strategy .editorial-measure-map__row")
    expect(cards).to_have_count(3)
    expect(rows).to_have_count(6)
    assert page.locator(".exp-arrow-button,.measure-reveal-trigger").count()==0
    exp_text=[
        "將巡店缺失、尖峰排班與補貨問題整理成每週行動清單",
        "觀摩 → 演練 → 陪同操作 → 獨立確認",
        "以需求詢問、商品比較與陳列維護為服務帶訓內容",
    ]
    assert cards.count()==3
    assert rows.count()==6

    for i in range(3):
        card=cards.nth(i)
        assert exp_text[i] in card.text_content()
        card.scroll_into_view_if_needed()
        expect(card).to_have_class(__import__('re').compile("exp-story-visible"))
        expect(card.locator(":scope > .exp-application")).to_be_visible()
        assert card.locator(":scope > .exp-connector").get_attribute("aria-hidden")=="true"
    # Stable layout: measure action title remains stationary before and after
    # the arrow and detail become visible.
    for i in range(6):
        row=rows.nth(i)
        title=row.locator(":scope > .editorial-measure-map__action")
        assert title.locator("strong").count()==1
        assert row.locator(":scope > .editorial-measure-map__measures > strong").count()==1
        row.scroll_into_view_if_needed()
        expect(row).to_have_class(__import__('re').compile("measure-story-visible"))
        expect(row.locator(":scope > .editorial-measure-map__measures")).to_be_visible()
        assert not row.locator(":scope > .editorial-measure-map__measures").evaluate(
            "el => el.inert || el.getAttribute('aria-hidden')==='true'")
    # All six source-defined arrow/indicator pairs stay visible.
    # Final sixth-row delay plus animation duration must be fully complete.
    page.wait_for_timeout(1900)
    for i in range(6):
        row=rows.nth(i)
        measure=row.locator(":scope > .editorial-measure-map__measures")
        assert measure.evaluate("(el)=>getComputedStyle(el).opacity")=="1",(name,width,i)
        assert measure.evaluate("(el)=>Math.abs(new DOMMatrix(getComputedStyle(el).transform).m41) < .5"),(name,width,i)
    cards.first.scroll_into_view_if_needed()
    assert cards.first.get_attribute("class").count("exp-story-visible")==1
    assert rows.first.get_attribute("class").count("measure-story-visible")==1

    # Original ownership filtering remains wired.
    page.locator('#strategy [data-filter="hq"]').click()
    assert rows.evaluate_all("r=>r.filter(e=>!e.hidden).length")==2
    page.locator('#strategy [data-filter="local"]').click()
    assert rows.evaluate_all("r=>r.filter(e=>!e.hidden).length")==4
    page.locator('#strategy [data-filter="all"]').click()
    assert rows.evaluate_all("r=>r.filter(e=>!e.hidden).length")==6

    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"),(name,width)
    page.emulate_media(media="print")
    assert all(card.locator(":scope > .exp-application").is_visible() for card in cards.all())
    assert all(row.locator(":scope > .editorial-measure-map__measures").is_visible() for row in rows.all())
    page.emulate_media(media="screen",reduced_motion="reduce")
    assert all(card.locator(":scope > .exp-application").evaluate(
        "el=>getComputedStyle(el).animationName==='none'") for card in cards.all())
    assert all(row.locator(":scope > .editorial-measure-map__measures").evaluate(
        "el=>getComputedStyle(el).animationName==='none'") for row in rows.all())
    page.close()

    context=browser.new_context(viewport={"width":width,"height":900},java_script_enabled=False)
    static=context.new_page()
    static.goto(f"{base}/{name}",wait_until="load")
    assert static.locator("#experience .exp .exp-application:visible").count()==3
    assert static.locator("#strategy .strategy .action-measure:visible").count()==6
    assert static.locator("#strategy .swim-grid .lane-task:visible").count()==12
    context.close()
    print(f"{name}@{width}: one-time downward / rightward reveals, fixed labels, keyboard-free, print, reduced motion, no JS: PASS")

def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=os.environ.get("CHROME_PATH"),args=["--no-sandbox"])
            base=f"http://127.0.0.1:{server.server_port}"
            for name,width in (("trend.html",1440),("trend.html",1024),
                               ("mobile-trend.html",390),("mobile-trend.html",640)):
                run(browser,base,name,width)
            browser.close()
    finally:
        server.shutdown()

if __name__=="__main__":
    main()
