# Deploy ResumeFit on Vercel

The repository is configured for Vercel's native Flask support. `server.py` exports the Flask `app`; no extra API wrapper, catch-all rewrite, Gunicorn process, or frontend build is needed.

## Import the repository

1. In [Vercel](https://vercel.com/new), import **SamuelJi528/ResumeFit** from GitHub.
2. Select the **Flask** framework preset if it is not detected automatically.
3. Use the repository root (`./`) as the Root Directory.
4. Leave Install Command, Build Command, and Output Directory overrides disabled. Vercel installs `requirements.txt`; `.python-version` selects Python 3.12. Do not enter `python server.py` as a build command.
5. Keep **Fluid Compute** enabled. `vercel.json` sets a 300-second maximum duration for the `server.py` function so generation and one repair attempt have time to finish.
6. Add the environment variables below before deploying. Set them for Production and for Preview if you intend to test preview deployments.
7. Click **Deploy**. Later pushes to `main` trigger production deployments when the Git integration is connected.

## Environment variables

| Name | Value |
| --- | --- |
| `GEMINI_API_KEY` | Your real Gemini API key; required for reviews |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite`, or a model available to your API project |
| `TRUST_PROXY` | `1` to use Vercel's forwarded client IP and HTTPS scheme |
| `SITE_ACCESS_CODE` | Optional shared demo code, recommended for a class demo |
| `REQUESTS_PER_MINUTE` | `5` |
| `DAILY_GENERATION_LIMIT` | `100` |

The real key belongs in Vercel's environment settings, not in GitHub or frontend code. Your local `.env` is ignored by Git and excluded from deployment uploads. Updating environment variables requires a new deployment; use **Redeploy** after changing them.

`PORT` is only used by the local launcher. Do not configure a port or start command on Vercel.

## Files and runtime behavior

- `vercel.json` selects Flask, configures the function duration, and excludes development/private files from the Python bundle.
- `.vercelignore` excludes local environments, credentials, test files, and documentation from CLI uploads. `.vercel/` is also ignored by Git.
- `public/static/` contains only public CSS, JavaScript, and the favicon. Vercel serves these at `/static/` from its CDN. Never put keys, uploads, or private documents under `public/`.
- `templates/` and the fictional `samples/` inputs are included in the function bundle.
- Uploads are processed in memory. The app does not need writable persistent storage.
- Local development still uses `run_windows.bat` or `python server.py`.

The request and daily counters are **per instance**. Vercel may start multiple instances or restart an idle instance, so these settings are best-effort demo protection, not a shared daily cap or billing limit. Use a demo code and configure your Gemini project's quota. A sustained public service needs shared rate-limit storage.

Uploads remain capped at 3 MB. Vercel also enforces its own request-size and execution limits. A slow or incomplete Gemini response can still time out; retry with shorter inputs and inspect Runtime Logs if generation fails. The project does not require a paid plan by configuration, but account/model availability and usage charges depend on your services.

## Verify the deployment

- Open `/api/health`: expect `status: ok` and `ready: true` after configuring the key.
- Open the homepage and confirm `/static/app.js`, `/static/styles.css`, and `/static/favicon.svg` load successfully.
- Load the sample, generate a real review, refine a bullet, and download the report.
- Upload a PDF, DOCX, or TXT document and check desktop and mobile layouts.
- If using a demo code, confirm a missing/incorrect code is rejected and the correct code works.
- Confirm `/.env` and `/server.py` return 404 and the key never appears in browser responses.
- To let classmates or graders access the site, review Vercel's Deployment Protection settings for the URL you share.

Local automated tests use controlled AI responses. A real Vercel build and Gemini request must still be verified on the deployed site.

Official references: [Flask on Vercel](https://vercel.com/docs/frameworks/backend/flask), [Python runtime](https://vercel.com/docs/functions/runtimes/python), [function duration](https://vercel.com/docs/functions/configuring-functions/duration), [function limits](https://vercel.com/docs/functions/limitations), and [environment variables](https://vercel.com/docs/environment-variables).
