"""Render the download and optional six-page-family print review from shared CSS."""
from pathlib import Path
import argparse, functools, http.server, threading, shutil
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--review', action='store_true')
args = parser.parse_args()

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(args=['--no-sandbox'])
        names = ['index']
        if args.review:
            names += ['mobile', 'contact', 'mobile-contact', 'trend', 'mobile-trend']
        out = root / 'print-review'
        if args.review:
            out.mkdir(exist_ok=True)
        for name in names:
            page = browser.new_page(viewport={'width': 1280, 'height': 900}, reduced_motion='reduce')
            page.route('https://fonts.googleapis.com/**', lambda r: r.abort())
            page.goto(f'http://127.0.0.1:{server.server_port}/{name}.html?view={"mobile" if name.startswith("mobile") else "desktop"}', wait_until='domcontentloaded')
            page.emulate_media(media='print')
            page.evaluate("document.querySelectorAll('img').forEach(i => i.loading = 'eager')")
            page.evaluate('document.fonts.ready')
            page.evaluate("Promise.race([Promise.all(Array.from(document.images, i => i.decode().catch(() => {}))), new Promise(r => setTimeout(r, 20000))])")
            path = root / 'resume.pdf' if name == 'index' else out / f'{name}.pdf'
            state = page.evaluate("Array.from(document.querySelectorAll('details'), el => el.open)")
            page.pdf(path=str(path), print_background=True, prefer_css_page_size=True, tagged=True, outline=True)
            if args.review:
                if name == 'index':
                    shutil.copyfile(path, out / 'resume.pdf')
                # Regression: filtered cards and collapsed details must be restored.
                assert state == page.evaluate("Array.from(document.querySelectorAll('details'), el => el.open)")
            page.close()
        browser.close()
finally:
    server.shutdown()
