# Editorial refinement / 五方向設計規格

Baseline: e7390d19e1d6311bff3783e39bb7146c4c4bbb00. Preserve all résumé facts, photos, original section ordering, print layout, existing navigation and chapter-lock marquee. No invented research or metrics.

## 1. Visual system
Inventory effective CSS across desktop/mobile and research pages, including override layers and generated bundles. Preserve page-specific brand accents. Proposed editorial tokens: warm ivory #F7F5F0, rose heading #57313f, body #49363e; keep existing navy/yellow where brand-specific. Align spacing on 4/8px rhythm, consistent card borders and heading hierarchy; verify contrast rather than replacing all colors blindly.

## 2. Motion
Preserve chapter-lock marquee and work-history reveal (680ms, 80ms stagger capped at 240ms). Harmonize other reveal easing only where justified; no extra motion on scrolling; honor reduced motion, focus and touch. No newly hidden content when JS fails.

## 3. Research presentation
Inventory charts, units, denominators, time periods, citations and evidence quality. Use direct labels, accessible chart alternatives, consistent legends and distinguish observations from recommendations. No data changes without verified primary source; keep original wording and figures otherwise.

## 4. Responsive reading
Compare desktop, tablet and mobile layouts; tune prose measure, padding, chart overflow and touch targets as warranted. Preserve routing and navigation order, ensure keyboard focus visible and no horizontal page overflow. Maintain print output.

## 5. Technical maintenance
Inspect build and source/bundle parity, asset loading and existing CI. Only evidence-based changes; preserve security checks, no blind Lighthouse chasing. Audit image reuse rights and CSP as unresolved unless verified. Avoid unrelated refactor.

## Acceptance and release
Work on this isolated branch. Inspect current baseline before editing; use minimal reviewed diffs and expected SHA for writes. Keep existing test assertions; target changed functionality and rely on existing workflow results for unchanged tests, do not manually rerun successful jobs. Check relevant source/bundle parity, responsive layout, motion, accessibility, print and research content integrity. Record limitations of automated checks. Open PR for review; do not merge or deploy until release authorization is explicit for this refinement. Stop on unexpected competing changes. No public deployment from this planning document alone.
