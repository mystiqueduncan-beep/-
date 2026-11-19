"""Screenshots and focused browser regression for research marquee parity.

Does not touch source files or the public website.
"""
import functools, http.server, threading, os, json, argparse
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument("--out",required=True);args=p.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(H,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
result=[]
with sync_playwright() as browserapi:
 browser=browserapi.chromium.launch(executable_path=os.environ.get("CHROME_PATH"),args=["--no-sandbox"])
 for name,width,mobile in (("trend",1440,False),("mobile-trend",390,True)):
  page=browser.new_page(viewport={"width":width,"height":860},is_mobile=mobile,has_touch=mobile,reduced_motion="reduce")
  page.route("https://**/*",lambda r:r.abort())
  page.goto(f"http://127.0.0.1:{server.server_port}/{name}.html?view="+("mobile" if mobile else "desktop"),wait_until="domcontentloaded")
  nav=page.locator("nav.trend-bilingual-nav")
  expect(nav).to_have_count(1)
  expect(nav.locator("a.nav-btn-mk")).to_have_count(11)
  expect(nav.locator(".bilingual-nav-jp")).to_have_count(11)
  expect(page.locator(".bilingual-current")).to_have_count(0)
  track=nav.locator(".keycap-marquee__belt")
  for pseudo in ("::before","::after"):
   assert track.evaluate("(e,p)=>getComputedStyle(e,p).content",pseudo) in ('""',"none"),(name,pseudo)
  assert nav.evaluate("e=>getComputedStyle(e).position")=="sticky",name
  assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),name
  page.wait_for_timeout(150)
  page.screenshot(path=str(out/f"{name}-top.png"),full_page=False)
  page.evaluate("() => document.getElementById('strategy').scrollIntoView({behavior:'instant'})")
  page.wait_for_timeout(350)
  geometry=page.evaluate("""(isMobile) => {
   const n=document.querySelector('nav.trend-bilingual-nav').getBoundingClientRect();
   const h=document.querySelector('.mobile-top-bar');
   const t=document.querySelector('#strategy').getBoundingClientRect();
   return {scrollY:scrollY,navTop:n.top,navBottom:n.bottom,
     headerBottom:isMobile&&h?h.getBoundingClientRect().bottom:0,
     sectionTop:t.top,position:getComputedStyle(document.querySelector('nav.trend-bilingual-nav')).position,
     overflow:document.documentElement.scrollWidth-innerWidth};
  }""",mobile)
  assert geometry["scrollY"]>250,(name,geometry)
  assert geometry["position"]=="sticky",(name,geometry)
  top=geometry["headerBottom"] if mobile else 0
  assert abs(geometry["navTop"]-top)<=9,(name,geometry)
  assert geometry["sectionTop"]>=geometry["navBottom"]-5,(name,geometry)
  assert geometry["overflow"]<=1,(name,geometry)
  page.screenshot(path=str(out/f"{name}-sticky.png"),full_page=False)
  result.append({"page":name,"width":width,**geometry})
  page.close()
 browser.close()
server.shutdown()
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
print("PASS: research bilingual sticky marquee desktop/mobile; four real browser screenshots",flush=True)
