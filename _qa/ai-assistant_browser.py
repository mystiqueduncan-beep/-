"""Browser acceptance tests for the no-API portfolio assistant."""
import functools
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"

try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for file_name, width, height, variant in (
            ("index.html", 1440, 900, "desktop"),
            ("mobile.html", 390, 844, "mobile"),
            ("trend.html", 1440, 900, "desktop"),
            ("mobile-trend.html", 390, 844, "mobile"),
            ("contact.html", 1440, 900, "desktop"),
            ("mobile-contact.html", 390, 844, "mobile"),
            ("data-visualization.html", 390, 844, None),
        ):
            page = browser.new_page(viewport={"width": width, "height": height})
            page.route("https://**/*", lambda route: route.abort())
            mode = f"?view={variant}" if variant else ""
            page.goto(f"{base}/{file_name}{mode}", wait_until="domcontentloaded")
            opener = page.get_by_role("button", name="開啟履歷 AI 導覽")
            expect(opener).to_be_visible()
            expect(opener.locator(".bs-ai-launcher-label")).to_have_text("AI問答小助手")
            expect(opener.locator(".bs-ai-launcher-emblem")).to_have_text("♥")
            expect(opener.locator(".bs-ai-launcher-star")).to_have_count(2)
            assert opener.locator(".bs-ai-launcher-face").evaluate("e=>getComputedStyle(e).animationName")=="bs-ai-float"
            assert opener.locator(".bs-ai-launcher-emblem").evaluate("e=>getComputedStyle(e).animationName")=="bs-ai-heartbeat"
            assert opener.locator(".bs-ai-launcher-star").first.evaluate("e=>getComputedStyle(e).animationIterationCount")=="infinite"
            assert opener.locator(".bs-ai-launcher-face").evaluate("e=>getComputedStyle(e,'::after').animationName")=="bs-ai-halo"
            opener.click()
            assert opener.locator(".bs-ai-launcher-face").evaluate("e=>getComputedStyle(e).animationName")=="none"
            assert opener.locator(".bs-ai-launcher-emblem").evaluate("e=>getComputedStyle(e).animationName")=="none"
            panel = page.get_by_role("region", name="黃博詩的 AI 履歷導覽")
            expect(panel).to_be_visible()
            expect(panel.get_by_text("您好！我是黃博詩的 AI 數位分身", exact=False)).to_be_visible()
            box = panel.bounding_box()
            assert box is not None
            assert box["x"] >= -1 and box["x"] + box["width"] <= width + 1, (file_name, box)
            assert box["y"] >= -1 and box["y"] + box["height"] <= height + 1, (file_name, box)
            if "mobile" in file_name:
                nav = page.locator(".mobile-bottom-bar")
                if nav.count() and nav.is_visible():
                    button_box = page.locator(".bs-ai-launcher").bounding_box()
                    nav_box = nav.bounding_box()
                    assert button_box["y"] + button_box["height"] <= nav_box["y"] + 1 or button_box["x"] >= nav_box["x"] + nav_box["width"] or button_box["x"] + button_box["width"] <= nav_box["x"], (file_name, button_box, nav_box)
            panel.get_by_role("button", name="產業分析專題").click()
            expect(panel.get_by_text("改善提案，不代表已實施", exact=False)).to_be_visible(timeout=3000)
            target = "mobile-trend.html#market" if "mobile" in file_name else "trend.html#market"
            if file_name == "data-visualization.html":
                target = "trend.html#market"
            assert panel.get_by_role("link", name="閱讀完整產業研究").get_attribute("href") == target
            prompt = panel.get_by_role("textbox", name="輸入作品集相關問題")
            prompt.fill("Levi's 的工作內容")
            prompt.press("Enter")
            expect(panel.get_by_text("在 Levi's 任職約 2 年", exact=False)).to_be_visible(timeout=3000)
            prompt.fill("今天台北的天氣如何")
            prompt.press("Enter")
            expect(panel.get_by_text("無法回答網站未提供的資訊", exact=False)).to_be_visible(timeout=3000)
            page.keyboard.press("Escape")
            expect(panel).to_be_hidden()
            expect(page.get_by_role("button", name="開啟履歷 AI 導覽")).to_be_visible()
            page.close()

        narrow = browser.new_page(viewport={"width": 320, "height": 568}, reduced_motion="reduce")
        narrow.goto(f"{base}/mobile.html?view=mobile", wait_until="domcontentloaded")
        narrow_opener=narrow.get_by_role("button", name="開啟履歷 AI 導覽")
        assert narrow_opener.locator(".bs-ai-launcher-face").evaluate("e=>getComputedStyle(e).animationName")=="none"
        narrow_opener.click()
        box = narrow.locator("#bs-ai-panel").bounding_box()
        assert box and box["x"] >= -1 and box["y"] >= -1, box
        assert box["x"] + box["width"] <= 321, box
        assert box["y"] + box["height"] <= 569, box
        narrow.get_by_role("button", name="如何聯絡你").click()
        expect(narrow.get_by_role("link", name="前往聯絡資訊")).to_be_visible(timeout=1500)
        assert narrow.get_by_role("link", name="前往聯絡資訊").get_attribute("href") == "mobile-contact.html"
        narrow.close()
        browser.close()
finally:
    server.shutdown()
