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
def digest(source):return hashlib.sha256(re.sub(r'\s+','',''.join(Text(source).parts)).lstrip('\ufeff').encode()).hexdigest()
if __name__=='__main__':
 manifest=json.loads((ROOT/'_audit/editorial-main-text-sha256.json').read_text())
 approved=json.loads((ROOT/'_audit/regional-analysis-approved-sha1.json').read_text())['pages']
 current={}
 for name,expected in manifest['pages'].items():
  if name in approved:
   raw=(ROOT/name).read_bytes()
   actual=hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\\0'+raw).hexdigest()
   assert actual==approved[name],name+': regional analysis content not approved'
   current[name]=actual
  else:
   actual=digest((ROOT/name).read_text(encoding='utf-8'))
   assert actual==expected,name+': main text changed'
   current[name]=actual
  print(name+': approved content and factual data preserved')
 print('CURRENT_EDITED_TEXT_FINGERPRINT='+json.dumps(current,ensure_ascii=False,sort_keys=True),flush=True)
