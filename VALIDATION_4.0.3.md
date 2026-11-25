# Beta 4.0.3 validation

- 86 Python unittest checks passed with pinned requirements, covering source-backed assignments, stale fields, full-name styling, education associations, adjacent education pairs, certification fragmentation, swapped descriptions, employer-group reordering, intentional exclusions, guarded API exports and score regression.
- 16 React/jsdom integration checks passed against the real FastAPI TestClient. New flows cover name/education repairs, field assignment/refresh and record failure blocking download after approval.
- TypeScript/Vite production build and ESLint passed.
- 30 document/template round trips passed export quality checks: supplied Aakash and Abdul PDFs plus eight bundled sample PDFs/DOCXs, each in all three styles. Existing low-score examples retain their honest scores rather than receiving a template bonus.
- Aakash: original and all generated styles score 100, three certifications are preserved and 14 structured entries are checked. Full-name title and degree/institution association are preserved.
- Rendered DOCXs were inspected in all three styles. Refreshed fictional samples/thumbnails are included; private resume files and diagnostic exports are excluded from the release.

Limits: these are local parser checks, not employer ATS benchmarks. jsdom tests DOM/state/API behavior rather than actual browser layout. Word/LibreOffice page breaks and fonts can differ. No live GitHub/Render deployment was performed. Source-backed field detection still has limits and unknown content requires review. AI and PDF export remain deferred.
