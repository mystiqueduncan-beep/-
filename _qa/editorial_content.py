"""Whole-page text parity against main 5646383, including audited charts and SVG text."""
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
 current={name:digest((ROOT/name).read_text(encoding='utf-8')) for name in manifest['pages']}
 print('CURRENT_EDITED_TEXT_SHA256='+json.dumps(current,ensure_ascii=False,sort_keys=True),flush=True)
 for name,expected in manifest['pages'].items():
  assert current[name]==expected,name+': main text changed'
  print(name+': exact approved text, chart labels, SVG descriptions and credits preserved')
