# CHART 01-A / 01-B validation

Date: 2026-11-08 (Asia/Taipei)
Base: `7a6affd88dd80273be6138f2c89192db6c494073` (`origin/main`).
Open PR inspection: #16 changes only pending work-photo CSS and source-review documentation; no overlap.

## Changes

- `trend.html`, `mobile-trend.html`: identical 45.2% / 42.5% metric cards; four channel rows with full names, visible percentages and a 0–100% scale; three concise summary cards. Original analysis and source text retained in each page.
- `assets/trend-charts.css`: shared magazine styling, fixed-layout horizontal bars, visible keyboard focus, responsive cards and category label wrapping. The 01-B SVG scales to 280px on desktop / 240px on narrow screens, with original circles, colors and percentages unchanged.
- `assets/trend-charts.js`: one-time IntersectionObserver animation (650–750ms), transform/opacity only; no persistent hidden state. Reduced motion, missing/failed observer, preference changes and printing restore full content. Existing section reveal, marquee and router code untouched; child chart animations use their own classes and properties.
- `_qa/trend-charts.test.cjs`: observer fallback, completion and live reduced-motion regression tests.
- `_qa/trend-charts.browser.cjs`: real Chromium data, geometry, responsiveness and interaction checks.

01-A remains a multiple-response sample selection survey; no normalization, pie chart or market-share inference. 01-B remains the original category sales structure. The original per-page wording and per-page category colors are preserved.

## Automated and browser results

- `node --test _qa/*.test.cjs`: **25/25 passed**, including all 22 existing router/marquee tests.
- `node _qa/trend-charts.browser.cjs`: **passed** for both pages at 320, 375, 768 and 1440px. Requires Playwright and Chromium; serve repository at `http://127.0.0.1:8000` first. Test uses `/usr/bin/chromium`; adapt executable path for another environment.
- Four exact values and card consistency; rendered fill widths match percentages against full 100% tracks.
- All original SVG circle markup identical to main; all original paragraph text and everything after these chart sections identical to main.
- No document horizontal overflow at any tested width; full names wrap without truncation.
- Four bar entrance animations observed on first viewport entry; none on scroll away/back. Touch interaction and visible keyboard focus passed.
- JavaScript disabled, reduced motion at startup, live reduced-motion changes, and missing/failed observer scenarios passed.
- Existing viewport tags retain browser zoom support; no `user-scalable=no` or maximum scale restrictions added. Touch emulation used; no physical-device pinch gesture test was performed.
- axe-core scan of `.channel-study` and `.category-study`: **0 violations** on both pages, evaluated after transitions with reduced motion to avoid measuring transitional opacity. This is automated checking, not a complete manual screen-reader audit.
- Desktop and mobile screenshots visually inspected for 01-A and 01-B: readable labels, balanced donut/legend, responsive card stacking. Actual SVG geometry is preserved.
- `git diff --check`: passed.

## Lighthouse

Local HTTP server, system Chromium, Lighthouse default mobile throttling and desktop preset. Explicit `view` query selects each existing page. Final measurements ran separately after concurrent browser checks ended.

| Page | Performance | Accessibility | Best practices | SEO | CLS |
| --- | ---: | ---: | ---: | ---: | ---: |
| Desktop main baseline | 100 | 100 | 96 | 100 | 0 |
| Desktop modified | 100 | 100 | 96 | 100 | 0 |
| Mobile main baseline | 99 | 100 | 96 | 66 | 0 |
| Mobile modified | 99 | 100 | 96 | 66 | 0 |

Initial concurrent runs scored 98 desktop / 84 mobile for performance; isolated reruns match baseline. Scores describe this local test environment, not a production deployment.

## Remaining limits and merge decision

- **Mobile SEO 66 is below the requested minimum 80**, caused by its existing `<meta name="robots" content="noindex,follow">`. Preserved because changing indexing policy is outside the chart scope. All other requested Lighthouse categories exceed 80.
- Best practices 96 on baseline and modified pages: Chromium reports `ERR_CERT_AUTHORITY_INVALID` for an existing external resource in this test environment. TLS verification was not disabled.
- No existing automated test regressions or isolated Lighthouse score regressions observed.
- Ready for code/visual review; the strict all-four-categories ≥80 acceptance condition remains unmet until the existing mobile indexing policy is explicitly resolved or accepted as an exception.
- No merge or production deployment performed. Merge/deployment decision remains with the repository owner.
