# Beta 4.0.2 — parser associations and export spacing

## Cause of the reported 75 → 75 result

The parser rejected work dates ending with durations such as `(2 years 9 months)`. The supplied PDF therefore produced zero job records and extensive unassigned experience. Plain Education also lost a college credential to Certifications, and some study-program descriptions were treated as missing qualifications. Exporting the same unresolved associations could not fix them. Separately, wrapped-prose joining merged two profile URLs into a paragraph that triggered a new Other warning. Compact styling made the work history look especially dense.

## Fixes

- Accept bounded duration annotations after date ranges; reject arbitrary prose suffixes.
- Recognize employer/total-tenure/role/date layouts and grouped promotions. Preserve employer evidence and source wording. Do not use ordinary previous jobs to fill unknown employers.
- Reject narrative sentence fragments as employer names.
- Keep plain-Education credentials with their school. Preserve a detected study program separately from a qualification; never manufacture an awarded degree.
- Keep URL paragraph boundaries and handle older pure multi-URL lines without dropping mixed explanatory prose.
- Give section headings at least 18 pt before and 8 pt after in every style; keep headings with the next paragraph. Increase body line/paragraph spacing, job spacing and short-subheading emphasis.
- Check the actual generated DOCX heading properties, display verification in the review, and block download on a failed spacing check.
- Refresh sample DOCXs and template thumbnails to match the exported styles.
- Bump API/UI/package version to 4.0.2-beta and rubric interpretation to 1.1. Weights remain unchanged.

## Validation and limits

See VALIDATION_4.0.2.md. The supplied original and freshly generated Classic/Modern/Compact files each score 100 with seven jobs, four education entries, no unassigned experience and no review findings. All approved words are preserved. The original improves too because the previous score reflected parser limitations; no export bonus or forced green status is added. Existing downloaded documents are unchanged, so regenerate from the original.

The score describes this parser only. Extra whitespace can add pages. Remaining ambiguous records still require user review, and no AI, database or external resume API is added.
