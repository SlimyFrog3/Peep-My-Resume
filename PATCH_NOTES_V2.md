# Peep-My-Resume V2 patch notes

## Backend first
- Added Summary, Certifications, Projects, Leadership, Volunteer Work, Links, Awards & Activities, Languages, and Other / Unclassified alongside the existing four sections.
- Added heading aliases and inline labels: `Skills & Activities`, `Computer Languages:`, `Volunteer:`, etc. Inline labels route their own values without permanently changing the parent section.
- Preserved unclassified content instead of dropping it from displayed results.
- Added explicit email, phone, and URL detection across extracted text. Contact still includes a candidate opening block; names and locations are not fully structured or verified.
- Added conservative PDF column detection: headings on both sides plus a low-overlap gutter. Main-column pages are read together before sidebar pages to preserve main-column continuations. Ambiguous layouts keep standard extraction.
- Added reading notes for detected columns, unclassified text, and missing email addresses. Notes identify potential issues, not an accuracy score.
- Updated `/health` to version `2.0.0`. Kept stateless FastAPI, existing document readers, limits, and licenses.

## Frontend second
- Analysis begins immediately on file selection or drop; removed the required Analyze button.
- New selections cancel the preceding browser request and ignore stale results. Canceling the browser request does not guarantee Python processing already started will stop.
- Added retry after request errors and allowed replacement during processing.
- Show only populated cards, with an expandable list of sections not detected.
- Added the extra cards and kept extracted text and parsing warnings available.
- Changed website copy to `resume`. Original uploaded text keeps its spelling and accents.
- Switched to white/light lavender backgrounds, charcoal text, purple emphasis, and red/yellow accents. Kept the eye logo, purple My, and yellow hyphens.
- Single-column cards on phones and natural card heights reduce narrow text wrapping and blank space.

## Validation
- 14 backend tests passed, including synthetic two-column and right-aligned-date PDF fixtures.
- TypeScript/Vite production build and ESLint passed.
- Production FastAPI page serving, health version, and PDF/DOCX response fields passed.

## Limits
- No OCR, AI inference, database, or employer-specific ATS emulation.
- Columns remain heuristic; complex headers, text boxes, and unusual layouts may still misread.
- Data is grouped text, not fully structured job/degree records.
- Only screenshots of the real test resumes were supplied. Their exact PDF/DOCX extraction cannot be reproduced until those original documents are tested.
- The Docker image and public Render deployment must be checked on redeployment; this ZIP is not automatically published.

Browser interaction and visual checks could not be completed because the preparation environment could not download a browser. Verify automatic analysis, file replacement/retry, and phone layout after deployment.
