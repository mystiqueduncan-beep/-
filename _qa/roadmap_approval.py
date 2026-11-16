"""Allow only the approved interactive 90-day roadmap within immutable research pages.

The two byte-exact snapshots preserve the original data and every phase's
original prose. Normalization is for historical Git blob comparisons only.
"""
from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
BEFORE_PATH = ROOT / "_audit/roadmap-original-20261116.html"
AFTER_PATH = ROOT / "_audit/roadmap-interactive-20261116.html"
BEFORE_SHA1 = "233289310bc999bf004daf611794907f654a0e0f"
AFTER_SHA1 = "099acb3959f9aaea9d3ce47e5471ccdb8d80aecd"


def git_blob_hash(content):
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


def restore_approved_roadmap(rel, raw):
    if rel not in ("trend.html", "mobile-trend.html"):
        return raw
    before = BEFORE_PATH.read_bytes()
    after = AFTER_PATH.read_bytes()
    assert git_blob_hash(before) == BEFORE_SHA1, "original roadmap audit source changed"
    assert git_blob_hash(after) == AFTER_SHA1, "approved interactive roadmap audit source changed"
    cards = lambda html: re.findall(rb'<article\\b[^>]*>(.*?)</article>', html, re.S)
    original_cards, new_cards = cards(before), cards(after)
    assert len(original_cards) == len(new_cards) == 3
    assert original_cards == new_cards, "approved roadmap card facts were modified"
    # Japanese UI is separately checked then stripped before the historical hash.
    jp = '<span class="sec-title-jp" lang="ja">90日間のエリア運営推進計画</span>'.encode("utf-8")
    assert before.count(jp) == after.count(jp) == 1
    before = before.replace(jp, b"", 1)
    after = after.replace(jp, b"", 1)
    assert raw.count(after) == 1, rel + ": unexpected roadmap interaction or content edit"
    return raw.replace(after, before, 1)
