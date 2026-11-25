# Deploy Beta 4.0.3 on the existing Render service

1. Keep the current Git commit as a rollback point.
2. Extract the release ZIP. Upload its CONTENTS into the existing repository root. You should see backend/, src/, public/, Dockerfile, package.json and render.yaml at the same level. Do not upload the wrapper folder or ZIP itself.
3. Replace matching frontend/backend files together. Ensure backend/structured.py and src/components/RecordEditor.tsx are included. GitHub uploads do not delete obsolete files; backend/ai_review.py can remain deleted from the earlier update.
4. Commit to Render’s tracked branch. Wait for deployment or choose Manual Deploy > Deploy latest commit. Confirm Live and the matching commit.
5. Open https://peep-my-resume.onrender.com/health and confirm {"status":"ok","version":"4.0.3-beta"}. /capabilities should still report rubricVersion 1.1.
6. Refresh the page and upload the original PDF/DOCX again. Older downloaded files are not changed by this update.
7. Open Review & create DOCX. Inspect detected fields, compare repair suggestions, and try applying a name or education wrap repair. Edit content first if adding/changing wording; then refresh fields/suggestions.
8. Test all three templates. In the preview verify Export checks passed, record-preservation details and section-spacing verification. A generated regression should block download with an explanation.
9. Review names, institutions, employer/client relationships, dates and achievements. Resolve placement and approve any additions/omissions. Download and inspect in Word or LibreOffice.
10. For the supplied Aakash test, expect a unified full-name heading, the degree attached to SMU, three certification records, and 100 before/after in local validation. Employer-group observations remain visible. Check your live result against the original.
11. Reorder or edit content after previewing and confirm approval is cleared. A child role moved out of its employer group may need correction before it can pass preservation checks.
12. Test another resume and check mobile/desktop usability. Existing ambiguous resumes can still retain review findings; the update does not force every result green.

No new service, database or paid API is needed. Do not upload node_modules, dist, .venv, environment files or real resumes to the public repository. No AI provider is active.
