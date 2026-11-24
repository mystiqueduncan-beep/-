"""Magazine contents, compact navigation, chapter flow and data preservation."""
import functools
import http.server
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

server=http.server.ThreadingHTTPServer(
    ("127.0.0.1",0),functools.partial(QuietHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
root=f"http://127.0.0.1:{server.server_port}"
chapters=["market","competition","consumer","location","digital","people",
          "experience","strategy","roadmap","metrics","sources"]

try:
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        for file,width,height,view in (
            ("trend.html",1440,900,"desktop"),
            ("mobile-trend.html",390,844,"mobile"),
            ("mobile-trend.html",320,640,"mobile")):
            page=browser.new_page(viewport={"width":width,"height":height},reduced_motion="reduce")
            page.route("https://**/*",lambda route:route.abort())
            page.goto(f"{root}/{file}?view={view}",wait_until="domcontentloaded")
            guide=page.locator("main.trend-main > .reader-guide")
            expect(guide).to_be_visible()
            expect(guide.locator(".reader-guide__intro")).to_have_text("可以自由選章節閱讀")
            expect(guide.locator(".reader-index-group")).to_have_count(3)
            expect(guide.locator("a.reader-index-link")).to_have_count(11)
            assert guide.locator("a.reader-index-link").evaluate_all("es=>es.map(e=>e.hash)") == ["#"+id for id in chapters]
            expect(guide.locator("select,button")).to_have_count(0)
            expect(page.locator("nav.trend-bilingual-nav:visible")).to_have_count(0)
            compact=page.locator(".reader-compact")
            expect(compact).to_be_hidden()
            expect(page.locator("main.trend-main > section[id]")).to_have_count(11)
            assert page.locator("#market .stats .stat").count()==3
            assert page.locator("#strategy .strategy").count()==6
            assert page.locator("#metrics .metric-tile").count()==6
            assert page.locator("#roadmap [data-phase]").count()==3
            assert page.locator('a[href*="mnscdn.moea.gov.tw"]').count()>=1
            guide.locator('a[href="#strategy"]').click()
            expect(compact).to_be_visible()
            expect(compact.locator(".reader-compact-name")).to_have_text("改善方針")
            expect(compact.locator("[role=progressbar]")).to_have_attribute("aria-valuenow","8")
            assert compact.evaluate("e=>getComputedStyle(e).position")=="fixed"
            assert compact.evaluate("e=>e.getBoundingClientRect().height")<=56
            assert compact.evaluate("e=>getComputedStyle(e).gridTemplateColumns.split(' ').length")==4
            assert compact.locator(".reader-compact-step").all_text_contents()==["‹","›"]
            assert compact.locator("button:visible, a:visible").evaluate_all("es=>es.every(e=>e.getBoundingClientRect().width>=44 && e.getBoundingClientRect().height>=44)")
            # Fixed throughout reading: the bar never disappears in either direction.
            assert compact.evaluate("e=>getComputedStyle(e).backgroundColor")=="rgba(255, 250, 248, 0.2)"
            initial_top=compact.evaluate("e=>e.getBoundingClientRect().top")
            for delta in (220,-220,350,-120):
                page.mouse.wheel(0,delta)
                page.wait_for_timeout(150)
                expect(compact).to_be_visible()
                assert compact.evaluate("e=>getComputedStyle(e).opacity")=="1"
                assert abs(compact.evaluate("e=>e.getBoundingClientRect().top")-initial_top)<=1
            page.mouse.wheel(0,-230)
            page.wait_for_timeout(150)
            assert compact.evaluate("e=>e.getBoundingClientRect().top")>=0
            expect(guide.locator('a[aria-current="location"]')).to_have_attribute("href","#strategy")
            compact.get_by_role("button",name="下一章：90天計畫").click()
            expect(compact.locator(".reader-compact-name")).to_have_text("90天計畫")
            compact.get_by_role("button",name="上一章：改善方針").click()
            expect(compact.locator(".reader-compact-name")).to_have_text("改善方針")
            assert all(page.locator(f"#{id}").evaluate("e=>getComputedStyle(e).display!=='none'") for id in chapters)
            assert page.locator("#strategy").evaluate("e=>e.getBoundingClientRect().top") >= compact.evaluate("e=>e.getBoundingClientRect().bottom")-2
            trigger=compact.get_by_role("button",name="研究目次")
            menu=compact.locator(".reader-quick-index")
            expect(menu).to_be_hidden()
            y=page.evaluate("scrollY")
            trigger.click()
            expect(menu).to_be_visible()
            expect(trigger).to_have_attribute("aria-expanded","true")
            assert abs(page.evaluate("scrollY")-y)<=2
            expect(menu.locator(".reader-quick-link")).to_have_count(11)
            if width<=720:
                expect(menu.locator(".reader-quick-group:visible")).to_have_count(1)
                menu.get_by_role("button",name="市場與消費").click()
                expect(menu.locator(".reader-quick-link:visible")).to_have_count(4)
            else:
                expect(menu.locator(".reader-quick-group:visible")).to_have_count(3)
                expect(menu.locator(".reader-quick-link:visible")).to_have_count(11)
            menu.locator('a[href="#consumer"]').click()
            expect(menu).to_be_hidden()
            expect(compact.locator(".reader-compact-name")).to_have_text("消費心理")
            expect(trigger).to_have_attribute("aria-expanded","false")
            trigger.click()
            expect(menu.locator('a[aria-current="location"]')).to_have_attribute("href","#consumer")
            page.keyboard.press("Escape")
            expect(menu).to_be_hidden()
            expect(trigger).to_be_focused()
            trigger.click()
            page.mouse.click(5, height-150)
            expect(menu).to_be_hidden()
            expect(compact).to_be_visible()
            page.emulate_media(media="print")
            expect(guide).to_be_hidden()
            expect(compact).to_be_hidden()
            assert all(page.locator(f"#{id}").evaluate("e=>getComputedStyle(e).display!=='none'") for id in chapters)
            page.emulate_media(media="screen",reduced_motion="reduce")
            # Sources remain in the DOM and a printable outline stays intact.
            assert page.locator("main.trend-main").inner_text().count("90 天")>=1
            overflow=page.evaluate(
                "({scroll:document.documentElement.scrollWidth,window:innerWidth})")
            assert overflow["scroll"]<=width+2,(file,overflow)
            page.close()
        for file,view in (("index.html","desktop"),("mobile.html","mobile")):
            page=browser.new_page(viewport={"width":390 if view=="mobile" else 1440,"height":844})
            page.route("https://**/*",lambda route:route.abort())
            page.goto(f"{root}/{file}?view={view}",wait_until="domcontentloaded")
            assert page.locator("#career").count()==1
            assert page.locator("#research").count()==1
            assert page.locator("main .reader-guide").count()==0
            assert page.locator('a[href*="trend.html"]').count()>=1
            page.close()
        browser.close()
finally:
    server.shutdown()
