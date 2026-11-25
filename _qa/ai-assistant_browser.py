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
            opener = page.locator(".bs-ai-launcher")
            expect(opener).to_be_visible()
            expect(opener.locator(".bs-ai-launcher-label")).to_have_text("閱讀小助手")
            expect(opener.locator(".bs-ai-launcher-caption")).to_have_text("找資料・直達章節")
            expect(opener.locator(".bs-ai-launcher-emblem")).to_have_text("♥")
            expect(opener.locator(".bs-ai-launcher-star")).to_have_count(2)
            assert page.locator(".bs-ai-dock").evaluate("e=>getComputedStyle(e).animationName")=="bs-ai-float"
            assert opener.locator(".bs-ai-launcher-emblem").evaluate("e=>getComputedStyle(e).animationName")=="bs-ai-heartbeat"
            assert opener.locator(".bs-ai-launcher-star").first.evaluate("e=>getComputedStyle(e).animationIterationCount")=="infinite"
            assert opener.locator(".bs-ai-launcher-face").evaluate("e=>getComputedStyle(e,'::after').animationName")=="bs-ai-halo"
            expect(page.locator(".bs-ai-guide-hint")).to_have_attribute("aria-hidden", "true")
            opener.click()
            assert page.locator(".bs-ai-dock").evaluate("e=>getComputedStyle(e).animationName")=="none"
            assert opener.locator(".bs-ai-launcher-emblem").evaluate("e=>getComputedStyle(e).animationName")=="none"
            panel = page.get_by_role("region", name="黃博詩的閱讀小助手")
            expect(panel).to_be_visible()
            expect(panel.locator(".bs-ai-chip")).to_have_count(6)
            expect(page.locator(".bs-ai-guide-hint")).to_have_attribute("aria-hidden", "true")
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
            if variant != "mobile":
                expect(panel.get_by_role("button", name="請自我介紹", exact=True)).to_be_visible()
                expect(panel.get_by_role("button", name="如何聯絡", exact=True)).to_be_visible()
            assert not any("簡歷" in x for x in panel.locator(".bs-ai-chip").all_text_contents())
            intro = panel.get_by_role("button", name="請自我介紹", exact=True)
            if intro.count():
                intro.click()
                expect(panel.get_by_text("您好，我是黃博詩，目前就讀", exact=False)).to_be_visible(timeout=3000)
                expect(panel.locator(".bs-ai-facts").first).to_be_visible()
                panel.get_by_role("button", name="重新開始對話", exact=False).click()
                expect(panel.locator(".bs-ai-chip")).to_have_count(6)
                expect(panel.get_by_text("您好，我是黃博詩，目前就讀", exact=False)).to_have_count(0)
            prompt = panel.get_by_role("textbox", name="輸入作品集相關問題")
            prompt.fill("介紹你的產業分析專題")
            prompt.press("Enter")
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
            expect(page.get_by_role("button", name="開啟閱讀小助手")).to_be_visible()
            page.close()

        # Virtual clock exercises real production intervals without a long sleep.
        guide = browser.new_page(viewport={"width": 390, "height": 844})
        guide.route("https://**/*", lambda route: route.abort())
        guide.clock.install()
        guide.goto(f"{base}/mobile-trend.html?view=mobile", wait_until="domcontentloaded")
        hint=guide.locator(".bs-ai-guide-hint")
        words=hint.locator(".bs-ai-guide-hint-text")
        guide.clock.run_for(2100)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        guide.clock.run_for(1400)
        expect(words).to_have_text("想找什麼嗎？")
        box=hint.bounding_box()
        assert box and 0<=box["x"] and box["x"]+box["width"]<=390,box
        assert box["width"]<125,box
        guide.clock.run_for(9000)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        guide.clock.run_for(2000)
        expect(hint).to_have_attribute("aria-hidden","true")
        # Cross-page session timing does not reset to the first greeting.
        guide.goto(f"{base}/mobile-contact.html?view=mobile", wait_until="domcontentloaded")
        hint=guide.locator(".bs-ai-guide-hint")
        words=hint.locator(".bs-ai-guide-hint-text")
        guide.clock.run_for(3000)
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.clock.run_for(20000)
        assert words.inner_text() in ["需要我帶路嗎？","有什麼想了解的嗎？","想先看看重點嗎？","不知道從哪裡看起嗎？","有需要我幫忙的嗎？","想讓我為你介紹嗎？","想找聯絡方式嗎？","想了解教育背景嗎？","想了解應徵方向嗎？"],words.inner_text()
        hint.click()
        expect(guide.locator("#bs-ai-panel")).to_be_visible()
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.clock.run_for(35000)
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.keyboard.press("Escape")
        guide.clock.run_for(15000)
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.clock.run_for(7000)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        guide.close()

        # A stable large section triggers a fresh hint before the normal 20-second gap.
        contextual = browser.new_page(viewport={"width": 390,"height":844})
        contextual.route("https://**/*",lambda route:route.abort())
        contextual.clock.install()
        contextual.goto(f"{base}/mobile-trend.html?view=mobile",wait_until="domcontentloaded")
        contextual.clock.run_for(14000)
        hint=contextual.locator(".bs-ai-guide-hint")
        expect(hint).to_have_attribute("aria-hidden","true")
        contextual.evaluate("document.getElementById('roadmap').scrollIntoView({behavior:'instant',block:'start'})")
        contextual.clock.run_for(4100)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        # Both children have the same positioned ancestor and no individual float.
        assert hint.evaluate("e=>e.parentElement.classList.contains('bs-ai-dock')")
        assert contextual.locator(".bs-ai-launcher").evaluate("e=>e.parentElement.classList.contains('bs-ai-dock')")
        contextual.locator(".bs-ai-launcher").click()
        expect(contextual.locator(".bs-ai-chip").first).to_have_attribute("data-topic","roadmap")
        contextual.locator(".bs-ai-chip").first.click()
        contextual.get_by_role("button",name="重新開始對話",exact=False).click()
        contextual.clock.run_for(2000)
        expect(contextual.locator(".bs-ai-chip")).to_have_count(6)
        expect(contextual.locator(".bs-ai-message--user")).to_have_count(0)
        contextual.close()

        narrow = browser.new_page(viewport={"width": 320, "height": 568}, reduced_motion="reduce")
        narrow.goto(f"{base}/mobile.html?view=mobile", wait_until="domcontentloaded")
        narrow_opener=narrow.get_by_role("button", name="開啟閱讀小助手")
        assert narrow.locator(".bs-ai-dock").evaluate("e=>getComputedStyle(e).animationName")=="none"
        narrow_opener.click()
        box = narrow.locator("#bs-ai-panel").bounding_box()
        assert box and box["x"] >= -1 and box["y"] >= -1, box
        assert box["x"] + box["width"] <= 321, box
        assert box["y"] + box["height"] <= 569, box
        narrow.get_by_role("textbox", name="輸入作品集相關問題").fill("如何聯絡")
        narrow.get_by_role("textbox", name="輸入作品集相關問題").press("Enter")
        expect(narrow.get_by_role("link", name="前往聯絡資訊")).to_be_visible(timeout=1500)
        assert narrow.get_by_role("link", name="前往聯絡資訊").get_attribute("href") == "mobile-contact.html"
        narrow.close()
        browser.close()
finally:
    server.shutdown()
