# ResumeFit

**Live website:** [resumefit-topaz.vercel.app](https://resumefit-topaz.vercel.app/)

ResumeFit compares a resume with a job description and helps students and recent graduates improve their existing bullet points. It shows evidence from both documents, explains gaps, and suggests the next edits to make. Built for the CS4680 AI Assistant Project using Flask, HTML, CSS, JavaScript, and the Gemini API, with deployment configured for Vercel.

## Current features

- **Resume import:** Upload a PDF, DOCX, or UTF-8 TXT resume, or paste the text. Imported text remains editable before review.
- **Job comparison:** Paste a job description to receive a summary, extracted requirements, and prioritized improvements.
- **Evidence for each requirement:** Requirements are labeled Required or Preferred, with a status of Supported, Partial, or Not shown. Results show supporting excerpts and advice.
- **Requirement coverage:** View a weighted coverage percentage and counts of supported requirements and gaps.
- **Bullet suggestions:** Review up to three rewritten bullets alongside their original text and an explanation of each change.
- **Iterative revisions:** Request changes such as "Make it shorter," view the updated bullet, and expand its revision history.
- **Text report download:** Export the summary, requirement evidence, improvements, bullet suggestions, and revision history as `resume_review.txt`.
- **Example-guided feedback:** Toggle the two prompt examples on or off while keeping the same recruiter persona.
- **Sample and clear controls:** Load fictional resume/job inputs or clear the current workspace.
- **Changed-input detection:** Refinement pauses when the resume, job description, or example setting differs from the reviewed inputs. Run a new review or restore the original inputs to continue.
- **Responsive interface:** Includes result tabs, keyboard tab navigation, input counts, loading states, and error feedback.

The backend also provides an optional demo access code, request limits, structured output validation, and one repair attempt when generated output fails validation. The Gemini key is configured on the server; visitors do not enter or receive it.

## Use the website

1. Open the [live website](https://resumefit-topaz.vercel.app/) and go to the workspace.
2. Upload or paste your resume and paste a job description, or load the sample inputs.
3. Choose whether to use example-guided feedback. Enter the demo access code if one is required.
4. Click **Review my resume** and inspect the requirements, bullet suggestions, and improvements.
5. Request a revision to a suggested bullet, then use **Download review** to save the report.

The sample button only fills the input fields. Generating a review or revision still calls Gemini and requires the server's API project to have available quota.

## What the results mean

Coverage summarizes the requirements extracted by the model. Required items have weight 2 and Preferred items weight 1. Supported receives full credit, Partial half credit, and Not shown zero. This percentage is not an ATS score or a hiring prediction.

The backend checks that evidence excerpts and original bullets occur in the supplied source text, allowing differences in whitespace and letter case. It rejects duplicate requirements and new numeric strings in rewritten bullets. These checks cannot establish that every interpretation or suggested claim is accurate; review the output before using it.

## Run locally

Use Python 3.11 or newer; the Vercel deployment is pinned to Python 3.12. Internet access and a Gemini API key are required for generation.

On Windows, run these commands from the project folder:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Create a key in [Google AI Studio](https://aistudio.google.com/apikey), then edit your local `.env`:

```dotenv
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

`GEMINI_MODEL` is configurable; use a model available to your API project. Start the app:

```powershell
.venv\Scripts\python.exe server.py
```

Open `http://127.0.0.1:8000`. Alternatively, `run_windows.bat` creates the virtual environment if needed, installs missing dependencies, creates `.env` if absent, and starts the server. Add your key to `.env` and restart the server after changing it.

On macOS/Linux, use `python3 -m venv .venv`, `.venv/bin/python` for Python commands, and `cp .env.example .env` to create the settings file.

## Deploy on Vercel

Import **SamuelJi528/ResumeFit** using the **Flask** preset and the repository root (`./`). Leave install, build, and output overrides unset. Add `GEMINI_API_KEY` as a Secret environment variable for **Production** and set `TRUST_PROXY=1`. Include Preview if you want preview deployments to generate reviews. Save and redeploy after changing environment variables.

`server.py` exports the Flask application. `vercel.json` configures its function duration to 300 seconds, `.python-version` selects Python 3.12, and Vercel serves `public/static/` at `/static/`. Flask serves those same asset URLs locally.

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full setup and deployment checks. `/api/health` reports whether a key is configured; `ready: true` does not verify the key's validity, model access, or remaining quota.

## Configuration and secrets

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | Empty | Server-side key required for review and refinement |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Gemini model ID used by the backend |
| `SITE_ACCESS_CODE` | Empty | Optional shared demo code; empty allows access without a code |
| `REQUESTS_PER_MINUTE` | `5` | Review/refinement attempts per IP per instance |
| `DAILY_GENERATION_LIMIT` | `100` | Review/refinement attempts per instance per UTC day |
| `TRUST_PROXY` | `0` | Use `1` on Vercel; keep `0` locally |
| `PORT` | `8000` | Local server port |

Keep the real key in Vercel's environment settings or the local `.env` file. Git ignores `.env`, local credentials, and private upload folders; `.vercelignore` excludes them from CLI deployment uploads. Keep the committed `.env.example` key blank. Do not place secrets in source code, documentation, or `public/`.

At most two generations run concurrently per instance. Limits are held in memory and reset when an instance restarts. Vercel may run multiple instances, so these limits are not a site-wide quota or billing cap. Each generation attempt can make two Gemini calls if output needs repair.

## Limits and data handling

| Input | Limit |
| --- | --- |
| Resume file | 3 MB; PDF, DOCX, or UTF-8 TXT |
| PDF length | 12 pages |
| Resume text | 100–12,000 characters |
| Job description | 100–8,000 characters |
| Revision request | 600 characters |
| Revisions in one exported report | 50 across all bullets |

Both document inputs must contain at least 100 characters after trimming surrounding whitespace. Scanned PDFs need OCR outside the app. Complex layouts may require corrections after import.

There are no user accounts or saved review database. Uploads are extracted in memory, and the current inputs, results, and revision history live in the browser tab. Refreshing the page resets that workspace. Review and refinement send input text to Google's Gemini API; hosting and provider processing are subject to their respective policies. The application does not intentionally log resume bodies or API keys.

## How the AI workflow works

`prompts.py` uses three prompt patterns: a recruiter **persona**, two **few-shot examples**, and **iterative refinement** using the original bullet, latest draft, and requested change. The example-guided checkbox controls the few-shot examples.

`providers.py` calls Gemini's REST API. `reviewer.py` parses and validates the structured result and requests one repair if validation fails. The application uses an existing model; it does not train one.

## Project structure

| Path | Purpose |
| --- | --- |
| `server.py` | Flask routes, request validation, access control, and request limits |
| `templates/index.html` | Landing page and review workspace |
| `public/static/` | Browser JavaScript, responsive styles, and favicon |
| `providers.py` | Gemini configuration and REST calls |
| `prompts.py` | Persona, examples, review task, and refinement prompts |
| `models.py` | Result schemas, source checks, and coverage calculation |
| `reviewer.py` | Review/refinement generation and repair flow |
| `file_utils.py` | In-memory PDF, DOCX, and TXT extraction |
| `reports.py` | Downloadable text report formatting |
| `samples/` | Fictional resume and job description |
| `tests/` | Python tests and frontend state regression tests |
| `vercel.json`, `.python-version`, `.vercelignore` | Vercel deployment configuration |

## Tests and project documentation

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

Frontend state tests require Node.js 22 or newer:

```powershell
node --test tests/test_frontend.cjs
```

Automated tests use controlled Gemini responses and do not consume API credits. Node.js is only needed for the frontend tests, not to run the Flask app. Verify actual generation with your API project on the deployed website.

Additional documentation: [validation checklist](docs/VALIDATION.md), [presentation outline](docs/PRESENTATION.md), and [assignment checklist](docs/ASSIGNMENT_CHECKLIST.md).
