"""Optional browser QA. Requires Playwright; axe-core path is passed explicitly."""
import argparse,functools,http.server,json,shutil,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--out',required=True);ap.add_argument('--axe');args=ap.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
 def translate_path(self,path):return super().translate_path(path.removeprefix('/-'))
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=args.root))
threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/-/'
results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium') or None,args=['--no-sandbox'])
 for name in ['index.html','contact.html','trend.html','mobile.html','mobile-contact.html','mobile-trend.html']:
  for width in [320,375,390,430,768,1024,1440]:
   page=browser.new_page(viewport={'width':width,'height':844});errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   # Same explicit offline-font condition as the recorded audit; no public CWV claim.
   page.route('https://**/*',lambda r:r.abort());page.goto(base+name)
   for img in page.locator('img').all():img.scroll_into_view_if_needed();page.wait_for_timeout(100)
   page.wait_for_timeout(200);page.evaluate('scrollTo(0,0)')
   row=page.evaluate('''()=>({overflow:document.documentElement.scrollWidth>innerWidth,brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.currentSrc)})''')
   row.update(file=name,width=width,errors=errors)
   if width in (390,1440):
    page.screenshot(path=str(out/f'{name}-{width}.png'),full_page=True)
    if args.axe:
     page.add_script_tag(path=args.axe)
     row['axe']=page.evaluate('''async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']}});return {violations:r.violations,incomplete:r.incomplete}}''')
   results.append(row);page.close()
 browser.close()
server.shutdown();(out/'browser.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
failed=[r for r in results if r['overflow'] or r['brokenImages'] or r['errors'] or r.get('axe',{}).get('violations')]
print(f'{len(results)} viewport cases; {len(failed)} failed. Review axe incomplete items manually.')
raise SystemExit(bool(failed))
