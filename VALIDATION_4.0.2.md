# Beta 4.0.2 validation

- 67 Python unittest checks passed with the pinned requirements installed, including duration tails, grouped roles, false employer prevention, incomplete records, school/program distinctions, URL boundaries, actual DOCX spacing, word preservation and all three template round trips.
- 12 React/jsdom editing-flow checks passed against the real FastAPI TestClient, including a failed DOCX spacing check blocking download even after approval.
- Production TypeScript/Vite build and ESLint passed.
- The supplied PDF was parsed with the pinned dependencies: 100/100, seven job records, four education records and zero unassigned experience. Fresh Classic, Modern and Compact exports all reparsed at 100/100, with approved word preservation, six correctly spaced section headings and no review findings.
- Visually inspected rendered exports and refreshed one-page fictional samples in all three styles. The long supplied test is six pages in Compact and seven in Classic/Modern with the added whitespace. Content was preserved rather than condensed.
- Release excludes private resumes, test screenshots, original template references, dependencies, build output and environment files.

Limits: jsdom checks state/API behavior, not actual browser layout. Word/LibreOffice font substitutions and page breaks can differ from the browser preview. No live GitHub/Render deployment or employer ATS benchmark was performed. AI remains removed.
