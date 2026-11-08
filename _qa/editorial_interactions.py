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
  mobile=name.startswith('mobile');page=browser.new_page(viewport={'width':390 if mobile else 1440,'height':844},has_touch=mobile,is_mobile=mobile)
  page.route('https://**/*',lambda r:r.abort())
  url=f'http://127.0.0.1:{server.server_port}/{name}.html?view='+('mobile' if mobile else 'desktop')
  page.goto(url);nav=page.locator('[data-keycap-marquee]');belt=nav.locator('.keycap-marquee__belt');link=nav.locator('a').first
  expect(nav).to_have_class(__import__('re').compile('.*is-enhanced.*'))
  assert belt.evaluate('e=>getComputedStyle(e).animationName')!='none'
  assert not page.locator('.keycap-marquee__toggle').count()
  # Real computed transform advances while the rest of the page scrolls.
  before=belt.evaluate('e=>getComputedStyle(e).transform');page.evaluate('scrollTo(0,500)');page.wait_for_timeout(150)
  assert belt.evaluate('e=>getComputedStyle(e).transform')!=before
  if mobile:
   link.dispatch_event('pointerdown',{'pointerType':'touch'});link.dispatch_event('pointerup',{'pointerType':'touch'})
   page.wait_for_timeout(1400);assert not nav.evaluate('e=>e.classList.contains("is-touch-paused")')
  else:
   link.dispatch_event('pointerover',{'pointerType':'mouse'});assert belt.evaluate('e=>getComputedStyle(e).animationPlayState')=='paused'
   nav.dispatch_event('pointerleave',{'pointerType':'mouse'});assert belt.evaluate('e=>getComputedStyle(e).animationPlayState')=='running'
  link.dispatch_event('click');page.wait_for_timeout(200)
  assert belt.evaluate('e=>getComputedStyle(e).animationPlayState')=='running'
  assert page.locator('meta[name=viewport]').get_attribute('content').find('user-scalable=no')<0
  # Keyboard focus must remain visible; reduced-motion removes continuous animation.
  link.focus();expect(link).to_be_focused();assert link.evaluate('e=>getComputedStyle(e).outlineStyle')!='none'
  page.emulate_media(reduced_motion='reduce');assert belt.evaluate('e=>getComputedStyle(e).animationName')=='none'
  rows.append({'page':name,'marquee':'pass','touch' if mobile else 'hover':'pass'});page.close()
 # Same-tab cross-document navigation uses the existing transition mechanism.
 page=browser.new_page();page.route('https://**/*',lambda r:r.abort());page.goto(f'http://127.0.0.1:{server.server_port}/index.html?view=desktop')
 assert page.locator('a[href="contact.html"]').first.get_attribute('target') in (None,'_self')
 page.locator('a[href="contact.html"]').first.click();page.wait_for_url('**/contact.html*');page.wait_for_timeout(800)
 assert len(browser.contexts[-1].pages)==1
 assert page.evaluate('getComputedStyle(document.body).opacity')=='1'
 page.go_back();page.wait_for_timeout(800);assert page.locator('h1').inner_text()=='黃博詩'
 browser.close()
server.shutdown();print(json.dumps(rows,ensure_ascii=False,indent=2));print('Same-tab transition and history passed.')
