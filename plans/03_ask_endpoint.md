# Public /ask endpoint

## Context
The app has `/haiku` and `/fortune`, which send fixed prompts to Gemini. We're adding `GET /ask?q=...`, which sends the caller's question to Gemini using the same client and settings. It will be public and every call costs money, so bad input must be rejected before any Gemini call, and answers must be short.

## Current repo state
`main` is checked out and has no app code. The app is on `gemini_endpoints` (`01caf4c`), which isn't merged or pushed. The `__pycache__/` showing as untracked on `main` appears only because `main` has no `.gitignore` yet; it's harmless and I'll leave it alone.

## Steps

1. **Branch:** create `ask_endpoint` from `gemini_endpoints`. No commits, pushes, merges or PRs; the user does those.
2. **Project rules:**
   - Log the prompt verbatim in `PROMPTS.md` with its timestamp (2026-11-05 00:38 UTC). Plan mode blocked logging it earlier.
   - Save this plan as `plans/03_ask_endpoint.md`.
3. **App:** update `main.py`.
   - Add constants:
     ```python
     ASK_SYSTEM_INSTRUCTION = "Answer the user's question in three sentences or fewer."
     ASK_MAX_OUTPUT_TOKENS = 200
     ASK_MAX_QUESTION_LENGTH = 200
     ```
   - Extend the existing `ask_gemini` so all three endpoints share it, with `/haiku` and `/fortune` behaving as before:
     ```python
     def ask_gemini(prompt, max_output_tokens=MAX_OUTPUT_TOKENS, system_instruction=None):
         ...
         config=types.GenerateContentConfig(
             max_output_tokens=max_output_tokens,
             system_instruction=system_instruction,
         ),
     ```
   - Add the endpoint:
     ```python
     @app.get("/ask")
     def ask(q: str | None = None):
         question = (q or "").strip()
         if not question:
             return JSONResponse(
                 status_code=400,
                 content={"error": "Query parameter 'q' is required and can't be empty."},
             )
         if len(question) > ASK_MAX_QUESTION_LENGTH:
             return JSONResponse(
                 status_code=400,
                 content={
                     "error": f"Query parameter 'q' can't be longer than {ASK_MAX_QUESTION_LENGTH} characters."
                 },
             )
         return ask_gemini(
             question,
             max_output_tokens=ASK_MAX_OUTPUT_TOKENS,
             system_instruction=ASK_SYSTEM_INSTRUCTION,
         )
     ```
   - **Manual checks instead of FastAPI's `Query` limits:** those return a 422 in FastAPI's own format. Manual checks give a 400 in the app's `{"error": ...}` format.
   - **Whitespace:** a `q` of only spaces counts as empty, because it would otherwise cost a Gemini call. The length check runs after trimming, so at most 200 characters are ever sent.
   - **Separate instruction:** the system instruction goes in the config and isn't mixed into the caller's text.
4. **`README.md`:** add `/ask` to the endpoints table with a `curl` example, its limits, and the `400` error. Mention `/ask` in the description and the Gemini setup section, and add a Cloud Run cost note: the endpoint has no rate limiting, so set maximum instances and a budget alert.

No new packages, so `pyproject.toml`, `poetry.lock` and `requirements.txt` don't change.

## Out of scope
No rate limiting, authentication or caching, since none were requested. The final report will flag this as the main remaining cost risk.

## Verification
The live tests make a few real Gemini calls, billed to the current gcloud project at a very small cost. The project ID is passed only as a shell variable and isn't written to any file.
- **Rejections cost nothing:** run with `GOOGLE_CLOUD_PROJECT` unset. If a request gets past validation it returns 500, so a 400 proves it never reached Gemini. Test missing `q`, `q=`, spaces only, and 201 characters, and confirm a 200-character `q` gets the 500.
- **Happy path:** with the project set, confirm `/ask?q=...` returns 200 with a JSON answer, including a question with special characters.
- **Answer limits:** directly check the sentence count, token use and finish reason on a question that invites a long answer ("Explain in detail how TCP works"), and on one that tells the model to ignore its instruction.
- **Exact limit:** confirm a 200-character `q` returns 200 with the project set.
- **Regression:** confirm `/hello`, `/goodbye`, `/haiku` and `/fortune` still work, and that a nonexistent model gives a 502 on `/ask`.
- **Windows side:** test from Windows on port 8081, because Apache holds 8080 there. Leave the updated app running on 8081 with the project set.
- **Git:** confirm we're on `ask_endpoint`, nothing is committed, and no project ID appears in files git would commit.
