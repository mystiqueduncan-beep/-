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
            # Homepage must share the research strip's centered geometry.
            # Check the actual key bounds and every wrapped row, not just CSS.
            for wide_width in (1280,1440,1920):
                page.set_viewport_size({"width":wide_width,"height":900})
                alignment=page.evaluate("""() => {
                  const nav=document.querySelector('nav.home-keycap-strip');
                  const port=nav.querySelector('.keycap-marquee__viewport');
                  const bounds=nav.getBoundingClientRect(), p=port.getBoundingClientRect();
                  const rows=[];
                  [...nav.querySelectorAll('.keycap-marquee__group a')].forEach(link=>{
                    const r=link.getBoundingClientRect();
                    let row=rows.find(row=>Math.abs(row.top-r.top)<3);
                    if(!row){row={top:r.top,left:r.left,right:r.right};rows.push(row);}
                    else{row.left=Math.min(row.left,r.left);row.right=Math.max(row.right,r.right);}
                  });
                  return {shellCenter:(bounds.left+bounds.right)/2,
                    groupCenter:(p.left+p.right)/2,
                    rowCenters:rows.map(row=>(row.left+row.right)/2),
                    overflow:document.documentElement.scrollWidth-innerWidth};
                }""")
                assert alignment["rowCenters"] and len(alignment["rowCenters"])<=2,(name,wide_width,alignment)
                assert abs(alignment["shellCenter"]-alignment["groupCenter"])<=16,(name,wide_width,alignment)
                assert all(abs(x-alignment["groupCenter"])<=16 for x in alignment["rowCenters"]),(name,wide_width,alignment)
                assert alignment["overflow"]<=1,(name,wide_width,alignment)
                print("HOME_NAV_CENTER_PASS",wide_width,alignment,flush=True)
            page.set_viewport_size({"width":width,"height":900})
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
