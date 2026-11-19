"""Browser regression for active chapter keycaps, method slides, and contact actions."""
import functools
import http.server
import threading

from playwright.sync_api import sync_playwright

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0), functools.partial(Handler, directory=str(ROOT))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}/"

with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-sandbox"])

    for name, target in [
        ("index", "competencies"),
        ("mobile", "competencies"),
        ("trend", "experience"),
        ("mobile-trend", "experience"),
    ]:
        mobile = name.startswith("mobile")
        page = browser.new_page(viewport={"width":390 if mobile else 1440, "height":844})
        page.route("https://**/*", lambda route: route.abort())
        page.goto(f'{base}{name}.html?view={"mobile" if mobile else "desktop"}')
        # Removed presentation-only labels stay absent in the homepage DOM.
        if name == "index":
            assert page.locator(".target-role-badge, .hero-position-highlight").count() == 0
            assert page.locator(".mag-footer .footer-inner > div").count() == 1
            assert "Matsumoto Kiyoshi" not in page.locator("body").inner_text()
            assert "志願應徵職位：" not in page.locator("body").inner_text()
        # Both charts still exist and animate automatically, but neither
        # desktop nor mobile page may create a replay button.
        chart_bars = page.locator("#market .animated-bar" if "trend" in name else "#research .data-bar-fill")
        assert chart_bars.count() > 0, (name, "chart data should remain")
        assert page.locator(".portfolio-chart").count() >= 1, (name, "chart enhancement missing")
        assert page.locator(".portfolio-chart-replay").count() == 0, (name, "replay button was removed")
        nav = page.locator("[data-keycap-marquee]")
        assert nav.count() == 1, name
        page.wait_for_function(
            '() => document.querySelector("[data-keycap-marquee]")?.classList.contains("is-enhanced")'
        )
        nav_strip = nav.locator("xpath=..") if mobile and name == "mobile" else page.locator(
            ".trend-bilingual-nav" if "trend" in name else ".home-keycap-strip"
        )
        color = nav_strip.evaluate("(el)=>getComputedStyle(el).backgroundColor")
        assert color == "rgba(0, 0, 0, 0)", (name, "sticky shell", color)
        color = nav.evaluate("(el)=>getComputedStyle(el).backgroundColor")
        # Current shared chrome: .96 at the top, .20 while reading.
        page.wait_for_function("""() => {const n=document.querySelector('[data-keycap-marquee]');return getComputedStyle(n).backgroundColor === (n.classList.contains('is-reading-section') ? 'rgba(255, 249, 247, 0.2)' : 'rgba(255, 249, 247, 0.96)')}""")
        color = nav.evaluate("(el)=>getComputedStyle(el).backgroundColor")

        belt = nav.locator(".keycap-marquee__belt")
        background = belt.evaluate("(el)=>getComputedStyle(el).backgroundColor")
        assert background == "rgba(0, 0, 0, 0)", (name, background)
        decoration = belt.evaluate('(el)=>getComputedStyle(el,"::after").content')
        assert "♡" in decoration and "✦" in decoration, (name, decoration)
        # Both ornaments sit about 20px from the nearest chapter key, not
        # centered hundreds of pixels away in the native-scroll run-out.
        ornament_layout = belt.evaluate("""(el) => {
          const first = getComputedStyle(el, "::before");
          const last = getComputedStyle(el, "::after");
          return {
            firstAlign: first.justifyContent,
            firstGap: first.paddingRight,
            lastAlign: last.justifyContent,
            lastGap: last.paddingLeft,
            letterSpacing: first.letterSpacing
          };
        }""")
        assert ornament_layout["firstAlign"] == "flex-end", (name, ornament_layout)
        assert ornament_layout["lastAlign"] == "flex-start", (name, ornament_layout)
        assert ornament_layout["firstGap"] == "20px", (name, ornament_layout)
        assert ornament_layout["lastGap"] == "20px", (name, ornament_layout)
        assert ornament_layout["letterSpacing"] == "6px", (name, ornament_layout)

        section = page.locator("#" + target)
        section.evaluate('(el)=>{el.scrollIntoView({block:"start",behavior:"instant"});dispatchEvent(new Event("scroll"));}')
        page.wait_for_timeout(220)
        active = nav.locator('.keycap-marquee__group a[aria-current="location"]')
        assert active.count() == 1, (name, "one scroll-synced active chapter expected")
        assert active.get_attribute("href") == "#" + target, (name, active.get_attribute("href"))
        selected_bg = active.evaluate("(el)=>getComputedStyle(el).backgroundColor")
        assert selected_bg == "rgb(223, 173, 193)", (name, selected_bg)
        print("marquee:", name, target, selected_bg, color)

        if "trend" in name:
            methods = page.locator("#experience .exp .exp-application")
            assert methods.count() == 3, name
            for method in methods.all():
                method.evaluate('(el)=>el.scrollIntoView({block:"center",behavior:"instant"})')
                page.wait_for_timeout(1100)
                assert method.evaluate('(el)=>el.classList.contains("exp-method-in")'), name
                assert method.evaluate('(el)=>getComputedStyle(el).opacity') == "1", name
                assert method.evaluate('(el)=>new DOMMatrix(getComputedStyle(el).transform).m42') == 0, name
            page.emulate_media(reduced_motion="reduce")
            assert all(
                method.evaluate('(el)=>getComputedStyle(el).opacity') == "1"
                for method in methods.all()
            ), name
        page.close()

    for name in ("contact", "mobile-contact"):
        mobile = name.startswith("mobile")
        page = browser.new_page(viewport={"width":390 if mobile else 1440, "height":844})
        page.route("https://**/*", lambda route: route.abort())
        page.goto(f'{base}{name}.html?view={"mobile" if mobile else "desktop"}')
        cards = page.locator("div.method-card")
        assert cards.count() == 3, name
        first_x = None
        for card in cards.all():
            # Reveal the one-time card animation before measuring its final box.
            card.scroll_into_view_if_needed()
            page.wait_for_timeout(1050)
            actions = card.locator(".method-action-btns")
            buttons = actions.locator("a, button")
            assert buttons.count() == 2, (name, "each method needs two actions")
            display = actions.evaluate('(el)=>getComputedStyle(el).display')
            assert display == "grid", (name, display)
            cols = actions.evaluate(
                '(el)=>getComputedStyle(el).gridTemplateColumns.trim().split(/\s+/).length'
            )
            assert cols == (1 if mobile else 2), (name, cols)
            r0, r1 = [button.bounding_box() for button in buttons.all()]
            assert abs(r0["x"]-r1["x"]) < 2 if mobile else abs(r0["y"]-r1["y"]) < 2, name
            assert r0["height"] >= 47 and r1["height"] >= 47, (name, "button final heights", r0, r1)
            assert all(button.evaluate(
                '(el)=>getComputedStyle(el).textAlign') == "center"
                for button in buttons.all()
            ), name
            if first_x is None:
                first_x = r0["x"]
            else:
                assert abs(r0["x"]-first_x) < 2, (name, r0, first_x)
        print("contact alignment:", name, "three matching method grids")
        page.close()

    browser.close()
server.shutdown()
print("Active chapter highlights, transparent decorations, top-down methods and aligned contacts: OK")
