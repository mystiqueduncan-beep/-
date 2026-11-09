"""Verify that GitHub Pages serves the resume and the exact checked-in site assets.

This temporary PR checks the just-published research-aligned homepage CSS.

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
)
ASSETS = (
    "assets/site.css",
    "assets/mk-inspired.css",
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
        print(f"OK {page}: HTTP 200, HTML present", flush=True)
    for path in ASSETS:
        actual = remote_file(path)
        expected = expected_file(path)
        if hashlib.sha256(actual).digest() != hashlib.sha256(expected).digest():
            raise RuntimeError(f"{path}: deployed file differs from "
                               + ("PR base" if BASE_SHA else "latest main"))
        print(f"OK {path}: published bytes match "
              + ("PR base" if BASE_SHA else "latest main"), flush=True)

if __name__ == "__main__":
    for attempt in range(1, 13):
        try:
            verify()
            print("PASS: GitHub Pages served all 6 pages and 7 exact assets.", flush=True)
            break
        except (HTTPError, URLError, RuntimeError, OSError, subprocess.CalledProcessError) as exc:
            print(f"Attempt {attempt}/12: {exc}", flush=True)
            if attempt == 12:
                raise SystemExit("FAIL: GitHub Pages publication is not verified")
            time.sleep(15)
