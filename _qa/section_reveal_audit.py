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
        # Count actual observer entrances, including any accidental re-observation.
        page.add_init_script('''window.revealCounts = new Map();
          const IO = window.IntersectionObserver;
          window.IntersectionObserver = class extends IO {
            constructor(callback, options) { super((entries, observer) => {
              for (const e of entries) if (e.isIntersecting && e.target.matches('.mk-motion-item,.mk-pop-item'))
                revealCounts.set(e.target, (revealCounts.get(e.target) || 0) + 1);
              callback(entries, observer);
            }, options); }
          };''')
        held = browser.new_page(viewport={'width':390 if mobile else 1440,'height':844})
        held.route('https://**/*', lambda r: r.abort())
        held.add_init_script('window.IntersectionObserver=class {observe(){} unobserve(){} disconnect(){}}')
        held.goto(url)
        held.wait_for_timeout(800)
        # Independent coverage contract: page sections, articles, card units and source notes.
        units = held.locator('.mag-header > .container, main section, main article, .key-pillar-card, .hero-action-card, .star-field-box, .stage-meta-box, .candidate-info-box, .candidate-specs-box, .source-verification, main .method-card')
        for unit in units.all():
            assert unit.evaluate('(e)=>e.matches(".mk-motion-pending,.mk-pop-pending")'), (name, unit.get_attribute('class'))
        states = held.locator('.mk-motion-pending,.mk-pop-pending').evaluate_all('(es)=>es.map(e=>({x:new DOMMatrix(getComputedStyle(e).transform).m41,opacity:getComputedStyle(e).opacity}))')
        assert states and all(x['x'] > 0 and x['opacity'] == '0' for x in states), (name, states)
        assert held.evaluate('document.documentElement.scrollWidth<=innerWidth'), name
        held.close()
        page.goto(url)
        page.wait_for_timeout(800)
        # Allow any in-progress CSS transitions to fully settle before asserting
        # pending-state opacity. A section near the top of a shorter page may
        # still be mid-transition after the initial 800 ms budget.
        page.wait_for_function(
            'function(){var el=document.querySelector(".mk-motion-pending,.mk-pop-pending");return !el||+getComputedStyle(el).opacity===0;}',
            timeout=1500
        )
        items = page.locator('.mk-motion-item,.mk-pop-item')
        assert items.count() > 0, name
        if 'contact' in name:
            assert page.locator('.mk-pop-item').count() == 3
        if name == 'mobile':
            assert page.locator('.timeline-job-card.mk-motion-item').count() == 3
            assert page.locator('.mobile-case-box.mk-motion-item').count() == 3
        # Confirm the pending state has the requested direction/scale.
        for selector, kind in (('.mk-motion-pending', 'slide'), ('.mk-pop-pending', 'pop')):
            item = page.locator(selector).last
            if item.count():
                state = item.evaluate('(e)=>{const s=getComputedStyle(e); const m=new DOMMatrix(s.transform);return {opacity:s.opacity,x:m.m41,scale:m.a}}')
                assert state['opacity'] == '0', (name, state)
                assert state['x'] > 0 and (kind == 'slide' or state['scale'] < 1), (name, state)
        for item in items.all():
            item.evaluate('(e)=>scrollTo({top:scrollY+e.getBoundingClientRect().top-180,behavior:"instant"})')
            expect(item).not_to_have_class(re.compile('.*(?:mk-motion-pending|mk-pop-pending).*'))
            expect(item).to_have_css('opacity', '1')
        # Revisit every item from the bottom: no target is concealed or replayed.
        for item in reversed(items.all()):
            item.evaluate('(e)=>scrollTo({top:scrollY+e.getBoundingClientRect().top-180,behavior:"instant"})')
        page.wait_for_timeout(800)
        assert page.locator('.mk-motion-pending,.mk-pop-pending').count() == 0
        assert page.evaluate('Array.from(revealCounts.values()).every(n=>n===1)')
        rows.append({'page': name, 'revealedOnce': items.count(), 'contactPops': page.locator('.mk-pop-in').count()})
        # Focus into an offscreen pending unit must reveal all ancestors.
        page.goto(url)
        focus = page.locator('main a, main button').last
        focus.evaluate('(e)=>e.focus({preventScroll:true})')
        assert focus.evaluate('(e)=>!e.closest(".mk-motion-pending,.mk-pop-pending")')
        # Direct and changed hashes expose descendant targets and their ancestors.
        anchor = 'emailText' if 'contact' in name else ('career' if name in ('index', 'mobile') else 'weaknesses')
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
