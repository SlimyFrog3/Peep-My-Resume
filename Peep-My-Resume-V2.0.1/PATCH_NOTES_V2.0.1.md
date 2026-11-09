# V2.0.1 - page boundaries and accurate errors

## Fixed
- `backend/parser.py`: every column/header crop now uses the actual `page.bbox`, including a nonzero left edge or negative top coordinate. This resolves the supplied PDF's out-of-bounds failure.
- A ValueError in optional layout analysis falls back to ordinary page text extraction and adds a reading-order warning. If ordinary extraction also fails, normal error handling still applies.
- Password instructions appear only for the PDF library's confirmed password-required exception.
- PDF structure and DOCX archive/XML errors get format-specific recovery instructions without declaring the file corrupted.
- Empty extraction states the observed problem and makes scan/OCR guidance conditional.
- Unexpected parser failures return HTTP 500 with a neutral message. The server logs the exception class without document text or contact details.
- The frontend distinguishes size/validation, rate limits, unavailable service, unknown server errors, missing endpoint, network failures, timeout, cancellation, and unreadable responses. It does not show arbitrary server details for HTTP 500.
- `/health` and package version are now `2.0.1`.

## Validation
- 21 backend tests passed, covering existing PDF/DOCX behavior, shifted page bounds, fallback, confirmed password errors, structure errors, no-text outcomes, and neutral unexpected errors.
- The supplied real PDF returned HTTP 200 and 13,342 extracted characters using the pinned Python requirements. This confirms successful reading, not complete section-classification accuracy.
- TypeScript/Vite production build, ESLint, and direct frontend HTTP-message mapping checks passed.
- No interactive browser or Docker build verification was performed for this patch. Verify the deployed upload flow after Render is Live.

## Future work only
ATS_TIPS_PLAN.md proposes evidence-based formatting tips. No recommendation service, scoring system, or tips panel has been added.

## Deployment
Upload the project contents to the same repository root, commit and push. Let the existing Render service redeploy, or deploy its latest commit manually. Confirm `/health` says 2.0.1 and retry the supplied PDF. Detailed steps remain in REDEPLOY.md. The live site has not been modified by preparing this package.
