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
        # Homepage charts retain their automatic bars; research charts are now
        # rendered inline as an accessible product-mix stack and channel list.
        if "trend" in name:
            chart_bars = page.locator(".inline-research-viz__stack > span, .inline-research-viz__rows > li")
            assert page.locator(".inline-research-viz").count() == 2, (name, "inline research charts missing")
            assert page.locator(".portfolio-chart").count() == 0, (name, "research chart should use inline layout")
            assert not any("查看數據視覺化示範" in text for text in page.locator("a").all_text_contents()), (name, "no separate chart demo link")
        else:
            chart_bars = page.locator("#research .data-bar-fill")
            assert page.locator(".portfolio-chart").count() >= 1, (name, "chart enhancement missing")
        assert chart_bars.count() > 0, (name, "chart data should remain")
        assert page.locator(".portfolio-chart-replay").count() == 0, (name, "replay button was removed")
        if mobile:
            assert page.locator("[data-keycap-marquee]").count()==0,name
            bottom=page.locator("nav.mobile-bottom-bar")
            assert bottom.count()==1 and bottom.is_visible(),name
            assert bottom.evaluate("e=>getComputedStyle(e).position")=="fixed",name
            assert bottom.locator('a[href="mobile-contact.html"]').count()==1,name
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"),name
            print("mobile bottom tabs:",name,"upper chapter strip removed")
        else:
            nav=page.locator("[data-keycap-marquee]")
            assert nav.count()==1,name
            assert nav.evaluate("e=>e.classList.contains('is-static-nav')"),name
            assert not nav.evaluate("e=>e.classList.contains('is-enhanced')"),name
            belt=nav.locator(".keycap-marquee__belt")
            for pseudo in ("::before","::after"):
                assert belt.evaluate("(el,p)=>getComputedStyle(el,p).display",pseudo)=="none",name
            section=page.locator("#"+target)
            section.evaluate('(el)=>{el.scrollIntoView({block:"start",behavior:"instant"});dispatchEvent(new Event("scroll"));}')
            page.wait_for_timeout(220)
            active=nav.locator('.keycap-marquee__group a[aria-current="location"]')
            assert active.count()==1 and active.get_attribute("href")=="#"+target,name
            selected_bg=active.evaluate("(el)=>getComputedStyle(el).backgroundColor")
            assert selected_bg=="rgb(233, 198, 211)",name
            print("desktop current chapter:",name,target)

        if "trend" in name:
            methods = page.locator("#experience .exp .exp-application")
            arrows = page.locator("#experience .exp .exp-arrow-button")
            assert methods.count() == arrows.count() == 3, name
            for index, method in enumerate(methods.all()):
                arrow = arrows.nth(index)
                arrow.scroll_into_view_if_needed()
                arrow.click()
                assert arrow.get_attribute("aria-expanded") == "true", name
                method.wait_for(state="visible")
                page.wait_for_timeout(400)
                assert method.evaluate('(el)=>getComputedStyle(el).opacity') == "1", name
                assert method.evaluate('(el)=>new DOMMatrix(getComputedStyle(el).transform).m42') == 0, name
                arrow.click()
                assert arrow.get_attribute("aria-expanded") == "false", name
                assert method.evaluate('(el)=>el.textContent.trim().length > 15'), name
            page.emulate_media(reduced_motion="reduce")
            arrows.first.click()
            assert arrows.first.get_attribute("aria-expanded") == "true", name
            assert methods.first.evaluate('(el)=>getComputedStyle(el).opacity') == "1", name
            assert methods.first.evaluate('(el)=>getComputedStyle(el).transitionDuration.split(",").every(x=>parseFloat(x)===0)'), name
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
