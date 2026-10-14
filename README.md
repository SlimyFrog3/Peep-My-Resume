# Peep-My-Resume — DeployedV1

A test-ready résumé X-Ray. Upload a text-based PDF or DOCX, click **Analyze résumé**, and see actual extracted text grouped into Contact, Experience, Education, and Skills. Your wording and purple/red/yellow frontend are preserved. This version uses pdfplumber and python-docx.



## How everything connects

`ResumeUploader` selects a browser File. `App` stores it in React state. Clicking Analyze calls `parseResume(file)` in `src/services/parserApi.ts`.

That function puts the file in `FormData` and sends a multipart HTTP POST to `/parse`. During development, `vite.config.ts` forwards `/parse` to the Python server at port 8000. This keeps the browser on one origin; no separate CORS setup is required in this configuration.

FastAPI receives the upload in `backend/main.py`. It reads up to the 10 MB limit and calls `backend/parser.py` in a worker thread. The parser selects a reader by filename extension and checks the document's format:

- PDF → pdfplumber reads each page's text.
- DOCX → python-docx reads paragraphs and table cells in document body order.

The next step walks the extracted lines. Recognized headings such as **Work Experience**, **Education**, and **Technical Skills** change the current section. Following lines belong to that section until another recognized heading appears. It also supports inline headings such as `Skills: Python, SQL`.

Summary, Projects, Certifications, and other known headings stop the previous section; their contents remain in raw text but are not displayed as one of the four main groups. The opening text before the first heading is shown as a candidate contact block, up to 12 nonblank lines. We do not infer a person's name or invent missing values.

The backend returns JSON matching `src/types/ParseResult.ts`: arrays named `contact`, `experience`, `education`, and `skills`, plus `extractedText` and `warnings`. `App` receives it and `ParseResults` renders it. Loading/error states are controlled by App. The API client times out after 90 seconds and reports backend errors. It never silently falls back to mock data in live mode.

## Limitations that matter for testing

- **For local development, both servers must run.** The hosted Docker version runs the website and parser together.
- Two-column PDFs may interleave text. Word headers, footers, text boxes, and nested tables are not supported in this first version.
- Experience/education are grouped lines, not separate structured employer/degree/date records. Skills remain extracted lines rather than inferred proficiency scores.
- Contact is a candidate opening block, not validated personal data.
- Maximum upload: 10 MB; PDF: 20 pages; extracted text: 200,000 characters; DOCX expanded archive: 40 MB.
- Uploads are not saved by application code. FastAPI may temporarily spool uploads, then closes them when the request finishes. There is no database or external AI call.
- This demonstrates our parser's behavior; it does not reproduce every employer's ATS.

## Troubleshooting

**Could not reach parser / request failed:** confirm Terminal 1 is running, check `/health`, and restart Vite after updating configuration. Port 8000 must be free.

## Checks
Seven backend test methods cover PDF/DOCX uploads, missing headings, section boundaries, corrupted/unsupported/empty uploads, size limits, missing file fields, and health. These passed in the build environment. TypeScript/Vite build and ESLint also passed. A full interactive browser test was not available in that environment, so please do the first-test sequence above locally.


## Licensing

pdfplumber and python-docx use MIT licenses. MIT permits commercial use while requiring retention of copyright and permission notices. Their dependencies have their own licenses; `THIRD_PARTY_NOTICES.txt` includes the available license texts for the tested Python components. Preserve the notices and review the exact dependency set used for distribution. No pyresume code is included. The custom grouping code belongs to this project and its intended distribution license should be decided by the project owner.
