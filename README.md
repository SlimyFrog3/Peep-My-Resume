# Peep-My-Resume V2.0.1

A simple React/TypeScript frontend and Python/FastAPI resume parser. Choose a text-based PDF or DOCX and analysis starts immediately. Results show detected sections and the extracted text so you can compare against the original. Real parsing is the default; no AI API or database is used.

See **PATCH_NOTES_V2.md** for changes and limitations, and **REDEPLOY.md** to update your existing Render service.

## Local setup in VS Code (Windows)

Use Python 3.12 and Node.js 22.12 or newer. Open the folder containing `package.json` and `requirements.txt`.

Terminal 1:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
npm ci
npm run dev
```

Open the Local URL Vite prints, usually http://localhost:5173. Keep both terminals running. On macOS/Linux use `python3` and `.venv/bin/python`. No `.env` file is required. Remove old `.env.local` settings if you unintentionally see sample results; `VITE_USE_MOCK=true` explicitly enables demo mode.

## How it connects

1. `ResumeUploader` validates the selected file and passes it to `App`.
2. `App` starts the request immediately. It cancels the previous browser request and uses a request number so stale responses cannot replace a newer upload.
3. `parserApi.ts` sends the file as multipart `FormData` to `/parse`. Vite proxies the request to Python during development. The client allows 90 seconds for a response.
4. FastAPI reads a bounded upload and runs the parser in a worker thread. It closes the upload after processing.
5. `pdfplumber` extracts PDF text. The custom layout helper attempts a column split only with headings on both sides and a clear gutter. `python-docx` reads paragraphs and table cells in body order.
6. The grouping layer matches explicit heading aliases and inline labels. Email, phone, and link patterns find explicit contact details. Unknown content remains in Other / Unclassified. No missing content is invented.
7. JSON returns arrays for 13 categories, plus `extractedText` and `warnings`. React renders populated categories and lists the categories not detected. "Not detected" does not prove a section is missing.

## Where to edit

| File | Purpose |
|---|---|
| `backend/parser.py` | Extraction, column heuristic, headings, grouping, warnings |
| `backend/main.py` | Upload endpoint, health, built frontend serving |
| `src/types/ParseResult.ts` | Category keys and display titles |
| `src/services/parserApi.ts` | Request, cancellation, timeout, JSON validation |
| `src/App.tsx` | Selection, automatic processing, result/error state |
| `src/components/ResumeUploader.tsx` | Browse/drop UI and file validation |
| `src/components/ParseResults.tsx` | Cards, not-detected list, warnings, raw text |
| `src/App.css` / `src/index.css` | Layout and light-theme palette |
| `public/eye-logo.svg` | Replaceable eye logo |
| `Dockerfile` / `render.yaml` | Existing single-host Render deployment |

To add a category, update the backend headings, frontend sections list, and sample result together. To personalize the colors, edit the palette variables near the bottom of App.css. Major UI elements remain separate components; no new frontend library was added.

## Checks and test documents

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
npm run build
npm run lint
```

All 21 backend tests, the production build, and lint passed during preparation. `examples/simple.pdf` and `.docx` contain synthetic Jordan Lee data. `two-column.pdf` tests separate columns and page continuation; `right-aligned-dates.pdf` checks dates are not treated as a sidebar. Original real-resume PDF/DOCX files were not supplied, so compare your own results after redeployment.

## Production

The Dockerfile builds React in Node and copies `dist` into the Python image. FastAPI serves both the page and `/parse` on one HTTPS origin. There is no separate frontend deployment or CORS setup. Keep Docker runtime and `/health` health check on Render. Docker itself was not available for an image build during preparation; verify Render build logs.

## Limits and privacy

- Text-based documents only; no OCR for scans/images.
- Heading rules and column heuristics can misread complex layouts. Contact is still a candidate block rather than validated name/location fields.
- Job and education contents are grouped lines, not fully structured records.
- Limits: 10 MB upload, 20 PDF pages, 200,000 extracted characters, 40 MB expanded DOCX.
- Application code does not save uploads. The framework may spool them temporarily and closes them after each request. No external AI call is made.
- Browser cancellation prevents stale display; backend work may finish even after cancellation.

## Licensing

The existing pdfplumber and python-docx readers are MIT licensed; their dependency notices remain in `THIRD_PARTY_NOTICES.txt` and are copied into the Docker image. Preserve these notices and review the exact distributed dependency set. The owner decides the distribution license for custom project code.

Browser interaction and visual checks could not be completed because the preparation environment could not download a browser. Verify automatic analysis, file replacement/retry, and phone layout after deployment.

## V2.0.1 maintenance update

See PATCH_NOTES_V2.0.1.md for the PDF page-boundary fix, layout fallback, and more accurate errors. The supplied Aakash PDF now returns HTTP 200 and 13,342 extracted characters in a local API test; it is not included in this package because it contains personal information. ATS_TIPS_PLAN.md describes possible future formatting tips; that feature is not implemented.
