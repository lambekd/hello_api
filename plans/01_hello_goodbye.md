# Hello/Goodbye FastAPI app

## Context
The repo contains only `CLAUDE.md`. We need a small FastAPI app, managed with Poetry, with two casual JSON GET endpoints. It will later deploy to Google Cloud Run from GitHub, so it must read its port from `PORT` (default 8080) and ship a `requirements.txt` exported from Poetry.

## Steps

1. **Branch:** create `hello_goodbye_api` from `main` before changing anything. No commits, pushes, merges or PRs; the user does those.
2. **Project rules:**
   - Create `PROMPTS.md` and log the prompt verbatim with its timestamp (2026-11-04 00:58 UTC). Plan mode blocked logging it earlier.
   - Save this plan as `plans/01_hello_goodbye.md`.
3. **Poetry setup:** add `pyproject.toml`.
   - `package-mode = false`, because this is an app and not a library.
   - `requires-python = ">=3.12,<4.0"`, so the local Python 3.14 works and Cloud Run isn't tied to one version.
   - `poetry add fastapi uvicorn`. These are the only dependencies. No test packages, in line with "don't add packages we don't need".
4. **App:** add `main.py` at the project root.
   ```python
   import os

   import uvicorn
   from fastapi import FastAPI

   app = FastAPI()


   @app.get("/hello")
   def hello():
       return {"message": "Hey there! What's up?"}


   @app.get("/goodbye")
   def goodbye():
       return {"message": "Later, gator! Catch you around."}


   if __name__ == "__main__":
       uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
   ```
   Binding to `0.0.0.0` is required for Cloud Run to reach the container.
5. **Requirements:** run `poetry export -f requirements.txt --output requirements.txt`. The export plugin is already installed.
6. **`.gitignore`:** cover `.venv/`, `__pycache__/`, and `.env`, so that secrets and local files stay out of commits.
7. **`README.md`:** cover install (`poetry install`), run (`poetry run python main.py`), setting `PORT`, the endpoints with example responses, and re-exporting `requirements.txt` after dependency changes.

## Files created
`PROMPTS.md`, `plans/01_hello_goodbye.md`, `pyproject.toml`, `poetry.lock`, `main.py`, `requirements.txt`, `.gitignore`, `README.md`

## Out of scope
No Dockerfile, Procfile or deployment config, since deployment comes later and wasn't requested.

## Verification
- Run `poetry run python main.py`, then `curl` `/hello` and `/goodbye` on port 8080 and confirm the JSON responses.
- Run `PORT=9000 poetry run python main.py` and confirm the app answers on 9000.
- Install `requirements.txt` into a throwaway venv in the scratchpad and start the app from it, to prove the export works on its own.
- Run `git status` to confirm we're on `hello_goodbye_api`, nothing is committed, and no `.venv` or cache files show up as untracked.
