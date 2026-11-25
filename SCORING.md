# Parsing Readiness Rubric 1.1

The score measures our implemented readability and extraction checks. It is not a hiring score, candidate ranking or guarantee that another ATS will read the document identically.

| Category | Maximum | What earns points |
| --- | --- | --- |
| Readable text | 30 | Text without unusually long joined words, replacement/control characters or recorded layout/blank-page failures |
| Section separation | 25 | Little text left in Other and little long prose in Contact |
| Record associations | 25 | Detected job title/employer/date groups and institution/qualification-or-program pairs, with little unassigned experience |
| Contact and links | 20 | 10 for a detected email or phone; 10 when no incomplete profile URL was detected |

Absent optional sections and absent links do not cause deductions. A blank image-only page cannot be diagnosed as a scan with certainty.

## Calculation

Implementation lives in backend/scoring.py. Each category is rounded before addition.

- **Readable text** starts with a noise fraction: 8 times the fraction of words over 35 characters (excluding tokens containing / or @), plus 30 times the fraction of replacement/control characters. Clamp noise to 1. Subtract another .25 for each recorded blank-page, layout-fallback or overlapping-column finding, capped at .75. Multiply the remaining nonnegative fraction by 30.
- **Section separation** is 25 times 1 minus the fraction of review text characters in Other or in Contact lines over 22 words, clamped between 0 and 1.
- **Record associations** is 25 times the fraction of expected fields detected among actual job and education records. For experience, also multiply by the fraction of experience characters not left unassigned. Employer overviews with separately detected child roles are excluded from title completeness.
- **Contact and links** is the sum of its two 10-point checks.

A document with text but too little recognizable resume information shows **Couldn't assess** with no number. A file from which no readable text can be extracted shows **0/100**, with the actual extraction error. Network, server and password errors show no number.

**100/100** means all these checks passed; it does not prove all information was extracted. It is possible to receive 100 and still have an amber review finding, such as an employer overview that warrants checking.

Green **Looks good** requires a score at least 90 and no actionable review findings. Other assessable results of 55 or above are yellow **Needs review**. Scores below 55 are red **Needs attention**. Unassessable results/errors are red. The original and actual generated DOCX are scored with the same rubric version.

Scores may stay the same or decrease after reformatting. The comparison reports word additions and omissions independently, and requires review of changes before download.


## Feedback added in 4.0.1

The numeric formula is unchanged. A checklist explains the 90-point threshold and each unresolved finding, using its existing next-step guidance.

Categories now report assessed, strength and status. “What’s working well” displays only observed positives. Record associations can receive no-deduction points when absent, but are explicitly labeled not assessed and receive no praise. Detecting an email/phone earns a contact observation; absent links never produce a claim that profile URLs were verified.

A 98 or 100 with a remaining finding stays yellow. User approval is not substituted for a fresh parser result, and deleting content does not automatically prove improvement.


## Record interpretation in 4.0.2 / rubric 1.1

The weights and numeric formula remain 30/25/25/20. An education record can pair a named institution with an explicitly detected field of study/program as well as an awarded qualification. The API distinguishes `program` from `qualification`, and the UI labels a program without inferring a degree. A school alone still raises a finding. These checks measure readable associations, not whether someone graduated or holds an award.

Formatting verification is separate from the score. The generated DOCX must contain real Heading 1 paragraphs with at least 18 pt before, 8 pt after and keep-with-next; download is blocked if this check fails. Spacing does not automatically award association points or erase other findings. Equal original/export scores are valid when both files are already readable by these checks.


## Export verification in 4.0.3

The numeric weights are unchanged. A recognized employer overview with complete linked roles is informational and does not prevent green; incomplete records remain findings. User approval does not erase an unresolved parser error.

Export verification is separate from the score. Known structured records must retain their approved fields and supporting text after reparsing. New findings, a lower score than the approved-content baseline, lost words or failed heading spacing block download. Original-to-approved edits are still disclosed separately. A file can score 100 and fail export verification because record structure changed. The UI reports both results.
