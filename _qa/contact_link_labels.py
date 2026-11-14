"""Strictly normalize only the user-approved contact LINK labels for historical checks.

The on-page buttons are required to say 「個人聯絡資訊」.  When comparing older,
unchanged factual-text fingerprints and approved research source blobs, restore
only those seven exact anchor labels to their prior display text.  Any missing,
extra, or differently worded contact link fails the regression checks.
"""
import re

CONTACT_LINK_COUNT = {
    "index.html": 1,
    "mobile.html": 2,
    "trend.html": 1,
    "mobile-trend.html": 2,
    "mobile-contact.html": 1,
}
LINK = re.compile(r'(<a\b[^>]*\bhref="(?:mobile-)?contact\.html"[^>]*>)([\s\S]*?)(</a>)')


def restore_historical_contact_link_labels(rel, html):
    expected = CONTACT_LINK_COUNT.get(rel)
    if expected is None:
        return html

    found = 0

    def rewrite(match):
        nonlocal found
        begin, contents, end = match.groups()
        label = re.sub(r'<[^>]*>', '', contents).strip()
        assert label == '個人聯絡資訊', (
            rel + ': unexpected personal contact link label: ' + label)
        assert contents.count('個人聯絡資訊') == 1, (
            rel + ': ambiguous personal contact link')
        found += 1
        return begin + contents.replace(
            '個人聯絡資訊', '個人及聯絡資訊', 1) + end

    restored = LINK.sub(rewrite, html)
    assert found == expected, (
        f'{rel}: expected {expected} personal contact links, found {found}')
    return restored
