"""Smoke-test printed A4 pagination without changing portfolio facts."""
from pathlib import Path
from functools import partial
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from tempfile import TemporaryDirectory
from threading import Thread
from pypdf import PdfReader
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "index.html", "mobile.html", "contact.html", "mobile-contact.html",
    "trend.html", "mobile-trend.html",
)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def validate_pdf(pdf_path, label):
    reader = PdfReader(str(pdf_path))
    if not (1 <= len(reader.pages) <= 45):
        raise AssertionError(f"{label}: unexpected page count: {len(reader.pages)}")
    for number, sheet in enumerate(reader.pages, start=1):
        size = (float(sheet.mediabox.width), float(sheet.mediabox.height))
        if abs(size[0] - 595.28) > 1 or abs(size[1] - 841.89) > 1:
            raise AssertionError(f"{label} page {number}: not A4: {size}")
        stream = sheet.get_contents()
        if stream is None or len(stream.get_data()) < 60:
            raise AssertionError(f"{label} page {number}: blank or missing content")
    print(f"{label}: {len(reader.pages)} A4 pages, no empty content streams")


def verify_first_page_contacts():
    """Ensure that the download contains the site-approved contacts on page one."""
    contact_html = (ROOT / "contact.html").read_text(encoding="utf-8")
    expected = []
    for element_id in ("phoneText", "emailText", "lineIdText"):
        match = re.search(r'id="' + element_id + r'"[^>]*>([^<]+)<', contact_html)
        if not match:
            raise AssertionError(f"contact.html: missing {element_id}")
        expected.append(match.group(1).strip())
    reader = PdfReader(str(ROOT / "resume.pdf"))
    if len(reader.pages) > 11:
        raise AssertionError(f"resume.pdf: unexpectedly expanded to {len(reader.pages)} pages")
    page_one = re.sub(r"\\s+", "", reader.pages[0].extract_text() or "")
    for item in expected:
        if re.sub(r"\\s+", "", item) not in page_one:
            raise AssertionError(f"resume.pdf page 1: missing contact from contact.html: {item}")
    print("resume.pdf: all three verified contacts are present on A4 page 1")


def main():
    validate_pdf(ROOT / "resume.pdf", "downloadable resume.pdf")
    verify_first_page_contacts()

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(Quiet, directory=str(ROOT))
    )
    Thread(target=server.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as playwright, TemporaryDirectory() as temp:
            browser = playwright.chromium.launch(args=["--no-sandbox"])
            try:
                for name in PAGES:
                    page = browser.new_page(
                        viewport={"width": 1280, "height": 900},
                        reduced_motion="reduce",
                    )
                    # Deterministic layout audit; the actual PDF generator
                    # independently attempts to include credited web photos.
                    page.route("https://**/*", lambda route: route.abort())
                    page.goto(
                        f"http://127.0.0.1:{server.server_port}/{name}?view="
                        f"{'mobile' if name.startswith('mobile') else 'desktop'}",
                        wait_until="domcontentloaded",
                    )
                    page.emulate_media(media="print")
                    result = page.evaluate(
                        """() => ({
                            printLink: [...document.querySelectorAll('link[rel=stylesheet]')]
                              .filter(link => link.getAttribute('href') === 'assets/print-layout.css').length,
                            font: getComputedStyle(document.body).fontFamily,
                            main: !!document.querySelector('main'),
                            width: getComputedStyle(document.querySelector('main')).width
                        })"""
                    )
                    if result["printLink"] != 1 or not result["main"]:
                        raise AssertionError(f"{name}: missing shared print layout or main")
                    if "Noto Sans CJK TC" not in result["font"]:
                        raise AssertionError(f"{name}: missing print font; {result}")
                    output = Path(temp) / (name + ".pdf")
                    page.pdf(path=str(output), print_background=True, prefer_css_page_size=True)
                    validate_pdf(output, name)
                    page.close()
            finally:
                browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
