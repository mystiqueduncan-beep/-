"""Reverse only the six explicitly reviewed UI edits for historical fact checks.
The manifest holds exact before/after fragments, not a generalized text filter.
Unknown/missing fragments must fail instead of weakening the pinned baseline.
"""
import json
from pathlib import Path
PATCHES = json.loads(Path(__file__).with_name("portfolio_polish_approved.json").read_text(encoding="utf-8"))

def restore_portfolio_polish(name, html):
    for patch in reversed(PATCHES.get(name, [])):
        old, new = patch["old"], patch["now"]
        count = patch.get("count", 1)
        if name == "mobile.html" and old.startswith('<span class="role-pill">'):
            marker = '<span class="en-name">HUANG BO-SHIH (コウ・ハクシ)</span>\n'
            assert html.count(marker + new) == 1, name + ": candidate title fragment"
            html = html.replace(marker + new, marker + old, 1)
        elif name == "contact.html" and old.startswith('<a href="index.html" class="nav-btn-mk" style='):
            marker = '<div class="contact-bottom-links">\n          '
            assert html.count(marker + new) == 1, name + ": footer return control"
            html = html.replace(marker + new, marker + old, 1)
        else:
            assert html.count(new) == count, name + ": approved UI fragment missing or repeated: " + new[:100]
            html = html.replace(new, old, count)
    return html
