"""PR-only screenshots and browser assertions for the homepage sticky marquee.

Run with: python3 _qa/sticky_nav_preview.py --out /tmp/sticky-nav-preview
This script never edits any public site or source file.
"""
import argparse
import functools
import http.server
import json
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args = parser.parse_args()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass

server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0), functools.partial(Handler, directory=str(ROOT))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
checks = []

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(
        executable_path=os.environ.get("CHROME_PATH"), args=["--no-sandbox"]
    )
    for name, width, mobile in (("index", 1440, False), ("mobile", 390, True)):
        page = browser.new_page(
            viewport={"width": width, "height": 860 if mobile else 900},
            is_mobile=mobile,
            has_touch=mobile,
            reduced_motion="reduce",
        )
        page.route("https://**/*", lambda route: route.abort())
        page.goto(
            f"http://127.0.0.1:{server.server_port}/{name}.html"
            f"?view={'mobile' if mobile else 'desktop'}",
            wait_until="domcontentloaded",
        )
        if mobile:
            expect(page.locator(".bilingual-mobile-strip")).to_have_count(0)
            expect(page.locator("[data-keycap-marquee]")).to_have_count(0)
            nav=page.locator("nav.mobile-bottom-bar")
            expect(nav).to_have_count(1)
            assert nav.is_visible(),name
            assert nav.evaluate('e=>getComputedStyle(e).position')=='fixed',name
            assert nav.locator('a[href="#cases"]').count()==1,name
            assert nav.locator('a[href="mobile-trend.html"]').count()==1,name
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),name
            page.screenshot(path=str(out / f"{name}-top.png"),full_page=False)
            nav.locator('a[href="#cases"]').click()
            page.wait_for_timeout(250)
            assert page.evaluate("location.hash")=="#cases",name
            geometry=page.evaluate("""() => {
                const n=document.querySelector('.mobile-bottom-bar').getBoundingClientRect();
                return {navTop:n.top,navBottom:n.bottom,navPosition:getComputedStyle(
                     document.querySelector('.mobile-bottom-bar')).position,
                     scrollY:scrollY,overflow:document.documentElement.scrollWidth-innerWidth};
            }""")
            assert geometry["navPosition"]=="fixed" and geometry["overflow"]<=1,(name,geometry)
            assert geometry["navBottom"]<=page.viewport_size["height"]+1,(name,geometry)
            page.screenshot(path=str(out / f"{name}-sticky.png"),full_page=False)
        else:
            nav=page.locator(".home-keycap-strip")
            expect(nav).to_have_count(1)
            expect(nav.locator('.keycap-marquee__group a.nav-btn-mk')).to_have_count(6)
            assert nav.evaluate("e=>getComputedStyle(e).position")=="sticky",name
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),name
            page.screenshot(path=str(out / f"{name}-top.png"),full_page=False)
            page.evaluate("() => document.getElementById('cases').scrollIntoView({behavior:'instant'})")
            page.wait_for_timeout(350)
            geometry=page.evaluate("""() => {
                const nav=document.querySelector('.home-keycap-strip').getBoundingClientRect();
                const section=document.getElementById('cases').getBoundingClientRect();
                return {navTop:nav.top,navBottom:nav.bottom,navPosition:getComputedStyle(
                  document.querySelector('.home-keycap-strip')).position,
                  sectionTop:section.top,scrollY:scrollY,
                  overflow:document.documentElement.scrollWidth-innerWidth};
            }""")
            assert geometry["scrollY"]>250 and geometry["navPosition"]=="sticky",(name,geometry)
            assert abs(geometry["navTop"])<=9,(name,geometry)
            assert geometry["sectionTop"]>=geometry["navBottom"]-5,(name,geometry)
            assert geometry["overflow"]<=1,(name,geometry)
            page.screenshot(path=str(out / f"{name}-sticky.png"),full_page=False)
        checks.append({"page":name,"viewport":width,**geometry})
        page.close()
    browser.close()

server.shutdown()
print(json.dumps(checks, ensure_ascii=False, indent=2), flush=True)
print("PASS: desktop/mobile sticky nav, six links, clean track, scroll offset, screenshots", flush=True)
