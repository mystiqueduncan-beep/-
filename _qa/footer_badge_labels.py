"""Normalize only the user-approved footer MK -> JHP badge for historical audits.

This comparison-only reversal does not alter the rendered website. Every
other portfolio fact and every other text character remains protected by
the existing immutable source checks.
"""
import re

FOOTER_PAGES = ("index.html", "mobile.html", "mobile-contact.html")
BADGE = re.compile(
    r'(<span style="background: var\(--mk-yellow\); color: var\(--mk-navy\); '
    r'padding: 2px 6px; font-weight: (?:800|900); '
    r'border: 1px solid var\(--mk-navy\);">)JHP(</span>)'
)


def restore_historical_footer_badge(rel, html):
    if rel not in FOOTER_PAGES:
        return html
    restored, count = BADGE.subn(r'\g<1>MK\g<2>', html)
    assert count == 1, rel + ": expected exactly one approved JHP footer badge"
    return restored
