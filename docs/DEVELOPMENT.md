# Local development

Use Python 3.11 or newer. The Vercel deployment targets Python 3.12. Internet access and a Gemini API key are required for generation.

## Install and run

Clone the repository and open its directory. On Windows:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

On macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Create a key in [Google AI Studio](https://aistudio.google.com/apikey) and set `GEMINI_API_KEY` in `.env`. The default model is `gemini-3.5-flash-lite`; change `GEMINI_MODEL` to a model available to the API project if needed. Keep `TRUST_PROXY=0` for local development.

Start the server on Windows:

```powershell
.venv\Scripts\python.exe server.py
```

Use `.venv/bin/python server.py` on macOS/Linux. Open `http://127.0.0.1:8000`.

The Windows launcher `run_windows.bat` can create the virtual environment, install missing dependencies, create `.env` if absent, and start the server. Restart the server after changing `.env`.

Keep real credentials in `.env`, which is ignored by Git. Leave the committed `.env.example` key blank. Never place credentials in browser assets under `public/`.

## Tests

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

Use `.venv/bin/python` on macOS/Linux. Frontend state tests require Node.js 22 or newer:

```bash
node --test tests/test_frontend.cjs
```

The tests use controlled AI responses and do not consume Gemini API credits. Node.js is only needed for frontend tests. See the [validation checklist](VALIDATION.md) for manual checks.

## Source layout

| Path | Purpose |
| --- | --- |
| `server.py` | Flask routes, request validation, access control, and request limits |
| `templates/index.html` | Landing page and review workspace |
| `public/static/` | Browser JavaScript, styles, and favicon |
| `providers.py` | Gemini configuration and REST calls |
| `prompts.py` | Persona, examples, review task, and refinement prompts |
| `models.py` | Result schemas, source checks, and coverage calculation |
| `reviewer.py` | Review/refinement generation and repair flow |
| `file_utils.py` | In-memory PDF, DOCX, and TXT extraction |
| `reports.py` | Downloadable text report formatting |
| `samples/` | Fictional resume and job description |
| `tests/` | Python tests and frontend regression tests |

See the [deployment guide](DEPLOYMENT.md) for environment settings and the limits of in-memory request counters on Vercel.
