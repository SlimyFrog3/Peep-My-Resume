# Peep-My-Resume — DeployedV1

A test-ready résumé X-Ray. Upload a text-based PDF or DOCX, click **Analyze résumé**, and see actual extracted text grouped into Contact, Experience, Education, and Skills. Your wording and purple/red/yellow frontend are preserved. This version uses pdfplumber and python-docx, not pyresume or an AI API.

## Start on Windows in VS Code

Install Python 3.10+ (Python 3.12 recommended) and Node.js 22.12+ first. Open **this project folder** in VS Code; it contains both `package.json` and `requirements.txt`.

**Terminal 1 — backend:**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Using the virtual environment's Python directly avoids PowerShell activation-policy problems. Leave this terminal running. If `py` is unavailable, use `python` for the first command.

**Terminal 2 — frontend:**

```powershell
npm install
npm run dev
```

Open the exact **Local** URL printed by Vite, usually http://localhost:5173. Leave both terminals running. No `.env` file is needed for normal local testing. If you copied an old `.env.local`, remove it or set `VITE_USE_MOCK=false` and leave `VITE_API_BASE_URL` empty, then restart Vite.

On macOS/Linux use `python3 -m venv .venv`, then `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`.

## First test

1. Open http://127.0.0.1:8000/health. It should show `status: ok`.
2. In the website choose `examples/simple.pdf` or `examples/simple.docx`.
3. Click **Analyze résumé**. The results should include Jordan Lee, Example Software Inc., Example State University, May 2027, and six skills in a text line.
4. Open **View extracted text**. It should contain the uploaded résumé's text.
5. Upload your own résumé and compare its output with the original. Different files should produce different results.
6. Test an invalid file, a scanned PDF, and missing section headings. The app should show errors or reading notes rather than substitute sample results.

The example files are synthetic and contain no real user's personal information.

## How everything connects

`ResumeUploader` selects a browser File. `App` stores it in React state. Clicking Analyze calls `parseResume(file)` in `src/services/parserApi.ts`.

That function puts the file in `FormData` and sends a multipart HTTP POST to `/parse`. During development, `vite.config.ts` forwards `/parse` to the Python server at port 8000. This keeps the browser on one origin; no separate CORS setup is required in this configuration.

FastAPI receives the upload in `backend/main.py`. It reads up to the 10 MB limit and calls `backend/parser.py` in a worker thread. The parser selects a reader by filename extension and checks the document's format:

- PDF → pdfplumber reads each page's text.
- DOCX → python-docx reads paragraphs and table cells in document body order.

The next step walks the extracted lines. Recognized headings such as **Work Experience**, **Education**, and **Technical Skills** change the current section. Following lines belong to that section until another recognized heading appears. It also supports inline headings such as `Skills: Python, SQL`.

Summary, Projects, Certifications, and other known headings stop the previous section; their contents remain in raw text but are not displayed as one of the four main groups. The opening text before the first heading is shown as a candidate contact block, up to 12 nonblank lines. We do not infer a person's name or invent missing values.

The backend returns JSON matching `src/types/ParseResult.ts`: arrays named `contact`, `experience`, `education`, and `skills`, plus `extractedText` and `warnings`. `App` receives it and `ParseResults` renders it. Loading/error states are controlled by App. The API client times out after 90 seconds and reports backend errors. It never silently falls back to mock data in live mode.

## What we changed to implement version 1

1. Kept your latest frontend and wording; restored its referenced eye-logo image, which was absent from the ZIP.
2. Added the PDF/DOCX text readers and conservative heading rules.
3. Added FastAPI's `/parse` upload route and `/health` check.
4. Switched the API client to real analysis by default and exposed readable backend errors.
5. Added Vite's development proxy so the two local servers communicate.
6. Added reading notes to the results and retained full extracted text for inspection.
7. Added example résumés, backend tests, pinned direct dependencies, and a Dockerfile for a later deployment.

## Files you should understand

| File | Responsibility |
| --- | --- |
| `src/App.tsx` | Workflow state: file, results, loading, errors |
| `src/components/ResumeUploader.tsx` | File selection and Analyze button |
| `src/services/parserApi.ts` | HTTP request and response validation |
| `src/components/ParseResults.tsx` | Results, reading notes, raw text |
| `src/types/ParseResult.ts` | JSON contract between frontend and backend |
| `backend/main.py` | HTTP endpoint and upload lifecycle |
| `backend/parser.py` | Document extraction and section grouping |
| `vite.config.ts` | Local proxy to Python |
| `src/App.css` / `src/index.css` | Theme, layout, background |
| `public/eye-logo.svg` | Replaceable logo |

## Limitations that matter for testing

