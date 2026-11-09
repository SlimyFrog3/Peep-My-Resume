# Redeploy V2.0.1 using your existing GitHub + Render service

1. Download and extract the V2 ZIP to a new folder. Back up your existing local files or retain the V1 Git commit.
2. Copy the extracted contents into your existing repository folder, replacing matching source files. At the repository root you must see `Dockerfile`, `render.yaml`, `package.json`, `src`, and `backend`. Do not put the ZIP or an extra V2 folder into the repository. Keep `.git`; do not copy `node_modules`, `.venv`, `dist`, `.env.local`, or real resumes.
3. Commit the complete frontend and backend update together, then push to the branch your Render service uses (usually `main`). Updating both together is necessary because V2 expects the expanded response fields.
4. Open your existing Render **peep-my-resume** web service. On Commit auto-deployment will normally begin after the push. If not, choose **Manual Deploy → Deploy latest commit**. You do not need a new Blueprint or service.
5. Wait for **Live** and confirm the deployment's commit matches your update. Open your existing public URL and refresh the page.
6. Open the public URL followed by `/health`. Confirm `{"status":"ok","version":"2.0.1"}`. If it says 1.0.0 or 2.0.0, the old backend is still running.
7. With local Python/npm servers stopped, select a PDF or DOCX. It should start processing without an Analyze click. Test your resumes and the included example documents. Confirm summary/certifications/etc. appear when detected, and test from a phone.
8. If the site shows an unexpected results-format error, check that both frontend and backend came from the same V2 commit. If the build fails, copy the relevant Render log error. A sleeping free service can need a minute to wake; retry after it wakes.

Optional Git commands, from your existing repository after copying files:

```sh
git status
git add .
git commit -m "Add V2 resume sections, auto analysis, and light theme"
git push
```

Review `git status` before committing to ensure no personal documents or environment files are included. If using GitHub's upload page instead, upload the extracted project contents to the existing repository root and commit them.

Official deployment controls: https://render.com/docs/deploys
