"""Regression guard: every portfolio entry keeps the same early floral favicon."""
from pathlib import Path
import re
import hashlib
import struct
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
FAVICON = (ROOT / "favicon.ico").resolve()

assert FAVICON.is_file(), "Shared flower favicon ICO is missing"
ico = FAVICON.read_bytes()
assert hashlib.sha256(ico).hexdigest() == (
    "0c158022ad427a34a7873d53b069bfc94c289bad766b9bf5d77dc8eb659953c8"
), "Favicon ICO differs from the approved flower render"
reserved, image_type, count = struct.unpack_from("<HHH", ico)
assert (reserved, image_type, count) == (0, 1, 2), "Expected valid 2-resolution ICO"
sizes = set()
for i in range(count):
    width, height, _, _, _, _, length, offset = struct.unpack_from(
        "<BBBBHHII", ico, 6 + i * 16)
    assert offset + length <= len(ico), "Truncated favicon ICO bitmap"
    assert ico[offset:offset + 8] == b"\x89PNG\r\n\x1a\n", (
        "ICO bitmap must be PNG-encoded")
    sizes.add((width, height))
assert sizes == {(16, 16), (32, 32)}, "Missing tab icon pixel resolution"
svg = ElementTree.fromstring((ROOT / "assets/favicon-floral-20261114.svg").read_bytes())
assert svg.tag.endswith("svg"), "Original flower SVG missing"
assert not any(el.tag.endswith("text") for el in svg.iter()), (
    "Original flower icon was replaced by a text glyph")
for page in PAGES:
    source = (ROOT / page).read_text(encoding="utf-8")
    head = source.split("</head>", 1)[0]
    links = re.findall(r'<link\s+[^>]*rel="icon"[^>]*>', head)
    assert len(links) == 1, f"{page}: expected exactly one favicon link"
    hrefs = re.findall(r'href="([^"]+)"', links[0])
    assert len(hrefs) == 1, f"{page}: favicon href missing"
    actual = ((ROOT / page).parent / hrefs[0].split("?", 1)[0]).resolve()
    assert actual == FAVICON, f"{page}: favicon points to different file: {hrefs[0]}"
    assert "favicon-floral-20261114.svg" not in head, f"{page}: former SVG icon URL still in page"
    assert head.index(links[0]) < 1024, f"{page}: favicon declared too late"
    if page in ("index.html", "mobile.html", "contact.html", "mobile-contact.html"):
        assert head.index(links[0]) < head.index("<script"), f"{page}: router runs before favicon"
    if page.startswith("mobile/"):
        assert head.index(links[0]) < head.index('http-equiv="refresh"'), f"{page}: redirect starts before favicon"
    print(f"{page}: shared floral favicon in early head")
print("Favicon consistency PASS")
