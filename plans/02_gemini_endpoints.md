# Gemini endpoints: /haiku and /fortune

## Context
The app has `/hello` and `/goodbye`. We're adding two GET endpoints whose text is written by Gemini through Vertex AI, using the `google-genai` SDK and Application Default Credentials (ADC) only. Failures must return clear JSON errors, and `/hello` and `/goodbye` must keep working even if Gemini isn't configured.

Already confirmed on this machine: ADC gives a valid token, the Vertex AI API is enabled on the gcloud project, and `google-genai` 2.34.0 is available.

## Steps

1. **Branch:** create `gemini_endpoints` from the current `hello_goodbye_api`, which holds the app and isn't merged to `main` yet. No commits, pushes, merges or PRs; the user does those.
2. **Project rules:**
   - Log the prompt verbatim in `PROMPTS.md` with its timestamp (2026-11-04 23:07 UTC). Plan mode blocked logging it earlier.
   - Save this plan as `plans/02_gemini_endpoints.md`.
3. **Dependency:** `poetry add google-genai`, then re-export `requirements.txt`.
4. **App:** update `main.py`.
   ```python
   import logging
   import os
   from functools import lru_cache

   import uvicorn
   from fastapi import FastAPI
   from fastapi.responses import JSONResponse
   from google import genai
   from google.genai import types

   logger = logging.getLogger(__name__)

   HAIKU_PROMPT = "Write a short haiku about DevOps. Reply with only the haiku."
   FORTUNE_PROMPT = (
       "Write a one-sentence, software-themed fortune-cookie message. "
       "Reply with only the message."
   )
   MAX_OUTPUT_TOKENS = 100
   TIMEOUT_MS = 30_000


   @lru_cache
   def get_client(project, location):
       return genai.Client(
           vertexai=True,
           project=project,
           location=location,
           http_options=types.HttpOptions(timeout=TIMEOUT_MS),
       )


   def ask_gemini(prompt):
       project = os.environ.get("GOOGLE_CLOUD_PROJECT")
       if not project:
           return JSONResponse(
               status_code=500,
               content={"error": "GOOGLE_CLOUD_PROJECT is not set."},
           )

       location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
       model = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
       try:
           response = get_client(project, location).models.generate_content(
               model=model,
               contents=prompt,
               config=types.GenerateContentConfig(max_output_tokens=MAX_OUTPUT_TOKENS),
           )
           text = response.text
       except Exception:
           logger.exception("Gemini call failed")
           return JSONResponse(
               status_code=502,
               content={"error": "The call to Gemini failed. Please try again later."},
           )

       if not text:
           logger.error("Gemini returned no text: %s", response)
           return JSONResponse(
               status_code=502,
               content={"error": "Gemini returned an empty response."},
           )
       return {"message": text.strip()}
   ```
   Plus `@app.get("/haiku")` and `@app.get("/fortune")`, each returning `ask_gemini(...)` with its fixed prompt.
   - **Response format:** `{"message": ...}` matches the existing endpoints, and errors use `{"error": ...}`.
   - **Status codes:** 500 for the missing project setting (our configuration) and 502 for Gemini failures (upstream).
   - **Broad `except`:** auth, network and API failures raise unrelated exception types. Details go to the server log and aren't sent to the caller.
   - **Lazy client:** it's created on first use, so a missing setting can't stop the app from starting or break `/hello` and `/goodbye`.
   - **Timeout:** 30 seconds, so a stalled call can't hang a request.
   - **Possible adjustment:** if thinking tokens use up the 100-token limit and cut off or empty the replies, turn thinking down in the config. The live test below will show this.
5. **`README.md`:** cover the new endpoints, the three environment variables, local auth with `gcloud auth application-default login`, the 500/502 errors, and a deployment note that Cloud Run needs `GOOGLE_CLOUD_PROJECT` set and a service account with the Vertex AI User role (`roles/aiplatform.user`). Use a placeholder project ID. Update the app description.

## Out of scope
No API keys, key files, `.env` loader, or test packages. No deployment changes.

## Verification
The live tests make a few real Gemini calls, billed to the current gcloud project at a very small cost. The project ID is passed only as a shell variable and isn't written to any file.
- **Happy path:** with `GOOGLE_CLOUD_PROJECT` set to the gcloud project, call `/haiku` and `/fortune`. Confirm 200, JSON, a real haiku and a one-sentence fortune, neither cut off.
- **Missing setting:** without `GOOGLE_CLOUD_PROJECT`, confirm `/haiku` returns the 500 JSON error and `/hello` still returns 200.
- **Gemini failure:** with `GEMINI_MODEL` set to a nonexistent model, confirm a 502 JSON error and that the app keeps running.
- **Export:** install `requirements.txt` into a clean venv in the scratchpad and call `/haiku` from it.
- **Windows side:** test from Windows on port 8081, because Apache holds 8080 there. Leave the updated app running on 8081 with the project set.
- **Secrets and git:** check that no project ID, key or credential appears in tracked files, and that nothing is committed.