- **For local development, both servers must run.** The hosted Docker version runs the website and parser together.
- Scanned/image-only PDFs need OCR, which is not included. Empty or unreadable files return a clear error.
- Heading matching uses explicit aliases, not semantic understanding. Unrecognized headings can cause text to remain ungrouped or join the preceding section. Always inspect raw text.
- Two-column PDFs may interleave text. Word headers, footers, text boxes, and nested tables are not supported in this first version.
- Experience/education are grouped lines, not separate structured employer/degree/date records. Skills remain extracted lines rather than inferred proficiency scores.
- Contact is a candidate opening block, not validated personal data.
- Maximum upload: 10 MB; PDF: 20 pages; extracted text: 200,000 characters; DOCX expanded archive: 40 MB.
- Uploads are not saved by application code. FastAPI may temporarily spool uploads, then closes them when the request finishes. There is no database or external AI call.
- This demonstrates our parser's behavior; it does not reproduce every employer's ATS.

## Troubleshooting

**Could not reach parser / request failed:** confirm Terminal 1 is running, check `/health`, and restart Vite after updating configuration. Port 8000 must be free.

**Still shows sample results:** remove an old `.env.local` or set `VITE_USE_MOCK=false`; restart Vite.

**Missing sections:** compare View extracted text to the original. Add a heading alias in `backend/parser.py` if appropriate; don't add fake results.

**Different logo:** replace `public/eye-logo.svg` with your SVG. For PNG, update the path in App.tsx and index.html.

## Checks

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
npm run build
npm run lint
```

Seven backend test methods cover PDF/DOCX uploads, missing headings, section boundaries, corrupted/unsupported/empty uploads, size limits, missing file fields, and health. These passed in the build environment. TypeScript/Vite build and ESLint also passed. A full interactive browser test was not available in that environment, so please do the first-test sequence above locally.

## Deploy to Render

This is the deployment-ready DeployedV1 package. It is not yet hosted: a Render deployment must be created from your GitHub repository before a public URL exists.

### How the hosted version works

Render builds the Dockerfile in two stages. Node builds React into static HTML, CSS, and JavaScript. The Python stage installs the parser dependencies and copies that build into `dist`. One FastAPI service then serves both the website and `/parse`, using Render's assigned `PORT`. Your browser uploads to the same HTTPS host, so you do not need a separate frontend host, CORS setup, or an API URL setting. Your local Python and npm servers can be turned off once deployment succeeds.

### Publish steps

1. Extract this ZIP. Create a GitHub repository and upload the **contents** of DeployedV1 to the repository root. `Dockerfile`, `render.yaml`, `package.json`, and `backend` must be directly at the root. Do not upload `.venv`, `node_modules`, `.env.local`, or your real résumé.
2. Sign into Render and connect that repository. Choose **New → Blueprint**, select the repository and branch, and apply the included `render.yaml`. It defines one free Docker web service named `peep-my-resume`, with `/health` as its health check. Review the selected plan before creating the service.
3. If using **New → Web Service** instead, select the repository, Docker runtime, repository root, and `/health` health-check path. The Dockerfile supplies the startup command; no separate npm start or Python command is needed.
4. Wait for the service to become Live. Open the HTTPS URL shown in the Render dashboard. Render chooses the actual available hostname; this package does not reserve one.
5. Open that URL plus `/health`; it should return `status: ok`. Upload both included example documents, then your own résumé. Compare the results and extracted text. Also test from your phone with your local servers off. This verifies that the hosted parser is doing the work.
6. Future changes pushed to the connected branch can trigger a new deployment. Keep edits in your repository rather than changing files inside the running container.

Free Render services sleep after 15 minutes without traffic; waking can take about a minute. The client allows 90 seconds for an analysis request, but if the first visit/request still fails, wait for the service to wake and retry. Use an always-on plan if you need consistent response times. This release is suitable for your remote parser trial; successful deployment alone does not establish parser accuracy for every résumé layout.

### What changed for DeployedV1

- Preserved your wording and colors, made `My` darker purple and both brand hyphens yellow, and made only `résumé` white in the main tagline.
- Added a Render Blueprint and retained the single-service Docker deployment.
- Included third-party notices in the runtime image.
- Extended the request timeout to accommodate a sleeping free service.
- Kept real parsing as the default and preserved your tested PDF/DOCX extraction and section grouping.

### Optional Docker test

```sh
docker build -t peep-my-resume-deployedv1 .
docker run --rm -p 8000:8000 peep-my-resume-deployedv1
```

Then open http://localhost:8000. Docker is unavailable in the preparation environment, so the container build must be confirmed by Render's build logs or on your own machine. The React production build and same-host FastAPI behavior were checked separately.

Official instructions: https://render.com/docs/docker and https://render.com/docs/blueprint-spec. Free-tier behavior: https://render.com/docs/free.

## Licensing

pdfplumber and python-docx use MIT licenses. MIT permits commercial use while requiring retention of copyright and permission notices. Their dependencies have their own licenses; `THIRD_PARTY_NOTICES.txt` includes the available license texts for the tested Python components. Preserve the notices and review the exact dependency set used for distribution. No pyresume code is included. The custom grouping code belongs to this project and its intended distribution license should be decided by the project owner.
