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
  elif ('audited-visual' in classes or 'audited-source-note' in classes or (t=='figure' and 'career-photo' in classes)) and t not in voids:
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
 return compact(''.join(text).replace('跳至主要內容','')).replace('2024年藥粧零售業銷售商品結構個人清潔化粧保養47.7%、藥品及醫療用品21.4%、食品13.7%、家庭器具及用品7.3%、衣著鞋襪配件及個人用品7.0%、其他2.9%。','')
def expected_text(rel,text):
 # User-approved removal: homepage contact blocks now live only on full contact pages.
 if rel=='index.html':
  start=text.index('CONTACT & RESUME DOWNLOAD')-2
  if text[start:start+3]!=['08','聯絡資訊與履歷下載','CONTACT & RESUME DOWNLOAD']:raise ValueError('unexpected desktop contact baseline')
  end=text.index('MK',start)
  s=''.join(text[:start]+text[end:])
 elif rel=='mobile.html':
  start=text.index('09/ 聯絡資訊與履歷下載')
  end=text.index('MK',start)
  s=''.join(text[:start]+text[end:])
 else:
  s=''.join(text)
 if rel=='index.html':
  s=s.replace('新分頁開啟 ✦', '原分頁開啟 ✦', 1)
 # User-approved contact navigation labels; retain icons and version switches.
 contact_labels={
  'index.html': [('聯絡我 (電話 / 信箱)', '聯絡資訊')],
  'mobile.html': [('聯絡資訊與履歷下載', '聯絡資訊'), ('聯絡我', '聯絡資訊')],
  'trend.html': [('查看聯絡資訊', '聯絡資訊')],
  'mobile/contact.html': [('如未自動轉跳請點此', '聯絡資訊')]
 }
 for old_label,new_label in contact_labels.get(rel,[]):
  if s.count(old_label)!=1:raise ValueError('unexpected contact navigation baseline: '+rel)
  s=s.replace(old_label,new_label,1)
 if rel in ('contact.html','mobile-contact.html'):
  # User-approved LINE actions; the older baseline stays unchanged.
  needle='複製 Email'
  if s.count(needle)!=1:raise ValueError('unexpected contact baseline')
  s=s.replace(needle,needle+'LINE 帳號 (LINE)bobozhihuang開啟 LINE複製 LINE ID',1)
 if rel in ('index.html','mobile.html'):
  for credit in ("出處：TOMOD'S 官方商標",'出處：築心動物醫院',"出處：LEVI'S 官方素材"):
   if s.count(credit)!=1:raise ValueError('unexpected original logo credit: '+rel)
   s=s.replace(credit,'',1)
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
 # All mobile chapter marquees were removed by explicit request.
 # The legacy chart labels moved inside audited-visual in PR #26. Validate
 # that independent chart below rather than silently dropping its data contract.
 if rel in ('trend.html','mobile-trend.html'):
  legacy = ('藥妝店（松本清、屈臣氏、康是美等）45.2%網路（電商平台、品牌官方旗艦店）42.5%生活百貨（寶雅、唐吉訶德等）28.7%百貨專櫃24.4%' if rel=='trend.html' else '藥妝店（松本清、屈臣氏等）45.2%網路（電商平台、官方旗艦店）42.5%生活百貨（寶雅、唐吉訶德等）28.7%百貨專櫃24.4%')
  s=compact(s).replace(legacy,'',1)
 s=compact(s)
 if rel=='contact.html':
  start=s.index('01/首頁↗')
  end=s.index('PORTFOLIO✦個人應徵作品集',start)
  s=s[:start]+s[end:]
 if rel in ('contact.html','mobile-contact.html'):
  s=s.replace('出勤安排到職時間、排班與巡店安排，可於面談時進一步確認。','',1)
  a='✦區域營運經理3大核心戰力優勢速覽' if rel=='contact.html' else '✦區域營運經理3大核心戰力速覽'
  b='返回履歷專刊首頁↗' if rel=='contact.html' else '←返回手機履歷專刊首頁'
  s=s[:s.index(a)]+s[s.index(b,s.index(a)):]
 if rel=='index.html':
  s=s.replace('專題/完整趨勢研究↗','藥妝專題研究')
  s=s.replace('閱讀完整實體通路趨勢研究報告↗','藥妝專題研究')
  # User requested removing only the desktop homepage marquee contact shortcut.
  s=s.replace('08/聯絡資訊','',1)
 if rel=='mobile.html':
  s=s.replace('專題閱讀完整通路趨勢專題↗','藥妝專題研究')
  s=s.replace('工作經歷趨勢研究聯絡資訊','工作經歷藥妝專題研究聯絡資訊')
 if rel=='contact.html':s=s.replace('07/實體通路趨勢研究↗','藥妝專題研究')
 if rel=='mobile-contact.html':
  s=s.replace('實體通路趨勢研究專題↗','藥妝專題研究')
  s=s.replace('職涯歷程趨勢研究聯絡資訊','職涯歷程藥妝專題研究聯絡資訊')
 return compact(s)
