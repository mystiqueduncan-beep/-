"""Create a real downloadable A4 PDF from the approved two-page resume.html.

This exporter never edits resume facts or substitutes a new PDF template.
The PDF and the printed webpage share exactly the same HTML/CSS.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "resume.pdf"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT)))
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(args=["--no-sandbox"])
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
                page.goto(f"http://127.0.0.1:{server.server_port}/resume.html", wait_until="networkidle")
                assert page.locator(".paper").count() == 2, "The approved resume is exactly two sheets"
                headings = page.locator(".dossier-header .left").all_inner_texts()
                assert headings == ["PERSONAL RÉSUMÉ ✦ 個人簡歷"] * 2, headings
                assert page.locator(".summary-note").count() == 0, "Removed editorial note returned"
                page.emulate_media(media="print")
                page.evaluate("() => document.fonts.ready")
                assert page.locator(".screen-control").evaluate(
                    "(el) => getComputedStyle(el).display"
                ) == "none", "Web buttons leaked into PDF"
                page.pdf(
                    path=str(OUTPUT),
                    print_background=True,
                    prefer_css_page_size=True,
                    tagged=True,
                    outline=True,
                )
            finally:
                browser.close()
        pdf = PdfReader(str(OUTPUT))
        assert len(pdf.pages) == 2, f"Expected two A4 pages, got {len(pdf.pages)}"
        for number, p in enumerate(pdf.pages, start=1):
            w, h = float(p.mediabox.width), float(p.mediabox.height)
            assert abs(w - 595.28) < 1 and abs(h - 841.89) < 1, (number, w, h)
            data = p.get_contents()
            assert data and len(data.get_data()) > 150, f"Empty page {number}"
        assert OUTPUT.stat().st_size > 20_000, "Unexpectedly small PDF"
        print(f"Created approved two-page A4 download: {OUTPUT.stat().st_size} bytes")
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
