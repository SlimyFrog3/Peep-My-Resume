# Peep My Resume Beta 4.0.3

Upload a PDF or DOCX to see how our parser reads it, review the readability score, arrange your content, and export an editable resume in one of three styles.

Start with [REDEPLOY.md](REDEPLOY.md), [PATCH_NOTES_4.0.3.md](PATCH_NOTES_4.0.3.md), and [SCORING.md](SCORING.md).

## What changed in 4.0.3

- Review entries carry evidence-backed structured fields for a full name, employment, education and certifications, plus supporting descriptions where detected. Templates reconnect confirmed fields instead of treating every extracted line as a new paragraph.
- The editor shows detected fields, lets you assign wording already in the content, and provides before/after formatting repairs. Editing content clears stale fields; Refresh fields & suggestions rebuilds detection. New wording still goes through the existing additions/omissions approval.
- Actual generated DOCX records are compared against approved entries: fields, employer-group relationships and supporting text. Equal counts or a 100 score alone do not pass this check.
- Downloads are blocked if record preservation, word preservation, section spacing, score non-regression against approved content, or new-finding checks fail. The direct export API enforces the same guard.
- Names remain one title, wrapped degree/school pairs remain connected, and certifications use normal Word Heading 2 titles so descriptions stay under their credential.
- Complete, detected employer groups are informational observations. Incomplete child roles remain actionable findings; no job title or employer is invented.

## Earlier fixes in 4.0.2

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
8. Inspect Detected fields and relationships. Assign existing text to the appropriate fields when necessary. Review and optionally apply formatting repairs; use Refresh fields & suggestions after editing.
9. Build the preview. The backend creates the actual DOCX, reparses it and checks approved word preservation, record associations and real DOCX section spacing. Review the Export checks panel; generation regressions block download. Pending text is included in the preview for inspection but blocks download until resolved.
10. Inspect the original/new scores and word additions/omissions. A simpler layout does not guarantee a higher score.
11. Approve the content and any additions/omissions, then download. The browser downloads the exact DOCX bytes returned with that preview.

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
| backend/structured.py | Evidence-backed record fields, safe line-wrap formatting and specific repair suggestions |
| backend/workflow.py | Validated ordered blocks, shared document model, DOCX export, reparse and preservation checks |

Pdfplumber reads PDFs; python-docx reads and generates DOCX files. They run inside the backend. No external parsing or AI service is called.

The document model contains ordered sections, ordered blocks and paragraphs with formatting roles such as name, entry header, date, body and bullet. These roles do not invent missing employers or qualifications. Words remain editable; obvious wrapped prose may be joined without rewriting its content.

### API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | /health | Version 4.0.3-beta and health |
| GET | /capabilities | Export capability, template IDs and rubric version |
| GET | /templates | Three style definitions |
| POST | /parse | Multipart PDF/DOCX upload |
| POST | /review/prepare | Refresh structured field detection and repair suggestions from reviewed blocks |
| POST | /review/preview | Generate actual DOCX, reparse and return document model, comparison, record preservation, export quality, unresolved IDs and DOCX bytes as base64 |
| POST | /review/export | Direct DOCX export for API clients; rejects unresolved placement and failed export checks |

Preview/export requests contain original and blocks arrays. Each block has id, section, text and resolution (pending, include or exclude). A block may include record with kind, fields, sourceText, and details. Fields and supporting detail strings must be backed by that entry’s text; stale records are rejected. Parent organization is context checked by the export relationship comparison. Requests also include templateId (classic, modern, compact) and sectionOrder (all known section IDs, each exactly once). Defaults preserve compatibility with older API clients.

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

For the UI integration check, run from an activated Python environment containing requirements-dev.txt, or set PYTHON to that environment's Python executable. It uses jsdom and the real Python API through TestClient, not a paid external service. See VALIDATION_4.0.3.md.

The three layouts are original implementations guided by the supplied references, adapted to a single reading column. Sample text, original source files and branding from the references are not distributed.

This remains a heuristic parser. A green result is not proof of perfect extraction or employer ATS acceptance. Intentional Additional Information or incomplete employer groups may still produce parser findings after a fresh parse. The checklist explains these findings; user approval does not silently erase them from the score.


## What the export guard means

The uploaded original, your approved edits and the actual exported file are distinct. Original-to-edited word changes remain visible for approval. Record preservation compares the generated file with your approved entries, including intentional exclusions. The quality score baseline is a fresh parse of the approved, normalized content; deliberate user edits are not misreported as generator damage to the original.

Each known record is matched to a recovered record using content overlap, then its fields and supporting word counts are compared. Extra recovered records are reported. This catches descriptions moving between roles or one certification becoming many fragments. It does not prove factual accuracy, preserve all punctuation or validate employer ATS behavior. Only detected/assigned structured entries are assessed; the UI reports the count. Unrecognized content still needs placement/review, and ambiguous multi-entry blocks may need splitting.

Word checks normalize a hyphenated word at an extracted line break so a formatting repair does not look like word deletion. School/qualification pairs can be placed together with parentheses, without expanding abbreviations or adding claims. No AI rewriting, automatic condensation or PDF export is added.
