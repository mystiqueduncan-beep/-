"""Online release audit: external images, screenshots and Lighthouse."""
import argparse,functools,http.server,json,os,subprocess,threading,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--out',default='/tmp/release-audit');args=ap.parse_args()
root=Path(args.root)
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',8765),functools.partial(Handler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
rows=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH'),args=['--no-sandbox'])
 for name,width in [('index.html',1440),('mobile.html',390),('trend.html',1440),('mobile-trend.html',390),('contact.html',1440),('mobile-contact.html',390)]:
  page=browser.new_page(viewport={'width':width,'height':900},reduced_motion='reduce')
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto('http://127.0.0.1:8765/'+name+'?view='+('mobile' if name.startswith('mobile') else 'desktop'),wait_until='networkidle')
  for img in page.locator('img').all():
   target=img.locator('xpath=ancestor::figure[1]')
   if target.count():target.scroll_into_view_if_needed()
   elif img.is_visible():img.scroll_into_view_if_needed()
   try: img.evaluate("(i)=>i.decode()")
   except Exception: pass
  row=page.evaluate("()=>({overflow:document.documentElement.scrollWidth>innerWidth,images:[...document.images].map(i=>({src:i.currentSrc,loaded:i.complete&&i.naturalWidth>0}))})")
  row.update(file=name,width=width,errors=errors)
  rows.append(row)
  page.evaluate('scrollTo({top:0,behavior:"instant"})')
  page.screenshot(path=str(out/(name+'-top.png')))
  if page.locator('#career').count():
   page.locator('#career').scroll_into_view_if_needed()
   page.screenshot(path=str(out/(name+'-career.png')))
  page.screenshot(path=str(out/(name+'-full.png')),full_page=True)
  page.close()
 browser.close()
 chrome=os.environ.get('CHROME_PATH') or p.chromium.executable_path
print('ONLINE_IMAGES_AND_LAYOUT='+json.dumps(rows),flush=True)
(out/'online.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
env=dict(os.environ,CHROME_PATH=chrome)
npx_cmd = shutil.which('npx') or 'npx'
summaries=[]
for name,view in [('index.html','desktop'),('mobile.html','mobile')]:
 for attempt in range(3):
  report=out/(name+f'-{attempt+1}-lighthouse.json')
  cmd=[npx_cmd,'--yes','lighthouse@12.8.2','http://127.0.0.1:8765/'+name+'?view='+view,'--chrome-flags=--no-sandbox --headless','--output=json','--output-path='+str(report),'--quiet']
  if view=='desktop':cmd+=['--preset=desktop']
  subprocess.run(cmd,env=env,check=True)
  data=json.loads(report.read_text(encoding='utf-8'))
  summary={'page':name,'run':attempt+1,'lighthouseVersion':data.get('lighthouseVersion'),'environment':data.get('environment'),'configSettings':data.get('configSettings'),'scores':{k:v['score'] for k,v in data['categories'].items()},'runtimeError':data.get('runtimeError'),'findings':[{'id':k,'title':v['title'],'score':v.get('score'),'displayValue':v.get('displayValue')} for k,v in data['audits'].items() if v.get('score') is not None and v['score']<1]}
  summaries.append(summary)
print('LIGHTHOUSE_SUMMARY='+json.dumps(summaries),flush=True)
(out/'lighthouse-summary.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
server.shutdown()
assert all(not r['overflow'] and not r['errors'] and all(i['loaded'] for i in r['images']) for r in rows),'Online image/layout checks failed'
assert all(not r['runtimeError'] for r in summaries),'Lighthouse runtime failed'
