# Milestone 5 Notes

## What I built

- `query.py` now handles the end-to-end question flow:
  - retrieve top chunks from ChromaDB
  - filter out weak or low-signal matches
  - call Groq's `llama-3.3-70b-versatile`
  - return both the grounded answer and a programmatic source list
- `app.py` provides a Gradio interface with:
  - a question box
  - an answer box
  - a `Retrieved from` source list
  - a `Retrieved snippets` debug panel

## Grounding behavior

- The system prompt tells the model to use only the retrieved context
- If the context is weak or missing, the system returns:
  - `I don't have enough information on that.`
- Source attribution is not left to the model alone
  - the app always builds the final source list from the actual retrieved chunks

## End-to-end checks

I tested the full pipeline with Groq on these questions:

1. `What background does CS 6515 expect before a student takes it?`
   - Returned the expected prerequisite answer from the official course page

2. `Is CS 6300 Software Development Process a good first OMSCS course?`
   - Returned a grounded yes-with-caveat answer from the review corpus

3. `What risk shows up repeatedly in student feedback for CS 6310 Software Architecture and Design?`
   - Returned group-project and grading/feedback risks from the review corpus

4. `What do students say about on-campus parking near the CS building?`
   - Correctly declined with `I don't have enough information on that.`

5. `How is CS 6603 AI, Ethics, and Society positioned compared with the other courses in this set?`
   - Safely declined instead of hallucinating, which is better than inventing a comparison
   - This is still a useful failure case because retrieval found related snippets, but not enough direct comparative evidence

## Interface verification

- `gradio==4.44.1` was used instead of `gradio>=6.9.0`
  - the project venv is on Python 3.9, and Gradio 6 requires Python 3.10+
- I verified that the interface imported successfully and served locally at:
  - `http://127.0.0.1:8011`
- I used port `8011` for testing because the default `7860` range was already occupied in this environment
