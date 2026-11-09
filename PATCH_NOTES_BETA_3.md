# Beta 3.0.0

- Parse Check at the top of the X-Ray: green Looks good, amber Needs review, red Couldn't assess. It summarizes issues detected by this parser; it is not a job-match or ATS acceptance score. A failed request shows the actual error in the red state.
- PDF reading order uses word positions to find the gutter and reads each region independently, even when there are no matching headings on both sides. Full-width opening text and actual page bounds are respected; uncertain layouts keep ordinary text and a review note.
- Work history is grouped into roles and employer overviews using nearby organizations, titles, and dates. Main-column descriptions can continue on the next page. Year/month precision is preserved. Client names listed within an employer overview retain that context without asserting who employed the candidate.
- Education and credentials have separate records. Source text is available for each record; original text and unassigned experience are also available.
- Embedded PDF/DOCX link targets are extracted, with conservative same-column repair for common wrapped profile links. Incomplete roots are not displayed as complete profiles.
- Spaced headings and additional aliases are recognized. Programming languages listed under Languages move to Skills; spoken languages stay in Languages. Plausible wrapped lines are joined within their region.

## Validation

The existing PDF, DOCX, and error tests plus the new synthetic two-page sidebar and Parse Check tests pass. The supplied three-page resume was also checked locally: eight titled roles plus one employer overview, three certification records (including one in progress), a separate degree, and full LinkedIn and GitHub profiles. The personal resume is not bundled.

## Beta limits

Layout and grouping still use heuristics. Scans without text, deeply nested layouts, unusual job headings, and ambiguous employer/client relationships may need manual review. DOCX is read in document order, including table cells; this does not simulate Word rendering. Parse Check measures issues we detect, so a green result does not guarantee all fields were recovered. No comparison against a particular employer's ATS was performed.
