# Website demo

Open the deployed website and test your actual Gemini key/model before class. If using a free host, allow time for it to wake up. A local backup can run with `python server.py`, but both routes need internet for Gemini.

## Live presentation

1. Show the homepage and explain that students need help connecting their experience to a job.
2. Go to the workspace and load the sample.
3. Click **Review my resume** and let Gemini return a real result.
4. Open a requirement to show the job and resume excerpts.
5. Open **Bullet suggestions**, request "Make it shorter," and show the revision.
6. Download the report.
7. Show Persona, Few-Shot, and Iterative Refinement in `prompts.py`.
8. Explain one limitation and one future improvement.

The sample only fills inputs. It does not load canned AI answers. Describe what the actual model returned.

## Published video: target 110 seconds

- **0-15s:** Show the homepage and explain the problem.
- **15-35s:** Load the sample and run a review.
- **35-55s:** Show a requirement and the source excerpts.
- **55-80s:** Refine a bullet and show the change.
- **80-100s:** Explain the three prompt patterns.
- **100-110s:** Download the result and mention a future feature.

Keep the published video under two minutes. Short captions and readable zoom levels help. Label any cut generation wait in the recording. The live demo must still work in real time.

## Explain the implementation

The browser sends documents to Flask. Flask builds the prompts, calls Gemini using a server-side key, validates the result, and returns it to the browser. The app does not train a model.

Persona sets the recruiter's role. Few-shot examples demonstrate the expected comparison and source-based rewriting. Iterative refinement sends the original source, latest draft, and user's requested change.

Source checks and numeric checks catch some errors, but they cannot establish that every AI interpretation is correct. Coverage is a weighted summary of extracted requirements, not an ATS score.

A possible future feature is collecting verified details before generating stronger bullet points. Another is evaluating several prompt variants on human-reviewed examples. These are future ideas, not completed features.
