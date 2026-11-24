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
        elif name=="trend":
            guide=page.locator(".reader-guide")
            assert guide.locator(".reader-index-link").count()==11
            assert not page.locator("nav.trend-bilingual-nav").is_visible()
            section=page.locator("#"+target)
            section.evaluate('(el)=>{el.scrollIntoView({block:"start",behavior:"instant"});dispatchEvent(new Event("scroll"));}')
            page.wait_for_function('() => document.querySelector(".reader-index-link[aria-current=location]")?.hash==="#experience"')
            assert page.locator(".reader-compact").is_visible()
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
            assert selected_bg=="rgb(217, 225, 213)",name
            print("desktop current chapter:",name,target)

        if "trend" in name:
            methods = page.locator("#experience .exp .exp-application")
            arrows = page.locator("#experience .exp .exp-connector")
            cards = page.locator("#experience .exp")
            assert methods.count() == arrows.count() == cards.count() == 3, name
            assert page.locator("#experience .exp-arrow-button").count() == 0, name
            for i in range(3):
                card=cards.nth(i)
                card.scroll_into_view_if_needed()
                page.wait_for_function(
                    "(i) => document.querySelectorAll('#experience .exp')[i].classList.contains('exp-story-visible')",
                    arg=i
                )
                page.wait_for_timeout(1500)
                assert methods.nth(i).is_visible(), (name,i)
                assert methods.nth(i).evaluate('(el)=>getComputedStyle(el).opacity')=="1", (name,i)
                assert methods.nth(i).evaluate('(el)=>new DOMMatrix(getComputedStyle(el).transform).m42')==0, (name,i)
                assert arrows.nth(i).get_attribute("aria-hidden")=="true", (name,i)
            # An already-seen card does not restart on scroll or interaction.
            cards.first.scroll_into_view_if_needed()
            assert cards.first.get_attribute("class").count("exp-story-visible")==1, name
            page.emulate_media(reduced_motion="reduce")
            assert all(
                method.evaluate('(el)=>getComputedStyle(el).opacity')=="1"
                for method in methods.all()
            ),name
        page.close()

    for name in ("contact", "mobile-contact"):
        mobile = name.startswith("mobile")
        page = browser.new_page(viewport={"width":390 if mobile else 1440, "height":844})
        page.route("https://**/*", lambda route: route.abort())
        page.goto(f'{base}{name}.html?view={"mobile" if mobile else "desktop"}')
        # User-approved compact contact card: identical four rows at both widths.
        specs = page.locator(".candidate-specs-box")
        assert specs.count() == 1, name
        assert specs.locator(".specs-box-title").inner_text().strip() == "應徵資訊", name
        assert specs.locator(".spec-entry .k").all_inner_texts() == ["應徵職位", "志願區域", "居住區域", "到職與排班"], name
        assert specs.locator(".spec-entry .v").all_inner_texts() == ["區域營運經理", "桃竹苗、大台北", "桃園市大園區", "面談確認"], name
        assert specs.locator('[lang="en"]').inner_text() == "CAREER PROFILE", name
        assert specs.locator('[lang="ja"]').inner_text() == "応募情報", name
        assert specs.evaluate("e=>e.scrollWidth<=e.clientWidth+1"), name
        assert page.locator("#education").count() == 1, name
        assert "萬能科技大學" in page.locator("#education").inner_text(), name
        assert "Tomod's 6年門市實務" in page.locator("body").inner_text(), name
        assert "動物醫院任職4年期間兼任新人帶訓工作" in page.locator("body").inner_text(), name
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"), name
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
