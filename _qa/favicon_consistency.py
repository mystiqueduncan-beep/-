"""Regression guard: every portfolio entry keeps the same early floral favicon."""
from pathlib import Path
import re
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "index.html",
    "mobile.html",
    "contact.html",
    "mobile-contact.html",
    "trend.html",
    "mobile-trend.html",
    "resume.html",
    "mobile/index.html",
    "mobile/contact.html",
    "mobile/trend.html",
)
# New filename is essential: browsers may keep favicon bitmaps separately
# from the normal HTTP cache and reuse the old yellow-character icon by URL.
FAVICON = (ROOT / "assets/favicon-floral-20261114.svg").resolve()

assert FAVICON.is_file(), "Shared floral favicon is missing"
assert FAVICON.read_bytes() == (ROOT / "assets/favicon.svg").read_bytes(), (
    "Published versioned icon must exactly match the approved pink flower")
root = ElementTree.fromstring(FAVICON.read_bytes())
assert root.tag.endswith("svg"), "Versioned favicon is not an SVG"
assert not any(child.tag.endswith("text") for child in root.iter()), (
    "A text glyph was unexpectedly reintroduced in the floral favicon")
for page in PAGES:
    source = (ROOT / page).read_text(encoding="utf-8")
    head = source.split("</head>", 1)[0]
    links = re.findall(r'<link\s+[^>]*rel="icon"[^>]*>', head)
    assert len(links) == 1, f"{page}: expected exactly one favicon link"
    hrefs = re.findall(r'href="([^"]+)"', links[0])
    assert len(hrefs) == 1, f"{page}: favicon href missing"
    actual = ((ROOT / page).parent / hrefs[0].split("?", 1)[0]).resolve()
    assert actual == FAVICON, f"{page}: favicon points to different file: {hrefs[0]}"
    assert "favicon.svg" not in head, f"{page}: stale icon URL still appears"
    assert head.index(links[0]) < 1024, f"{page}: favicon declared too late"
    if page in ("index.html", "mobile.html", "contact.html", "mobile-contact.html"):
        assert head.index(links[0]) < head.index("<script"), f"{page}: router runs before favicon"
    if page.startswith("mobile/"):
        assert head.index(links[0]) < head.index('http-equiv="refresh"'), f"{page}: redirect starts before favicon"
    print(f"{page}: shared floral favicon in early head")
print("Favicon consistency PASS")
