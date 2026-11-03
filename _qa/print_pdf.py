"""Generate the reviewed A4 PDF with local CJK fonts and no remote font dependency."""
from pathlib import Path
import functools,http.server,threading,shutil
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium') or None,args=['--no-sandbox'])
 page=b.new_page();page.route('https://**/*',lambda r:r.abort())
 page.goto(f'http://127.0.0.1:{server.server_port}/index.html');page.emulate_media(media='print')
 page.evaluate("document.querySelectorAll('img').forEach(i=>i.loading='eager')")
 page.evaluate('document.fonts.ready');page.wait_for_timeout(500)
 page.pdf(path=str(root/'resume.pdf'),print_background=True,prefer_css_page_size=True,tagged=True,outline=True)
 b.close()
server.shutdown()
