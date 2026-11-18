# Parsing Readiness Rubric 1

The score measures our implemented readability and extraction checks. It is not a hiring score, candidate ranking or guarantee that another ATS will read the document identically.

| Category | Maximum | What earns points |
| --- | --- | --- |
| Readable text | 30 | Text without unusually long joined words, replacement/control characters or recorded layout/blank-page failures |
| Section separation | 25 | Little text left in Other and little long prose in Contact |
| Record associations | 25 | Detected job title/employer/date groups and institution/qualification pairs, with little unassigned experience |
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

Green **Looks good** requires a score at least 90 and no review findings. Other assessable results are yellow **Needs review**. Unassessable results/errors are red. The original and actual generated DOCX are scored with the same rubric version.

Scores may stay the same or decrease after reformatting. The comparison reports word additions and omissions independently, and requires review of changes before download.
