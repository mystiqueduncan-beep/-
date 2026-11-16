"""Browser regression checks for the accessible single-panel 90-day roadmap."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGES = ("trend.html", "mobile-trend.html")


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def expect_stage(page, stage):
    tabs = page.locator("#roadmap [data-phase]")
    cards = page.locator("#roadmap [data-phase-card]")
    assert tabs.count() == cards.count() == 3
    for index in range(3):
        tab = tabs.nth(index)
        card = cards.nth(index)
        assert tab.get_attribute("aria-pressed") == str(index == stage).lower()
        assert tab.get_attribute("aria-controls") == card.get_attribute("id")
        assert card.is_visible() == (index == stage)
        assert card.evaluate("(element) => element.hidden") == (index != stage)
    assert page.locator("#roadmap .roadmap-step-count").inner_text() == f"{stage + 1:02d} / 03"
    assert page.locator("#roadmap [data-phase-prev]").is_disabled() == (stage == 0)
    assert page.locator("#roadmap [data-phase-next]").is_disabled() == (stage == 2)


def test_page(browser, base, file, width):
    page = browser.new_page(viewport={"width": width, "height": 900})
    view = "mobile" if file.startswith("mobile-") else "desktop"
    page.goto(base + "/" + file + "?view=" + view, wait_until="load")
    page.locator("#roadmap.roadmap-ready").wait_for()
    expect_stage(page, 0)
    page.locator("#roadmap [data-phase='1']").click()
    expect_stage(page, 1)
    assert "第二階段" in page.locator("#roadmap .timeline-summary").inner_text()
    page.locator("#roadmap [data-phase='1']").press("ArrowRight")
    expect_stage(page, 2)
    assert page.locator("#roadmap [data-phase='2']").evaluate("(el) => document.activeElement === el")
    page.locator("#roadmap [data-phase-prev]").click()
    expect_stage(page, 1)
    page.locator("#roadmap [data-phase='1']").press("Home")
    expect_stage(page, 0)
    page.locator("#roadmap [data-phase='0']").press("End")
    expect_stage(page, 2)
    selected_width = page.locator("#roadmap [data-phase-card='2']").evaluate("(el) => el.getBoundingClientRect().width")
    container_width = page.locator("#roadmap .roadmap").evaluate("(el) => el.getBoundingClientRect().width")
    assert selected_width >= container_width * 0.95, file + ": active card is not full width"

    # Print always contains all original phases, not only the one browsed.
    page.emulate_media(media="print")
    for i in range(3):
        assert page.locator(f"#roadmap [data-phase-card='{i}']").evaluate(
            "(el) => getComputedStyle(el).display !== 'none'"
        ), file + ": phase hidden from printed report"
    page.emulate_media(media="screen", reduced_motion="reduce")
    animation = page.locator("#roadmap [data-phase-card='2']").evaluate(
        "(el) => getComputedStyle(el).animationName"
    )
    assert animation == "none", file + ": reduced motion still animates"
    page.close()

    # Without JavaScript the original three complete plans remain readable.
    context = browser.new_context(viewport={"width": width, "height": 900}, java_script_enabled=False)
    no_js = context.new_page()
    no_js.goto(base + "/" + file, wait_until="load")
    assert no_js.locator("#roadmap [data-phase-card]").count() == 3
    assert no_js.locator("#roadmap [data-phase-card]:visible").count() == 3
    context.close()
    print(f"{file} @ {width}px: stage selection, keyboard, print, reduced-motion and no-JS OK")


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Quiet, directory=str(ROOT)))
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as play:
            browser = play.chromium.launch(args=["--no-sandbox"])
            try:
                for file in PAGES:
                    for width in (1280, 390):
                        test_page(browser, base, file, width)
            finally:
                browser.close()
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
