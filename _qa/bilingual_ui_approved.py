"""Reconstruct only the reviewed Nov 16 bilingual UI diffs for existing
immutable resume checks. Each exact new fragment is checked before reversal;
unchanged factual paragraphs, links, and figures remain protected by _qa checks.
"""
from pathlib import Path
import json

_ROOT = Path(__file__).resolve().parents[1]
_MAPPINGS = json.loads((Path(__file__).with_name("bilingual_ui_approved.json")).read_text(encoding="utf-8"))

def restore_bilingual_home_ui(rel, html):
    if rel not in _MAPPINGS or "assets/bilingual-pastel-chapters.css" not in html:
        return html
    if rel=="mobile.html":
        # Reverse ONLY the removed upper mobile chapter strip for legacy text
        # fingerprint verification. The actual page keeps only bottom tabs.
        assert "bilingual-chapter-nav" not in html,rel+": old mobile top nav reappeared"
        fragment=next(x["new"] for x in _MAPPINGS[rel] if x["label"]=="mobile marquee")
        marker='</header>\n\n\n  <!-- Content Container -->'
        assert html.count(marker)==1,rel+": mobile nav removal boundary changed"
        html=html.replace(marker,'</header>'+fragment+'\n\n  <!-- Content Container -->',1)
        script='<script src="assets/trend-marquee.js" defer></script>'
        assert script not in html,rel+": removed mobile marquee script reappeared"
        anchor='  <script src="assets/mk-inspired.js" defer></script>'
        assert html.count(anchor)==1,rel+": mobile script location changed"
        html=html.replace(anchor,script+'\n'+anchor,1)
    for asset in ("assets/bilingual-pastel-chapters.css",):
        assert (_ROOT / asset).is_file(), rel + ": missing approved bilingual asset " + asset
    assert html.count("bilingual-chapter-nav") == 1, rel + ": chapter marquee must appear once"
    assert html.count('class="bilingual-nav-jp"') == 6, rel + ": exactly six Japanese button subtitles required"
    for removed in ("bilingual-current", "data-bilingual-title", "data-bilingual-nav", "data-chapter=", "assets/bilingual-chapters.js"):
        assert removed not in html, rel + ": stale current-chapter tracker " + removed
    for item in _MAPPINGS[rel]:
        new_fragment = item["new"]
        if rel == "mobile.html" and item["label"] == "mobile marquee assets":
            # The mobile homepage now loads the exact same ordered CSS via
            # its generated bundle. Validate the real bundle before reversing
            # only the historical marquee script fragment for text comparison.
            from mobile_css_bundle import check, NAMES
            check()
            assert "trend-marquee.css" in NAMES
            css_link = '<link rel="stylesheet" href="assets/trend-marquee.css">\n'
            assert new_fragment.startswith(css_link)
            new_fragment = new_fragment[len(css_link):]
        assert html.count(new_fragment) == 1, rel + ": approved UI fragment missing/duplicated: " + item["label"]
        html = html.replace(new_fragment, item["old"], 1)
    assert "bilingual-chapter-nav" not in html, rel + ": unexpected bilingual markup outside reviewed fragments"
    return html
