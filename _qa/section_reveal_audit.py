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
        # Check the real viewport entrance rather than first-pixel intersections.
        held = browser.new_page(viewport={'width':390 if mobile else 1440,'height':844})
        held.route('https://**/*', lambda r: r.abort())
        held.add_init_script('window.IntersectionObserver=class {observe(){} unobserve(){} disconnect(){}}; window.requestAnimationFrame=()=>0')
        held.goto(url)
        held.wait_for_timeout(800)
        # Slower (1.4s) transitions may still be settling towards the hidden
        # pending pose; verify the final pose, not a mid-transition frame.
        held.wait_for_function(
            '() => [...document.querySelectorAll(".mk-motion-pending,.mk-pop-pending")].every(e => getComputedStyle(e).opacity === "0")',
            timeout=3500,
            polling=100  # Held-page RAF is intentionally disabled.
        )
        # Independent coverage contract: page sections, articles, card units and source notes.
        units = held.locator('.mag-header > .container, main section, main article, .key-pillar-card, .hero-action-card, .star-field-box, .stage-meta-box, .candidate-info-box, .candidate-specs-box, .source-verification, main .method-card')
        for unit in units.all():
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
            assert page.locator('.mk-pop-item').count() == 3
        if name in ('index', 'mobile'):
            selector = '.hero-cta-group > .mk-pop-item' if name == 'index' else '.mobile-hero-actions > .mk-pop-item'
            buttons = page.locator(selector)
            assert buttons.count() == 4, name
            assert page.locator('.mk-pop-item').count() == 4, name
            delays = buttons.evaluate_all('(es)=>es.map(e=>getComputedStyle(e).transitionDelay)')
            first_delays = [float(v.split(',')[0].strip().rstrip('s')) for v in delays]
            if not all(abs(actual - expected) < 0.01 for actual,expected in zip(first_delays, [0, 0.1, 0.2, 0.3])):
                print('CTA_DELAY_DEBUG', name, buttons.evaluate_all('''(es)=>es.map((e,i)=>({i,selector:e.matches('.hero-cta-group > .mk-pop-item:nth-child(2)'),style:e.getAttribute('style'),className:e.className,delay:getComputedStyle(e).transitionDelay,sheet:[...document.styleSheets].some(s=>s.href?.includes('mk-inspired.css'))}))'''), flush=True)
            assert all(abs(actual - expected) < 0.01 for actual,expected in zip(first_delays, [0, 0.1, 0.2, 0.3])), (name, delays)
            assert buttons.last.evaluate('(e)=>e.tagName.toLowerCase()') == 'button', name
        if name == 'mobile':
            assert page.locator('.timeline-job-card.mk-motion-item').count() == 3
            assert page.locator('.mobile-case-box.mk-motion-item').count() == 3
        # Confirm restrained chapter slide, card fade, and action pop geometry.
        chapter_durations = page.locator('.mk-motion-item:not(.mk-fade-item)').evaluate_all('(es)=>es.map(e=>getComputedStyle(e).transitionDuration)')
        fade_durations = page.locator('.mk-motion-item.mk-fade-item').evaluate_all('(es)=>es.map(e=>getComputedStyle(e).transitionDuration)')
        assert chapter_durations and all(abs(float(d.split(",")[0].strip().rstrip("s")) - .58) < .02 for d in chapter_durations), (name, chapter_durations)
        assert fade_durations and all(abs(float(d.split(",")[0].strip().rstrip("s")) - .42) < .02 for d in fade_durations), (name, fade_durations)
        for selector, kind in (('.mk-motion-pending:not(.mk-fade-item)', 'slide'), ('.mk-motion-pending.mk-fade-item', 'fade'), ('.mk-pop-pending', 'pop')):
            item = page.locator(selector).last
            if item.count():
                # Observer callbacks can reveal this target between locator resolution
                # and style sampling. Held-observer coverage above proves the exact
                # pending pose independently; accept either stable lifecycle state here.
                item.evaluate("(e)=>Promise.all(e.getAnimations().map(a=>a.finished.catch(()=>{})))")
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
        # Center each unit to give short elements full visibility and tall ones
        # at least 80% viewport coverage; the animation must then complete.
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
        # Revisit every item from the bottom: no target is concealed or replayed.
        for item in reversed(items.all()):
            item.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
        page.wait_for_timeout(800)
        assert page.locator('.mk-motion-pending,.mk-pop-pending').count() == 0
        assert page.locator('.mk-motion-in,.mk-pop-in').count() == items.count()
        rows.append({'page': name, 'revealedOnce': items.count(), 'contactPops': page.locator('.mk-pop-in').count()})
        # Focus into an offscreen pending unit must reveal all ancestors.
        page.goto(url)
        focus = page.locator('main summary').last if name == 'mobile-trend' else page.locator('main a, main button').last
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
