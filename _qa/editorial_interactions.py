"""Browser contracts for desktop and touch chapter navigation and page transitions."""
import functools,http.server,threading,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1]
class H(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(H,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
rows=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH'),args=['--no-sandbox'])
 for name in ['index','trend','mobile','mobile-trend']:
  mobile=name.startswith('mobile')
  page=browser.new_page(viewport={'width':390 if mobile else 1440,'height':844},
                        has_touch=mobile,is_mobile=mobile)
  page.route('https://**/*',lambda r:r.abort())
  url=f'http://127.0.0.1:{server.server_port}/{name}.html?view='+('mobile' if mobile else 'desktop')
  page.goto(url)
  if mobile:
   # A single existing bottom bar replaces the redundant top chapter strip.
   expect(page.locator('[data-keycap-marquee]')).to_have_count(0)
   bottom=page.locator('nav.mobile-bottom-bar')
   expect(bottom).to_have_count(1)
   assert bottom.is_visible(),name
   assert bottom.evaluate('e=>getComputedStyle(e).position')=='fixed',name
   assert page.locator('meta[name=viewport]').get_attribute('content').find('user-scalable=no')<0
   if name=='mobile':
    for fragment in ['#top','#advantages','#cases','#career']:
     anchor=bottom.locator('a[href="'+fragment+'"]')
     expect(anchor).to_have_count(1)
     assert page.locator(fragment).count()==1,(name,fragment)
    bottom.locator('a[href="#cases"]').click()
    assert page.evaluate('location.hash')=='#cases',name
   else:
    assert bottom.locator('a[aria-current="page"][href="mobile-trend.html"]').count()==1,name
    assert bottom.locator('a[href="mobile.html"]').count()==1,name
    assert bottom.locator('a[href="mobile-contact.html"]').count()==1,name
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),name
   rows.append({'page':name,'topChapterNav':'removed','bottomNavigation':'pass'})
  elif name=="trend":
   guide=page.locator(".reader-guide")
   expect(guide.locator(".reader-index-link")).to_have_count(11)
   expect(page.locator("nav.trend-bilingual-nav")).to_be_hidden()
   guide.locator('a[href="#market"]').click()
   expect(page.locator(".reader-compact-name")).to_have_text("市場判讀")
   assert page.evaluate("location.hash")=="#market"
   rows.append({"page":name,"magazineNavigation":"pass"})
  else:
   nav=page.locator('[data-keycap-marquee]')
   expect(nav).to_have_count(1)
   keys=nav.locator('.keycap-marquee__group a.nav-btn-mk')
   expect(keys).to_have_count(11 if name=='trend' else 6)
   assert nav.evaluate("e=>e.classList.contains('is-static-nav')"),name
   assert not nav.evaluate("e=>e.classList.contains('is-enhanced')"),name
   viewport=nav.locator('.keycap-marquee__viewport')
   before=viewport.evaluate('e=>e.scrollLeft')
   page.wait_for_timeout(260)
   assert abs(viewport.evaluate('e=>e.scrollLeft')-before)<=1,('no autoplay',name)
   first=keys.first
   first.click()
   assert page.evaluate('location.hash')==first.get_attribute('href'),name
   assert first.get_attribute('aria-current')=='location',name
   rows.append({'page':name,'stationaryDesktopNav':'pass'})
  page.close()
 # Same-tab cross-document navigation uses the existing transition mechanism.
 page=browser.new_page();page.route('https://**/*',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}/index.html?view=desktop')
 assert page.locator('a[href="contact.html"]').first.get_attribute('target') in (None,'_self')
 page.locator('a[href="contact.html"]').first.click();page.wait_for_url('**/contact.html*');page.wait_for_timeout(800)
 assert len(browser.contexts[-1].pages)==1
 assert page.evaluate('getComputedStyle(document.body).opacity')=='1'
 page.go_back();page.wait_for_timeout(800);assert page.locator('h1').inner_text()=='黃博詩'
 # A malformed percent escape in a shared link must not abort page
 # initialization or subsequent valid chapter navigation.
 for name in ['index','mobile','trend','mobile-trend']:
  mobile=name.startswith('mobile')
  page=browser.new_page(viewport={'width':390 if mobile else 1440,'height':844},
                        reduced_motion='reduce')
  page.route('https://**/*',lambda r:r.abort())
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  url=f'http://127.0.0.1:{server.server_port}/{name}.html?view='+('mobile' if mobile else 'desktop')
  page.goto(url+'#%E0%A4%A',wait_until='load')
  chart_selector='.inline-research-viz' if 'trend' in name else '.portfolio-chart'
  expect(page.locator(chart_selector).first).to_be_attached()
  toggle=page.locator('.portfolio-disclosure-toggle').first
  if 'trend' in name:
   # Research details are ordinary scroll content; no disclosure toggles.
   expect(toggle).to_have_count(0)
   detail=page.locator('#consumer .cards-2x2-grid > .feature-card .feature-card-data').first
   assert detail.inner_text().strip(),name
   assert detail.evaluate('(e)=>!e.closest("[inert],[aria-hidden=true]")'),name
  else:
   # Homepage competency/case toggles are intentionally preserved.
   expect(toggle).to_have_attribute('aria-expanded','false')
   toggle.click()
   expect(toggle).to_have_attribute('aria-expanded','true')
  page.evaluate("location.hash = '%ZZ'")
  page.wait_for_timeout(80)
  page.evaluate("location.hash = " + ("'#market'" if name=='mobile-trend' else "'#cases'" if name=='mobile' else "document.querySelector('[data-keycap-marquee] a').hash"))
  page.wait_for_timeout(80)
  assert not errors, ('malformed hash must not raise page errors',name,errors)
  assert page.evaluate("document.getElementById(decodeURIComponent(location.hash.slice(1))) !== null")
  rows.append({'page':name,'malformedHash':'pass'})
  page.close()
 browser.close()
server.shutdown();print(json.dumps(rows,ensure_ascii=False,indent=2));print('Same-tab transition and history passed.')
