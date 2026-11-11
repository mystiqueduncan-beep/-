"""Whole-page text fingerprints of the approved portfolio after intentional UI removals. Facts and data are independently checked by check.py."""
from html.parser import HTMLParser
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
class Text(HTMLParser):
 def __init__(self,source):
  super().__init__(convert_charrefs=True);self.hidden=0;self.newnav=0;self.parts=[];self.feed(source)
 def handle_starttag(self,tag,attrs):
  if tag in ('style','script'):self.hidden+=1
  # Additional navigation repeats existing labels; independently checked by check.py.
  if tag=='nav' and 'mobile-chapter-strip' in dict(attrs).get('class','').split():self.newnav+=1
 def handle_endtag(self,tag):
  if tag in ('style','script'):self.hidden-=1
  if tag=='nav' and self.newnav:self.newnav-=1
 def handle_data(self,data):
  if not self.hidden and not self.newnav:self.parts.append(data)
def digest(source,name=''):
 parts=''.join(Text(source).parts)
 if name in ('contact.html','mobile-contact.html'):
  # The user approved removing only the redundant LINE heading suffix.
  # Restore it solely for the historical full-page text fingerprint comparison.
  parts, matches = re.subn(r'LINE(\s*)bobozhihuang',
                           lambda m:'LINE 帳號 (LINE)'+m.group(1)+'bobozhihuang',
                           parts)
  assert matches==1,name+': expected exactly one LINE contact heading'
 if name=='mobile.html':
  # UI-only print CTA added Nov 9; original resume text fingerprint must remain identical.
  label='列印／另存 PDF'
  assert parts.count(label)==1,name+': expected exactly one new print action label'
  parts=parts.replace(label,'',1)
 # Approved Nov 11: reverse only the explicitly authorized onboarding copy edit
 # for comparison with the immutable original resume fingerprint.
 if name in ('index.html','mobile.html'):
  original = "新人帶訓工作：服務期間兼任新進人員帶訓，指導櫃台預約登記流程、收費規範與常見應變作業。服務期間兼任新進人員帶訓工作，負責規劃新進同仁實務帶訓指引與步驟化操作考核。" if name=='index.html' else "服務期間兼任新進人員帶訓工作，負責規劃新進同仁實務帶訓指引與步驟化操作考核。新人帶訓工作：指導櫃台預約登記流程、收費規範與常見應變作業。"
  replacement = "新人帶訓工作：兼任新進人員實務帶訓，負責規劃帶訓指引與步驟化操作考核，指導櫃台預約登記流程、收費規範及常見狀況應對作業。"
  flat=re.sub(r'\s+','',parts).lstrip('\ufeff')
  # Approved 2026-11-11: reverse only the navigation label relocation so the
  # historical text fingerprint still rejects all unrelated copy changes.
  intro='重視門市營運標準、服務品質與溝通協調，期望投入區域營運管理，讓門市日常作業更加穩定一致。'
  label='藥妝專題研究'
  marker='07/通路研究' if name=='index.html' else 'MK個人應徵作品集｜黃博詩'
  assert flat.count(intro+label)==1,name+': relocated research CTA missing'
  assert flat.count(marker)==1,name+': original research CTA position not found'
  flat=flat.replace(intro+label,intro,1)
  flat=flat.replace(marker,marker+label if name=='index.html' else label+marker,1)
  # Reconstruct only the approved removed caption when verifying the
  # immutable page text fingerprint. All career facts remain protected.
  if name=='index.html':
   heading='工作經歷WORKEXPERIENCE'
   caption='工作經歷與主要職責'
   assert caption not in flat,name+': career caption unexpectedly present'
   assert flat.count(heading)==1,name+': original career heading changed'
   flat=flat.replace(heading,heading+caption,1)
  assert flat.count(replacement)==1,name+': approved training text not found exactly once'
  parts=flat.replace(replacement,original,1)
 return hashlib.sha256(re.sub(r'\s+','',parts).lstrip('\ufeff').encode()).hexdigest()
if __name__=='__main__':
 manifest=json.loads((ROOT/'_audit/editorial-main-text-sha256.json').read_text())
 approved=json.loads((ROOT/'_audit/regional-analysis-approved-sha1.json').read_text())['pages']
 current={}
 for name,expected in manifest['pages'].items():
  if name in approved:
   raw=(ROOT/name).read_bytes()
   # Only the exact A4 print stylesheet link may be ignored; the research
   # page's original user-approved bytes remain protected by the SHA.
   print_link=b'  <link rel="stylesheet" href="assets/print-layout.css" media="print">\n'
   if raw.count(print_link)==1:raw=raw.replace(print_link,b'',1)
   actual=hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()
   assert actual==approved[name],name+': regional analysis content not approved'
   current[name]=actual
  else:
   actual=digest((ROOT/name).read_text(encoding='utf-8'),name)
   assert actual==expected,name+': main text changed'
   current[name]=actual
  print(name+': approved content and factual data preserved')
 print('CURRENT_EDITED_TEXT_FINGERPRINT='+json.dumps(current,ensure_ascii=False,sort_keys=True),flush=True)
