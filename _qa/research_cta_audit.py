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
            style = link.evaluate("""e => {
              const c=getComputedStyle(e);
              return {background:c.backgroundImage,border:c.borderBottomWidth,
                before:getComputedStyle(e,"::before").content,
                after:getComputedStyle(e,"::after").content,
                color:c.color,animation:c.animationName,radius:c.borderRadius};
            }""")
            # Polaroid frame is the same on all four pages.
            assert "gradient" in style["background"], (name, style)
            assert float(style["border"].replace("px","")) >= 8, (name, style)
            assert style["before"] == '""', (name, style)
            assert "♡" in style["after"], (name, style)
            assert link.evaluate('(e)=>e.classList.contains("site-button-motion")'),(name,"shared button contract")
            assert link.locator(".research-meteor").count() == 1, (name, "meteor")
            assert link.evaluate("""e => {
                const overlay=e.querySelector(".research-meteor");
                return overlay.getBoundingClientRect().width >= e.getBoundingClientRect().width*.6;
            }"""), (name, "full button light beam")
            # Animation assertions run after the button enters the viewport,
            # when its 0.52-second pop and 6.4-second blush glow are active.
            # Reveals once when scrolled to, then stays revealed.
            link.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
            expect(link).to_have_class(__import__("re").compile(".*research-pop-in.*"), timeout=5000)
            expect(link).to_have_css("opacity", "1", timeout=5000)
            expect(link).to_have_class(__import__("re").compile(".*site-button-active.*"),timeout=5000)
            animated=link.evaluate("""e=>({
              names:getComputedStyle(e).animationName,
              iterations:getComputedStyle(e).animationIterationCount,
              durations:getComputedStyle(e).animationDuration,
              shine:getComputedStyle(e.querySelector(".research-meteor"),"::before").animationName,
              shineIterations:getComputedStyle(e.querySelector(".research-meteor"),"::before").animationIterationCount,
              flow:getComputedStyle(e.querySelector(".research-meteor"),"::after").animationName,
              flowIterations:getComputedStyle(e.querySelector(".research-meteor"),"::after").animationIterationCount,
              flowBackground:getComputedStyle(e.querySelector(".research-meteor"),"::after").backgroundImage
            })""")
            assert "site-button-pop-once" in animated["names"],(name,animated)
            assert "site-button-blush-pulse" in animated["names"],(name,animated)
            assert animated["iterations"].replace(" ","")=="1,infinite",(name,animated)
            assert animated["durations"].replace(" ","")=="0.52s,6.4s",(name,animated)
            assert animated["shine"]=="research-dream-sweep",(name,animated)
            assert animated["flow"]=="research-dream-flow",(name,animated)
            assert animated["flowIterations"]=="infinite",(name,animated)
            assert "gradient" in animated["flowBackground"],(name,animated)
            assert animated["shineIterations"]=="infinite",(name,animated)
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
            assert link.locator(".research-meteor").evaluate("e=>getComputedStyle(e,'::after').animationName")=="none",name
        reduced.close()

        fallback = browser.new_page(viewport={"width":390 if mobile else 1440,"height":844})
        fallback.add_init_script("window.IntersectionObserver=undefined;")
        fallback.route("https://**/*", lambda route: route.abort())
        fallback.goto(url, wait_until="domcontentloaded")
        fallback.wait_for_timeout(650)
        for link in fallback.locator(f'a[href="{href}"]').all():
            assert "research-pop-wait" not in (link.get_attribute("class") or ""), name
            assert link.evaluate("(e)=>getComputedStyle(e).opacity") == "1", name
        fallback.close()
        print(name + ": research CTAs, glow, one-time entrance, reduced motion, and no-observer fallback verified")
    # The same pop/glimmer rhythm covers utility and chapter controls on
    # all six desktop/mobile editions; a long article never strobe-flashes
    # all its navigation keys at the same instant.
    for name in ("index","mobile","trend","mobile-trend","contact","mobile-contact"):
        mobile=name.startswith("mobile")
        url=f'http://127.0.0.1:{server.server_port}/{name}.html?view={"mobile" if mobile else "desktop"}'
        page=browser.new_page(viewport={"width":390 if mobile else 1440,"height":844})
        page.route("https://**/*",lambda r:r.abort())
        page.goto(url,wait_until="domcontentloaded")
        controls=page.locator(".site-button-motion")
        assert controls.count()>=3,(name,controls.count())
        first=page.locator(".site-button-motion:visible").first
        assert first.count()==1,name
        first.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
        expect(first).to_have_class(__import__("re").compile(".*site-button-active.*"),timeout=5000)
        animation=first.evaluate('''e=>{
          const s=getComputedStyle(e);
          return {name:s.animationName,duration:s.animationDuration,
             iteration:s.animationIterationCount,delay:s.animationDelay};
        }''')
        assert "site-button-pop-once" in animation["name"],(name,animation)
        assert "site-button-blush-pulse" in animation["name"],(name,animation)
        assert "6.4s" in animation["duration"],(name,animation)
        assert "infinite" in animation["iteration"],(name,animation)
        first.hover(force=True)
        assert "paused" in first.evaluate('e=>getComputedStyle(e).animationPlayState'),name
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"),name
        page.close()
        reduced=browser.new_page(viewport={"width":390 if mobile else 1440,"height":844},reduced_motion="reduce")
        reduced.route("https://**/*",lambda r:r.abort())
        reduced.goto(url,wait_until="domcontentloaded")
        controls=reduced.locator(".site-button-motion")
        assert controls.count()>=3,name
        assert controls.evaluate_all('''els=>els.every(e=>
          getComputedStyle(e).animationName==='none'
        )'''),(name,"reduced motion must disable recurring button animation")
        reduced.close()
        print(name+": site-wide pop, stagger, gentle repeated glow and reduced motion passed")
    browser.close()
server.shutdown()
