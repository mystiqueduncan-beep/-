"""Browser checks for every cross-page link to the drugstore research report."""
import functools
import http.server
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
pages = {
    "index": (2, "trend.html"),
    "mobile": (2, "mobile-trend.html"),
    "contact": (2, "trend.html"),
    "mobile-contact": (2, "mobile-trend.html"),
}
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Handler, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, (count, href) in pages.items():
        mobile = name.startswith("mobile")
        url = f'http://127.0.0.1:{server.server_port}/{name}.html?view={"mobile" if mobile else "desktop"}'
        page = browser.new_page(viewport={"width": 390 if mobile else 1440, "height": 844})
        page.route("https://**/*", lambda route: route.abort())
        page.goto(url, wait_until="domcontentloaded")
        links = page.locator(f'a[href="{href}"]')
        assert links.count() == count, (name, links.count())
        for link in links.all():
            assert "藥妝專題研究" in link.inner_text(), name
            # Polaroid mat, rose gradient, tape, heart, and visible text.
            style = link.evaluate("""e => {
              const c=getComputedStyle(e);
              return {background:c.backgroundImage,border:c.borderBottomWidth,
                before:getComputedStyle(e,"::before").content,
                after:getComputedStyle(e,"::after").content,
                color:c.color,animation:c.animationName};
            }""")
            assert "gradient" in style["background"], (name, style)
            assert float(style["border"].replace("px","")) >= 8, (name, style)
            assert style["before"] == '""', (name, style)
            assert "♡" in style["after"], (name, style)
            assert "research-soft-glow" in style["animation"], (name, style)
            # Reveals once when scrolled to, then stays revealed.
            link.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
            expect(link).to_have_class(__import__("re").compile(".*research-pop-in.*"), timeout=5000)
            expect(link).to_have_css("opacity", "1", timeout=5000)
        page.evaluate("scrollTo({top:0,behavior:'instant'})")
        for link in links.all():
            assert "research-pop-in" in (link.get_attribute("class") or ""), name
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), name
        page.close()

        reduced = browser.new_page(
            viewport={"width": 390 if mobile else 1440, "height": 844},
            reduced_motion="reduce"
        )
        reduced.route("https://**/*", lambda route: route.abort())
        reduced.goto(url, wait_until="domcontentloaded")
        for link in reduced.locator(f'a[href="{href}"]').all():
            assert "research-pop-wait" not in (link.get_attribute("class") or ""), name
            state = link.evaluate("(e)=>({opacity:getComputedStyle(e).opacity,animation:getComputedStyle(e).animationName})")
            assert state == {"opacity":"1","animation":"none"}, (name, state)
        reduced.close()

        fallback = browser.new_page(viewport={"width":390 if mobile else 1440,"height":844})
        fallback.add_init_script("window.IntersectionObserver=undefined;")
        fallback.route("https://**/*", lambda route: route.abort())
        fallback.goto(url, wait_until="domcontentloaded")
        for link in fallback.locator(f'a[href="{href}"]').all():
            assert "research-pop-wait" not in (link.get_attribute("class") or ""), name
            assert link.evaluate("(e)=>getComputedStyle(e).opacity") == "1", name
        fallback.close()
        print(name + ": research CTAs, glow, one-time entrance, reduced motion, and no-observer fallback verified")
    browser.close()
server.shutdown()
