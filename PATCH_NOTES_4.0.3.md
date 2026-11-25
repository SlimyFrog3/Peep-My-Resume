# Beta 4.0.3 — structured records and verified export

## Fixed

- Split name lines now form one consistently styled full-name title when supported by the detected/assigned field.
- Degree and institution fields remain associated through a Word export. Adjacent education entries are resolved before another school can attach to the previous qualification.
- Certification titles use Heading 2; the DOCX reader preserves the title/description grouping. Three detected credentials no longer become dozens of separate fragments.
- Supporting descriptions use source-backed wrap repairs. Hyphenated line wraps are normalized consistently in formatting and word comparison.
- Complete employer overviews with detected child roles are informational. Missing child fields still require review, and client/employer context remains visible.

## Added

- Structured review records: kind, fields, sourceText and supporting details. Every local field/detail must match the approved text; stale or mismatched assignments are rejected.
- A field-assignment panel, before/after repair suggestions and Refresh fields & suggestions. New facts are never filled in automatically. Editing text clears stale detection; moving or splitting entries resets relevant checks/approval.
- Per-record export verification: compares approved fields and supporting text against recovered records, detects extra fragments and changed parent relationships.
- Export quality summary: checks records, words, spacing, score against approved content and newly introduced findings. Failed generation checks block both browser download and direct export API.
- POST /review/prepare for refreshing records and suggestions. Deploy the frontend and backend together.

## Results and limitations

See VALIDATION_4.0.3.md. The Aakash test returns 100/100 before and after each style, with one full-name heading, the education association intact, three certifications and 14 structured entries checked. This is an observed result for this parser, not a guarantee of ATS acceptance. Scores receive no template bonus. Equal scores can be appropriate.

Record verification covers detected or manually assigned fields, not factual truth. Unknown or incorrectly grouped input still needs review. Output can use more pages than a dense multi-column original. AI, persistence, automatic rewriting and PDF export remain deferred.
