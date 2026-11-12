"""Optional browser QA. Requires Playwright; axe-core path is passed explicitly."""
import argparse,functools,http.server,json,shutil,threading,os
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
  for width in [320,375,390,428,768,820,900,1024,1440,1920]:
   page=browser.new_page(viewport={'width':width,'height':(1024 if width==768 else 768 if width==1024 else 844)});errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   # Offline external resources: audit local assets only; report remote images separately.
   page.route('https://**/*',lambda r:r.abort());page.goto(base+name+'?view='+('mobile' if name.startswith('mobile') else 'desktop'))
   for img in page.locator('img').all():
    # Scroll stable parent figure or visible image; avoid hidden failed elements
    target = img.locator('xpath=ancestor::figure[1]')
    if target.count():
     if target.is_visible(): target.scroll_into_view_if_needed()
    elif img.is_visible():
     img.scroll_into_view_if_needed()
    page.wait_for_timeout(100)
   page.wait_for_timeout(200);page.evaluate('scrollTo(0,0)')
   row=page.evaluate('''()=>({overflow:document.documentElement.scrollWidth>innerWidth,externalImagesNotChecked:[...document.images].filter(i=>new URL(i.src).origin!==location.origin).map(i=>i.src),brokenImages:[...document.images].filter(i=>new URL(i.src).origin===location.origin&&(!i.complete||!i.naturalWidth)).map(i=>i.currentSrc)})''')
   row.update(file=name,width=width,errors=errors)
   if name in ('index.html','trend.html') and width == 1440:
    # The pause toggle was intentionally removed. Verify the marquee itself.
    marquee=page.locator('[data-keycap-marquee]')
    belt=marquee.locator('.keycap-marquee__belt')
    expect(marquee).to_have_count(1)
    expect(belt).to_have_count(1)
    expect(page.locator('.keycap-marquee__toggle')).to_have_count(0)
    assert marquee.locator('.keycap-marquee__group:not(.keycap-marquee__group--duplicate) a').count() > 0
    if name == 'index.html':
     expect(marquee.locator('a[href="contact.html"]')).to_have_count(0)
     expect(page.locator('.hero-cta-group a[href="contact.html"]')).to_have_count(1)
    motion_allowed=page.evaluate("""() => matchMedia('(min-width: 769px) and (hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)').matches""")
    if motion_allowed:
     assert marquee.evaluate("e=>e.classList.contains('is-enhanced')")
     assert belt.evaluate("e=>getComputedStyle(e).animationName") == 'none'
     v=marquee.locator(".keycap-marquee__viewport")
     before=v.evaluate("e=>e.scrollLeft")
     page.wait_for_timeout(320)
     assert v.evaluate("e=>e.scrollLeft") > before, ("native autoplay",name)
     first_key = page.locator('.keycap-marquee__group a').first
     first_key.dispatch_event('pointerover', {'pointerType': 'mouse'})
     assert marquee.evaluate("e=>e.classList.contains('is-hover-paused')")
     marquee.dispatch_event('pointerleave', {'pointerType': 'mouse'})
     assert not marquee.evaluate("e=>e.classList.contains('is-hover-paused')")
     page.locator('h1').click()
     page.keyboard.press('Tab')
    page.emulate_media(reduced_motion='reduce')
    assert belt.evaluate("e=>getComputedStyle(e).animationName") == 'none'
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
 # Contact details must be visually exclusive to personal/contact pages.
 # Use the approved page as the source rather than duplicating any personal
 # number or address inside the test.
 contact_source=browser.new_page(viewport={'width':1440,'height':844})
 contact_source.goto(base+'contact.html?view=desktop')
 approved=[contact_source.locator('#'+identity).inner_text().strip()
           for identity in ('phoneText','emailText','lineIdText')]
 assert all(approved), "source contact page has missing detail"
 contact_source.close()
 for name in ('index.html','mobile.html','trend.html','mobile-trend.html',
              'contact.html','mobile-contact.html'):
  is_mobile=name.startswith('mobile')
  page=browser.new_page(viewport={'width':390 if is_mobile else 1440,'height':844})
  page.goto(base+name+'?view='+('mobile' if is_mobile else 'desktop'))
  visible_text=page.evaluate('() => document.body.innerText')
  personal=name in ('contact.html','mobile-contact.html')
  for value in approved:
   assert (value in visible_text)==personal, ("contact scope",name,personal)
  if name=='index.html':
   assert not page.locator('.mag-top-ticker span').filter(
       has_text=approved[0]).is_visible(), "desktop top ticker phone still showing"
  if name=='mobile.html':
   assert page.locator('.specs-table.pastel-profile-notes .spec-row:visible').count()==4, (
       "mobile cover contact rows or spacing still showing")
   assert page.locator('a[href="mobile-contact.html"]').count()>0, (
       "personal page action was removed")
  page.close()
 print("Contact details appear only on contact pages in all six screen views.")

 # Explicit tablet and navigation acceptance checks on all six versions.
 for name in ['index.html','contact.html','trend.html','mobile.html','mobile-contact.html','mobile-trend.html']:
  is_mobile=name.startswith('mobile')
  page=browser.new_page(viewport={'width':820 if not is_mobile else 390,'height':1100})
  page.goto(base+name+'?view='+('mobile' if is_mobile else 'desktop'))
  switchbar=page.locator('body > nav.view-mode-switch[aria-label="瀏覽版本切換"]')
  expect(switchbar).to_have_count(1)
  switch=switchbar.locator('a.view-mode-switch__option')
  expect(switch).to_have_count(2)
  assert [x.strip() for x in switch.all_text_contents()]==['電腦版','手機版'],name
  current=switchbar.locator('a[aria-current="page"]')
  expect(current).to_have_count(1)
  assert current.text_content().strip()==('手機版' if is_mobile else '電腦版'),name
  other=switchbar.locator('a:not([aria-current="page"])')
  assert other.get_attribute('href').endswith('?view='+('desktop' if is_mobile else 'mobile')),name
  assert switchbar.evaluate('(e)=>e.getBoundingClientRect().top<25'),name
  assert other.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(152, 87, 115)',name
  destination='mobile-contact.html' if is_mobile else 'contact.html'
  for link in page.locator('a[href="'+destination+'"]').all():
   assert link.text_content().strip()=='個人及聯絡資訊',(name,link.text_content())
  if name in ('index.html','mobile.html'):
   assert page.locator('#education').count()==0,name
   assert page.locator('#career .career-photo img').count()==3,name
   intro=page.locator('.mobile-profile-intro' if is_mobile else '.hero-professional-intro').text_content()
   assert '萬能科技大學' not in intro and "Tomod's" not in intro,name
  if name in ('contact.html','mobile-contact.html'):
   education=page.locator('#education')
   expect(education).to_have_count(1)
   assert '萬能科技大學' in education.text_content()
   assert '2026.10' in education.text_content() and '2030.06' in education.text_content()
  if name=='contact.html':
   columns=page.locator('.contact-dossier-grid.interview-spread').evaluate(
    '(e)=>getComputedStyle(e).gridTemplateColumns.trim().split(/\s+/).length')
   assert columns==1,('tablet contact columns',columns)
  page.close()
 # Print-card relocation and deleted download must work on desktop, tablet,
 # and mobile widths. The card is a website action, not printed resume content.
 for name in ('contact.html','mobile-contact.html'):
  for width in (390,820,1440):
   page=browser.new_page(viewport={'width':width,'height':844})
   page.goto(base+name+'?view='+('mobile' if name.startswith('mobile') else 'desktop'))
   cards=page.locator('.method-card')
   print_card=page.locator('.method-card--print')
   expect(print_card).to_have_count(1)
   assert cards.first.evaluate('(e)=>e.classList.contains("method-card--print")'),(
    'print card must precede phone',name,width)
   print_link=print_card.locator('a[href="resume.html"]')
   expect(print_link).to_have_count(1)
   assert print_link.inner_text().strip()=='列印簡歷',(name,width)
   assert print_link.get_attribute('target') in (None,'_self'),(name,width)
   assert print_card.evaluate('(e)=>getComputedStyle(e).borderTopStyle')=='dashed',(
    'pink dashed print card border',name,width)
   assert print_card.evaluate('(e)=>getComputedStyle(e).borderTopColor')=='rgb(212, 150, 173)',(
    'print border should remain pastel pink',name,width)
   assert page.locator('a[href="resume.pdf"], a[download]').count()==0,(name,width)
   assert page.locator('#phoneText').count()==1 and page.locator('#emailText').count()==1
   print_link.scroll_into_view_if_needed()
   assert print_link.is_visible(),('print action must be visible',name,width)
   page.emulate_media(media='print')
   assert not print_card.is_visible(),('do not print action card',name,width)
   page.close()
 assert not (Path(args.root)/'resume.pdf').exists(), 'deleted PDF has been regenerated'
 print('Print card placed before phone, pink dashed, link and deleted download verified.')

 # Restore only the three work-history photos, not the hero portrait.
 for name in ('index.html','mobile.html'):
  page=browser.new_page(viewport={'width':390 if name.startswith('mobile') else 1440,'height':844})
  page.goto(base+name+'?view='+('mobile' if name.startswith('mobile') else 'desktop'))
  expect(page.locator('.career-photo img')).to_have_count(3)
  assert page.locator('img').count()==3,name
  # Verify the 0.32s one-time left entrance and accessibility fallback.
  page.emulate_media(reduced_motion='no-preference')
  states=page.locator('.career-photo').evaluate_all(
   '(es)=>es.map(e=>{const s=getComputedStyle(e);const m=new DOMMatrix(s.transform);return {p:s.transitionProperty,d:s.transitionDuration,x:m.m41,y:m.m42}})')
  assert all(v['p']=='opacity, transform' and v['d']=='0.32s, 0.32s' and -16.1 <= v['x'] <= 0.1 and abs(v['y']) < 0.1 for v in states),(name,states)
  page.emulate_media(reduced_motion='reduce')
  assert all(x=='0s' for x in page.locator('.career-photo').evaluate_all(
   '(es)=>es.map(e=>getComputedStyle(e).transitionDuration)')),name
  page.close()
 for name in ('contact.html','mobile-contact.html'):
  # Short viewport keeps the photo below the fold: must stay transparent
  # until visible, then take 1.5s to fade in once without position changes.
  page=browser.new_page(viewport={'width':390 if name.startswith('mobile') else 1440,'height':240})
  page.goto(base+name+'?view='+('mobile' if name.startswith('mobile') else 'desktop'))
  photo=page.locator('img[src="assets/portrait-img3264.webp"]')
  expect(photo).to_have_count(1)
  photo.evaluate('(e)=>e.decode()')
  assert photo.evaluate('(e)=>e.complete && e.naturalWidth===512 && e.naturalHeight===640')
  assert photo.evaluate('(e)=>getComputedStyle(e.closest(".photo-frame")).borderRadius==="50%"')
  assert photo.evaluate('(e)=>getComputedStyle(e).objectPosition==="50% 0%"'),(name,'portrait crop must preserve full hairline')
  assert photo.evaluate('(e)=>{const b=e.closest(".photo-frame").getBoundingClientRect();return Math.abs(b.width-b.height)<2}')
  if name.startswith('mobile'):
   assert photo.evaluate('(e)=>getComputedStyle(e.closest(".photo-frame")).maxHeight==="none"')
  expect(page.locator('html.portrait-reveal-js')).to_have_count(1)
  assert photo.evaluate('(e)=>getComputedStyle(e).opacity')=='0',(name,'photo not pending before first viewport entry')
  # Direct scrolling avoids Playwright waiting for a parent reveal to settle.
  photo.evaluate('(e)=>scrollTo({top:scrollY+e.getBoundingClientRect().top-80,behavior:"instant"})')
  page.wait_for_function('() => !!document.querySelector(".contact-portrait-photo.portrait-in-view")')
  appearance=photo.evaluate("""e=>{const s=getComputedStyle(e);return {
   name:s.animationName,duration:s.animationDuration,iterations:s.animationIterationCount,
   fit:s.objectFit,filter:s.filter,transform:s.transform}}""")
  assert appearance=={'name':'contact-portrait-soft-fade','duration':'1.5s','iterations':'1',
                      'fit':'cover','filter':'none','transform':'none'},(name,appearance)
  # Sample the native CSS Animation at its actual midpoint (0.75 s of 1.5 s).
  # This checks a rendered intermediate opacity without timing flakiness.
  midway=photo.evaluate("""e=>{
    const a=e.getAnimations().find(a=>a.animationName==='contact-portrait-soft-fade');
    if(!a)return -1;
    a.pause();
    a.currentTime=750;
    return parseFloat(getComputedStyle(e).opacity);
  }""")
  assert .03 < midway < .97,(name,'opacity must interpolate between transparent and opaque',midway)
  finished=photo.evaluate("""e=>{
    const a=e.getAnimations().find(a=>a.animationName==='contact-portrait-soft-fade');
    a.finish();
    return parseFloat(getComputedStyle(e).opacity);
  }""")
  assert finished>.99,(name,'photo must end fully opaque',finished)
  page.evaluate('scrollTo(0,0)')
  photo.evaluate('(e)=>scrollTo({top:scrollY+e.getBoundingClientRect().top-80,behavior:"instant"})')
  assert photo.evaluate('(e)=>getComputedStyle(e).animationIterationCount')=='1'
  page.emulate_media(reduced_motion='reduce')
  assert photo.evaluate('(e)=>getComputedStyle(e).animationName')=='none'
  assert photo.evaluate('(e)=>getComputedStyle(e).opacity')=='1'
  page.close()
 browser.close()
server.shutdown();(out/'browser.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
failed=[r for r in results if r['overflow'] or r['brokenImages'] or r['errors'] or r.get('axe',{}).get('violations')]
print(json.dumps([{'file':r['file'],'width':r['width'],'overflow':r['overflow'],'brokenImages':r['brokenImages'],'errors':r['errors'],'externalImagesNotChecked':r.get('externalImagesNotChecked',[]),'violations':[{'id':v['id'],'nodes':[n['target'] for n in v['nodes']]} for v in r.get('axe',{}).get('violations',[])]} for r in failed], ensure_ascii=False))
print(f'{len(results)} viewport cases; {len(failed)} failed. Review axe incomplete items manually.')
raise SystemExit(bool(failed))
