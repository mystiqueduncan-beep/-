"""Real-browser regression for one-time reveals on all six portfolio pages."""
import functools
import http.server
import json
import os
import re
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

root = Path(__file__).resolve().parents[1]
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(root)))
threading.Thread(target=server.serve_forever, daemon=True).start()
rows = []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROME_PATH'), args=['--no-sandbox'])
    for name in ('index', 'mobile', 'trend', 'mobile-trend', 'contact', 'mobile-contact'):
        mobile = name.startswith('mobile')
        url = f'http://127.0.0.1:{server.server_port}/{name}.html?view={"mobile" if mobile else "desktop"}'
        page = browser.new_page(viewport={'width': 390 if mobile else 1440, 'height': 844})
        page.route('https://**/*', lambda r: r.abort())
        # Check an early, roughly 15% entrance rather than first-pixel intersections.
        held = browser.new_page(viewport={'width':390 if mobile else 1440,'height':844})
        held.route('https://**/*', lambda r: r.abort())
        held.add_init_script('window.IntersectionObserver=class {observe(){} unobserve(){} disconnect(){}}; window.requestAnimationFrame=()=>0')
        held.goto(url)
        held.wait_for_timeout(800)
        # Capture exact pending styles for regression diagnostics.
        print("PENDING_STYLES", name, held.locator(".mk-motion-pending,.mk-pop-pending").evaluate_all(
            '(els)=>els.filter(e=>getComputedStyle(e).opacity!=="0").map(e=>({tag:e.tagName,class:e.className,opacity:getComputedStyle(e).opacity,html:e.outerHTML.slice(0,230)})).slice(0,12)'
        ), flush=True)
        # Verify the final hidden pending pose, not a mid-transition frame.
        held.wait_for_function(
            '() => [...document.querySelectorAll(".mk-motion-pending,.mk-pop-pending")].every(e => getComputedStyle(e).opacity === "0")',
            timeout=3500,
            polling=100  # Held-page RAF is intentionally disabled.
        )
        # Independent coverage contract: page sections, articles, card units and source notes.
        units = held.locator('.mag-header > .container, main section, main article, .key-pillar-card, .hero-action-card, .star-field-box, .stage-meta-box, .candidate-info-box, .candidate-specs-box, .source-verification, main .method-card')
        for unit in units.all():
            if unit.evaluate('(e)=>Boolean(e.closest(".portfolio-disclosure-panel[aria-hidden=true]"))'):
                continue
            if unit.get_attribute("data-phase-card") is not None:
                # Selectable roadmap panels use their own switch animation,
                # never a scroll-pending state that would trap hidden panels.
                assert not unit.evaluate('(e)=>e.matches(".mk-motion-pending,.mk-pop-pending")'), name
                continue
            assert unit.evaluate('(e)=>e.matches(".mk-motion-pending,.mk-pop-pending")'), (name, unit.get_attribute('class'))
        states = held.locator('.mk-motion-pending,.mk-pop-pending').evaluate_all('(es)=>es.map(e=>({x:new DOMMatrix(getComputedStyle(e).transform).m41,opacity:getComputedStyle(e).opacity,pop:e.classList.contains("mk-pop-pending"),fade:e.classList.contains("mk-fade-item")}))')
        assert states and all((x['x'] > 0 if x['pop'] else abs(x['x']) < 0.01 if x['fade'] else x['x'] < 0) and x['opacity'] == '0' for x in states), (name, states)
        # Both motion types must exist on editorial pages. Each nested element
        # still participates in the same one-time lifecycle.
        assert held.locator('.mk-motion-pending:not(.mk-fade-item)').count() >= 1, name
        assert held.locator('.mk-motion-pending.mk-fade-item').count() >= 1, name
        assert held.evaluate('document.documentElement.scrollWidth<=innerWidth'), name
        held.close()
        page.goto(url)
        page.wait_for_timeout(800)
        # Allow any in-progress CSS transitions to fully settle before asserting
        # pending-state opacity. A section near the top of a shorter page may
        # still be mid-transition after the initial 800 ms budget.
        page.wait_for_function(
            'function(){var el=document.querySelector(".mk-motion-pending,.mk-pop-pending");return !el||+getComputedStyle(el).opacity===0;}',
            timeout=3500
        )
        items = page.locator('.mk-motion-item,.mk-pop-item')
        assert items.count() > 0, name
        if 'contact' in name:
            # The print action is now a fourth matching contact-style card.
            assert page.locator('.mk-pop-item').count() == 4
            assert page.locator('.method-card--print.mk-pop-item').count() == 1
        if name in ('index', 'mobile'):
            selector = '.hero-cta-group > .mk-pop-item' if name == 'index' else '.mobile-hero-actions > .mk-pop-item'
            buttons = page.locator(selector)
            assert buttons.count() == 2, name
            assert page.locator('.mk-pop-item').count() == 2, name
            delays = buttons.evaluate_all('(es)=>es.map(e=>getComputedStyle(e).transitionDelay)')
            first_delays = [float(v.split(',')[0].strip().rstrip('s')) for v in delays]
            if not all(abs(actual - expected) < 0.01 for actual,expected in zip(first_delays, [0, 0.1])):
                print('CTA_DELAY_DEBUG', name, buttons.evaluate_all('''(es)=>es.map((e,i)=>({i,selector:e.matches('.hero-cta-group > .mk-pop-item:nth-child(2)'),style:e.getAttribute('style'),className:e.className,delay:getComputedStyle(e).transitionDelay,sheet:[...document.styleSheets].some(s=>s.href?.includes('mk-inspired.css'))}))'''), flush=True)
            assert all(abs(actual - expected) < 0.01 for actual,expected in zip(first_delays, [0, 0.1])), (name, delays)
            assert buttons.last.evaluate('(e)=>e.tagName.toLowerCase()') == 'a', name
        if name in ('index', 'mobile'):
            # Work history is never a disclosure: exact list content matches
            # no-JS markup, and each existing row uses the one-time fade.
            cards = page.locator('#career .career-entry-card, #career .timeline-job-card')
            assert cards.count() == 3
            expect(page.locator('#career .portfolio-disclosure-toggle, #career .portfolio-disclosure-panel')).to_have_count(0)
            duties = page.locator('#career .duty-bullet-list > li, #career .duty-list > li')
            assert duties.count() > 3
            assert duties.evaluate_all('(rows)=>rows.every(r=>getComputedStyle(r).color==="rgb(73, 54, 62)")'), ('career body color',name)
            assert duties.locator('strong').evaluate_all('(labels)=>labels.length>0 && labels.every(e=>getComputedStyle(e).color==="rgb(87, 49, 63)")'), ('career label color',name)
            assert duties.evaluate_all('(rows)=>rows.every(r=>r.matches(".mk-motion-item.mk-fade-item") && !r.closest("[inert], [aria-hidden=true]"))')
            plain = browser.new_page(java_script_enabled=False, viewport={'width':390 if mobile else 1440,'height':844})
            plain.route('https://**/*', lambda route: route.abort())
            plain.goto(url)
            original = plain.locator('#career .duty-bullet-list > li, #career .duty-list > li').all_text_contents()
            assert duties.all_text_contents() == original, ('career wording/order',name)
            plain.close()
            # Later rows reveal when scrolled into view, stay revealed, and
            # remain accessible without the user clicking any toggle.
            row = duties.last
            expect(row).to_have_class(re.compile('.*mk-motion-pending.*'))
            row.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
            expect(row).to_have_class(re.compile('.*mk-motion-in.*'))
            expect(row).to_have_css('opacity','1',timeout=3500)
            assert row.evaluate('e=>!e.closest("[inert],[aria-hidden=true]")')
            page.evaluate('scrollTo({top:0,behavior:"instant"})')
            expect(row).to_have_class(re.compile('.*mk-motion-in.*'))
            # Reload for the existing independent pending/reveal checks below.
            page.goto(url)
            page.wait_for_timeout(800)
            items = page.locator('.mk-motion-item,.mk-pop-item')
        if name == 'mobile':
            assert page.locator('.timeline-job-card.mk-motion-item').count() == 3
            assert page.locator('.mobile-case-box.mk-motion-item').count() == 3
        # Confirm restrained chapter slide, card fade, and action pop geometry.
        chapter_durations = page.locator('.mk-motion-item:not(.mk-fade-item)').evaluate_all('(es)=>es.map(e=>getComputedStyle(e).transitionDuration)')
        fade_durations = page.locator('.mk-motion-item.mk-fade-item').evaluate_all('(es)=>es.map(e=>getComputedStyle(e).transitionDuration)')
        assert chapter_durations and all(abs(float(d.split(",")[0].strip().rstrip("s")) - .88) < .02 for d in chapter_durations), (name, chapter_durations)
        assert fade_durations and all(abs(float(d.split(",")[0].strip().rstrip("s")) - .68) < .02 for d in fade_durations), (name, fade_durations)
        for selector, kind in (('.mk-motion-pending:not(.mk-fade-item)', 'slide'), ('.mk-motion-pending.mk-fade-item', 'fade'), ('.mk-pop-pending', 'pop')):
            item = page.locator(selector).last
            if item.count():
                # Observer callbacks can reveal this target between locator resolution
                # and style sampling. Held-observer coverage above proves the exact
                # pending pose independently; accept either stable lifecycle state here.
                item.evaluate("(e)=>Promise.all(e.getAnimations().filter(a=>a.effect?.getComputedTiming().iterations !== Infinity).map(a=>a.finished.catch(()=>{})))")
                if not item.count():
                    continue
                state = item.evaluate('(e)=>{const s=getComputedStyle(e); const m=new DOMMatrix(s.transform);return {opacity:s.opacity,x:m.m41,scale:m.a}}')
                assert state['opacity'] == '0', (name, state)
                assert (state['x'] < 0 if kind == 'slide' else abs(state['x']) < .01 if kind == 'fade' else state['x'] > 0 and state['scale'] < 1), (name, state)
        # A mere 25 px glimpse at the fold must not reveal a section.
        probe = page.locator('.mk-motion-item').last
        probe.evaluate('(e)=>scrollTo({top:scrollY+e.getBoundingClientRect().top-innerHeight+25,behavior:"instant"})')
        page.wait_for_timeout(100)
        assert probe.evaluate('(e)=>e.classList.contains("mk-motion-pending")'), name
        # Center each unit; every visible unit must reveal and remain visible.
        for item in items.all():
            item.evaluate('''(e)=>{
              e.scrollIntoView({block:"center",behavior:"instant"});
              const r=e.getBoundingClientRect();
              const h=document.documentElement.clientHeight||innerHeight;
              const bottom=h-Math.min(48,Math.max(20,h*0.06));
              // CSS scroll-padding-top may center a nearly screen-height
              // block below the usable viewport. Finish the physical scroll.
              if(r.height<=bottom){
                if(r.bottom>bottom)scrollBy({top:r.bottom-bottom+3,behavior:"instant"});
                else if(r.top<0)scrollBy({top:r.top-3,behavior:"instant"});
              }
              dispatchEvent(new Event("scroll"));
            }''')
            try:
                expect(item).not_to_have_class(re.compile('.*(?:mk-motion-pending|mk-pop-pending).*'))
            except AssertionError:
                print('Reveal position:', name, item.evaluate('(e)=>({cls:e.className,rect:e.getBoundingClientRect().toJSON(),y:scrollY,vh:innerHeight,scrollHeight:document.documentElement.scrollHeight})'))
                raise
        # Resolve all finite 1.4s transitions together rather than serially
        # waiting for each card on six pages.
        page.wait_for_timeout(1750)
        for item in items.all():
            expect(item).to_have_css('opacity', '1')
        # Chart regression: preserve the original percentages and shared rose
        # palette; each chart finishes its entrance and stays filled on revisit.
        chart_specs = {
            'index': [('#research .data-bars-container', [47.7, 21.4, 13.7, 7.3, 7.0])],
            'mobile': [('#research .portfolio-chart', [47.7, 21.4, 13.7, 7.3, 7.0])],
        }
        for chart_selector, values in chart_specs.get(name, []):
            chart = page.locator(chart_selector)
            expect(chart).to_have_count(1)
            expect(chart).to_have_class(re.compile(r'.*portfolio-chart.*'))
            bars = chart.locator('.portfolio-bar')
            expect(bars).to_have_count(len(values))
            chart.evaluate('(e)=>{e.scrollIntoView({block:"center",behavior:"instant"});dispatchEvent(new Event("scroll"))}')
            expect(chart).to_have_class(re.compile(r'.*portfolio-chart-active.*'))
            for i, value in enumerate(values):
                bar = bars.nth(i)
                expect(bar).to_have_css('transform', 'matrix(1, 0, 0, 1, 0, 0)', timeout=6500)
                info = bar.evaluate('''e=>({width:parseFloat(e.style.width),
                    ratio:100*e.getBoundingClientRect().width/e.parentElement.getBoundingClientRect().width,
                    gradient:getComputedStyle(e).backgroundImage,
                    delay:e.style.getPropertyValue("--portfolio-bar-delay")})''')
                assert abs(info['width']-value)<.01 and abs(info['ratio']-value)<1, (name, chart_selector, value, info)
                palettes = [('rgb(239, 179, 199)', 'rgb(198, 138, 161)')]
                assert any(all(color in info['gradient'] for color in palette) for palette in palettes), (name, info)
                assert info['delay']==str(i*250)+'ms', (name, info)
            page.evaluate('scrollTo({top:0,behavior:"instant"})')
            chart.evaluate('(e)=>{e.scrollIntoView({block:"center",behavior:"instant"});dispatchEvent(new Event("scroll"))}')
            expect(chart).to_have_class(re.compile(r'.*portfolio-chart-active.*'))
            for bar in bars.all():
                expect(bar).to_have_css('transform', 'matrix(1, 0, 0, 1, 0, 0)')
            print('CHART_REGRESSION_PASS', name, chart_selector, values, flush=True)
        inline_chart_specs = {
            'trend': [('.inline-research-viz--mix', [47.7, 21.4, 13.7, 7.3, 7.0, 2.9]),
                      ('.inline-research-viz--channels', [45.2, 42.5, 28.7, 24.4])],
            'mobile-trend': [('.inline-research-viz--mix', [47.7, 21.4, 13.7, 7.3, 7.0, 2.9]),
                             ('.inline-research-viz--channels', [45.2, 42.5, 28.7, 24.4])],
        }
        for chart_selector, values in inline_chart_specs.get(name, []):
            chart=page.locator(chart_selector)
            expect(chart).to_have_count(1)
            chart.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
            if chart_selector.endswith('--mix'):
                segments=chart.locator('.inline-research-viz__stack > span')
                expect(segments).to_have_count(len(values))
                shares=segments.evaluate_all('(els)=>els.map(e=>parseFloat(e.style.getPropertyValue("--share")))')
                legend=chart.locator('.inline-research-viz__legend b').all_text_contents()
                legend_values=[float(v.rstrip("%")) for v in legend]
                assert all(abs(a-b)<.01 for a,b in zip(shares,values)), (name,chart_selector,shares)
                assert all(abs(a-b)<.01 for a,b in zip(legend_values,values)), (name,chart_selector,legend_values)
                assert abs(sum(shares)-100)<.01, (name,shares)
            else:
                rows=chart.locator('.inline-research-viz__rows > li')
                expect(rows).to_have_count(len(values))
                labels=rows.locator('b').all_text_contents()
                actual=[float(v.rstrip("%")) for v in labels]
                scales=rows.locator('.inline-research-viz__track > i').evaluate_all('(els)=>els.map(e=>parseFloat(e.style.getPropertyValue("--value")))')
                assert all(abs(a-b)<.01 for a,b in zip(actual,values)), (name,chart_selector,actual)
                assert all(abs(a-b/50*100)<.15 for a,b in zip(scales,values)), (name,chart_selector,scales)
            print('INLINE_CHART_REGRESSION_PASS',name,chart_selector,values,flush=True)
        # Revisit every item from the bottom: no target is concealed or replayed.
        for item in reversed(items.all()):
            item.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
        page.wait_for_timeout(800)
        assert page.locator('.mk-motion-pending,.mk-pop-pending').count() == 0
        assert page.locator('.mk-motion-in,.mk-pop-in').count() == items.count()
        rows.append({'page': name, 'revealedOnce': items.count(), 'contactPops': page.locator('.mk-pop-in').count()})
        # Focus into an offscreen pending unit must reveal all ancestors.
        page.goto(url)
        focus = page.locator('main summary').last if name in ('trend', 'mobile-trend') else page.locator('main a, main button').last
        focus.evaluate('(e)=>e.focus({preventScroll:true})')
        assert focus.evaluate('(e)=>!e.closest(".mk-motion-pending,.mk-pop-pending")')
        # Direct and changed hashes expose descendant targets and their ancestors.
        anchor = 'emailText' if 'contact' in name else ('career' if name in ('index', 'mobile') else 'market')
        page.goto(url + '#' + anchor)
        assert page.locator('#' + anchor).evaluate('(e)=>!e.closest(".mk-motion-pending,.mk-pop-pending")')
        page.goto(url + '#%E0%A4%A')
        page.evaluate('(id)=>{location.hash=id}', anchor)
        page.wait_for_timeout(100)
        assert page.locator('#' + anchor).evaluate('(e)=>!e.closest(".mk-motion-pending,.mk-pop-pending")')
        page.emulate_media(media='print')
        for item in page.locator('.mk-motion-item,.mk-pop-item').all():
            expect(item).to_have_css('opacity', '1')
            expect(item).to_have_css('transform', 'none')
        page.close()
        for mode in ('no-js', 'no-observer', 'observer-throws', 'observe-throws', 'reduced', 'runtime-reduced'):
            page = browser.new_page(viewport={'width':390 if mobile else 1440,'height':844}, java_script_enabled=mode!='no-js', reduced_motion='reduce' if mode=='reduced' else 'no-preference')
            page.route('https://**/*', lambda r: r.abort())
            if mode == 'no-observer': page.add_init_script('delete window.IntersectionObserver')
            if mode == 'observer-throws': page.add_init_script('window.IntersectionObserver=class {constructor(){throw Error("test")}}')
            if mode == 'observe-throws': page.add_init_script('window.IntersectionObserver=class {observe(){throw Error("test")} disconnect(){}}')
            page.goto(url)
            if mode == 'runtime-reduced': page.emulate_media(reduced_motion='reduce')
            expect(page.locator('.mk-motion-pending,.mk-pop-pending')).to_have_count(0)
            for item in page.locator('main > section, main .method-card').all():
                expect(item).to_have_css('opacity', '1')
            page.close()
    browser.close()
server.shutdown()
print(json.dumps(rows, indent=2))
print('Six pages: one-time scrolling, contact pops, focus, hashes, print and fallbacks passed.')
