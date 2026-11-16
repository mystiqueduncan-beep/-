"""Standard-library source integrity, local links and SEO checks. Run from any cwd."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, re, hashlib
from japanese_titles import strip_approved_japanese_ui
from contact_link_labels import restore_historical_contact_link_labels
from roadmap_approval import restore_approved_roadmap
from footer_badge_labels import restore_historical_footer_badge
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
  # User-approved removal of the redundant research-footer hint only.
  research_hint='原分頁開啟 ✦ 包含 4 大優勢、4 大挑戰、案例分析與完整資料來源列表'
  if s.count(research_hint)!=1:raise ValueError('unexpected research hint baseline')
  s=s.replace(research_hint,'',1)
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
  # Approved LINE actions, and user's requested icon-only / LINE-only heading on both contact pages.
  needle='複製 Email'
  if s.count(needle)!=1:raise ValueError('unexpected contact baseline')
  s=s.replace(needle,needle+'LINEbobozhihuang開啟 LINE複製 LINE ID',1)
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
 # Both research views now share the homepage-style bilingual sticky
 # marquee; original section IDs and research text are immutable.
 nav=re.search(r'<nav aria-label="專題導覽" class="trend-subnav-strip trend-bilingual-nav">.*?</nav>',html,re.S)
 if not nav or html.count('data-keycap-marquee')!=1:
  errors.append(rel+': bilingual research chapter marquee missing or duplicated')
 else:
  links=re.findall(r'<a href="#([^"]+)" class="nav-btn-mk"><span class="bilingual-nav-cn">([^<]+)</span><span class="bilingual-nav-jp" lang="ja">([^<]+)</span></a>',nav.group(0))
  expected=[('market','市場判讀','市場動向を運営判断につなげる'),
            ('experience','經驗連結','現場経験を複数店舗の管理へ'),
            ('strategy','改善方針','六つの改善方針と担当体制'),
            ('roadmap','90天計畫','90日間のエリア運営推進計画'),
            ('metrics','成效追蹤','売上だけでなく改善コストも評価'),
            ('sources','研究來源','情報源と提案の適用範囲')]
  if links!=expected or 'bilingual-current' in nav.group(0):
   errors.append(rel+': research bilingual marquee chapter labels or anchors changed')
 if rel=='mobile-trend.html' and 'class="mobile-bottom-bar"' not in html:
  errors.append(rel+': mobile research footer navigation missing')
 
# Preserve the earlier original contact portrait as a provenance backup.
# The newly selected photo (IMG_3264) is resized for the unchanged circular contact frame, without facial retouching.
portrait_path=ROOT/'contact-portrait-20261109.jpg'
portrait_sha256='07b12e127431934991eb06749525344e02389b28919bd0465879848897f0ffef'
if not portrait_path.is_file() or hashlib.sha256(portrait_path.read_bytes()).hexdigest()!=portrait_sha256:
 errors.append('contact portrait: prior original photograph differs from approved source')
avatar_path=ROOT/'assets/portrait-img3264.webp'
if not avatar_path.is_file():
 errors.append('new circular profile image asset missing')
else:
 avatar_data=avatar_path.read_bytes()
 if (not avatar_data.startswith(b'RIFF') or b'WEBP' not in avatar_data[:16]
     or hashlib.sha256(avatar_data).hexdigest()!='c5af73491750af2a29b19a223f316ef4ca41546ba4d018da487744d56f44bb29'):
  errors.append('new profile photo: WebP does not match the approved IMG_3264 conversion')
for rel in ('contact.html','mobile-contact.html'):
 html=(ROOT/rel).read_text(encoding='utf-8')
 if len(re.findall(r'<img\b',html))!=1:
  errors.append(rel+': expected exactly one personal portrait image')
 if len(re.findall(r'<img\b[^>]*src="assets/portrait-img3264.webp"',html))!=1:
  errors.append(rel+': new circular portrait missing')
 if 'contact-portrait-fade.css' not in html:
  errors.append(rel+': portrait fade style missing')
for rel in ('index.html','mobile.html','trend.html','mobile-trend.html'):
 if 'assets/portrait-img3264.webp' in (ROOT/rel).read_text(encoding='utf-8'):
  errors.append(rel+': new portrait must stay contact-only')
# Shared top-positioned version switch and contact-only photo reveal.
for rel in ('index.html','mobile.html','trend.html','mobile-trend.html','contact.html','mobile-contact.html'):
 html=(ROOT/rel).read_text(encoding='utf-8')
 for resource in ('assets/view-mode-switch.css','assets/view-mode-switch.js'):
  if html.count(resource)!=1:errors.append(rel+': missing unique top version selector '+resource)
 if rel in ('contact.html','mobile-contact.html'):
  if 'portrait-reveal-js' not in html or html.count('assets/contact-portrait-reveal.js')!=1:
   errors.append(rel+': visible-entry photo fade initialization missing')
 else:
  if 'assets/contact-portrait-reveal.js' in html:errors.append(rel+': photo fade must stay contact-only')
manifest=json.loads((ROOT/'_audit/original-manifest.json').read_text(encoding='utf-8'))
for name,item in manifest.items():
 if name.endswith('.jpg') and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=item['sha256']:errors.append(name+': original image changed')
report={'pages':results,'local_links_and_resources_checked':links,'errors':errors}
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(bool(errors))
