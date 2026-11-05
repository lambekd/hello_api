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
ASK_SYSTEM_INSTRUCTION = "Answer the user's question in three sentences or fewer."
MAX_OUTPUT_TOKENS = 100
ASK_MAX_OUTPUT_TOKENS = 200
ASK_MAX_QUESTION_LENGTH = 200
TIMEOUT_MS = 30_000

app = FastAPI()


@lru_cache
def get_client(project, location):
    return genai.Client(
        vertexai=True,
        project=project,
        location=location,
        http_options=types.HttpOptions(timeout=TIMEOUT_MS),
    )


def ask_gemini(prompt, max_output_tokens=MAX_OUTPUT_TOKENS, system_instruction=None):
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
            config=types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                system_instruction=system_instruction,
            ),
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


@app.get("/hello")
def hello():
    return {"message": "Hey there! What's up?"}


@app.get("/goodbye")
def goodbye():
    return {"message": "Later, gator! Catch you around."}


@app.get("/haiku")
def haiku():
    return ask_gemini(HAIKU_PROMPT)


@app.get("/fortune")
def fortune():
    return ask_gemini(FORTUNE_PROMPT)


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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
