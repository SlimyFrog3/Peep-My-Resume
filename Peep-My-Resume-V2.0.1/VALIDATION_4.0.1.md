# Beta 4.0.1 validation

Completed:
- 53 Python tests, covering the earlier parser/API regressions and new template choices, muted-green settings, word preservation, exact section/entry order, placement decisions, exclusions, invalid input, score boundaries and observed strengths.
- React editing-flow integration checks in jsdom, calling the real Python FastAPI TestClient: style selection, section moves, entry moves, pending placement blocking download, explicit keep, approval, exact-preview download, invalidation on style change, no AI calls, yellow 98 explanation and red 54.
- Production TypeScript/Vite build and ESLint.
- Rendered and visually inspected short and two-page long fictional resumes in all three styles.
- The release archive excludes private resumes, original template references, environment files, dependencies and build output.

Limit:
- Chromium could not start in this environment. jsdom verifies DOM/state/API behavior, not actual browser layout, hover placement or native dialog rendering. Complete the desktop/mobile acceptance steps in REDEPLOY.md.
- No live GitHub/Render deployment was performed.
- Fonts and exact page breaks can differ between Word, LibreOffice and a browser preview.
- No employer ATS benchmarking or AI testing is included; AI code has been removed.
