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
                # Read contact details from the already approved contact page,
                # instead of keeping a second, potentially stale PDF-only copy.
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/contact.html?view=desktop",
                    wait_until="domcontentloaded",
                )
                contact = page.evaluate(
                    """() => {
                      const get = id => document.getElementById(id)?.textContent?.trim();
                      const phone = get('phoneText');
                      const email = get('emailText');
                      const line = get('lineIdText');
                      const phoneLink = document.querySelector('a[href^="tel:"]');
                      const emailLink = document.querySelector('a[href^="mailto:"]');
                      if (!phone || !email || !line ||
                          !phoneLink || !emailLink ||
                          phone.replace(/\\D/g,'') !== phoneLink.getAttribute('href').slice(4).replace(/\\D/g,'') ||
                          email !== emailLink.getAttribute('href').slice(7)) {
                        throw new Error('Unverified or missing source contact details');
                      }
                      return { phone, email, line };
                    }"""
                )
                page.goto(
                    f"http://127.0.0.1:{server.server_port}/index.html?view=desktop",
                    wait_until="domcontentloaded",
                )
                # The approved homepage is byte-for-byte unchanged; this panel
                # exists only inside the generated PDF. It is deliberately
                # placed in the opening cover, not an appended contact page.
                page.evaluate(
                    """contact => {
                      const anchor = document.querySelector(
                        '.cover-heading .hero-position-highlight'
                      );
                      if (!anchor) throw new Error('Resume cover anchor not found');
                      const panel = document.createElement('section');
                      panel.className = 'print-contact-card';
                      panel.setAttribute('aria-label', '聯絡資訊');
                      const title = document.createElement('h2');
                      title.className = 'print-contact-card__title';
                      title.textContent = '聯絡資訊  /  CONTACT';
                      panel.appendChild(title);
                      const grid = document.createElement('div');
                      grid.className = 'print-contact-card__grid';
                      for (const [label, value] of [
                        ['電話', contact.phone],
                        ['電子郵件', contact.email],
                        ['LINE ID', contact.line]
                      ]) {
                        const cell = document.createElement('div');
                        cell.className = 'print-contact-card__item';
                        const caption = document.createElement('span');
                        caption.className = 'print-contact-card__label';
                        caption.textContent = label;
                        const detail = document.createElement('strong');
                        detail.className = 'print-contact-card__value';
                        detail.textContent = value;
                        cell.append(caption, detail);
                        grid.appendChild(cell);
                      }
                      panel.appendChild(grid);
                      anchor.insertAdjacentElement('afterend', panel);
                    }""",
                    contact,
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
                assert page.locator(".print-contact-card").count() == 1
                assert page.locator(".print-contact-card__item").count() == 3
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
