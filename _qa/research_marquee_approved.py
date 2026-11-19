"""Allow only the exact approved research navigation UI change for immutable checks.

The user's original research, sources, chart figures, headings and interactive
90-day roadmap remain byte-exact. A changed/unexpected nav fails loudly.
"""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
APPROVED=json.loads((HERE/"research_marquee_approved.json").read_text(encoding="utf-8"))
ROOT=HERE.parent

def restore_research_marquee_ui(rel, html):
    if rel not in APPROVED:
        return html
    p=APPROVED[rel]
    assert (ROOT/"assets/research-marquee-pastel.css").is_file(), "Research marquee stylesheet missing"
    for tag in (p["nav_after"],p["css_link"]):
        assert html.count(tag)==1,rel+": research UI nav/CSS unexpected or duplicated"
    assert html.count("class=\"bilingual-nav-cn\"")==11,rel+": exactly eleven Chinese keys expected"
    assert html.count("class=\"bilingual-nav-jp\" lang=\"ja\"")==11,rel+": exactly eleven Japanese keys expected"
    assert "bilingual-current" not in html,rel+": current-section header must not exist"
    html=html.replace(p["nav_after"],p["nav_before"],1)
    html=html.replace(p["css_link"],"",1)
    return html