base=json.loads((ROOT/'_audit/baseline-text.json').read_text(encoding='utf-8'))
errors=[];links=0;results=[]
for rel,old in base.items():
 f=ROOT/rel;p=Page(f.read_text(encoding='utf-8'));ids=[a['id'] for t,a in p.tags if 'id' in a]
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
    targetids=[a.get('id') for t,a in Page(target.read_text(encoding='utf-8')).tags]
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
# The contact button must be absent from the homepage marquee only.
home=(ROOT/'index.html').read_text(encoding='utf-8')
if 'class="keycap-marquee"' not in home:errors.append('index.html: missing homepage marquee')
else:
 marquee=home.split('class="keycap-marquee"',1)[1].split('</nav>',1)[0]
 if 'href="contact.html"' in marquee:
  errors.append('index.html: contact shortcut still in marquee')
if 'href="contact.html"' not in home:
 errors.append('index.html: missing separate contact link')
# Independently validate metadata that is excluded from original-resume text parity.
for rel in ('index.html','mobile.html'):
 html=(ROOT/rel).read_text(encoding='utf-8')
 figures=re.findall(r'<figure class="career-photo"[^>]*>(.*?)</figure>',html,re.S)
 career=html.split('id="career"',1)[1].split('</section>',1)[0]
 if len(figures)!=3 or len(re.findall(r'<img\b',career))!=3 or len(re.findall(r'<img\b',html))!=3:
  errors.append(rel+': exactly three career images, no hero photo')
 for origin in ('3.bp.blogspot.com','www.zhuxin.com.tw','i.mdel.net'):
  if origin not in career:errors.append(rel+': missing career photo '+origin)

for rel in ('contact.html','mobile-contact.html'):
 html=(ROOT/rel).read_text(encoding='utf-8')
 if len(re.findall(r'<img\b',html))!=1 or 'src="contact-portrait.webp"' not in html:
  errors.append(rel+': contact photo mismatch')
for rel in ('index.html','mobile.html','trend.html','mobile-trend.html'):
 html=(ROOT/rel).read_text(encoding='utf-8')
 for origin in ('moea.gov.tw','ixresearch.com'):
  if origin not in html:errors.append(rel+': research source hyperlink missing '+origin)
for rel in ('trend.html','mobile-trend.html'):
 html=(ROOT/rel).read_text(encoding='utf-8')
 for origin in ('91app.com','kantarworldpanel.com'):
  if origin not in html:errors.append(rel+': research source hyperlink missing '+origin)
for rel in ('trend.html','mobile-trend.html'):
 html=(ROOT/rel).read_text(encoding='utf-8')
 chart=html.split('aria-label="購買管道調查圖表"',1)[1].split('class="channel-summary"',1)[0]
 for label,number in [('藥妝店','45.2'),('網路','42.5'),('生活百貨','28.7'),('百貨專櫃','24.4')]:
  if not re.search(r'aria-label="'+label+r'[^"共]*'+number+r'%"',chart):errors.append(rel+': chart label/value '+label)
  if 'width: '+number+'%' not in chart:errors.append(rel+': chart absolute scale '+number)
 if '複選題' not in chart or '非市場占有率' not in chart:errors.append(rel+': chart multiple-response meaning')
manifest=json.loads((ROOT/'_audit/original-manifest.json').read_text(encoding='utf-8'))
for name,item in manifest.items():
 if name.endswith('.jpg') and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=item['sha256']:errors.append(name+': original image changed')
report={'pages':results,'local_links_and_resources_checked':links,'errors':errors}
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
