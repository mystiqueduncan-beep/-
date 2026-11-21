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
        # The new editorial chapters intentionally slide in once; a held
        # observer may leave OFFSCREEN sections pending. Source text still
        # exists and above-fold content must never start blank.
        held = browser.new_page(viewport={'width':390 if mobile else 1440,'height':844})
        held.route('https://**/*', lambda r: r.abort())
        held.add_init_script('window.IntersectionObserver=class {observe(){} unobserve(){} disconnect(){}}; window.requestAnimationFrame=()=>0')
        held.goto(url)
        held.wait_for_timeout(350)
        units = held.locator('main section, main article, main .editorial-card, main .feature-card, main .method-card')
        readable = units.evaluate_all('''els=>els.filter(e=>!e.closest('[hidden],[aria-hidden="true"]') && !e.matches('.mobile-cover'))
            .map(e=>({opacity:getComputedStyle(e).opacity,
                 onscreen:e.getBoundingClientRect().top<innerHeight*.72 && e.getBoundingClientRect().bottom>0}))''')
        assert readable and all(float(unit['opacity']) > .99
                                for unit in readable if unit['onscreen']), (name, readable[:12])
        hero = held.locator('.mag-header > .container.mk-motion-pending, main .mobile-cover.mk-motion-pending')
        if hero.count():
            assert hero.first.evaluate('(e)=>+getComputedStyle(e).opacity<.1'), name
        assert held.evaluate('document.documentElement.scrollWidth<=innerWidth'), name
        held.close()

        page.goto(url)
        page.wait_for_timeout(550)
        items = page.locator('.mk-motion-item,.mk-pop-item')
        assert items.count() > 0, name
        # Only viewport-visible content must be immediately readable.
        # Below-fold content can animate once when reached.
        visible = page.locator('main section, main .editorial-card, main .feature-card').evaluate_all(
            '''els=>els.filter(e=>!e.closest('[hidden],[aria-hidden="true"]') &&
               !e.matches('.mobile-cover') && e.getBoundingClientRect().top<innerHeight*.7 &&
               e.getBoundingClientRect().bottom>0)
               .every(e=>+getComputedStyle(e).opacity>.99)''')
        assert visible, ('onscreen narrative visible', name)
        assert page.locator('html').evaluate('(e)=>e.classList.contains("magazine-motion-ready")'),name
        assert page.locator('.tri-type-pending,.tri-type-active').evaluate_all(
            '''els=>els.every(e=>getComputedStyle(e).clipPath==='none')'''), ('instant multilingual headings',name)
        # Consistent presentation contract across all six portfolio pages:
        # no decorative 01/02 round badges in primary chapter headings.
        numbered_heading_tokens = page.locator(
            '.section-editorial-header .sec-number, '
            '.tri-heading-primary > .sec-number, '
            'h2.bilingual-mobile-heading .sec-number, '
            'h2.mobile-card-title .ui-code, '
            '#education-title .sec-number'
        )
        assert numbered_heading_tokens.evaluate_all(
            '''els=>els.every(e=>getComputedStyle(e).display==='none')'''), ('numbered heading badge visible',name)
        if name in ('trend','mobile-trend'):
            assert page.locator('.trend-hero .research-edition').inner_text().strip()=='RESEARCH EDITION',name
        if name in ('trend','mobile-trend'):
            # Six unnumbered research sections: the hero and five quiet
            # bilingual divider labels keep their semantic contents.
            parts = page.locator('.trend-main .research-part')
            expect(parts).to_have_count(5)
            labels = parts.locator('.research-part-label').all_text_contents()
            assert labels == [
                'EXECUTIVE SUMMARY',
                'INDUSTRY TRENDS',
                'MARKET ANALYSIS',
                'REGIONAL STRATEGY',
                'EVIDENCE & LIMITS'
            ], (name, labels)
            assert page.locator('.trend-main .research-part .research-part-no').evaluate_all(
                '''els=>els.every(e=>getComputedStyle(e).display==='none')'''), name
            assert page.locator('.trend-main .research-part:not(.research-part--inside) .research-part-title').evaluate_all(
                '''els=>els.every(e=>getComputedStyle(e).display==='none')'''), name
            part_three = page.locator('.trend-main .research-part--inside .research-part-title')
            expect(part_three).to_have_count(1)
            expect(part_three).to_be_visible()
            assert part_three.inner_text() == '產業趨勢', name
            headings = page.locator('.trend-main .section-editorial-header h2.sec-title-main')
            expect(headings).to_have_count(11)
            assert headings.locator('.tri-heading-primary').count() == 0
            assert page.locator('.trend-main .section-editorial-header .sec-number').evaluate_all(
                '''els=>els.every(e=>getComputedStyle(e).display==='none')'''), name
            assert page.locator('.trend-main .section-editorial-header .tri-subtitle-line').count() == 11, name
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'), name
            print('RESEARCH_HEADING_HIERARCHY_PASS',name,labels,flush=True)
        if 'contact' in name:
            assert page.locator('.mk-pop-item').count() == 4, name
            assert page.locator('.method-card--print.mk-pop-item').count() == 1, name
        if name in ('index','mobile'):
            training = page.locator('#cases .magazine-training-flow')
            expect(training).to_have_count(1)
            assert training.locator('ol > li').all_text_contents()==['重點觀摩','步驟演練','陪同操作'],name
            selector = '.hero-cta-group > .mk-pop-item' if name == 'index' else '.mobile-hero-actions > .mk-pop-item'
            assert page.locator(selector).count() == 2, name
            cards = page.locator('#career .career-entry-card, #career .timeline-job-card')
            expect(cards).to_have_count(3)
            expect(page.locator('#career .portfolio-disclosure-toggle, #career .portfolio-disclosure-panel')).to_have_count(0)
            duties = page.locator('#career .duty-bullet-list > li, #career .duty-list > li')
            assert duties.count() > 3
            assert duties.evaluate_all('(rows)=>rows.every(r=>getComputedStyle(r).color==="rgb(73, 54, 62)")'), ('career copy',name)
            plain = browser.new_page(java_script_enabled=False, viewport={'width':390 if mobile else 1440,'height':844})
            plain.route('https://**/*', lambda route: route.abort())
            plain.goto(url)
            assert duties.all_text_contents()==plain.locator('#career .duty-bullet-list > li, #career .duty-list > li').all_text_contents(), ('career facts unchanged',name)
            plain.close()
        if name == 'mobile':
            assert page.locator('.timeline-job-card.mk-motion-item').count() == 3
            assert page.locator('.mobile-case-box.mk-motion-item').count() == 3
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
                    color:getComputedStyle(e).backgroundColor,
                    delay:e.style.getPropertyValue("--portfolio-bar-delay")})''')
                assert abs(info['width']-value)<.01 and abs(info['ratio']-value)<1, (name, chart_selector, value, info)
                colors = ['rgb(189, 130, 148)', 'rgb(233, 200, 95)',
                          'rgb(135, 168, 189)', 'rgb(156, 172, 146)', 'rgb(161, 141, 177)']
                assert info['color']==colors[i], (name, i, info)
                assert info['delay']==str(i*110)+'ms', (name, info)
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
                expect(chart).to_have_class(re.compile(r'.*magazine-mix-played.*'),timeout=5000)
            else:
                chart_rows=chart.locator('.inline-research-viz__rows > li')
                expect(chart_rows).to_have_count(len(values))
                labels=chart_rows.locator('b').all_text_contents()
                actual=[float(v.rstrip("%")) for v in labels]
                scales=chart_rows.locator('.inline-research-viz__track > i').evaluate_all('(els)=>els.map(e=>parseFloat(e.style.getPropertyValue("--value")))')
                assert all(abs(a-b)<.01 for a,b in zip(actual,values)), (name,chart_selector,actual)
                assert all(abs(a-b/50*100)<.15 for a,b in zip(scales,values)), (name,chart_selector,scales)
            if chart_selector.endswith('--channels'):
                # Same muted four colors as the home chart; animate only the
                # progress fill, not the labels or the verified data widths.
                expected_colors=['rgb(189, 130, 148)','rgb(233, 200, 95)',
                                 'rgb(135, 168, 189)','rgb(156, 172, 146)']
                progress_bars=chart.locator('.inline-research-viz__track > i')
                assert progress_bars.count()==4, (name,'channel progress count')
                assert progress_bars.evaluate_all('''els=>els.map(e=>getComputedStyle(e).backgroundColor)''')==expected_colors, name
                expect(chart).to_have_class(re.compile(r'.*inline-progress-played.*'),timeout=5000)
                for bar in progress_bars.all():
                    expect(bar).to_have_css('transform','matrix(1, 0, 0, 1, 0, 0)',timeout=5000)
                page.evaluate('scrollTo({top:0,behavior:"instant"})')
                chart.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
                expect(chart).to_have_class(re.compile(r'.*inline-progress-played.*'))
                for bar in progress_bars.all():
                    expect(bar).to_have_css('transform','matrix(1, 0, 0, 1, 0, 0)')
            print('INLINE_CHART_REGRESSION_PASS',name,chart_selector,values,flush=True)
        # Every magazine panel reveals after being scrolled into view, stays
        # revealed on revisit and never requires a repeated animation.
        magazine_panels=page.locator('main .magazine-slide')
        assert magazine_panels.count() >= 1,name
        for panel in magazine_panels.all():
            panel.evaluate('(e)=>e.scrollIntoView({block:"center",behavior:"instant"})')
            expect(panel).to_have_class(re.compile(r'.*magazine-slide-in.*'),timeout=3500)
        page.evaluate('scrollTo({top:0,behavior:"instant"})')
        for panel in magazine_panels.all():
            expect(panel).to_have_class(re.compile(r'.*magazine-slide-in.*'))
        rows.append({'page':name,'magazinePanelsRevealed':magazine_panels.count(),
                     'preservedChartChecks':True,'contactActions':page.locator('.mk-pop-item').count()})
        # Focus into an offscreen pending unit must reveal all ancestors.
        page.goto(url)
        focus = page.locator('main summary').last if name in ('trend', 'mobile-trend') else page.locator('main a, main button').last
        focus.evaluate('(e)=>e.focus({preventScroll:true})')
        assert focus.evaluate('(e)=>!e.closest(".mk-motion-pending,.mk-pop-pending,.magazine-slide-pending")')
        # Direct and changed hashes expose descendant targets and their ancestors.
        anchor = 'emailText' if 'contact' in name else ('career' if name in ('index', 'mobile') else 'market')
        page.goto(url + '#' + anchor)
        assert page.locator('#' + anchor).evaluate('(e)=>!e.closest(".mk-motion-pending,.mk-pop-pending,.magazine-slide-pending")')
        page.goto(url + '#%E0%A4%A')
        page.evaluate('(id)=>{location.hash=id}', anchor)
        page.wait_for_timeout(100)
        assert page.locator('#' + anchor).evaluate('(e)=>!e.closest(".mk-motion-pending,.mk-pop-pending,.magazine-slide-pending")')
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
