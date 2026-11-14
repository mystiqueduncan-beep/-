"""Strictly allow the user-approved Japanese *display labels* in the text baseline.

The original portfolio facts and the exact two approved research files remain
protected: this only strips a known, finite set of UI-only additions before
comparing against the immutable historical fingerprints. Unknown additions,
modified Chinese/English text, missing labels and changed data still fail CI.
"""
import re

SECTION_JP = {
    "index.html": [
        "応募動機", "主なマネジメント能力", "店舗運営の改善提案",
        "職務経歴", "入社後の業務構想", "実店舗の市場動向リサーチ",
    ],
    "trend.html": [
        "市場動向を運営判断につなげる", "現場経験を複数店舗の管理へ",
        "六つの改善方針と担当体制", "90日間のエリア運営推進計画",
        "売上だけでなく改善コストも評価", "情報源と提案の適用範囲",
    ],
    "mobile-trend.html": [
        "市場動向を運営判断につなげる", "現場経験を複数店舗の管理へ",
        "六つの改善方針と担当体制", "90日間のエリア運営推進計画",
        "売上だけでなく改善コストも評価", "情報源と提案の適用範囲",
    ],
    "mobile.html": [
        "応募者プロフィール", "志望動機と今後の目標",
        "四つの主要なマネジメント能力", "店舗運営の実務と改善提案",
        "職務経歴", "入社後の業務構想", "実店舗の将来性・課題と変革戦略",
    ],
}

STYLE_BLOCK = re.compile(
    r'<style id="japanese-section-heading-style">[\s\S]*?</style>\n'
)

def strip_approved_japanese_ui(rel, html):
    """Return original HTML, rejecting missing/altered/extra Japanese UI labels."""
    if rel not in (
        "index.html", "trend.html", "mobile-trend.html", "mobile.html",
        "contact.html", "mobile-contact.html"
    ):
        return html

    blocks = STYLE_BLOCK.findall(html)
    assert len(blocks) == 1, rel + ": expected exactly one approved label stylesheet"
    style = blocks[0]
    assert "font-family:" in style and (
        "sec-title-jp" in style or "mobile-section-jp" in style
        or "section-locale-line" in style
    ), rel + ": unexpected Japanese label CSS"
    assert "@import" not in style and "url(" not in style, rel + ": external style not approved"
    html = html.replace(style, "", 1)

    def remove_once(fragment):
        nonlocal html
        assert html.count(fragment) == 1, rel + ": missing/duplicated label " + fragment[:90]
        html = html.replace(fragment, "", 1)

    if rel == "index.html":
        for jp in SECTION_JP[rel]:
            remove_once('<span class="sec-title-jp" lang="ja">' + jp + '</span>')
        # Preserve the newline that precedes each original wrapper close.
        # Any extra whitespace is ignored only by the existing text digest.
        return html

    if rel in ("trend.html", "mobile-trend.html"):
        for jp in SECTION_JP[rel]:
            remove_once('<span class="sec-title-jp" lang="ja">' + jp + '</span>')
        remove_once('<span class="report-title-ja" lang="ja">'
                    'ドラッグストア業界動向調査・エリア運営改善提案</span>')
        return html

    if rel in ("contact.html", "mobile-contact.html"):
        remove_once('\n<p class="section-locale-line"><span lang="en">EDUCATION</span>'
                    '<span aria-hidden="true">／</span><span lang="ja">学歴</span></p>')
        return html

    if rel == "mobile.html":
        for jp in SECTION_JP[rel][:5]:
            remove_once('<span class="mobile-section-jp" lang="ja">' + jp + '</span>')
        remove_once('\n<span class="mobile-section-jp" lang="ja">職務経歴</span>')
        remove_once('\n<p class="mobile-section-jp" lang="ja">'
                    '実店舗の将来性・課題と変革戦略</p>')
        return html
    raise AssertionError(rel + ": unsupported page")
