"""Browser acceptance tests for the no-API portfolio assistant."""
import functools
import re
import http.server
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(
    ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT))
)
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f"http://127.0.0.1:{server.server_port}"

try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for file_name, width, height, variant in (
            ("index.html", 1440, 900, "desktop"),
            ("mobile.html", 390, 844, "mobile"),
            ("trend.html", 1440, 900, "desktop"),
            ("mobile-trend.html", 390, 844, "mobile"),
            ("contact.html", 1440, 900, "desktop"),
            ("mobile-contact.html", 390, 844, "mobile"),
            ("data-visualization.html", 390, 844, None),
        ):
            page = browser.new_page(viewport={"width": width, "height": height})
            page.route("https://**/*", lambda route: route.abort())
            mode = f"?view={variant}" if variant else ""
            page.goto(f"{base}/{file_name}{mode}", wait_until="domcontentloaded")
            opener = page.locator(".bs-ai-launcher")
            expect(opener).to_be_visible()
            expect(opener.locator(".bs-ai-launcher-label")).to_have_text("閱讀小助手")
            expect(opener.locator(".bs-ai-launcher-caption")).to_have_text("找資料・直達章節")
            expect(opener.locator(".bs-ai-launcher-emblem")).to_have_text("♥")
            expect(opener.locator(".bs-ai-launcher-star")).to_have_count(2)
            assert page.locator(".bs-ai-dock").evaluate("e=>getComputedStyle(e).animationName")=="bs-reading-shared-float"
            assert opener.locator(".bs-ai-launcher-emblem").evaluate("e=>getComputedStyle(e).animationName")=="bs-ai-heartbeat"
            assert opener.locator(".bs-ai-launcher-star").first.evaluate("e=>getComputedStyle(e).animationIterationCount")=="infinite"
            assert opener.locator(".bs-ai-launcher-face").evaluate("e=>getComputedStyle(e,'::after').animationName")=="bs-ai-halo"
            expect(page.locator(".bs-ai-guide-hint")).to_have_attribute("aria-hidden", "true")
            opener.click()
            assert page.locator(".bs-ai-dock").evaluate("e=>getComputedStyle(e).animationName")=="none"
            assert opener.locator(".bs-ai-launcher-emblem").evaluate("e=>getComputedStyle(e).animationName")=="none"
            panel = page.get_by_role("region", name="黃博詩的閱讀小助手")
            expect(panel).to_be_visible()
            expect(panel.locator(".bs-ai-chip")).to_have_count(6)
            expect(page.locator(".bs-ai-guide-hint")).to_have_attribute("aria-hidden", "true")
            expect(panel.get_by_text("您好！我是黃博詩的 AI 數位分身", exact=False)).to_be_visible()
            box = panel.bounding_box()
            assert box is not None
            assert box["x"] >= -1 and box["x"] + box["width"] <= width + 1, (file_name, box)
            assert box["y"] >= -1 and box["y"] + box["height"] <= height + 1, (file_name, box)
            if "mobile" in file_name:
                nav = page.locator(".mobile-bottom-bar")
                if nav.count() and nav.is_visible():
                    button_box = page.locator(".bs-ai-launcher").bounding_box()
                    nav_box = nav.bounding_box()
                    assert button_box["y"] + button_box["height"] <= nav_box["y"] + 1 or button_box["x"] >= nav_box["x"] + nav_box["width"] or button_box["x"] + button_box["width"] <= nav_box["x"], (file_name, button_box, nav_box)
            if variant != "mobile":
                expect(panel.get_by_role("button", name="請自我介紹", exact=True)).to_be_visible()
                expect(panel.get_by_role("button", name="如何聯絡", exact=True)).to_be_visible()
            assert not any("簡歷" in x for x in panel.locator(".bs-ai-chip").all_text_contents())
            intro = panel.get_by_role("button", name="請自我介紹", exact=True)
            if intro.count():
                intro.click()
                expect(panel.get_by_text("您好，我是黃博詩，目前就讀", exact=False)).to_be_visible(timeout=3000)
                expect(panel.locator(".bs-ai-facts").first).to_be_visible()
                panel.get_by_role("button", name="重新開始對話", exact=False).click()
                expect(panel.locator(".bs-ai-chip")).to_have_count(6)
                expect(panel.get_by_text("您好，我是黃博詩，目前就讀", exact=False)).to_have_count(0)
            prompt = panel.get_by_role("textbox", name="輸入作品集相關問題")
            prompt.fill("介紹你的產業分析專題")
            prompt.press("Enter")
            expect(panel.get_by_text("改善提案，不代表已實施", exact=False)).to_be_visible(timeout=3000)
            target = "mobile-trend.html#market" if "mobile" in file_name else "trend.html#market"
            if file_name == "data-visualization.html":
                target = "trend.html#market"
            assert panel.get_by_role("link", name="閱讀完整產業研究").get_attribute("href") == target
            prompt = panel.get_by_role("textbox", name="輸入作品集相關問題")
            prompt.fill("Levi's 的工作內容")
            prompt.press("Enter")
            expect(panel.get_by_text("在 Levi's 任職約 2 年", exact=False)).to_be_visible(timeout=3000)
            prompt.fill("今天台北的天氣如何")
            prompt.press("Enter")
            expect(panel.get_by_text("無法回答網站未提供的資訊", exact=False)).to_be_visible(timeout=3000)
            page.keyboard.press("Escape")
            expect(panel).to_be_hidden()
            expect(page.get_by_role("button", name="開啟閱讀小助手")).to_be_visible()
            page.close()

        # Virtual clock exercises real production intervals without a long sleep.
        guide = browser.new_page(viewport={"width": 390, "height": 844})
        guide.route("https://**/*", lambda route: route.abort())
        guide.clock.install()
        guide.goto(f"{base}/mobile-trend.html?view=mobile", wait_until="domcontentloaded")
        hint=guide.locator(".bs-ai-guide-hint")
        words=hint.locator(".bs-ai-guide-hint-text")
        guide.clock.run_for(1100)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        assert hint.evaluate("e=>e.tagName==='DIV' && e.tabIndex===-1 && getComputedStyle(e).pointerEvents==='none'")
        first_width=hint.bounding_box()["width"]
        first_target=hint.get_attribute("data-target")
        assert first_target not in ("market","research","data")
        guide.clock.run_for(1800)
        phrase=words.inner_text()
        assert phrase.endswith("嗎？") and "我" not in phrase,phrase
        box=hint.bounding_box()
        assert box and 0<=box["x"] and box["x"]+box["width"]<=390 and box["width"]<240,box
        assert abs(box["width"]-first_width)<.5,(box,first_width)
        guide.clock.run_for(3500)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        guide.clock.run_for(2400)
        expect(hint).to_have_attribute("aria-hidden","true")
        # Cross-page session timing/history do not reset.
        guide.goto(f"{base}/mobile-contact.html?view=mobile", wait_until="domcontentloaded")
        hint=guide.locator(".bs-ai-guide-hint")
        words=hint.locator(".bs-ai-guide-hint-text")
        guide.clock.run_for(1000)
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.clock.run_for(6000)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        assert hint.get_attribute("data-target")!=first_target
        assert hint.get_attribute("data-target")!="region"
        assert words.inner_text()!=phrase
        # Sample actual running motion WITHOUT aligning or manually changing animation clocks.
        motion = guide.evaluate("""async () => {
          const a=document.querySelector('.bs-ai-launcher-face'), b=document.querySelector('.bs-ai-guide-face'), dock=document.querySelector('.bs-ai-dock');
          const values=[];
          const x=a.getBoundingClientRect().top,y=b.getBoundingClientRect().top;
          values.push([x,y,x-y]);
          return {values,clock:dock.getAnimations().map(x=>x.animationName),faces:[a,b].map(e=>getComputedStyle(e).animationName)};
        }""")
        assert motion["clock"]==["bs-reading-shared-float"],motion
        assert motion["faces"]==["none","none"],motion
        gaps=[v[2] for v in motion["values"]]
        assert max(gaps)-min(gaps)<0.5,motion
        # Sample throughout a full cycle on the real browser clock (not a forced phase).
        safari = playwright.webkit.launch()
        for engine,file,view,width,height in ((browser,"index.html","desktop",1440,900),(browser,"mobile.html","mobile",390,844),(safari,"mobile.html","mobile",390,844)):
            if engine==safari:
                live_motion=engine.new_page(**playwright.devices["iPhone 13"])
            else:
                live_motion=engine.new_page(viewport={"width":width,"height":height})
            live_motion.route("https://**/*",lambda route:route.abort())
            live_motion.goto(f"{base}/{file}?view={view}",wait_until="load")
            live_motion.bring_to_front()
            if engine!=safari:
                live_motion.mouse.move(10,10)
            live_motion.evaluate("document.fonts.ready")
            live_motion.locator(".bs-ai-guide-hint-text").wait_for()
            expect(live_motion.locator(".bs-ai-guide-hint-text")).to_have_text(re.compile(r"^想[^我]+嗎？$"),timeout=6000)
            dock=live_motion.locator(".bs-ai-dock")
            assert dock.evaluate("e=>getComputedStyle(e).animationDuration")=="2.7s"
            samples=live_motion.evaluate("""async()=>{const a=document.querySelector('.bs-ai-launcher-face'),b=document.querySelector('.bs-ai-guide-face'),out=[];for(let i=0;i<16;i++){out.push([a.getBoundingClientRect().top,b.getBoundingClientRect().top,a.parentElement.getBoundingClientRect().top,b.parentElement.getBoundingClientRect().top]);await new Promise(r=>setTimeout(r,180));}return out;}""")
            assert 5.2<=max(x[0] for x in samples)-min(x[0] for x in samples)<=6.5,(engine==safari,file,dock.evaluate("e=>({state:getComputedStyle(e).animationPlayState,value:getComputedStyle(e).getPropertyValue('--bs-reading-y'),visibility:document.visibilityState})"),samples)
            assert max(x[0]-x[1] for x in samples)-min(x[0]-x[1] for x in samples)<0.5,samples
            assert all(max(x[i] for x in samples)-min(x[i] for x in samples)<0.5 for i in (2,3)),samples
            if view=="desktop":
                live_motion.locator(".bs-ai-launcher").hover()
                assert dock.evaluate("e=>getComputedStyle(e).animationPlayState")=="paused"
                live_motion.mouse.move(10,10)
                live_motion.keyboard.press("Tab")
                live_motion.locator(".bs-ai-launcher").focus()
                assert dock.evaluate("e=>getComputedStyle(e).animationPlayState")=="paused"
            live_motion.close()
        safari.close()
        # A physical click on the passive hint cannot open the panel.
        box=hint.bounding_box()
        if box:
            guide.mouse.click(box["x"]+box["width"]/2,box["y"]+box["height"]/2)
        expect(guide.locator("#bs-ai-panel")).to_be_hidden()
        guide.locator(".bs-ai-launcher").click()
        expect(guide.locator("#bs-ai-panel")).to_be_visible()
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.clock.run_for(35000)
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.keyboard.press("Escape")
        guide.clock.run_for(4000)
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.clock.run_for(1500)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        guide.close()

        # Real scroll events and real typing time: do not assume the browser
        # dispatched the scroll event at the moment scrollIntoView returned.
        contextual = browser.new_page(viewport={"width":390,"height":844})
        contextual.route("https://**/*",lambda route:route.abort())
        contextual.goto(f"{base}/mobile-trend.html?view=mobile",wait_until="domcontentloaded")
        hint=contextual.locator(".bs-ai-guide-hint")
        words=hint.locator(".bs-ai-guide-hint-text")
        expect(words).to_have_text(re.compile(r"^想[^我]+嗎？$"),timeout=6000)
        expect(hint).to_have_attribute("aria-hidden","true",timeout=8500)
        contextual.evaluate("""() => {
          const h=document.querySelector('.bs-ai-guide-hint'), t=h.querySelector('.bs-ai-guide-hint-text');
          const trace=window.__qaHintTrace={scrolls:[],shows:[],hides:[],chars:[]};
          window.addEventListener('scroll', e=>{
            if (!document.querySelector('.bs-ai-root').contains(e.target)) trace.scrolls.push(performance.now());
          },{capture:true,passive:true});
          new MutationObserver(()=>{
            (h.classList.contains('is-visible')?trace.shows:trace.hides).push(performance.now());
          }).observe(h,{attributes:true,attributeFilter:['class']});
          new MutationObserver(()=>{if(t.textContent)trace.chars.push({at:performance.now(),text:t.textContent});})
            .observe(t,{childList:true,characterData:true,subtree:true});
          document.getElementById('roadmap').scrollIntoView({behavior:'instant',block:'start'});
        }""")
        expect(hint).to_have_class("bs-ai-guide-hint is-visible",timeout=5000)
        expect(words).to_have_text(re.compile(r"^想[^我]+嗎？$"),timeout=3500)
        assert hint.get_attribute("data-target") not in ("roadmap","research")
        geometry=contextual.evaluate("""()=>{const r=document.getElementById('roadmap').getBoundingClientRect();return {top:r.top,bottom:r.bottom,y:innerHeight*.32}}""")
        assert geometry["top"]<=geometry["y"]<=geometry["bottom"],geometry
        trace=contextual.evaluate("window.__qaHintTrace")
        assert len(trace["shows"])==1 and trace["scrolls"],trace
        revealed=trace["shows"][0]
        last_scroll=max(t for t in trace["scrolls"] if t<=revealed)
        assert 950<=revealed-last_scroll<=2000,trace
        phrase=words.inner_text()
        letters=trace["chars"]
        assert [x["text"] for x in letters]==[phrase[:i] for i in range(1,len(phrase)+1)],trace
        assert abs(letters[0]["at"]-revealed)<=150,trace
        assert all(75<=b["at"]-a["at"]<=500 for a,b in zip(letters,letters[1:])),trace
        # Crossing two sections quickly must not interrupt the current
        # question. Only the final stable section is queued.
        first_target=hint.get_attribute("data-target")
        safe=[s for s in ("strategy","consumer","people","digital") if s!=first_target and not (first_target=="data" and s=="consumer")]
        contextual.evaluate("id=>document.getElementById(id).scrollIntoView({behavior:'instant',block:'start'})",safe[0])
        contextual.wait_for_timeout(300)
        contextual.evaluate("id=>document.getElementById(id).scrollIntoView({behavior:'instant',block:'start'})",safe[1])
        contextual.wait_for_timeout(1300)
        assert words.inner_text()==phrase,contextual.evaluate("window.__qaHintTrace")
        assert contextual.evaluate("window.__qaHintTrace.shows.length")==1
        expect(hint).to_have_attribute("aria-hidden","true",timeout=12000)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible",timeout=3500)
        expect(words).to_have_text(re.compile(r"^想[^我]+嗎？$"),timeout=3500)
        assert hint.get_attribute("data-target") not in (safe[1],first_target,"research")
        if safe[1]=="consumer":
            assert hint.get_attribute("data-target")!="data"
        trace=contextual.evaluate("window.__qaHintTrace")
        assert len(trace["shows"])==2 and len(trace["hides"])==1,trace
        assert 5800<=trace["hides"][0]-letters[-1]["at"]<=7000,trace
        assert 350<=trace["shows"][1]-trace["hides"][0]<=1400,trace
        contextual.evaluate("document.getElementById('roadmap').scrollIntoView({behavior:'instant',block:'start'})")
        # Both children have the same positioned ancestor and no individual float.
        assert hint.evaluate("e=>e.parentElement.classList.contains('bs-ai-dock')")
        assert contextual.locator(".bs-ai-launcher").evaluate("e=>e.parentElement.classList.contains('bs-ai-dock')")
        contextual.locator(".bs-ai-launcher").click()
        expect(contextual.locator(".bs-ai-chip").first).to_have_attribute("data-topic","roadmap")
        contextual.locator(".bs-ai-chip").first.click()
        contextual.get_by_role("button",name="重新開始對話",exact=False).click()
        contextual.wait_for_timeout(2000)
        expect(contextual.locator(".bs-ai-chip")).to_have_count(6)
        expect(contextual.locator(".bs-ai-message--user")).to_have_count(0)
        contextual.close()

        narrow = browser.new_page(viewport={"width": 320, "height": 568}, reduced_motion="reduce")
        narrow.goto(f"{base}/mobile.html?view=mobile", wait_until="domcontentloaded")
        narrow_opener=narrow.get_by_role("button", name="開啟閱讀小助手")
        assert narrow.locator(".bs-ai-dock").evaluate("e=>getComputedStyle(e).animationName")=="none"
        narrow_opener.click()
        box = narrow.locator("#bs-ai-panel").bounding_box()
        assert box and box["x"] >= -1 and box["y"] >= -1, box
        assert box["x"] + box["width"] <= 321, box
        assert box["y"] + box["height"] <= 569, box
        narrow.get_by_role("textbox", name="輸入作品集相關問題").fill("如何聯絡")
        narrow.get_by_role("textbox", name="輸入作品集相關問題").press("Enter")
        expect(narrow.get_by_role("link", name="前往聯絡資訊")).to_be_visible(timeout=1500)
        assert narrow.get_by_role("link", name="前往聯絡資訊").get_attribute("href") == "mobile-contact.html"
        narrow.close()
        browser.close()
finally:
    server.shutdown()
