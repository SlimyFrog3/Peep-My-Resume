# Beta 4 validation

Completed locally during release preparation:

- 42 Python tests passed: prior API/layout regressions plus spacing without literal spaces, heading/contact boundaries, page furniture, wrapped/ongoing jobs, education, Word text boxes, score behavior, actual DOCX round trip, word preservation, invalid review input and optional AI consent/source checks.
- Frontend TypeScript/Vite production build and ESLint passed.
- The locally attached Alex, Aakash, Naveen and Kamal documents were parsed and passed through the actual DOCX export/reparse pipeline. Approved word preservation passed in those checks. These are regression examples, not a claim that every field is correct. They are not shipped in the ZIP.
- The single-column DOCX template was rendered to a page image and visually inspected.
- OpenAI request/response wiring was tested with a mocked provider. No live paid API call was made.

Not completed here:

- Interactive desktop/mobile browser testing. Chromium could not start because this environment disallows its process singleton socket. Complete the browser acceptance steps in REDEPLOY.md after deployment.
- Live Render deployment and paid AI testing. These require your repository deployment and optional provider credentials.
- A benchmark against external employer ATS products.

Known behavior: scores need not improve after reformatting, even when the new copy is simpler. Missing or ambiguous facts still need user correction. The word-count check cannot certify factual accuracy.
