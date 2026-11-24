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
            expect(guide.locator('a[aria-current="location"]')).to_have_attribute("href","#strategy")
            compact.get_by_role("button",name="下一章：90天計畫").click()
            expect(compact.locator(".reader-compact-name")).to_have_text("90天計畫")
            compact.get_by_role("button",name="上一章：改善方針").click()
            expect(compact.locator(".reader-compact-name")).to_have_text("改善方針")
            assert all(page.locator(f"#{id}").evaluate("e=>getComputedStyle(e).display!=='none'") for id in chapters)
            assert page.locator("#strategy").evaluate("e=>e.getBoundingClientRect().top") >= compact.evaluate("e=>e.getBoundingClientRect().bottom")-2
            compact.get_by_role("link",name="研究目次").click()
            expect(compact).to_be_hidden()
            expect(guide).to_be_in_viewport()
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
