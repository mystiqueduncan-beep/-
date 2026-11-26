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
            assert page.locator(".bs-ai-launcher-face").evaluate("e=>getComputedStyle(e).animationName")=="bs-reading-shared-float"
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
        guide.clock.run_for(2100)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        guide.clock.run_for(1400)
        expect(words).to_have_text("想找什麼嗎？")
        box=hint.bounding_box()
        assert box and 0<=box["x"] and box["x"]+box["width"]<=390,box
        assert box["width"]<125,box
        guide.clock.run_for(9000)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        guide.clock.run_for(2000)
        expect(hint).to_have_attribute("aria-hidden","true")
        # Cross-page session timing does not reset to the first greeting.
        guide.goto(f"{base}/mobile-contact.html?view=mobile", wait_until="domcontentloaded")
        hint=guide.locator(".bs-ai-guide-hint")
        words=hint.locator(".bs-ai-guide-hint-text")
        guide.clock.run_for(3000)
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.clock.run_for(20000)
        assert words.inner_text() in ["需要我帶路嗎？","有什麼想了解的嗎？","想先看看重點嗎？","不知道從哪裡看起嗎？","有需要我幫忙的嗎？","想讓我為你介紹嗎？","想找聯絡方式嗎？","想了解教育背景嗎？","想了解應徵方向嗎？"],words.inner_text()
        # Sample actual running motion WITHOUT aligning or manually changing animation clocks.
        motion = guide.evaluate("""async () => {
          const a=document.querySelector('.bs-ai-launcher-face'), b=document.querySelector('.bs-ai-guide-face'), dock=document.querySelector('.bs-ai-dock');
          const values=[];
          const x=a.getBoundingClientRect().top,y=b.getBoundingClientRect().top;
          values.push([x,y,x-y]);
          return {values,clock:dock.getAnimations().map(x=>x.animationName),faces:[a,b].map(e=>getComputedStyle(e).animationName)};
        }""")
        assert motion["clock"]==[],motion
        assert motion["faces"]==["bs-reading-shared-float","bs-reading-shared-float"],motion
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
            live_motion.goto(f"{base}/{file}?view={view}",wait_until="domcontentloaded")
            live_motion.locator(".bs-ai-guide-hint-text").wait_for(state="attached")
            # The site-wide pop/glimmer must never attach to the widget.
            # Capture hit-target geometry immediately, before the greeting.
            initial=live_motion.evaluate("""async()=>{const a=document.querySelector('.bs-ai-launcher'),b=document.querySelector('.bs-ai-guide-hint'),out=[];for(let i=0;i<12;i++){out.push([a.getBoundingClientRect().top,b.getBoundingClientRect().top,getComputedStyle(a).animationName,getComputedStyle(b).animationName,a.classList.contains('site-button-motion'),b.classList.contains('site-button-motion')]);await new Promise(r=>setTimeout(r,100));}return out;}""")
            assert all(row[2:]==["none","none",False,False] for row in initial), (file,initial)
            assert all(max(row[i] for row in initial)-min(row[i] for row in initial)<0.5 for i in (0,1)), (file,initial)
            expect(live_motion.locator(".bs-ai-guide-hint-text")).to_have_text("想找什麼嗎？",timeout=6000)
            # Keep the pointer away from the widget during passive playback sampling.
            # No animation clock or phase is modified.
            if view=="desktop":
                live_motion.mouse.move(10,10)
            dock=live_motion.locator(".bs-ai-dock")
            print("Passive motion state",file,engine.browser_type.name,dock.evaluate("""e=>({state:getComputedStyle(e).animationPlayState,hover:e.matches(\":hover\"),focus:!!e.querySelector(\":focus-visible\"),animations:e.getAnimations().map(a=>({state:a.playState,time:a.currentTime})),y:getComputedStyle(e).getPropertyValue(\"--bs-reading-y\")})"""),flush=True)
            assert dock.evaluate("e=>[...e.querySelectorAll(\'.bs-ai-launcher-face,.bs-ai-guide-face\')].map(f=>getComputedStyle(f).animationDuration)")==["2.7s","2.7s"]
            samples=live_motion.evaluate("""async()=>{const a=document.querySelector('.bs-ai-launcher-face'),b=document.querySelector('.bs-ai-guide-face'),out=[];for(let i=0;i<16;i++){out.push([a.getBoundingClientRect().top,b.getBoundingClientRect().top,a.parentElement.getBoundingClientRect().top,b.parentElement.getBoundingClientRect().top]);await new Promise(r=>setTimeout(r,180));}return out;}""")
            assert 5.2<=max(x[0] for x in samples)-min(x[0] for x in samples)<=6.5,samples
            assert max(x[0]-x[1] for x in samples)-min(x[0]-x[1] for x in samples)<0.5,samples
            assert all(max(x[i] for x in samples)-min(x[i] for x in samples)<0.5 for i in (2,3)),samples
            if view=="desktop":
                live_motion.locator(".bs-ai-launcher").hover()
                assert dock.evaluate("e=>[...e.querySelectorAll(\'.bs-ai-launcher-face,.bs-ai-guide-face\')].map(f=>getComputedStyle(f).animationPlayState)")==["paused","paused"]
                live_motion.mouse.move(10,10)
                live_motion.keyboard.press("Tab")
                live_motion.locator(".bs-ai-launcher").focus()
                assert dock.evaluate("e=>[...e.querySelectorAll(\'.bs-ai-launcher-face,.bs-ai-guide-face\')].map(f=>getComputedStyle(f).animationPlayState)")==["paused","paused"]
            live_motion.close()
        safari.close()
        hint.click()
        expect(guide.locator("#bs-ai-panel")).to_be_visible()
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.clock.run_for(35000)
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.keyboard.press("Escape")
        guide.clock.run_for(15000)
        expect(hint).to_have_attribute("aria-hidden","true")
        guide.clock.run_for(7000)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible")
        guide.close()

        # Real scroll events and real typing time: do not assume the browser
        # dispatched the scroll event at the moment scrollIntoView returned.
        contextual = browser.new_page(viewport={"width":390,"height":844})
        contextual.route("https://**/*",lambda route:route.abort())
        contextual.goto(f"{base}/mobile-trend.html?view=mobile",wait_until="domcontentloaded")
        hint=contextual.locator(".bs-ai-guide-hint")
        words=hint.locator(".bs-ai-guide-hint-text")
        expect(words).to_have_text("想找什麼嗎？",timeout=6000)
        expect(hint).to_have_attribute("aria-hidden","true",timeout=12000)
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
        expect(words).to_have_text(re.compile(r"^(想了解執行計畫嗎？|想看看90天計畫嗎？)$"),timeout=3500)
        geometry=contextual.evaluate("""()=>{const r=document.getElementById('roadmap').getBoundingClientRect();return {top:r.top,bottom:r.bottom,y:innerHeight*.32}}""")
        assert geometry["top"]<=geometry["y"]<=geometry["bottom"],geometry
        trace=contextual.evaluate("window.__qaHintTrace")
        assert len(trace["shows"])==1 and trace["scrolls"],trace
        revealed=trace["shows"][0]
        last_scroll=max(t for t in trace["scrolls"] if t<=revealed)
        assert 1950<=revealed-last_scroll<=3000,trace
        phrase=words.inner_text()
        letters=trace["chars"]
        assert [x["text"] for x in letters]==[phrase[:i] for i in range(1,len(phrase)+1)],trace
        assert 500<=letters[0]["at"]-revealed<=1200,trace
        assert all(110<=b["at"]-a["at"]<=600 for a,b in zip(letters,letters[1:])),trace
        # Crossing two sections quickly must not interrupt the current
        # question. Only the final stable section is queued.
        contextual.evaluate("document.getElementById('strategy').scrollIntoView({behavior:'instant',block:'start'})")
        contextual.wait_for_timeout(300)
        contextual.evaluate("document.getElementById('consumer').scrollIntoView({behavior:'instant',block:'start'})")
        contextual.wait_for_timeout(2300)
        assert words.inner_text()==phrase,contextual.evaluate("window.__qaHintTrace")
        assert contextual.evaluate("window.__qaHintTrace.shows.length")==1
        expect(hint).to_have_attribute("aria-hidden","true",timeout=12000)
        expect(hint).to_have_class("bs-ai-guide-hint is-visible",timeout=3500)
        expect(words).to_have_text(re.compile(r"^(想了解消費者行為嗎？|想了解顧客需求嗎？)$"),timeout=3500)
        trace=contextual.evaluate("window.__qaHintTrace")
        assert len(trace["shows"])==2 and len(trace["hides"])==1,trace
        assert 9800<=trace["hides"][0]-letters[-1]["at"]<=11000,trace
        assert 550<=trace["shows"][1]-trace["hides"][0]<=1500,trace
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
