"""Source-preserving research visualization regression checks.

The improved presentations retain original five forces and all research copy.
Run on both desktop/mobile with JavaScript, reduced motion and no-JS fallbacks.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import os

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def assert_ready(page):
    page.locator("#market .mag-strategy-flow").wait_for()
    checks = {
        "#market .mag-strategy-flow > .compare-row": 4,
        "#competition .mag-swot .feature-card": 4,
        "#consumer .mag-customer-journey > .compare-row": 5,
        "#location .mag-trade-selector > .mag-trade-choice": 4,
        "#digital .mag-digital-steps > .compare-row": 3,
        "#people .mag-people-methods > .feature-card": 4,
        "#strategy .mag-strategy-board > .strategy": 6,
        "#strategy .swim-grid > .lane-task": 12,
        "#metrics .mag-metric-pairs > .metric-tile": 6,
        "#metrics .mag-branching": 1,
        "#competition .editorial-five-forces.five-force-interactive": 1,
    }
    for selector, expected in checks.items():
        got = page.locator(selector).count()
        assert got == expected, (selector, expected, got)

    assert page.locator("#market .mag-strategy-flow").inner_text().count("清楚介紹差異與核准優惠") == 1
    assert page.locator("#consumer .mag-customer-journey").inner_text().count("需求式分類與導引") == 1


def test_view(browser, base, filename, width):
    mobile = filename.startswith("mobile-")
    page=browser.new_page(viewport={"width": width, "height": 900},
                          is_mobile=mobile,has_touch=mobile)
    page.route("https://**/*", lambda r: r.abort())
    view="mobile" if mobile else "desktop"
    page.goto(f"{base}/{filename}?view={view}",wait_until="load")
    assert_ready(page)

    flow=page.locator("#market .mag-strategy-flow > .compare-row").first
    display=flow.evaluate("(el) => getComputedStyle(el).display")
    assert display=="grid",(filename,width,"strategy flow",display)
    if width>850:
        columns=flow.evaluate("(el) => getComputedStyle(el).gridTemplateColumns")
        assert len(columns.split())==3,(filename,width,columns)

    journey=page.locator("#consumer .mag-customer-journey")
    columns=journey.evaluate("(el) => getComputedStyle(el).gridTemplateColumns")
    if width<=690:
        assert len(columns.split())==1,(filename,"journey small",columns)
    elif width>1050:
        assert len(columns.split())==5,(filename,"journey desktop",columns)

    store=page.locator("#location .mag-trade-selector > .mag-trade-choice")
    hints=store.locator(":scope > .mag-trade-hint")
    assert hints.count()==4,(filename,"missing trade directions")
    assert store.first.get_attribute("aria-expanded")=="true"
    assert store.nth(1).get_attribute("aria-expanded")=="false"
    assert hints.first.inner_text()=="點擊－收合營運方向"
    assert hints.nth(1).inner_text()=="點擊＋查看營運方向"
    for card in store.all():
        assert card.locator(":scope > .mag-trade-hint").is_visible()
        assert card.evaluate("""el => {
          const a=el.getBoundingClientRect();
          const b=el.querySelector('.mag-trade-hint').getBoundingClientRect();
          return b.left>=a.left-1 && b.right<=a.right+1 && b.bottom<=a.bottom+1;
        }"""),(filename,width,"hint overflows card")
    store.nth(1).click()
    assert store.nth(1).get_attribute("aria-expanded")=="true"
    assert hints.nth(1).inner_text()=="點擊－收合營運方向"
    assert store.first.get_attribute("aria-expanded")=="false"
    assert hints.first.inner_text()=="點擊＋查看營運方向"
    assert store.nth(1).locator("strong").is_visible()
    assert not store.first.locator("strong").is_visible()
    store.nth(1).click()
    assert store.nth(1).get_attribute("aria-expanded")=="false"
    assert hints.nth(1).inner_text()=="點擊＋查看營運方向"
    assert not store.nth(1).locator("strong").is_visible()
    store.nth(1).focus()
    store.nth(1).press("ArrowRight")
    assert store.nth(2).get_attribute("aria-expanded")=="true"
    assert store.nth(2).evaluate("(el) => document.activeElement===el")
    assert store.nth(2).locator("strong").is_visible()
    assert hints.nth(2).inner_text()=="點擊－收合營運方向"
    assert store.nth(2).get_attribute("aria-controls") == store.nth(2).locator("strong").get_attribute("id")
    store.nth(2).press("Enter")
    assert store.nth(2).get_attribute("aria-expanded")=="false"
    assert hints.nth(2).inner_text()=="點擊＋查看營運方向"

    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), (filename,width,"horizontal overflow")
    page.emulate_media(media="print")
    for card in store.all():
        assert card.locator("strong").is_visible(),(filename,"print hides original response")
        assert not card.locator(":scope > .mag-trade-hint").is_visible(),(filename,"print displays click hint")
    page.emulate_media(media="screen",reduced_motion="reduce")
    animation=page.locator("#market .mag-strategy-flow > .compare-row").first.evaluate(
        "(el) => getComputedStyle(el).animationName")
    assert animation=="none", (filename,"reduced motion",animation)
    page.close()

    context=browser.new_context(viewport={"width":width,"height":900},java_script_enabled=False)
    static=context.new_page()
    static.goto(f"{base}/{filename}",wait_until="load")
    assert static.locator("#market .viz-comparison .compare-row:visible").count()==4
    assert static.locator("#location .viz-comparison .compare-row:visible").count()==4
    for result in static.locator("#location .viz-comparison .compare-row > strong").all():
        assert result.is_visible(),(filename,"no-JS source hidden")
    context.close()
    print(f"{filename}@{width}: diagrams, keyboard, touch, print, reduced-motion and no-JS OK")


def main():
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(
                executable_path=os.environ.get("CHROME_PATH"),
                args=["--no-sandbox"]
            )
            base=f"http://127.0.0.1:{server.server_port}"
            for filename,width in (
                ("trend.html",1440),
                ("trend.html",1024),
                ("mobile-trend.html",390),
                ("mobile-trend.html",640),
            ):
                test_view(browser,base,filename,width)
            browser.close()
    finally:
        server.shutdown()


if __name__=="__main__":
    main()
