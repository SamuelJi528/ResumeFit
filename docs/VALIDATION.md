# Testing

Run:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

Use `.venv/bin/python` on macOS/Linux.

Automated tests cover output/source validation, number checks, prompt examples, API errors, upload extraction, Flask endpoints, access-code checks, same-origin checks, request limits, and report export. They use controlled Gemini responses, not paid API calls.

Browser checks exercise the actual frontend/backend flow with controlled AI responses. Actual Gemini quality, your API account access, and a public hosting deployment still need verification.

At delivery, 61 automated tests passed. Desktop and phone browser checks completed uploads, reviews, revisions, report download, changed-input handling, clearing, and keyboard tab navigation without browser errors or horizontal overflow. The test API key did not appear in browser responses. Gunicorn served the homepage and health endpoint successfully. No real Gemini generation or public deployment was performed in this environment.

## Before presenting

- [ ] Configure a real key/model and generate a complete review.
- [ ] Inspect source excerpts and check for invented experience.
- [ ] Refine a bullet and read the downloaded report.
- [ ] Import a real or redacted resume.
- [ ] Change input text and confirm refinement is paused until a fresh review.
- [ ] Try few-shot examples on and off with identical inputs; record actual observations.
- [ ] Check the public URL on desktop and phone.
- [ ] Test the optional demo code if configured.
- [ ] Measure generation time and rehearse the live presentation.

The Windows launcher and Docker deployment need checking on their respective environments. Development testing runs on Linux. No real Gemini API credentials are available in the development environment.
