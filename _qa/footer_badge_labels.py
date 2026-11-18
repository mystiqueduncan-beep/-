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


# The homepage's three redundant display-only blocks were removed by request.
# Rebuild their exact historical markup ONLY in the immutable text audits;
# this never inserts them into the published site's HTML.
HISTORICAL_HOME_TARGET = "        <div class=\"target-role-badge\">\n          <span>應徵目標：<strong>台灣松本清 (Matsumoto Kiyoshi)</strong> ｜ 區域營運經理（門市督導）</span>\n        </div>\n"
HISTORICAL_HOME_POSITION = "<div class=\"hero-position-highlight\">\n<span>志願應徵職位：區域營運經理（門市營運督導）</span>\n<span class=\"sub\">｜ 希望服務區域：桃竹苗 ＆ 大台北門市</span>\n</div>"
HISTORICAL_HOME_FOOTER = "      <div style=\"display: flex; align-items: center; gap: 8px;\">\n        <span style=\"background: var(--mk-yellow); color: var(--mk-navy); padding: 2px 6px; font-weight: 800; border: 1px solid var(--mk-navy);\">JHP</span>\n        <strong style=\"color: var(--mk-navy);\">黃博詩 ｜ 個人應徵作品集</strong>\n        <span>（志願應徵目標：台灣松本清 區域營運經理）</span>\n      </div>\n"


def restore_removed_home_display_only(rel, html):
    if rel != "index.html":
        return html
    for forbidden in ('class="target-role-badge"', 'class="hero-position-highlight"',
                      '（志願應徵目標：台灣松本清 區域營運經理）'):
        assert forbidden not in html, "Removed homepage UI is unexpectedly visible: " + forbidden
    masthead_end = "      </div>\n\n      <!-- Hero Grid -->"
    position_end = "</div></div><div class=\"cover-introduction\">"
    footer_start = "<footer class=\"mag-footer\">\n    <div class=\"container footer-inner\">\n"
    for marker in (masthead_end, position_end, footer_start):
        assert html.count(marker) == 1, "Homepage UI restoration anchor changed"
    html = html.replace(masthead_end, HISTORICAL_HOME_TARGET + masthead_end, 1)
    html = html.replace(position_end, "</div>" + HISTORICAL_HOME_POSITION + "</div><div class=\"cover-introduction\">", 1)
    html = html.replace(footer_start, footer_start + HISTORICAL_HOME_FOOTER, 1)
    return html


def restore_historical_footer_badge(rel, html):
    html = restore_approved_footer_layout(rel, html)
    html = restore_removed_home_display_only(rel, html)
    if rel not in FOOTER_PAGES:
        return html
    restored, count = BADGE.subn(r'\g<1>MK\g<2>', html)
    assert count == 1, rel + ": expected exactly one approved JHP footer badge"
    return restored


