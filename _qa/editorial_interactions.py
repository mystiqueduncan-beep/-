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
  nav=page.locator('[data-keycap-marquee]')
  expect(nav).to_have_count(1)
  keys=nav.locator('.keycap-marquee__group a.nav-btn-mk')
  expect(keys).to_have_count(11 if 'trend' in name else 6)
  expect(nav.locator('.bilingual-nav-jp')).to_have_count(11 if 'trend' in name else 6)
  assert nav.evaluate("e=>e.classList.contains('is-static-nav')"),name
  assert not nav.evaluate("e=>e.classList.contains('is-enhanced')"),name
  assert nav.locator('.keycap-marquee__belt').evaluate(
   'e=>getComputedStyle(e).animationName')=='none',name
  viewport=nav.locator('.keycap-marquee__viewport')
  initial=viewport.evaluate('e=>e.scrollLeft')
  page.wait_for_timeout(290)
  assert abs(viewport.evaluate('e=>e.scrollLeft')-initial)<=1,('autoplay disabled',name)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),name
  if mobile:
   assert viewport.evaluate('e=>getComputedStyle(e).overflowX')=='auto',name
   assert viewport.evaluate('e=>e.scrollWidth>e.clientWidth'),name
   assert page.locator('.mobile-bottom-bar').count()==1,name
   viewport.evaluate('e=>e.scrollLeft=0')
   viewport.focus()
   page.keyboard.press('ArrowRight')
   moved=viewport.evaluate('e=>e.scrollLeft')
   assert moved>100, ('manual keyboard scroll',name,moved)
   # Reading changes may recolor the active link but cannot relocate the nav.
   page.evaluate('scrollBy({top:100,behavior:"instant"})')
   page.wait_for_timeout(170)
   assert abs(viewport.evaluate('e=>e.scrollLeft')-moved)<=1,('user position retained',name)
  else:
   assert viewport.evaluate('e=>getComputedStyle(e).overflowX')=='visible',name
  first=keys.first
  first.click()
  assert page.evaluate('location.hash')==first.get_attribute('href'),name
  assert first.get_attribute('aria-current')=='location',name
  assert page.locator('meta[name=viewport]').get_attribute('content').find('user-scalable=no')<0
  assert not page.locator('.keycap-marquee__toggle').count()
  rows.append({'page':name,'stationaryNav':'pass','chapterClick':'pass','manualScroll':mobile})
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
  expect(toggle).to_have_attribute('aria-expanded','false')
  toggle.click()
  expect(toggle).to_have_attribute('aria-expanded','true')
  page.evaluate("location.hash = '%ZZ'")
  page.wait_for_timeout(80)
  page.evaluate("location.hash = document.querySelector('[data-keycap-marquee] a').hash")
  page.wait_for_timeout(80)
  assert not errors, ('malformed hash must not raise page errors',name,errors)
  assert page.evaluate("document.getElementById(decodeURIComponent(location.hash.slice(1))) !== null")
  rows.append({'page':name,'malformedHash':'pass'})
  page.close()
 browser.close()
server.shutdown();print(json.dumps(rows,ensure_ascii=False,indent=2));print('Same-tab transition and history passed.')
