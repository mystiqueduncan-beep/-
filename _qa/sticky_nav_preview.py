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
        nav = page.locator(".bilingual-mobile-strip" if mobile else ".home-keycap-strip")
        expect(nav).to_have_count(1)
        expect(page.locator(".bilingual-current")).to_have_count(0)
        expect(page.locator('[data-bilingual-title]')).to_have_count(0)
        expect(page.locator('script[src$="bilingual-chapters.js"]')).to_have_count(0)
        original = nav.locator(".keycap-marquee__group")
        expect(original.locator("a.nav-btn-mk")).to_have_count(6)
        expect(original.locator(".bilingual-nav-jp")).to_have_count(6)
        assert original.evaluate("e=>[...e.children].every(c=>c.tagName==='LI')"), name
        assert nav.evaluate("e=>getComputedStyle(e).position") == "sticky", name
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), name
        page.wait_for_timeout(150)
        page.screenshot(path=str(out / f"{name}-top.png"), full_page=False)

        # Scroll to an actual section to verify sticky remains at the top
        # and the target heading stays below the navigation chrome.
        page.evaluate(
            "() => document.getElementById('cases').scrollIntoView({behavior:'instant'})"
        )
        page.wait_for_timeout(350)
        geometry = page.evaluate("""(mobile) => {
            const header = document.querySelector('.mobile-top-bar');
            const nav = document.querySelector(mobile ? '.bilingual-mobile-strip' : '.home-keycap-strip');
            const section = document.querySelector('#cases');
            const n=nav.getBoundingClientRect();
            const s=section.getBoundingClientRect();
            return {scrollY:scrollY,navTop:n.top,navBottom:n.bottom,
              headerBottom:header ? header.getBoundingClientRect().bottom : 0,
              sectionTop:s.top,navPosition:getComputedStyle(nav).position,
              overflow:document.documentElement.scrollWidth-innerWidth};
        }""", mobile)
        assert geometry["scrollY"] > 250, (name, geometry)
        assert geometry["navPosition"] == "sticky", (name, geometry)
        target_top = geometry["headerBottom"] if mobile else 0
        assert abs(geometry["navTop"] - target_top) <= 9, (name, "sticky offset", geometry)
        assert geometry["sectionTop"] >= geometry["navBottom"] - 5, (
            name, "anchor heading covered", geometry
        )
        assert geometry["overflow"] <= 1, (name, "horizontal overflow", geometry)
        page.screenshot(path=str(out / f"{name}-sticky.png"), full_page=False)
        checks.append({"page":name,"viewport":width,**geometry})
        page.close()
    browser.close()

server.shutdown()
print(json.dumps(checks, ensure_ascii=False, indent=2), flush=True)
print("PASS: desktop/mobile sticky nav, six links, clean track, scroll offset, screenshots", flush=True)
