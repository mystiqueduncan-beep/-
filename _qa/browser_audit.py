"""Optional browser QA. Requires Playwright; axe-core path is passed explicitly."""
import os,argparse,functools,http.server,json,shutil,threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--out',required=True);ap.add_argument('--axe');args=ap.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):return super().translate_path(path.removeprefix('/-'))
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=args.root))
threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/-/'
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH'),args=['--no-sandbox'])
 for name in ['index.html','contact.html','trend.html','mobile.html','mobile-contact.html','mobile-trend.html']:
  for width in [320,375,390,430,768,1024,1440]:
   page=browser.new_page(viewport={'width':width,'height':844});errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   # Offline external resources: audit local assets only; report remote images separately.
   page.route('https://**/*',lambda r:r.abort());page.goto(base+name+'?view='+('mobile' if name.startswith('mobile') else 'desktop'))
   # Scroll stable containers: failed remote images may intentionally be display:none.
   for figure in page.locator('.career-photo').all():
    figure.scroll_into_view_if_needed()
    expect(figure).to_have_class(__import__('re').compile(r'.*is-visible.*'))
    page.wait_for_timeout(850)
    assert figure.evaluate("e=>getComputedStyle(e).opacity") == '1'
    expect(figure.locator('.career-photo__fallback')).to_be_visible()
   for img in page.locator('img').all():
    if img.is_visible():img.scroll_into_view_if_needed();page.wait_for_timeout(100)
   page.wait_for_timeout(200);page.evaluate('scrollTo(0,0)')
   row=page.evaluate('''()=>({overflow:document.documentElement.scrollWidth>innerWidth,externalImagesNotChecked:[...document.images].filter(i=>new URL(i.src).origin!==location.origin).map(i=>i.src),brokenImages:[...document.images].filter(i=>new URL(i.src).origin===location.origin&&(!i.complete||!i.naturalWidth)).map(i=>i.currentSrc)})''')
   row.update(file=name,width=width,errors=errors)
   if name in ('index.html','trend.html') and width == 1440:
    toggle=page.locator('.keycap-marquee__toggle')
    toggle.click()
    assert toggle.get_attribute('aria-pressed') == 'true'
    assert page.locator('.keycap-marquee__belt').evaluate("e=>getComputedStyle(e).animationName") == 'none'
    page.mouse.move(0,0)
    assert toggle.get_attribute('aria-pressed') == 'true'
    toggle.click()
    assert toggle.get_attribute('aria-pressed') == 'false'
    assert page.locator('.keycap-marquee__belt').evaluate("e=>getComputedStyle(e).animationName") != 'none'
    page.keyboard.press('Shift+Tab')
    assert page.locator('.keycap-marquee').evaluate("e=>e.classList.contains('is-keyboard-paused')")
    assert page.evaluate("()=>{const r=document.activeElement.getBoundingClientRect();return r.left>=0&&r.right<=innerWidth}")
    page.locator('h1').click()
    page.emulate_media(reduced_motion='reduce')
    expect(toggle).to_be_hidden()
    page.emulate_media(reduced_motion='no-preference')
    row['marquee_interactions']='passed'

   if width in (390,1440):
    # Audit fully revealed content, not transient opacity during entrance effects.
    page.emulate_media(reduced_motion='reduce')
    page.wait_for_timeout(800)
    page.screenshot(path=str(out/f'{name}-{width}.png'),full_page=True)
    if args.axe:
     page.add_script_tag(path=args.axe)
     row['axe']=page.evaluate('''async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']}});return {violations:r.violations,incomplete:r.incomplete}}''')
   results.append(row);page.close()
 # Dedicated progressive-enhancement cases, independent of external image availability.
 for name in ('index.html','mobile.html'):
  view='mobile' if name.startswith('mobile') else 'desktop'
  for mode in ('normal','no-js','script-blocked','observer-failure','reduced','print'):
   page=browser.new_page(viewport={'width':390 if view=='mobile' else 1440,'height':844},java_script_enabled=mode!='no-js',reduced_motion='reduce' if mode=='reduced' else 'no-preference')
   page.route('https://**/*',lambda r:r.abort())
   if mode=='script-blocked':page.route('**/career-images.js',lambda r:r.abort())
   if mode=='observer-failure':page.add_init_script("window.IntersectionObserver=class {constructor(){throw Error('Injected IO failure')}}")
   page.goto(base+name+'?view='+view)
   if mode=='print':page.emulate_media(media='print')
   photos=page.locator('.career-photo');assert photos.count()==3
   if mode=='normal':
    expect(photos.first).to_have_class(__import__('re').compile(r'.*is-pending.*'))
    assert photos.first.evaluate("e=>getComputedStyle(e).opacity")=='0'
   for photo in photos.all():
    photo.scroll_into_view_if_needed();page.wait_for_timeout(950)
    assert photo.evaluate("e=>getComputedStyle(e).opacity")=='1', (name,mode)
    assert photo.locator('img').get_attribute('alt')
    if mode=='normal':
     assert photo.evaluate("e=>getComputedStyle(e).transitionDuration")=='0.8s, 0.8s'
     page.evaluate('scrollTo(0,0)');page.wait_for_timeout(100)
     assert photo.evaluate("e=>getComputedStyle(e).opacity")=='1'
   page.close()
 browser.close()
server.shutdown();(out/'browser.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
failed=[r for r in results if r['overflow'] or r['brokenImages'] or r['errors'] or r.get('axe',{}).get('violations')]
print(json.dumps([{'file':r['file'],'width':r['width'],'overflow':r['overflow'],'brokenImages':r['brokenImages'],'errors':r['errors'],'externalImagesNotChecked':r.get('externalImagesNotChecked',[]),'violations':[{'id':v['id'],'nodes':[n['target'] for n in v['nodes']]} for v in r.get('axe',{}).get('violations',[])]} for r in failed], ensure_ascii=False))
print(f'{len(results)} viewport cases; {len(failed)} failed. Review axe incomplete items manually.')
raise SystemExit(bool(failed))
