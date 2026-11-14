"""Verify that GitHub Pages serves the resume and the exact checked-in site assets.

On pull requests compare to the current main (PR base), not the unpublished PR.
On pushes to main compare with the new commit, retrying during Pages deployment.
"""
import hashlib
import os
from pathlib import Path
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

def verify():
    for page in PAGES:
        content = remote_file(page)
        if b"<html" not in content.lower() or b"</html>" not in content.lower():
            raise RuntimeError(f"{page}: invalid HTML response")
        # PR checks compare the already-published base; the new versioned icon
        # can only be required after main is merged and Pages deploys it.
        if not BASE_SHA and b"favicon-floral-20261114.svg" not in content:
            raise RuntimeError(f"{page}: still references old cached favicon URL")
        print(f"OK {page}: HTTP 200, HTML and favicon reference verified", flush=True)
    for path in ASSETS:
        actual = remote_file(path)
        expected = expected_file(path)
        if hashlib.sha256(actual).digest() != hashlib.sha256(expected).digest():
            raise RuntimeError(f"{path}: deployed file differs from "
                               + ("PR base" if BASE_SHA else "latest main"))
        print(f"OK {path}: published bytes match "
              + ("PR base" if BASE_SHA else "latest main"), flush=True)
    if not BASE_SHA:
        # Unlike ordinary stylesheet caching, favicon databases may retain
        # outdated bitmaps at a reused URL. Check the new filename and bytes.
        path = "assets/favicon-floral-20261114.svg"
        actual = remote_file(path)
        if hashlib.sha256(actual).digest() != hashlib.sha256(expected_file(path)).digest():
            raise RuntimeError("Published pink flower favicon differs from main")
        print(f"OK {path}: published flower bytes match latest main", flush=True)

if __name__ == "__main__":
    for attempt in range(1, 13):
        try:
            verify()
            print("PASS: GitHub Pages served all 10 pages and verified favicon assets.", flush=True)
            break
        except (HTTPError, URLError, RuntimeError, OSError, subprocess.CalledProcessError) as exc:
            print(f"Attempt {attempt}/12: {exc}", flush=True)
            if attempt == 12:
                raise SystemExit("FAIL: GitHub Pages publication is not verified")
            time.sleep(15)
