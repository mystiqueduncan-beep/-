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
  guide=page.locator(".reader-guide")
  compact=page.locator(".reader-compact")
  expect(guide.locator(".reader-index-group")).to_have_count(3)
  expect(guide.locator(".reader-index-link")).to_have_count(11)
  expect(page.locator("nav.trend-bilingual-nav:visible")).to_have_count(0)
  for w in ((390,320,640) if mobile else (1280,1440,1920)):
   page.set_viewport_size({"width":w,"height":860})
   guide.scroll_into_view_if_needed()
   cols=guide.locator(".reader-index-grid").evaluate("e=>getComputedStyle(e).gridTemplateColumns.split(' ').length")
   assert cols==(1 if w<=720 else 3),(name,w,cols)
   assert page.evaluate("document.documentElement.scrollWidth<=innerWidth+1"),(name,w)
  page.set_viewport_size({"width":width,"height":860})
  guide.scroll_into_view_if_needed()
  page.screenshot(path=str(out/f"{name}-top.png"),full_page=False)
  guide.locator('a[href="#strategy"]').click()
  expect(compact).to_be_visible()
  expect(compact.locator(".reader-compact-name")).to_have_text("改善方針")
  geometry=page.evaluate("""() => {
    const n=document.querySelector('.reader-compact').getBoundingClientRect();
    const t=document.getElementById('strategy').getBoundingClientRect();
    return {scrollY:scrollY,navTop:n.top,navBottom:n.bottom,sectionTop:t.top,
      position:getComputedStyle(document.querySelector('.reader-compact')).position,
      overflow:document.documentElement.scrollWidth-innerWidth};
  }""")
  assert geometry["scrollY"]>250 and geometry["position"]=="fixed",(name,geometry)
  assert geometry["navTop"]>=0 and geometry["sectionTop"]>=geometry["navBottom"]-3,(name,geometry)
  assert geometry["overflow"]<=1,(name,geometry)
  if mobile:
   assert page.locator("nav.mobile-bottom-bar").is_visible()
  page.screenshot(path=str(out/f"{name}-sticky.png"),full_page=False)
  result.append({"page":name,"width":width,**geometry})
  page.close()
 browser.close()
server.shutdown()
print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
print("PASS: magazine contents and compact research navigation desktop/mobile; four real browser screenshots",flush=True)
