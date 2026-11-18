# Peep My Resume Beta 4

Peep-My-Resume lets someone upload a PDF or DOCX, inspect the extracted information, review and correct the content, then download a simple editable DOCX. It measures the original and exported file using the same readability checks.

This version is **4.0.0-beta**. Start with [REDEPLOY.md](REDEPLOY.md) to update your Render service, [PATCH_NOTES_V4.md](PATCH_NOTES_V4.md) for changes, and [SCORING.md](SCORING.md) for the rubric.

## Run locally

Requires Python 3.12 and Node 22. In VS Code open the project folder containing this README, backend, src and package.json.

Windows PowerShell, first terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn backend.main:app --reload
```

Second terminal:

```powershell
npm install
npm run dev
```

Open the Local URL Vite prints, normally http://localhost:5173. Both terminals stay running. On macOS/Linux use python3 to create the environment, then .venv/bin/python in place of the Windows Python path.

## User workflow

1. Upload a text PDF or DOCX. Analysis starts immediately.
2. See Parsing Readiness out of 100 near the top, expand the rubric, and inspect the findings/source text. A number is a check of our own parser's output.
3. Open **Review & create DOCX**. The window contains editable source blocks. Each job normally has its own block.
4. Edit text, change sections, reorder blocks within a section, remove blocks, or add missing content. To split a block, insert a blank line and use **Split at blank lines**. Verify the names, dates, job associations and numbers against your original.
5. Optionally request AI section suggestions and accept or reject each one. This requires separate consent and server configuration.
6. Use **Build preview & reparse DOCX**. The server creates the actual DOCX bytes in memory, parses those bytes, and reports the new score.
7. Inspect the original versus new scores and the content-preservation check. Review any word additions/omissions. Improvement is not guaranteed.
8. Approve the content and any changes. Download the editable DOCX. Editing afterward invalidates the preview and approval, requiring a fresh check.

The browser preview shows the single-column content, not an exact Word page rendering. Open the downloaded file to check page breaks. PDF export and automatic rewriting are not part of this release.

## How the code connects

- **src/App.tsx** handles the file, upload request, loading and errors.
- **src/services/parserApi.ts** calls **POST /parse**. Vite proxies API calls to port 8000 locally. In production the Docker image builds Vite and FastAPI serves the frontend.
- **backend/parser.py** extracts with pdfplumber or python-docx, recognizes headings, groups sections and assembles review blocks.
- **backend/layout.py** reconstructs PDF spacing and reading regions from character/word positions. A narrower spacing threshold addresses PDFs with visually spaced words but no literal spaces.
- **backend/records.py** groups jobs, education and certifications, retaining source references. Missing fields stay missing.
- **backend/review.py** explains observed issues and next steps.
- **backend/scoring.py** applies the versioned 30/25/25/20 rubric. AI never assigns the score.
- **src/components/ResumeReview.tsx** is the review window. Edits stay in component state until the user sends a preview/export request. Closing the window keeps edits while that result is mounted; reloading or uploading another file clears them.
- **backend/workflow.py** validates blocks, builds the single-column DOCX and compares word counts. It does not generate achievements or fill missing facts.
- **backend/ai_review.py** calls OpenAI only on opt-in, returning proposed block IDs/sections/reasons. The original block text is never replaced by model output.

### API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | /health | Version and health |
| GET | /capabilities | Whether optional AI is configured |
| POST | /parse | Multipart PDF/DOCX upload |
| POST | /review/preview | Reviewed blocks to real DOCX, reparse and compare |
| POST | /review/export | Reviewed blocks to downloadable DOCX |
| POST | /ai/review | Optional consent-based block organization suggestions |

Preview/export JSON contains **original** and **blocks**, each an array of {id, section, text}. Source metadata is for the UI, not required in these requests. Inputs are limited to 100 blocks, 40,000 characters per block, 200,000 characters per version, and a 2 MiB request body. Blank resumes and duplicate IDs are rejected.

No resume database is used. Uploads, exports and review data are handled in memory for each request. Local browser edits are not saved across reloads. The comparison uses the client-supplied original blocks as its reference; it is feedback, not a tamper-proof certificate.

## Optional AI configuration

Leave AI disabled to use parsing, editing, scores and DOCX export with no AI service.

To enable organization suggestions, add these **backend environment variables** in Render:

```text
AI_ENABLED=true
OPENAI_API_KEY=your-private-api-key
OPENAI_MODEL=gpt-4.1-mini
```

The model must be available to your API project and support Responses API structured outputs. You can choose another compatible model. Keys go in Render environment settings, never GitHub, the ZIP or any VITE_ variable. Environment variables are read directly; local .env files are not automatically loaded. Set them in the terminal before launching Python.

AI sends current non-contact block text to OpenAI after the user's explicit consent. Emails and phone numbers detected in other blocks are redacted; this is not full anonymization, and names or addresses elsewhere may remain. OpenAI retention policies apply; the request sets store=false, which does not mean zero retention. See https://developers.openai.com/api/docs/guides/your-data.

The model can propose moving entire blocks. It cannot change their text. Python discards unknown IDs, duplicate IDs, invalid sections and moves involving Contact. A user can split a mixed block manually before requesting help. Suggestions are optional; if the API is unavailable, manual review/export still work.

Basic limits: 35,000 input characters, 3 requests per minute per direct client address, 60 requests per hour per server process, two concurrent provider calls and a 45-second provider timeout. Limits reset on process restart and are not shared across workers. Render's proxy may cause multiple visitors to share an address bucket. These basic caps are suitable for a small beta; configure a provider-side budget and stronger shared controls before a high-volume public rollout.

## Limitations and testing

This is a heuristic parser, not a clone of every employer ATS. Recognizing headings does not prove every field is correct. Screenshots alone cannot establish what went wrong in the underlying document. Scans need text extraction/OCR outside this app. Complex tables or text boxes can still require manual review.

Repeated PDF page furniture is suppressed only with margin/repetition evidence. The review window lets users restore excluded text. Word header/footer and text-box content is retained for review, but its placement can be uncertain. Missing information is not invented.

The word-preservation check catches many additions/omissions but does not prove that facts, dates or associations remain correct. A better score after removing content is flagged, not presented as proof of improvement. Export is blocked in the UI if generated paragraph words differ from approved content.

Run checks:

```text
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
npm ci
npm run build
npm run lint
```

Use examples/beta-sidebar.pdf and examples/simple.docx, plus the resumes you have permission to test. Real uploaded resumes are excluded from this release package. See VALIDATION_V4.md for completed checks and limits.
