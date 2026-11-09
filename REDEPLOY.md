# Redeploy Beta 3.0.0 on GitHub + Render

1. Extract the ZIP. Open the extracted folder and copy or upload the **items inside it** to the root of your existing GitHub repository. You should see the updated backend/, src/, Dockerfile, and render.yaml next to each other at the top level. Do not upload the wrapper folder or ZIP. Keep .git and exclude local dependencies, environment files, and real resumes.
2. Commit the updated frontend and backend together to the branch Render deploys. Verify backend/main.py at the repository root has VERSION = '3.0.0-beta'.
3. On the existing peep-my-resume service, wait for the commit deploy or use Manual Deploy → Deploy latest commit. Confirm the live deployment shows the correct commit.
4. Open https://peep-my-resume.onrender.com/health and expect {"status":"ok","version":"3.0.0-beta"}. If it still shows an older version, compare the live commit and check that the updated files are at the build root.
5. Upload examples/beta-sidebar.pdf. Check the green Parse Check, separate work and education records, full example profile links, and source details. Try your original resume. If testing a malformed PDF, expect a red Couldn't assess state with an error message.

To run the backend tests locally, install requirements-dev.txt and run python -m unittest discover -s tests -v. For the frontend, run npm ci, npm run build, and npm run lint.
