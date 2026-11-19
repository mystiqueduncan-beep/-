"""Check external resource/link policy for the six main pages and printable resume."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
PAGES=('index.html','mobile.html','trend.html','mobile-trend.html','contact.html','mobile-contact.html','resume.html')

class Audit(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.page=page
        self.errors=[]
        self.new_tabs=0
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        for key in ('src','href','action','formaction'):
            raw=(a.get(key) or '').strip()
            if not raw: continue
            url=urlsplit(raw)
            if url.scheme.lower() in ('http','javascript','vbscript'):
                self.errors.append((tag,key,url.scheme))
            if tag=='script' and key=='src' and (url.scheme or url.netloc):
                self.errors.append(('external-script',url.netloc))
        if tag=='a' and (a.get('target') or '').lower()=='_blank':
            self.new_tabs+=1
            if 'noopener' not in (a.get('rel') or '').lower().split():
                self.errors.append(('new-tab-without-noopener',))
        if tag in ('object','embed','iframe'):
            self.errors.append(('unexpected-embedded-content',tag))
    handle_startendtag=handle_starttag

errors=[]
for page in PAGES:
    audit=Audit(page)
    audit.feed((ROOT/page).read_text(encoding='utf-8'))
    errors.extend((page,entry) for entry in audit.errors)
    print(f'{page}: checked external resources and {audit.new_tabs} new-tab links')
assert not errors, errors
