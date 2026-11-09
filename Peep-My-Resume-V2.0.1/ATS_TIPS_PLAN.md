# Proposed formatting tips - not implemented

## Recommended first version: a small rules layer

Run a `build_formatting_tips()` step after extraction/grouping, based on document evidence and parser diagnostics. Return structured tips containing an ID, observation, suggested action, and whether the observation is detected or uncertain. React could show a "Formatting tips" panel below the results. A short static "General tips" block can provide guidance even when no file has been uploaded.

Keep three things distinct: a software/service failure, a detected document characteristic, and general advice. A page-coordinate offset such as the supplied PDF's offset is our software compatibility issue, not evidence that the resume is poorly formatted. Network errors, server failures, and parser bugs must not reduce a resume rating or generate demands to redesign it.

## Candidate rules and example wording

| Evidence needed | Example proposed tip | Qualification |
|---|---|---|
| Column detector identifies separate columns | "We detected a multi-column layout. Compare the extracted reading order; a single-column copy may be easier for some parsers to read." | Potential risk, not automatic failure. |
| No readable text on one or more pages | "We couldn't extract text from page 2. If it is a scan, export a text-based PDF or use OCR." | Empty extraction does not prove a scan. Track this per page first. |
| A heading was not recognized, or content is unclassified | "We couldn't identify an Experience section. If you have one, try a clear heading such as Work Experience." | Our heading rules may be incomplete. Don't claim the applicant has no experience. |
| No explicit email pattern found | "We couldn't detect an email address. Check that it appears as ordinary text in the main document." | Could be intentionally omitted or missed by extraction. |
| DOCX inspection finds contact details in a header/footer | "Contact details appear in a header/footer. Consider placing them in the main document body as well." | Requires new DOCX header/footer inspection; current omission alone cannot prove this. |
| DOCX inspection finds a layout table | "This document uses a table. If the extracted sections appear mixed, consider a simpler layout." | Tables are not universally unreadable. Inspect actual reading order. |
| Decorative letter spacing detected with sufficient evidence | "Some words appear as separated letters in extracted text. Use normal character spacing and recheck." | Need reliable detection; avoid flagging initials or short abbreviations. |

General tips can suggest clear section headings, selectable document text, a simple reading order, and contact details in the main body. Keep general advice labeled separately from findings detected in this particular resume.

## Alternative approaches

1. Static checklist: simplest to add; useful immediately, but not personalized.
2. Rules plus extraction diagnostics: best next step for this project; explainable, inexpensive, and testable without a new external service.
3. Optional AI explanation: later, a model could explain existing findings in friendlier language. Constrain it to supplied evidence and keep uncertain findings uncertain. It should not invent missing qualifications or guarantee ATS acceptance. This adds provider costs and a decision about transmitting resume content.

## Display and validation

- Prefer "Detected", "Check this", and "General guidance" over unsupported confidence percentages or an ATS score.
- Each personalized tip should state the observation and a specific action. Avoid accusations such as "your resume is broken".
- Compare before/after versions using extracted text and correct section assignments across a varied test set. Don't call a change successful merely because it produces fewer warnings.
- All employers' ATS systems do not behave identically; successful parsing in this tool is not a guarantee for another system.

## Primary source

Greenhouse documents columns, complex tables, headers/footers, contact details inside headers/footers/text boxes, image uploads, and unclear sections as possible causes of unsuccessful or partial parsing:
https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse

The proposed rules and UI above are our design proposal, not a claim that Greenhouse implements those checks or that its exact limitations apply universally.
