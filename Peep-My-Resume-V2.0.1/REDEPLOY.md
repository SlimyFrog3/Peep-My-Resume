# Redeploy Beta 4 on your existing Render service

1. Back up your current project or keep its Git commit.
2. Extract this ZIP. Upload the **contents inside the extracted folder** to your existing GitHub repository root, replacing matching files. You should see backend, src, Dockerfile, render.yaml and package.json together. Do not upload the ZIP or an extra wrapper directory.
3. Commit frontend and backend changes together to the branch your existing Render service deploys.
4. Wait for Render to deploy, or use **Manual Deploy > Deploy latest commit**. No new service or Blueprint is required.
5. Confirm the service is Live and its commit matches yours. Open https://peep-my-resume.onrender.com/health and confirm {"status":"ok","version":"4.0.0-beta"}.
6. Refresh the website, upload examples/beta-sidebar.pdf, check the score, then open Review & create DOCX. Build the preview, approve, download, and open the document in Word or LibreOffice.
7. Test an edit/removal and confirm a fresh preview and change approval are required. Check a phone as well as a desktop.
8. AI is optional. To enable it, set AI_ENABLED=true, OPENAI_API_KEY to your private API key, and OPENAI_MODEL=gpt-4.1-mini (or another available model supporting Responses structured outputs) in the Render backend environment, then restart/redeploy. Never put the key in GitHub or VITE_ variables. /capabilities should report aiEnabled:true.
9. Opt into AI review with a resume you are permitted to send to the provider. Accept/reject suggestions, and verify that wording remains intact. If AI fails, manual review/export should remain available.

Do not upload node_modules, dist, .venv, .env, private API keys or real resumes. The included Dockerfile installs dependencies and builds the frontend. PDF export is deferred; DOCX is the supported output.
