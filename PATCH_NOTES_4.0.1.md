# Beta 4.0.1

## Feedback
- Added a checklist below the score bar explaining why a high score can still be yellow.
- Green: at least 90 and no unresolved findings. Yellow: other assessable scores of 55 or above. Red: below 55 or unable to assess.
- Matched progress-bar color to the result state.
- Added observed strengths and per-category feedback. Missing optional records are not praised.
- Kept rubric weights unchanged at 30/25/25/20.

## Editing and export
- Added Classic Professional, Modern Accent and Compact Professional, guided by the supplied DOCX references. Modern uses muted green #527766.
- Added real example thumbnails to “Choose your style!”
- Added a shared document model and explicit section order.
- Whole-section arrows and within-section entry arrows now match document/export arrangement.
- Added thicker arrows, visible labels, hover tooltips and keyboard-focus explanations.
- Added an explicit placement fallback with keep/assign/exclude decisions. Excluded content remains restorable.
- The download uses the exact approved preview DOCX bytes.
- Content, order and style changes invalidate preview/approval.
- Added template examples and long-document checks.

## Removed AI
- Removed backend/ai_review.py, its API route, frontend controls and provider calls.
- AI development is deferred to V5. No AI credentials are required.
- When updating by GitHub upload, manually delete the old backend/ai_review.py if it remains in your repository; uploading a ZIP's contents does not delete older files automatically.

See REDEPLOY.md for deployment and acceptance checks.
