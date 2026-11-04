"""Standard-library source integrity, local links and SEO checks. Run from any cwd."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, re, hashlib
ROOT=Path(__file__).resolve().parents[1]
class Page(HTMLParser):
 def __init__(self,s):
  super().__init__(convert_charrefs=True);self.hidden=0;self.suppressed=0;self.text=[];self.tags=[];self.feed(s)
 def handle_starttag(self,t,a):
  self.tags.append((t,dict(a)))
  attrs=dict(a);classes=attrs.get('class','').split()
  voids=('img','source','br','hr','meta','link','input','area','wbr')
  if self.suppressed:
   if t not in voids:self.suppressed+=1
  elif ('audited-visual' in classes or 'audited-source-note' in classes or 'career-photo' in classes) and t not in voids:
   self.suppressed=1
  if t in ('style','script'):self.hidden+=1
 def handle_endtag(self,t):
  if t in ('style','script'):self.hidden-=1
  if self.suppressed:self.suppressed-=1
 def handle_data(self,d):
  if not self.hidden and not self.suppressed and d.strip():self.text.append(d.strip())
def compact(s):return re.sub(r'\s+','',s).lstrip('\ufeff')
training='服務期間兼任新進人員帶訓工作，負責規劃新進同仁實務帶訓指引與步驟化操作考核。'
def normalized(text):
 return compact(''.join(text).replace('跳至主要內容',''))
def expected_text(rel,text):
 s=''.join(text)
 if rel in ('index.html','mobile.html'):
  for note in ("出處：TOMOD'S 官方商標", '出處：築心動物醫院', "出處：LEVI'S 官方素材"):
   s=s.replace(note,'')
 s=re.sub(r'桃園市大園區(?:（機動巡店）)?','桃園市大園區（機動巡店）',s) if '/' not in rel else s
 additions={
  'index.html':'服務期間兼任新進人員帶訓，指導櫃台預約登記流程、收費規範與常見應變作業。',
  'contact.html':'動物醫院任職4年，期間兼任新人帶訓工作，具備耐心溝通與流程傳承經驗。',
  'mobile-contact.html':'具同理心與耐性，協助新進人員熟悉櫃台作業指引與流程。'
 }
 if rel in additions:s=s.replace(additions[rel],additions[rel]+training)
 # Whitelist verified corrections to the original source attributions only.
 s=s.replace('《批發、零售及餐飲業動態統計調查》','《114年批發、零售及餐飲業經營實況調查》')
 if rel in ('trend.html','mobile-trend.html'):
  s=s.replace('《2024 零售全通路 OMO 趨勢報告》','91APP 官方〈AI 驅動零售新體驗〉（2025/08/14）')
 if rel=='trend.html':
  # The summary content remains; only its redundant marquee shortcut was removed.
  s=s.replace('00/研究精要','',1)
  s=s.replace('台灣個人保養與美妝市場研究報告。探討底妝與香氛等品類在選購時對實體門市試用之質地確認需求。','Kantar 官方資料可支持美妝消費趨勢與實體專櫃服務體驗的相關討論；但特定「底妝與香氛試用需求」尚無可逐項核對的 Kantar 公開數據，故不歸因為已驗證的研究結論。')
 if rel=='mobile-trend.html':
  # Only the redundant navigation card is removed; research sections stay intact.
  removed_nav=('專題重點章節導覽NAV'
   '01/ 購買管道與結構'
   '02/ 4大核心優勢'
   '03/ 4大劣勢挑戰'
   '04/ 4大躍升策略'
   '05/ 劣勢改善對策'
   '06/ 標竿案例借鑑'
   '07/ 區域營運規劃'
   '08/ 權威資料來源')
  if s.count(removed_nav)!=1:raise ValueError('unexpected mobile trend navigation baseline')
  s=s.replace(removed_nav,'')
  s=s.replace('台灣個人保養與美妝市場研究報告。佐證底妝與香氛等品類在首次選購時高度依賴實體門市試用之行為洞察。','Kantar 公開資料可支持美妝市場與實體專櫃體驗的討論；但未找到可直接支持「底妝及香氛首次選購高度依賴實體試用」的 Kantar 原始數據，因此不將此歸因列為已證實結論。')
  s=s.replace('（2026/04/15 執行，藥妝店 45.2%','（2026/04/15 發布、2026/03/12–03/19 調查，藥妝店 45.2%')
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
# Independently validate metadata that is excluded from original-resume text parity.
for rel in ('index.html','mobile.html'):
 html=(ROOT/rel).read_text()
 photos=re.findall(r'<figure class="career-photo" data-career-reveal>(.*?)</figure>',html,re.S)
 if len(photos)!=3:errors.append(rel+': expected exactly three selected career photos')
 expected=[('3.bp.blogspot.com', 'wowonews.com/2019/01/tomods-.html', 'TOMOD’S'),('zhuxin.com.tw/proimage/images/1696680526.jpg','zhuxin.com.tw/about/inside-look','築心動物醫院'),('i.mdel.net/i/db/2026/3/2765277/2765277-800w.jpg','models.com/work/levis-levis-timeless-campaign-2026','Mark Mahaney')]
 for photo,(image,source,credit) in zip(photos,expected):
  parsed=Page(photo)
  imgs=[a for t,a in parsed.tags if t=='img']
  if len(imgs)!=1 or image not in imgs[0].get('src',''):errors.append(rel+': selected photo mismatch '+image)
  if not all(v in photo for v in (source,credit,'非本人工作照片')):errors.append(rel+': selected photo source missing '+source)
  if any(t in ('p','ul','li','h2','h3') for t,a in parsed.tags):errors.append(rel+': resume content inside photo metadata')
  if imgs and (imgs[0].get('loading')!='lazy' or imgs[0].get('decoding')!='async'):errors.append(rel+': photo loading metadata')
for rel in ('index.html','mobile.html','trend.html','mobile-trend.html'):
 html=(ROOT/rel).read_text()
 for origin in ('moea.gov.tw','ixresearch.com'):
  if origin not in html:errors.append(rel+': research source hyperlink missing '+origin)
for rel in ('trend.html','mobile-trend.html'):
 html=(ROOT/rel).read_text()
 for origin in ('91app.com','kantarworldpanel.com'):
  if origin not in html:errors.append(rel+': research source hyperlink missing '+origin)
manifest=json.loads((ROOT/'_audit/original-manifest.json').read_text())
for name,item in manifest.items():
 if name.endswith('.jpg') and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=item['sha256']:errors.append(name+': original image changed')
report={'pages':results,'local_links_and_resources_checked':links,'errors':errors}
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))

