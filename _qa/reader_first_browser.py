"""Reader-first design acceptance: chapter flow, focus mode and data preservation."""
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
            expect(guide.locator("select option")).to_have_count(11)
            expect(page.locator("main.trend-main > section[id]")).to_have_count(11)
            assert page.locator("#market .stats .stat").count()==3
            assert page.locator("#strategy .strategy").count()==6
            assert page.locator("#metrics .metric-tile").count()==6
            assert page.locator("#roadmap [data-phase]").count()==3
            assert page.locator('a[href*="mnscdn.moea.gov.tw"]').count()>=1
            page.get_by_role("button",name="啟用單章閱讀模式").click()
            assert page.locator("main.trend-main").evaluate(
                "e=>e.classList.contains('reader-focus-mode')")
            assert page.locator("main.trend-main > section.reader-focus-active").count()==1
            assert page.locator("#competition").evaluate(
                "e=>getComputedStyle(e).display==='none'")
            page.get_by_role("combobox",name="選擇研究章節").select_option("strategy")
            expect(page.locator("#strategy")).to_be_visible()
            assert page.locator("#market").evaluate(
                "e=>getComputedStyle(e).display==='none'")
            page.get_by_role("button",name="下一章 →").click()
            expect(page.locator("#roadmap")).to_be_visible()
            page.get_by_role("button",name="關閉單章閱讀，顯示完整研究").click()
            assert all(page.locator(f"#{id}").evaluate("e=>getComputedStyle(e).display!=='none'") for id in chapters)
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
