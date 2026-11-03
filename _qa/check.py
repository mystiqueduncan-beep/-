"""Standard-library source integrity, local links and SEO checks. Run from any cwd."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, re, hashlib
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self,s):
  super().__init__(convert_charrefs=True);self.hidden=0;self.text=[];self.tags=[];self.feed(s)
 def handle_starttag(self,t,a):
  self.tags.append((t,dict(a)))
  if t in ('style','script'):self.hidden+=1
 def handle_endtag(self,t):
  if t in ('style','script'):self.hidden-=1
 def handle_data(self,d):
  if not self.hidden and d.strip():self.text.append(d.strip())
def compact(s):return re.sub(r'\s+','',s).lstrip('\ufeff')
training='服務期間兼任新進人員帶訓工作，負責規劃新進同仁實務帶訓指引與步驟化操作考核。'
def normalized(text):
 return compact(''.join(text).replace('跳至主要內容',''))
def expected_text(rel,text):
 s=''.join(text)
 s=re.sub(r'桃園市大園區(?:（機動巡店）)?','桃園市大園區（機動巡店）',s) if '/' not in rel else s
 additions={
  'index.html':'服務期間兼任新進人員帶訓，指導櫃台預約登記流程、收費規範與常見應變作業。',
  'contact.html':'動物醫院任職4年，期間兼任新人帶訓工作，具備耐心溝通與流程傳承經驗。',
  'mobile-contact.html':'具同理心與耐性，協助新進人員熟悉櫃台作業指引與流程。'
 }
 if rel in additions:s=s.replace(additions[rel],additions[rel]+training)
 return compact(s)
base=json.loads((ROOT/'_audit/baseline-text.json').read_text())
errors=[];links=0;results=[]
for rel,old in base.items():
 f=ROOT/rel;p=Page(f.read_text());ids=[a['id'] for t,a in p.tags if 'id' in a]
 if len(ids)!=len(set(ids)):errors.append(rel+': duplicate id')
 same=expected_text(rel,old)==normalized(p.text)
 results.append({'page':rel,'text_matches_except_confirmed_additions':same})
 if not same:errors.append(rel+': unexpected content difference')
 for t,a in p.tags:
  for attr in (['href'] if t=='a' else ['src'] if t in ('img','script') else ['srcset'] if t=='source' else ['href'] if t=='link' and a.get('rel')=='stylesheet' else []):
   value=a.get(attr,'');u=urlsplit(value)
   if u.scheme or u.netloc:continue
   target=(f.parent/unquote(u.path)).resolve() if u.path else f
   if target.is_dir():target=target/'index.html'
   links+=1
   if not target.is_file():errors.append(rel+': missing '+value);continue
   if u.fragment and target.suffix=='.html':
    targetids=[a.get('id') for t,a in Page(target.read_text()).tags]
    if unquote(u.fragment) not in targetids:errors.append(rel+': missing fragment '+value)
  if t=='a' and a.get('target')=='_blank' and 'noopener' not in a.get('rel',''):errors.append(rel+': unsafe new tab')
  if t=='img' and any(k not in a for k in ['alt','width','height']):errors.append(rel+': image metadata missing')
 if '/' not in rel:
  canonical=[a.get('href') for t,a in p.tags if t=='link' and a.get('rel')=='canonical']
  if len(canonical)!=1 or not canonical[0].startswith('https://mystiqueduncan-beep.github.io/-/'):errors.append(rel+': canonical')
  if sum(t=='h1' for t,a in p.tags)!=1:errors.append(rel+': h1 count')
  for name in ['description']:
   if not any(t=='meta' and a.get('name')==name and a.get('content') for t,a in p.tags):errors.append(rel+': '+name)
  if 'mobile' in rel and not any(a.get('name')=='robots' and a.get('content')=='noindex,follow' for t,a in p.tags):errors.append(rel+': mobile indexing')
  for literal in ['萬能科技大學','企業管理系','2026.10','2030.06']:
   if literal not in compact(''.join(p.text)):errors.append(rel+': education '+literal)
manifest=json.loads((ROOT/'_audit/original-manifest.json').read_text())
for name,item in manifest.items():
 if name.endswith('.jpg') and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=item['sha256']:errors.append(name+': original image changed')
report={'pages':results,'local_links_and_resources_checked':links,'errors':errors}
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
