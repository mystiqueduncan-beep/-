"""Browser audit for six-page trilingual headings and one-time typing effects.

Chinese remains primary. The same inline editorial block contains English
and Japanese with matching meanings. On narrow screens, wrapping is natural
within that block, never a detached right-hand badge or subtitle row.
"""
import functools
import http.server
import json
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_args): pass

server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0), functools.partial(Handler, directory=str(ROOT))
)
threading.Thread(target=server.serve_forever, daemon=True).start()

HOME = [
    ("應徵動機", "MOTIVATION FOR APPLYING", "志望動機"),
    ("核心管理能力", "CORE MANAGEMENT COMPETENCIES", "主なマネジメント能力"),
    ("門市營運改善構想", "STORE OPERATIONS IMPROVEMENT PROPOSALS", "店舗運営の改善案"),
    ("工作經歷", "WORK EXPERIENCE", "職務経歴"),
    ("到任後工作構想", "POST-HIRE OPERATIONS PLAN", "入社後の業務計画"),
    ("實體通路趨勢研究摘要", "PHYSICAL RETAIL TRENDS: RESEARCH SUMMARY", "実店舗の市場動向調査概要"),
]
RESEARCH = [
    ("市場訊號，如何轉成營運決策？", "FROM MARKET SIGNALS TO OPERATIONAL DECISIONS", "市場動向を運営判断につなげる"),
    ("把既有經驗，轉成跨店管理方法", "APPLYING EXPERIENCE TO MULTI-STORE MANAGEMENT", "現場経験を複数店舗の管理に生かす"),
    ("六項改善方針，明確分工執行", "SIX IMPROVEMENT PRIORITIES & CLEAR RESPONSIBILITIES", "六つの改善方針と明確な役割分担"),
    ("90 天區域營運推進計畫", "90-DAY REGIONAL OPERATIONS ROADMAP", "90日間のエリア運営推進計画"),
    ("不只看業績，也看改善的代價", "BEYOND SALES: ASSESSING IMPROVEMENT COSTS", "売上だけでなく改善コストも評価する"),
    ("資料來源與提案邊界", "SOURCES & PROPOSAL SCOPE", "情報源と提案の適用範囲"),
]
MOBILE = [
    ("應徵者專訪特輯", "APPLICANT FEATURE", "応募者紹介特集"),
    ("應徵動機與志向", "MOTIVATION & CAREER GOALS", "志望動機と今後の目標"),
    ("四大核心管理能力", "FOUR CORE MANAGEMENT COMPETENCIES", "四つの主要なマネジメント能力"),
    ("門市營運實務與改善構想", "STORE OPERATIONS & IMPROVEMENT PROPOSALS", "店舗運営の実務と改善提案"),
    ("工作經歷", "WORK EXPERIENCE", "職務経歴"),
    ("到任後工作構想", "POST-HIRE OPERATIONS PLAN", "入社後の業務計画"),
    ("美妝實體通路未來優勢、挑戰與轉型策略", "BEAUTY RETAIL: OPPORTUNITIES, CHALLENGES & TRANSFORMATION", "実店舗型美容小売の強み・課題と変革戦略"),
]
EXPECT = {
    "index": HOME,
    "mobile": MOBILE,
    "trend": RESEARCH + [("藥粧產業趨勢研究", "DRUGSTORE INDUSTRY TRENDS & REGIONAL OPERATIONS PROPOSAL", "ドラッグストア業界の動向調査とエリア運営改善提案")],
    "mobile-trend": RESEARCH + [("藥粧產業趨勢研究", "DRUGSTORE INDUSTRY TRENDS & REGIONAL OPERATIONS PROPOSAL", "ドラッグストア業界の動向調査とエリア運営改善提案")],
    "contact": [("教育背景", "EDUCATION", "学歴")],
    "mobile-contact": [("教育背景", "EDUCATION", "学歴")],
}
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(executable_path=os.environ.get("CHROME_PATH"), args=["--no-sandbox"])
    for name, expected in EXPECT.items():
        width = 390 if name.startswith("mobile") else 1440
        context = browser.new_context(viewport={"width": width, "height": 844}, reduced_motion="reduce")
        page = context.new_page()
        page.route("https://**/*", lambda route: route.abort())
        url = f'http://127.0.0.1:{server.server_port}/{name}.html?view={"mobile" if name.startswith("mobile") else "desktop"}'
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_function("() => document.querySelectorAll('.tri-type-line').length > 0")
        actual = page.locator(".tri-type-line").evaluate_all(
            """(lines) => lines.map(row => {
                const en = row.querySelector('.trilingual-en');
                const ja = row.querySelector('.trilingual-ja');
                return {
                    text: row.textContent.replace(/\s+/g, ' ').trim(),
                    en: en?.textContent || '',
                    ja: ja?.textContent || '',
                    enLang: en?.lang || '',
                    jaLang: ja?.lang || '',
                    enWithin: !!en && row.contains(en),
                    jaWithin: !!ja && row.contains(ja),
                    clip: getComputedStyle(row).clipPath,
                    wrapper: row.tagName,
                };
            })"""
        )
        assert len(actual) == len(expected), (name, "count", len(actual), len(expected), actual)
        for zh, en, ja in expected:
            matches = [a for a in actual if (zh in a["text"] or (name in ("trend", "mobile-trend") and zh == "藥粧產業趨勢研究")) and a["en"] == en and a["ja"] == ja]
            assert len(matches) == 1, (name, "translation missing or mismatch", (zh,en,ja), actual)
            entry = matches[0]
            assert entry["enLang"] == "en" and entry["jaLang"] == "ja", (name, "language tags", entry)
            assert entry["clip"] == "none", (name, "reduced motion not visible", entry)

        # Explicit layout contract: use the same research-page heading component
        # across homepage, research and contact (desktop and mobile). English
        # and Japanese must be direct siblings in ONE caption, not separated
        # by justify-content:space-between or independent heading rows.
        layout = page.locator(".tri-type-line").evaluate_all(
            """(lines) => lines.map(row => {
              const caption = row.querySelector('.tri-subtitle-line');
              const primary = row.querySelector('.tri-heading-primary');
              const en = caption?.querySelector(':scope > .trilingual-en');
              const separator = caption?.querySelector(':scope > .tri-subtitle-divider');
              const ja = caption?.querySelector(':scope > .trilingual-ja');
              const box = (e) => {
                if (!e) return null;
                const r=e.getBoundingClientRect();
                return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width};
              };
              return {
                editorial:row.classList.contains('tri-editorial-line'),
                order:!!caption && [...caption.children].slice(0,3).map(e=>e.className),
                textOrder: !!caption && caption.children[0]===en && caption.children[1]===separator && caption.children[2]===ja,
                separator:separator?.textContent,
                en:box(en), ja:box(ja), primary:box(primary), caption:box(caption),
                captionDisplay:caption&&getComputedStyle(caption).display,
                row:box(row),
              };
            })"""
        )
        assert all(item["caption"] and item["en"] and item["ja"] and item["textOrder"] and item["separator"]=="／" for item in layout), (name,"detached subtitle",layout)
        for item in layout:
            if item["editorial"]:
                assert item["primary"], (name,"missing Chinese primary",item)
                assert item["primary"]["top"] <= item["caption"]["top"]+2, (name,"wrong heading order",item)
                assert abs(item["caption"]["left"]-item["primary"]["left"]) <= 24, (name,"subtitle not aligned with title",item)
                assert item["caption"]["top"]-item["primary"]["top"] <= 115, (name,"subtitle moved too far from title",item)
            assert item["captionDisplay"] in ("inline-flex","flex"), (name,"caption lost inline editorial style",item)
            assert item["caption"]["width"] <= item["row"]["width"] + 2, (name,"caption extends outside heading",item)
            if abs(item["en"]["top"]-item["ja"]["top"]) < 8:
                assert item["ja"]["left"] <= item["en"]["right"] + 38, (name,"English and Japanese drift apart",item)
        assert sum(item["editorial"] for item in layout) >= (6 if name in ("index","trend","mobile-trend") else 7 if name=="mobile" else 1), (name, "unified headings not found",layout)
        overflow = page.evaluate("() => document.documentElement.scrollWidth - innerWidth")
        assert overflow <= 1, (name, "viewport horizontal overflow", overflow)
        print(json.dumps({"page":name,"width":width,"headlines":len(actual),"overflow_px":overflow,"reduced_motion":"pass"}, ensure_ascii=False),flush=True)
        context.close()

    # Confirm each headline has a pending/active/done one-shot lifecycle. This
    # visual typing does not delete text nodes or affect accessible names.
    page = browser.new_page(viewport={"width":1440,"height":900}, reduced_motion="no-preference")
    page.route("https://**/*", lambda route: route.abort())
    page.goto(f"http://127.0.0.1:{server.server_port}/index.html?view=desktop", wait_until="domcontentloaded")
    first = page.locator("#motivation .tri-type-line")
    first.wait_for()
    first.scroll_into_view_if_needed()
    page.wait_for_function("() => document.querySelector('#motivation .tri-type-line')?.classList.contains('tri-type-done')", timeout=6000)
    assert first.get_attribute("class").count("tri-type-done") == 1, "typing must finish once"
    page.evaluate("scrollTo(0,document.body.scrollHeight)")
    page.evaluate("scrollTo(0,0)")
    assert first.evaluate("(e) => e.classList.contains('tri-type-done') && !e.classList.contains('tri-type-pending')"), "typing must not replay"
    print("TYPEWRITER: passed one-time viewport reveal and reduced-motion fallback", flush=True)
    page.close()
    browser.close()
server.shutdown()
