# Peep My Resume Beta 4.0.2

Upload a PDF or DOCX to see how our parser reads it, review the readability score, arrange your content, and export an editable resume in one of three styles.

Start with [REDEPLOY.md](REDEPLOY.md), [PATCH_NOTES_4.0.2.md](PATCH_NOTES_4.0.2.md), and [SCORING.md](SCORING.md).

## What changed in 4.0.2

- Date ranges followed by a parenthesized duration now parse correctly, including grouped roles under an employer heading and total tenure. Employer inheritance requires an explicit grouped-employer anchor; ordinary missing employers remain flagged.
- Plain Education keeps its own college credentials. Recognized subject/program descriptions are separate from awarded qualifications; no degree is inferred. Rubric 1.1 accepts a school/program association, with the same 30/25/25/20 weights.
- Profile URLs stay in separate paragraphs, including lowercase links. Older paragraphs containing only multiple URLs no longer create a false Other warning.
- Every template has more space around sections, jobs and short subheadings. Actual DOCX heading spacing is checked before download, independently from the parsing score.
- The supplied test PDF and fresh exports in all three styles each scored 100 locally after the parser fixes. A fresh export is needed; existing downloaded files are not changed. This result is not a guarantee for other resumes or employer ATS systems.

## Features retained from 4.0.1

- Green requires at least 90/100 and no unresolved parser findings. Yellow covers other assessable scores from 55 upward. Scores below 55 are red. A checklist below the bar explains what remains before green.
- “What’s working well” highlights observed strengths. Absent record types are labeled not assessed rather than praised.
- “Choose your style!” offers Classic Professional, Modern Accent and Compact Professional, with real rendered example thumbnails.
- Sections and entries can be reordered. The editor, document preview and exported file use the same order.
- Thick arrow controls have visible labels plus hover/focus tooltips.
- Unclassified text requires an explicit placement decision: assign a section, keep as Additional Information, or exclude. Excluded entries remain restorable in the review.
- OpenAI integration, its endpoint and its controls have been removed. AI work is deferred to V5.

## Run locally

Requires Python 3.12 and a supported Node version: 22.22.2+, 24.15+ or 26+. The included Render Dockerfile uses the current Node 22 image.

Windows PowerShell, first terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn backend.main:app --reload
```

Second terminal:

```powershell
npm ci
npm run dev
```

Open Vite's Local URL, normally http://localhost:5173. Both terminals stay running. On macOS/Linux use python3 for environment creation and .venv/bin/python instead of the Windows Python path.

## Review and export

1. Upload a text-based PDF or DOCX. Analysis starts automatically.
2. Inspect the score, observed strengths, rubric and “What it takes to get green.”
3. Open **Review & create DOCX**.
4. Choose a style. Template cards show fictional example content; the actual preview uses your content.
5. Arrange whole sections with section arrows. Arrange entries within a section with entry arrows. Use the dropdown to move an entry to a different section.
6. Edit source text and verify names, dates, achievements and associations against the original. Insert blank lines to split mixed content into separate entries.
7. Resolve “Needs placement” blocks. You can include them under Additional Information or exclude them explicitly. Nothing is silently thrown away.
8. Build the preview. The backend creates the actual DOCX, reparses it and checks approved word preservation and real DOCX section spacing. Pending text is included in the preview for inspection but blocks download until resolved.
9. Inspect the original/new scores and word additions/omissions. A simpler layout does not guarantee a higher score.
10. Approve the content and any additions/omissions, then download. The browser downloads the exact DOCX bytes returned with that preview.

Changing content, section order, entry order or template clears the preview and approvals. The selected template controls typography and spacing; it does not rearrange sections. Long content gains pages naturally. The browser preview matches the content model and style settings, but Word/LibreOffice determine exact page breaks and font substitution.

PDF export is deferred. examples/classic-style.docx, modern-style.docx and compact-style.docx contain the same fictional resume in each style. examples/template-sample.json is editable sample data.

## How the code connects

| File | Purpose |
| --- | --- |
| src/App.tsx | Upload state, analysis and error display |
| src/components/ReadabilityScore.tsx | Score, checklist, strengths and category feedback |
| src/components/ResumeReview.tsx | Review state, approvals, section/entry arrangement |
| src/components/MoveButton.tsx | Accessible arrows with tooltips |
| src/components/TemplateChooser.tsx | Three style choices |
| src/components/ResumeDocumentPreview.tsx | Renders the shared document model |
| src/services/parserApi.ts and reviewApi.ts | Browser-to-backend requests |
| backend/main.py | FastAPI endpoints and production frontend hosting |
| backend/parser.py and layout.py | File extraction, word spacing and section grouping |
| backend/records.py and links.py | Evidence-backed records and links |
| backend/review.py | Findings and recommended next steps |
| backend/scoring.py | Deterministic 30/25/25/20 rubric and observed strengths |
| backend/templates.py | Shared style definitions for three DOCX layouts |
| backend/workflow.py | Validated ordered blocks, shared document model, DOCX export, reparse and preservation checks |

Pdfplumber reads PDFs; python-docx reads and generates DOCX files. They run inside the backend. No external parsing or AI service is called.

The document model contains ordered sections, ordered blocks and paragraphs with formatting roles such as name, entry header, date, body and bullet. These roles do not invent missing employers or qualifications. Words remain editable; obvious wrapped prose may be joined without rewriting its content.

### API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /health | Version 4.0.1-beta and health |
| GET | /capabilities | Export capability, template IDs and rubric version |
| GET | /templates | Three style definitions |
| POST | /parse | Multipart PDF/DOCX upload |
| POST | /review/preview | Generate actual DOCX, reparse and return document model, comparison, unresolved IDs and DOCX bytes as base64 |
| POST | /review/export | Direct DOCX export for API clients; rejects unresolved placement |

Preview/export requests contain original and blocks arrays. Each block has id, section, text and resolution (pending, include or exclude). Requests also include templateId (classic, modern, compact) and sectionOrder (all known section IDs, each exactly once). Defaults preserve compatibility with older API clients.

Inputs are limited to 100 blocks, 40,000 characters per block, 200,000 characters per version and a 2 MiB review request body. Empty included resumes, duplicate IDs, unknown templates and invalid section orders are rejected.

## Data handling

No database or saved resume history is implemented. Exports and review processing happen in memory per request; upload handling may use temporary files. Browser edits and approved download bytes stay in memory until the page/result is replaced or reloaded. No AI provider receives resume content.

The comparison uses the client-provided original blocks. Word-count preservation flags additions and omissions but cannot certify factual accuracy, punctuation, word order or correct associations.

## Validation and limitations

Install requirements-dev.txt for Python tests. Then run:

```text
python -m unittest discover -s tests -v
npm run build
npm run lint
npm run test:ui
```

For the UI integration check, run from an activated Python environment containing requirements-dev.txt, or set PYTHON to that environment's Python executable. It uses jsdom and the real Python API through TestClient, not a paid external service. See VALIDATION_4.0.1.md.

The three layouts are original implementations guided by the supplied references, adapted to a single reading column. Sample text, original source files and branding from the references are not distributed.

This remains a heuristic parser. A green result is not proof of perfect extraction or employer ATS acceptance. Intentional Additional Information or ambiguous employer overviews may still produce parser findings after a fresh parse. The checklist explains these findings; user approval does not silently erase them from the score.
