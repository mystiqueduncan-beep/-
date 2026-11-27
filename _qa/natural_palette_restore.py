"""Reverse ONLY the exact user-approved color replacements in HTML style regions.
The existing content hashes remain unchanged; unexpected color edits fail.
No visible words, data values, links, layout or script changes are exempted.
"""
import json
import re
from pathlib import Path

EDITORIAL_PATCHES=json.loads(Path(__file__).with_name("editorial_style_approved.json").read_text(encoding="utf-8"))
CONTACT_PATCHES=json.loads(Path(__file__).with_name("contact_specs_approved.json").read_text(encoding="utf-8"))
PATCHES=json.loads(Path(__file__).with_name("natural_palette_html.json").read_text(encoding="utf-8"))
REGIONS=re.compile(r'<style\b[^>]*>[\s\S]*?</style>|\bstyle="[^"]*"',re.I)

def restore_natural_html(name, html):
    # Exact cache-key-only release normalization; preserve the immutable
    # historical offsets, hashes, approved content and all subsequent checks.
    widget_pages = {"index.html", "mobile.html", "contact.html", "mobile-contact.html", "trend.html", "mobile-trend.html", "data-visualization.html"}
    if name in widget_pages:
        current = 'href="assets/ai-assistant.css?v=20261127-passive-guidance"'
        previous = 'href="assets/ai-assistant.css?v=20261125-shared-bubble"'
        assert html.count(current) == 1 and previous not in html, (name, "reading widget CSS release key")
        html = html.replace(current, previous, 1)
        current = 'src="assets/ai-assistant.js?v=20261127-passive-guidance"'
        previous = 'src="assets/ai-assistant.js?v=20261125-shared-bubble"'
        assert html.count(current) == 1 and previous not in html, (name, "reading widget JS release key")
        html = html.replace(current, previous, 1)
    if name in widget_pages - {"data-visualization.html"}:
        current = 'src="assets/page-transitions.js?v=20261126-isolated-motion"'
        previous = 'src="assets/page-transitions.js?v=20261125-editorial"'
        assert html.count(current) == 1 and previous not in html, (name, "page transitions JS release key")
        html = html.replace(current, previous, 1)
    # Reverse only exact, user-approved editorial fragments; leave all original guards in force.
    for offset, old, new in reversed(EDITORIAL_PATCHES.get(name, [])):
        assert html[offset:offset+len(new)] == new, (name, offset, "unapproved editorial change")
        html = html[:offset] + old + html[offset+len(new):]
    # Reconstruct only the exact user-approved shortened contact card before
    # reversing color edits by ordinal. The complete historical content guard remains.
    if name in CONTACT_PATCHES:
        change=CONTACT_PATCHES[name]
        assert html.count(change["now"])==1,(name,"approved contact card missing or altered")
        html=html.replace(change["now"],change["old"],1)
    patches=dict(PATCHES.get(name, []))
    if not patches:
        return html
    ordinal=0
    def restore(match):
        nonlocal ordinal
        i=ordinal
        ordinal+=1
        region=match.group()
        if i not in patches:
            return region
        edits=patches.pop(i)
        if region.startswith("<"):
            split=region.index(">")+1
            prefix,body,suffix=region[:split],region[split:-8],region[-8:]
        else:
            prefix,body,suffix=region[:7],region[7:-1],region[-1:]
        for offset,current,previous in reversed(edits):
            assert body[offset:offset+len(current)]==current,(name,i,offset,"unapproved theme change")
            body=body[:offset]+previous+body[offset+len(current):]
        return prefix+body+suffix
    restored=REGIONS.sub(restore,html)
    assert not patches,(name,"missing approved style region")
    return restored

def restore_natural_bytes(name, raw):
    return restore_natural_html(name,raw.decode("utf-8")).encode("utf-8")
