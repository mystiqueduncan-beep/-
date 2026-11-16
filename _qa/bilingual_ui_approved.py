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
    for asset in ("assets/bilingual-pastel-chapters.css", "assets/bilingual-chapters.js"):
        assert (_ROOT / asset).is_file(), rel + ": missing approved bilingual asset " + asset
    assert html.count('data-bilingual-nav') == 1, rel + ": bilingual navigation must appear once"
    assert html.count('data-chapter=') == 6, rel + ": exactly six linked bilingual chapters required"
    for item in _MAPPINGS[rel]:
        new_fragment = item["new"]
        assert html.count(new_fragment) == 1, rel + ": approved UI fragment missing/duplicated: " + item["label"]
        html = html.replace(new_fragment, item["old"], 1)
    assert "bilingual-chapter-nav" not in html, rel + ": unexpected bilingual markup outside reviewed fragments"
    return html
