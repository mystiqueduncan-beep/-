"""Allow only the exact approved research navigation UI change for immutable checks.

The user's original research, sources, chart figures, headings and interactive
90-day roadmap remain byte-exact. A changed/unexpected nav fails loudly.
"""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
APPROVED=json.loads((HERE/"research_marquee_approved.json").read_text(encoding="utf-8"))
ROOT=HERE.parent

def restore_mobile_research_source(raw):
    """Reconstruct exactly two approved removed mobile presentation fragments.

    This is for immutable source hashes only. All substantive research bytes,
    quotes, figures, citations and headings remain covered by the old SHA.
    """
    p=APPROVED["mobile-trend.html"]
    nav=p["nav_after"].encode("utf-8")
    missing=b'</header><main class="trend-main container" id="main-content">'
    script=b'<script src="assets/trend-marquee.js?v=20261119-chapter-lock" defer></script>'
    next_script=b'<script src="assets/mk-inspired.js" defer></script>'
    assert raw.count(nav)==0, "mobile research top nav must be absent"
    assert raw.count(script)==0, "mobile research marquee script must be absent"
    assert raw.count(missing)==1, "mobile research nav removal insertion anchor"
    assert raw.count(next_script)==1, "mobile research script insertion anchor"
    raw=raw.replace(missing,b'</header>'+nav+b'<main class="trend-main container" id="main-content">',1)
    raw=raw.replace(next_script,script+next_script,1)
    return raw

def restore_research_marquee_ui(rel, html):
    if rel not in APPROVED:
        return html
    p=APPROVED[rel]
    if rel=="mobile-trend.html":
        # The actual mobile DOM has no upper chapter nav. Reconstruct only
        # its exact historical fragment for the approved UI source comparison.
        assert p["nav_after"] not in html,rel+": mobile research top nav reappeared"
        anchor='</header><main class="trend-main container" id="main-content">'
        assert html.count(anchor)==1,rel+": missing mobile nav removal boundary"
        html=html.replace(anchor,'</header>'+p["nav_after"]+'<main class="trend-main container" id="main-content">',1)
    assert (ROOT/"assets/research-marquee-pastel.css").is_file(), "Research marquee stylesheet missing"
    for tag in (p["nav_after"],p["css_link"]):
        assert html.count(tag)==1,rel+": research UI nav/CSS unexpected or duplicated"
    assert html.count("class=\"bilingual-nav-cn\"")==11,rel+": exactly eleven Chinese keys expected"
    assert html.count("class=\"bilingual-nav-jp\" lang=\"ja\"")==11,rel+": exactly eleven Japanese keys expected"
    assert "bilingual-current" not in html,rel+": current-section header must not exist"
    html=html.replace(p["nav_after"],p["nav_before"],1)
    html=html.replace(p["css_link"],"",1)
    return html
