# Deploy Beta 4.0.2 on the existing Render service

1. Keep the current Git commit as a rollback point.
2. Extract the ZIP. Upload the **contents inside it** to the root of the existing GitHub repository. Keep backend, src, public, Dockerfile, package.json and render.yaml together. Do not upload an extra wrapper folder.
3. In GitHub delete the obsolete **backend/ai_review.py** if present. It is absent from this ZIP. The new backend does not import it, but GitHub uploads do not remove old files.
4. Commit frontend and backend changes together to the branch Render deploys.
5. In Render remove the obsolete AI_ENABLED, OPENAI_MODEL and OPENAI_API_KEY variables if previously set. This version does not use them.
6. Wait for the commit deployment, or choose Manual Deploy > Deploy latest commit. Confirm Live and the matching commit.
7. Open https://peep-my-resume.onrender.com/health and confirm {"status":"ok","version":"4.0.2-beta"}.
8. Refresh the site. Check the rubric, checklist and observed strengths. A high score with a remaining finding should be yellow with a clear explanation; a score below 55 should be red.
9. Open Review & create DOCX. Check all three style cards and Modern's muted green.
10. Move Skills above Experience, reorder two entries within Experience, build the preview and download. Confirm Word shows the same order.
11. If unplaced text exists, choose its section, keep it as Additional Information or explicitly exclude it. Download should remain blocked while a nonempty block is pending.
12. Change style or content after previewing; approval/download must reset. Rebuild and approve again.
13. Test short and long resumes on desktop and phone. Check hover/focus arrow explanations on desktop and visible labels on mobile.

Do not upload node_modules, dist, .venv, private environment files, API keys or real resumes. The existing Dockerfile builds the frontend and installs backend requirements. No new Render service, database or paid API is needed.


### 4.0.2 acceptance test

Upload the original PDF again, rather than an older reformatted download. Check that duration-annotated dates yield separate job records, education credentials remain with their college, and subject-only education is labeled as a program without inventing a degree. Build each style and confirm the section-spacing verification passes. The supplied test should now score 100 for the original and each fresh export under rubric 1.1. Review the job associations against the original even when green. An equal score is valid; the export does not receive bonus points.

The refreshed templates deliberately use more whitespace and may add pages for long resumes. Wording is not shortened automatically. Check the real downloaded DOCX in Word/LibreOffice for pagination.
