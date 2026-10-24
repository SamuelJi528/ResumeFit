# Testing

Run:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

Use `.venv/bin/python` on macOS/Linux.

Automated tests cover output/source validation, number checks, prompt examples, API errors, upload extraction, Flask endpoints, access-code checks, same-origin checks, request limits, and report export. They use controlled Gemini responses, not paid API calls.

Browser checks exercise the actual frontend/backend flow with controlled AI responses. Actual Gemini quality, your API account access, and a public hosting deployment still need verification.

The earlier development baseline passed 61 automated tests. Desktop and phone browser checks completed uploads, reviews, revisions, report download, changed-input handling, clearing, and keyboard tab navigation without browser errors or horizontal overflow. The test API key did not appear in browser responses. No real Gemini generation or public Vercel deployment was performed in that baseline.

The Vercel preparation adds checks for public asset placement and local serving, HTTPS origin validation and client IP handling behind the proxy, and two frontend regressions for refinement controls. Run the frontend tests with `node --test tests/test_frontend.cjs` using Node.js 22 or newer. Vercel configuration is checked against its official schema; a successful live deployment still requires verification in Vercel.

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

The Python and frontend suites also run on Windows. The interactive Windows launcher and a real Vercel build/Gemini request still need checking in their respective environments. Automated tests do not require real Gemini credentials.