# Approved 2026-11-18: exact footer-only copy/layout simplification.
# Require the whole approved new fragment, including any existing action.
# Reverse ONLY that fragment for immutable historical comparisons.
FOOTER_LAYOUT = {
    "index.html": ("<footer class=\"mag-footer\">\n    <div class=\"container footer-inner\">\n      <div>\n        <span style=\"margin-right: 14px;\">內容更新日期：2026 年 11 月</span>\n        <a href=\"#top\" class=\"portfolio-back-to-top__link\" style=\"margin-right: 14px;\">↑ 回頂端</a>\n        <span>© 2026 BO-SHIH HUANG</span>\n      </div>\n    </div>\n  </footer>", "<footer class=\"mag-footer portfolio-footer-v2\" aria-label=\"頁尾\">\n    <div class=\"container footer-inner portfolio-footer-v2__inner\">\n      <div class=\"portfolio-footer-v2__actions\"><a href=\"#top\" class=\"portfolio-back-to-top__link\" style=\"margin-right: 14px;\">↑ 回頂端</a></div>\n      <p class=\"portfolio-footer-v2__copyright\" lang=\"en\">© 2026 BO-SHIH HUANG. ALL RIGHTS RESERVED.</p>\n    </div>\n  </footer>"),
    "mobile.html": ("<footer class=\"mobile-footer\">\n    <div style=\"margin-bottom: 6px;\">\n      <span style=\"background: var(--mk-yellow); color: var(--mk-navy); padding: 2px 6px; font-weight: 800; border: 1px solid var(--mk-navy);\">JHP</span>\n      <strong style=\"color: var(--mk-navy); margin-left: 4px;\">個人應徵作品集 ｜ 黃博詩</strong>\n    </div>\n    <div style=\"margin-bottom: 6px; color: var(--ink-secondary);\">\n      志願職位：台灣松本清 區域營運經理\n    </div>\n    <div style=\"margin-bottom: 8px;\">\n      內容更新日期：2026 年 11 月\n    </div>\n    <div>© 2026 BO-SHIH HUANG. ALL RIGHTS RESERVED.</div>\n  </footer>", "<footer class=\"mobile-footer portfolio-footer-v2\" aria-label=\"頁尾\">\n    <div class=\"container footer-inner portfolio-footer-v2__inner\">\n      <p class=\"portfolio-footer-v2__copyright\" lang=\"en\">© 2026 BO-SHIH HUANG. ALL RIGHTS RESERVED.</p>\n    </div>\n  </footer>"),
    "contact.html": ("<footer class=\"mag-footer\">\n    <div class=\"container footer-inner\">\n      <div>\n        <strong style=\"color: var(--mk-navy);\">台灣松本清 區域營運經理 應徵專刊</strong> ｜ 黃博詩 (HUANG BO-SHIH)\n      </div>\n      <div>\n        <span>黃博詩 應徵台灣松本清 區域營運經理</span>\n      </div>\n      <div>\n        <span>© 2026 BO-SHIH HUANG. ALL RIGHTS RESERVED.</span>\n      </div>\n    </div>\n  </footer>", "<footer class=\"mag-footer portfolio-footer-v2\" aria-label=\"頁尾\">\n    <div class=\"container footer-inner portfolio-footer-v2__inner\">\n      <p class=\"portfolio-footer-v2__copyright\" lang=\"en\">© 2026 BO-SHIH HUANG. ALL RIGHTS RESERVED.</p>\n    </div>\n  </footer>"),
    "mobile-contact.html": ("<footer class=\"mobile-footer\">\n    <div style=\"margin-bottom: 8px;\">\n      <span style=\"background: var(--mk-yellow); color: var(--mk-navy); padding: 2px 6px; font-weight: 900; border: 1px solid var(--mk-navy);\">JHP</span>\n      <strong style=\"color: var(--mk-navy); margin-left: 4px;\">個人應徵作品集 ｜ 黃博詩</strong>\n    </div>\n    <div style=\"margin-bottom: 10px;\">\n      志願目標：台灣松本清 區域營運經理\n    </div>\n    <div>© 2026 BO-SHIH HUANG. ALL RIGHTS RESERVED.</div>\n  </footer>", "<footer class=\"mobile-footer portfolio-footer-v2\" aria-label=\"頁尾\">\n    <div class=\"container footer-inner portfolio-footer-v2__inner\">\n      <p class=\"portfolio-footer-v2__copyright\" lang=\"en\">© 2026 BO-SHIH HUANG. ALL RIGHTS RESERVED.</p>\n    </div>\n  </footer>"),
    "trend.html": ("", "\n<footer class=\"mag-footer portfolio-footer-v2\" aria-label=\"頁尾\">\n    <div class=\"container footer-inner portfolio-footer-v2__inner\">\n      <p class=\"portfolio-footer-v2__copyright\" lang=\"en\">© 2026 BO-SHIH HUANG. ALL RIGHTS RESERVED.</p>\n    </div>\n  </footer>"),
    "mobile-trend.html": ("", "\n<footer class=\"mobile-footer portfolio-footer-v2\" aria-label=\"頁尾\">\n    <div class=\"container footer-inner portfolio-footer-v2__inner\">\n      <p class=\"portfolio-footer-v2__copyright\" lang=\"en\">© 2026 BO-SHIH HUANG. ALL RIGHTS RESERVED.</p>\n    </div>\n  </footer>"),
}

def restore_approved_footer_layout(rel, html):
    if rel not in FOOTER_LAYOUT:
        return html
    previous, approved = FOOTER_LAYOUT[rel]
    assert html.count(approved) == 1, rel + ": approved footer must appear exactly once"
    assert html.count('portfolio-footer-v2__copyright') == 1, rel + ": duplicate copyright"
    return html.replace(approved, previous, 1)
