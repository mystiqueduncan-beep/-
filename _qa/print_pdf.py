"""Regenerate the downloadable A4 resume from the same HTML/CSS as print preview.

Run from any working directory. Requires Playwright Chromium and system CJK fonts.
Do not modify resume facts or create a separate PDF-only content template.
"""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import shutil
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietServer(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(QuietServer, directory=str(ROOT))
    )
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=shutil.which("chromium") or None,
                args=["--no-sandbox"],
            )
            try:
                page = browser.new_page(
                    viewport={"width": 1280, "height": 900},
                    device_scale_factor=1,
                    reduced_motion="reduce",
                )
                # Local CJK faces make the PDF reproducible. Photographs stay
                # eligible to load; blocking every HTTPS request used to erase them.
                page.route(
                    "https://fonts.googleapis.com/**",
                    lambda route: route.abort(),
                )
                page.route(
                    "https://fonts.gstatic.com/**",
                    lambda route: route.abort(),
                )
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/index.html?view=desktop",
                    wait_until="domcontentloaded",
                )
                page.emulate_media(media="print")
                page.evaluate(
                    "() => { document.querySelectorAll('img').forEach(img => img.loading = 'eager'); }"
                )
                page.evaluate("() => document.fonts.ready")
                # Allow the printed local assets and any reachable credited
                # photographs to finish, but never block PDF export indefinitely.
                page.evaluate(
                    """async () => {
                      const images = [...document.images];
                      await Promise.race([
                        Promise.all(images.map(img => img.decode().catch(() => undefined))),
                        new Promise(resolve => setTimeout(resolve, 10000))
                      ]);
                    }"""
                )
                assert page.locator('link[href="assets/print-layout.css"]').count() == 1
                assert page.locator("main").count() >= 1
                page.pdf(
                    path=str(ROOT / "resume.pdf"),
                    print_background=True,
                    prefer_css_page_size=True,
                    tagged=True,
                    outline=True,
                )
                print("Regenerated resume.pdf from index.html with shared A4 print rules")
            finally:
                browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
