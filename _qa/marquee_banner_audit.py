"""Browser acceptance for stationary responsive chapter navigation.

Four page variants x six viewport widths. Desktop: wrapping, stationary
links. Mobile/small screens: one user-swipable row. No auto-play, duplicate
links, icon ornaments, or automatic horizontal reposition on chapter change.
Images are captured in the artifact directory for layout review.
"""
import argparse
import functools
import http.server
import json
import os
import threading
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, expect

WIDTHS = (390,430,768,1024,1440,1920)
PAGES = ("index.html","trend.html","mobile.html","mobile-trend.html")
parser=argparse.ArgumentParser()
parser.add_argument("--root",default=str(Path(__file__).resolve().parents[1]))
parser.add_argument("--out",required=True)
parser.add_argument("--baseline",action="store_true")
parser.add_argument("--url",help="Published site URL, including project path")
args=parser.parse_args()
out=Path(args.out)
out.mkdir(parents=True,exist_ok=True)

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*_args):pass
server=None
if args.url:
    base=args.url.rstrip("/")+"/"
else:
    server=http.server.ThreadingHTTPServer(
        ("127.0.0.1",0),functools.partial(Handler,directory=args.root))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f"http://127.0.0.1:{server.server_port}/"

METRICS="""() => {
 const nav=document.querySelector('[data-keycap-marquee]');
 const shell=nav.closest('nav'),view=nav.querySelector('.keycap-marquee__viewport');
 const belt=nav.querySelector('.keycap-marquee__belt');
 const group=nav.querySelector('.keycap-marquee__group');
 const links=[...group.querySelectorAll('a[href^="#"]')];
 const rect=e=>{const b=e.getBoundingClientRect();return {
  left:b.left,right:b.right,top:b.top,bottom:b.bottom,height:b.height,width:b.width}};
 return {
  nav:rect(nav),shell:rect(shell),viewport:rect(view),group:rect(group),
  shellPosition:getComputedStyle(shell).position,
  display:getComputedStyle(group).display,
  flexWrap:getComputedStyle(group).flexWrap,
  overflowX:getComputedStyle(view).overflowX,
  beltAnimation:getComputedStyle(belt).animationName,
  beltTransform:getComputedStyle(belt).transform,
  before:getComputedStyle(belt,'::before').display,
  after:getComputedStyle(belt,'::after').display,
  enhanced:nav.classList.contains('is-enhanced'),
  staticNav:nav.classList.contains('is-static-nav'),
  scrollWidth:view.scrollWidth,clientWidth:view.clientWidth,scrollLeft:view.scrollLeft,
  pageOverflow:document.documentElement.scrollWidth-innerWidth,
  links:links.map(a=>({
   href:a.getAttribute('href'),rect:rect(a),
   visible:getComputedStyle(a).display!=='none',
   textFits:a.scrollWidth<=a.clientWidth+2,
   current:a.getAttribute('aria-current')==='location',
   cn:getComputedStyle(a.querySelector('.bilingual-nav-cn')).display,
   jp:getComputedStyle(a.querySelector('.bilingual-nav-jp')).display,
  }))
 };
}"""

def verify(ok,msg,data=None):
    if not ok:
        raise AssertionError((msg,data))

