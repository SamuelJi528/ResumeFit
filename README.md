# ResumeFit

A website that compares a resume with a job description, shows supporting evidence, and helps rewrite existing bullet points. Built for the CS4680 AI Assistant Project.

The frontend is HTML, CSS, and JavaScript. A Flask backend handles uploads and calls the Gemini API. Visitors do not enter your Gemini API key; the key is configured on the server.

## Run locally

Use Python 3.11 or newer. From the project folder:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set your own `GEMINI_API_KEY`. Then run:

```powershell
.venv\Scripts\python.exe server.py
```

Open `http://127.0.0.1:8000`. The Windows launcher `run_windows.bat` can also install packages and start the server. Follow the setup steps above to configure your API key.

On macOS/Linux, create the environment with `python3 -m venv .venv`, use `.venv/bin/python` for the commands, and copy the example with `cp .env.example .env`.

## Deploy the website

Follow `docs/DEPLOYMENT.md`. The package includes a Render blueprint, a Dockerfile, and a production Gunicorn command. Upload the source to GitHub and configure the key in the host's environment settings.

This needs a Python web service. GitHub Pages alone cannot run the backend. You do not need Streamlit, Node.js, or a local LLM.

## Features

- Public website with navigation, a landing section, and a document workspace.
- PDF, DOCX, or UTF-8 TXT import; editable text inputs.
- Resume/job comparison with exact source excerpts.
- Requirement statuses, a summary, and prioritized improvements.
- Rewritten bullets with user-directed revisions and history.
- Downloadable text report.
- Few-shot examples on/off for prompt comparisons.
- Server-side API key, optional demo access code, and basic request limits.

The sample button loads fictional inputs. Reviews still call the configured Gemini model.

## Gemini setup and subscription

Create an API key at [Google AI Studio](https://aistudio.google.com/apikey). The default model is `gemini-3.5-flash-lite`; choose a model available to your project through `GEMINI_MODEL`.

Google AI Pro benefits in AI Studio do not automatically cover API calls from this website. External API usage has separate project quotas and billing. Check [Google AI plans](https://ai.google.dev/gemini-api/docs/google-ai-plans), [API pricing](https://ai.google.dev/gemini-api/docs/pricing), and your project's active quota. The current pricing page lists a free tier for the default model, but availability depends on your project.

The website sends input text to Google under the applicable Gemini API terms. Free-tier content may be used to improve Google's products.

## Prompt engineering

Three patterns are in `prompts.py`:

- **Persona:** A recruiter helping students and recent graduates.
- **Few-shot:** Two examples of source-based comparisons and honest rewrites.
- **Iterative refinement:** The original bullet, last draft, and user request guide a revision.

The workspace checkbox disables examples for a comparison while keeping the persona. Explain actual observed differences during the presentation.

## Code structure

| File | Purpose |
| --- | --- |
| `server.py` | Flask routes, input validation, access code, and request limits |
| `templates/index.html` | Website markup |
| `static/styles.css` | Responsive layout and styling |
| `static/app.js` | Uploads, API calls, results, tabs, revisions, and downloads |
| `providers.py` | Gemini REST request; reads the server-supplied key |
| `prompts.py` | Persona, examples, and refinement prompts |
| `models.py` | Output schema, source checks, and coverage calculation |
| `reviewer.py` | Review/refinement flow and one repair attempt |
| `file_utils.py` | In-memory document extraction |
| `reports.py` | Text report formatting |

## Server settings

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | Empty | Your server-side key; required for reviews |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Model available to your API project |
| `SITE_ACCESS_CODE` | Empty | Optional shared class-demo code |
| `REQUESTS_PER_MINUTE` | `5` | Review/refinement attempts per IP |
| `DAILY_GENERATION_LIMIT` | `100` | Total review/refinement attempts per UTC day |
| `TRUST_PROXY` | `0` | Set to 1 only behind one trusted reverse proxy |
| `PORT` | `8000` | Local port; the hosting platform supplies its own |

The supplied production command uses one worker and four threads. At most two generations run at once. Limits are held in memory, reset when the process restarts, and do not act as a billing cap. Each attempt can make two Gemini calls if output needs repair. Multiple workers/instances would each have separate limits; use shared storage if scaling.

For a public class demo, set an access code and share it with the people evaluating the project. The code is separate from your Gemini key.

## Limits and data

Uploads are capped at 3 MB, PDFs at 12 pages, resume text at 12,000 characters, and job text at 8,000. Both text inputs need at least 100 characters. Scanned PDFs need OCR outside this app. Complex layouts may need text correction after import.

There is no resume database. Uploads are read in memory; text/results remain in the current browser tab. The app does not intentionally log resume bodies or keys. Hosting and Google's processing are subject to their own policies.

Source checks confirm that quoted text is present, not that the AI's interpretation is correct. Numeric checks reject new numeric strings in rewritten bullets but cannot catch every invented claim. Users must review suggestions.

Coverage uses weights 2 for Required and 1 for Preferred; Supported receives full credit, Partial half, and Not shown zero. It covers the requirements extracted by AI, not an ATS score or hiring probability.

## Tests

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

The suite uses controlled Gemini responses and does not spend API credits. Complete a real-key test on the deployed website before your presentation. See `docs/VALIDATION.md`, `docs/PRESENTATION.md`, and `docs/ASSIGNMENT_CHECKLIST.md`.
