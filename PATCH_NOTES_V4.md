# Beta 4.0.0

## Parser corrections

- Reconstruct word spacing using character geometry, including PDFs that display spaces without encoding literal space characters.
- Recognize more summary, skills, academic, project and employment headings, ampersands and inline suffixes.
- Reduce summary leakage into Contact.
- Recognize wrapped employer/date headers, date-first jobs, ongoing dates and more role titles.
- Handle one-line education entries naming the qualification and institution with “from.”
- Suppress confidently identified repeated margin headers/page numbers, with excluded text available to restore.
- Stop treating a newly recognized project heading as a certification, and reduce over-merging dated credentials.
- Include Word header/footer and text-box content for review.

## Score and workflow

- Parsing Readiness out of 100, four expandable rubric categories and the existing green/yellow/red labels.
- Editable review window with section moves, block ordering/splitting, additions/removals and source comparison.
- Single-column editable DOCX export with clear headings and job blocks. No automatic rewriting or added facts.
- Fresh parse of the generated DOCX, original-versus-new score comparison and additions/omissions check.
- Explicit user approval before download; edits invalidate preview and approval.

## Optional AI

- Backend-only OpenAI integration with strict structured section-move suggestions.
- Consent, contact-block omission, basic email/phone redaction, source ID checks and basic request limits.
- AI is off until the owner configures the backend environment. Manual review/export work without it.
- No paid live AI call was performed during packaging. The provider integration was tested with a mocked response.

See README.md, SCORING.md, REDEPLOY.md and VALIDATION_V4.md.