rows=[]
try:
 with sync_playwright() as api:
  browser=api.chromium.launch(executable_path=os.environ.get("CHROME_PATH"),
                              args=["--no-sandbox"])
  for name in PAGES:
   for width in WIDTHS:
    mobile=name.startswith("mobile")
    manual=mobile or width<=720
    page=browser.new_page(viewport={"width":width,"height":844},
       is_mobile=mobile,has_touch=mobile,reduced_motion="no-preference")
    page.route("https://**/*",lambda route:route.abort())
    errors=[]
    page.on("pageerror",lambda e:errors.append(str(e)))
    item={"page":name,"width":width}
    try:
     page.goto(urljoin(base,name)+"?view="+("mobile" if mobile else "desktop"),
         wait_until="load",timeout=45000)
     if "trend" in name and not args.baseline:
      guide=page.locator(".reader-guide")
      compact=page.locator(".reader-compact")
      verify(guide.locator(".reader-index-link").count()==11,"11 magazine chapter links",name)
      verify(page.locator("nav.trend-bilingual-nav:visible").count()==0,"no duplicate desktop strip",name)
      verify(page.evaluate("document.documentElement.scrollWidth-innerWidth<=1"),"page overflow",name)
      guide.scroll_into_view_if_needed()
      page.screenshot(path=str(out/f"{Path(name).stem}-{width}-contents.png"))
      guide.locator('a[href="#strategy"]').click()
      expect(compact).to_be_visible()
      expect(compact.locator(".reader-compact-name")).to_have_text("改善方針")
      verify(compact.evaluate("e=>getComputedStyle(e).position")== "fixed","compact fixed",name)
      if mobile:
       verify(page.locator("nav.mobile-bottom-bar").is_visible(),"mobile cross-page nav retained",name)
      verify(not errors,"no research page script exception",errors)
      page.screenshot(path=str(out/f"{Path(name).stem}-{width}.png"))
      item["status"]="passed";rows.append(item);print(json.dumps(item,ensure_ascii=False),flush=True)
      page.close();continue
     if mobile and not args.baseline:
      # Dedicated phone layouts intentionally use just the fixed footer.
      # They must not contain hidden/duplicated top chapter links.
      verify(page.locator('[data-keycap-marquee]').count()==0,
             "redundant mobile chapter strip still mounted",name)
      verify(page.locator('nav.trend-bilingual-nav,nav.bilingual-mobile-strip').count()==0,
             "old mobile top nav remains",name)
      bottom=page.locator('nav.mobile-bottom-bar')
      verify(bottom.count()==1 and bottom.is_visible(),"mobile bottom bar exists",name)
      verify(bottom.evaluate('e=>getComputedStyle(e).position')=='fixed',
             "bottom bar fixed",name)
      verify(bottom.locator('a[href="mobile-contact.html"]').count()==1,
             "contact navigation",name)
      verify(bottom.locator('a[href="mobile-trend.html"]').count()==1,
             "research navigation",name)
      if name=='mobile.html':
       for anchor in ('#top','#advantages','#cases','#career'):
        verify(bottom.locator('a[href="'+anchor+'"]').count()==1 and
               page.locator(anchor).count()==1,"mobile section anchor",anchor)
      else:
       verify(bottom.locator('a[href="mobile.html"]').count()==1,
              "research page return to home",name)
      verify(page.evaluate('document.documentElement.scrollWidth-innerWidth<=1'),
             "mobile page horizontal overflow",name)
      page.screenshot(path=str(out/f"{Path(name).stem}-{width}.png"))
      page.evaluate("scrollTo({top:Math.min(1100,document.body.scrollHeight-innerHeight),behavior:'instant'})")
      page.wait_for_timeout(130)
      verify(bottom.is_visible() and bottom.evaluate('e=>getComputedStyle(e).position')=='fixed',
             "bottom bar remains visible after scrolling",name)
      verify(not errors,"no mobile page script exception",errors)
      item['status']='passed'
      rows.append(item)
      print(json.dumps({k:item[k] for k in ("page","width","status")},ensure_ascii=False),flush=True)
      page.close()
      continue
     page.wait_for_function("""() => document.querySelector('[data-keycap-marquee]')
        ?.classList.contains('is-static-nav')""")
     nav=page.locator("[data-keycap-marquee]")
     view=nav.locator(".keycap-marquee__viewport")
     metrics=page.evaluate(METRICS)
     item["initial"]=metrics
     if not args.baseline:
      verify(metrics["pageOverflow"]<=1,"whole-page horizontal overflow",metrics)
      verify(metrics["shellPosition"]=="sticky","navigation sticky",metrics)
      verify(metrics["staticNav"] and not metrics["enhanced"],
         "static nav cannot auto-enhance",metrics)
      verify(metrics["beltAnimation"]=="none","no belt animation",metrics)
      verify(metrics["before"]=="none" and metrics["after"]=="none",
         "no decorative moving run-in/out",metrics)
      verify(len(metrics["links"])==(11 if "trend" in name else 6),
         "expected original chapter links",metrics)
      verify(len({x["href"] for x in metrics["links"]})==len(metrics["links"]),
         "links cannot be duplicated")
      verify(all(x["visible"] and x["textFits"] and x["cn"]!="none" and x["jp"]=="none"
                 for x in metrics["links"]),"compact readable Chinese shortcuts",metrics)
      verify(sum(x["current"] for x in metrics["links"])==1,"single active chapter",metrics)
      initial=metrics["scrollLeft"]
      page.wait_for_timeout(300)
      verify(abs(view.evaluate("e=>e.scrollLeft")-initial)<=1,
         "autoplay must never move navigation",metrics)
      if manual:
       verify(metrics["overflowX"]=="auto","manual viewport scrolling enabled",metrics)
       verify(metrics["flexWrap"]=="nowrap","one mobile row",metrics)
       # Wide viewports may fit every key without scrolling; only overflow
       # cases should have movable content. Both remain user-controlled.
       if metrics["scrollWidth"]>metrics["clientWidth"]+12:
        view.evaluate("e=>{e.scrollLeft=0;e.focus({preventScroll:true})}")
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(120)
        moved=view.evaluate("e=>e.scrollLeft")
        verify(moved>8,"keyboard manual movement",moved)
        page.evaluate('scrollBy({top:95,behavior:"instant"})')
        page.wait_for_timeout(100)
        verify(abs(view.evaluate("e=>e.scrollLeft")-moved)<=2,
           "reading must not reposition manually moved strip",name)
       else:
        verify(all(x["rect"]["left"]>=metrics["viewport"]["left"]-2 and
             x["rect"]["right"]<=metrics["viewport"]["right"]+2
             for x in metrics["links"]),"all keys fully shown when no overflow",metrics)
      else:
       verify(metrics["flexWrap"]=="wrap","desktop wraps chapter keys",metrics)
       verify(metrics["scrollWidth"]<=metrics["clientWidth"]+2,
          "all desktop keys fit without horizontal scrolling",metrics)
       verify(all(x["rect"]["left"]>=metrics["viewport"]["left"]-2 and
         x["rect"]["right"]<=metrics["viewport"]["right"]+2
         for x in metrics["links"]),"desktop links not clipped",metrics)
      # Native hash navigation remains functional; no JS redirects.
      first=nav.locator(".keycap-marquee__group a").first
      first.click()
      verify(page.evaluate("location.hash")==first.get_attribute("href"),
          "link navigation",name)
      page.wait_for_timeout(130)
      verify(first.get_attribute("aria-current")=="location",
          "clicked section highlight",name)
      verify(not errors,"no script error",errors)
     page.screenshot(path=str(out/f"{Path(name).stem}-{width}.png"))
     item["status"]="captured" if args.baseline else "passed"
    except Exception as error:
     item["status"]="failed";item["error"]=str(error)
     page.screenshot(path=str(out/f"{Path(name).stem}-{width}-failure.png"))
    rows.append(item)
    print(json.dumps({k:item[k] for k in ("page","width","status","error") if k in item},
         ensure_ascii=False),flush=True)
    page.close()
  browser.close()
finally:
 if server:server.shutdown()
 (out/"results.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),
                                  encoding="utf-8")
assert len(rows)==len(PAGES)*len(WIDTHS) and all(row["status"]!="failed" for row in rows), \
  f"Static navigation failed; inspect {out/'results.json'}"
print(f"PASS: {len(rows)} stationary desktop/mobile chapter navigation cases",flush=True)
