"""Verify that GitHub Pages serves the resume and the exact checked-in site assets.

On pull requests compare to the current main (PR base), not the unpublished PR.
On pushes to main compare with the new commit, retrying during Pages deployment.
"""
import hashlib
import os
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, unquote
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://mystiqueduncan-beep.github.io/-/"
PAGES = (
    "index.html", "mobile.html", "contact.html",
    "mobile-contact.html", "trend.html", "mobile-trend.html",
    "resume.html", "mobile/index.html", "mobile/contact.html",
    "mobile/trend.html",
)
ASSETS = (
    "assets/site.css",
    "assets/mk-inspired.css",
    "assets/mk-inspired.js",
    "assets/research-cta.css",
    "assets/research-cta.js",
    "assets/pastel-details.css",
    "assets/page-transitions.js",
    "assets/career-images.css",
    "assets/contact-portrait-fade.css",
    "assets/trend-marquee.css",
)
BASE_SHA = os.environ.get("EXPECTED_BASE_SHA", "").strip()
REQUEST_ID = os.environ.get("GITHUB_RUN_ID", "check")

def expected_file(path):
    if BASE_SHA:
        return subprocess.check_output(["git", "show", f"{BASE_SHA}:{path}"], cwd=ROOT)
    return (ROOT / path).read_bytes()

def remote_file(path):
    # Unique query avoids confusing a cached old asset with a fresh deployment.
    url = SITE + path + "?verification=" + REQUEST_ID
    request = Request(url, headers={
        "User-Agent": "Resume-Pages-Deployment-Verification",
        "Cache-Control": "no-cache",
    })
    with urlopen(request, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(f"{path}: HTTP {response.status}")
        return response.read()

class LocalAssets(HTMLParser):
    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.page = page
        self.paths = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        raw = a.get('src') if tag == 'script' else a.get('href') if tag == 'link' else None
        if not raw:
            return
        url = urlsplit(urljoin(SITE + self.page, raw))
        root = urlsplit(SITE)
        if (url.scheme, url.netloc) != (root.scheme, root.netloc) or not url.path.startswith(root.path):
            return
        path = unquote(url.path[len(root.path):])
        if path.endswith(('.css', '.js')):
            self.paths.add(path)

    handle_startendtag = handle_starttag


def verify():
    assets = set(ASSETS)
    for page in PAGES:
        content = remote_file(page)
        if b"<html" not in content.lower() or b"</html>" not in content.lower():
            raise RuntimeError(f"{page}: invalid HTML response")
        expected = expected_file(page)
        if content != expected:
            raise RuntimeError(f'{page}: deployed HTML differs from ' + ('PR base' if BASE_SHA else 'checked commit'))
        parser = LocalAssets(page)
        parser.feed(expected.decode('utf-8-sig'))
        assets.update(parser.paths)
        # PR checks compare the already-published base; the new versioned icon
        # can only be required after main is merged and Pages deploys it.
        if not BASE_SHA:
            expected_icon = b'href="../favicon.ico"' if page.startswith("mobile/") else b'href="favicon.ico"'
            if expected_icon not in content:
                raise RuntimeError(f"{page}: does not declare the new 16/32 flower ICO")
            if b'favicon-floral-20261114.svg' in content:
                raise RuntimeError(f"{page}: still points at the older SVG icon URL")
        print(f"OK {page}: HTTP 200 and exact HTML bytes verified", flush=True)
    # Include every first-party stylesheet/script actually referenced by the
    # ten published HTML files, including versioned URLs and mobile bundles.
    for path in sorted(assets):
        actual = remote_file(path)
        expected = expected_file(path)
        if hashlib.sha256(actual).digest() != hashlib.sha256(expected).digest():
            raise RuntimeError(f"{path}: deployed file differs from "
                               + ("PR base" if BASE_SHA else "latest main"))
        print(f"OK {path}: published bytes match "
              + ("PR base" if BASE_SHA else "latest main"), flush=True)
    actual_pdf = remote_file('resume.pdf')
    if not actual_pdf.startswith(b'%PDF-') or actual_pdf != expected_file('resume.pdf'):
        raise RuntimeError('resume.pdf: invalid or out-of-sync published download')
    print('OK resume.pdf: exact downloadable PDF bytes verified', flush=True)
    if not BASE_SHA:
        # Compare the new ICO bytes as served by the public site, not merely
        # the repository file. All ten HTML pages must reference it.
        for path in ("favicon.ico", "assets/favicon-floral-20261114.svg"):
            actual = remote_file(path)
            if hashlib.sha256(actual).digest() != hashlib.sha256(expected_file(path)).digest():
                raise RuntimeError(path + ": published flower differs from latest main")
            print(f"OK {path}: deployed flower exactly matches main", flush=True)

if __name__ == "__main__":
    for attempt in range(1, 13):
        try:
            verify()
            print("PASS: GitHub Pages served all 10 exact pages, their local CSS/JS, the PDF download and required favicon assets.", flush=True)
            break
        except (HTTPError, URLError, RuntimeError, OSError, subprocess.CalledProcessError) as exc:
            print(f"Attempt {attempt}/12: {exc}", flush=True)
            if attempt == 12:
                raise SystemExit("FAIL: GitHub Pages publication is not verified")
            time.sleep(15)
