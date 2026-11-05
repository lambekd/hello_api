# hello_api

A small FastAPI app that says hello and goodbye, and asks Google's Gemini model (through Vertex AI) for haikus, fortunes, and answers to short questions.

## Install

You need Python 3.12 or newer and [Poetry](https://python-poetry.org/).

```bash
poetry install
```

## Configure Gemini

`/haiku`, `/fortune`, and `/ask` need a Google Cloud project with the Vertex AI API enabled. `/hello` and `/goodbye` work without any of this.

The app authenticates with Application Default Credentials only, so there are no API keys or key files to manage. To set up credentials on your machine, run:

```bash
gcloud auth application-default login
```

Settings are read from environment variables:

| Variable                | Required | Default                 |
| ----------------------- | -------- | ----------------------- |
| `GOOGLE_CLOUD_PROJECT`  | Yes      | None                    |
| `GOOGLE_CLOUD_LOCATION` | No       | `global`                |
| `GEMINI_MODEL`          | No       | `gemini-3.1-flash-lite` |

## Run

```bash
poetry run python main.py
```

The app listens on port 8080 by default. To use a different port, set the `PORT` environment variable:

```bash
PORT=9000 poetry run python main.py
```

To use the Gemini endpoints, also set your project ID:

```bash
GOOGLE_CLOUD_PROJECT=your_project_id poetry run python main.py
```

## Endpoints

| Endpoint         | Example response                                  |
| ---------------- | ------------------------------------------------- |
| `GET /hello`     | `{"message": "Hey there! What's up?"}`            |
| `GET /goodbye`   | `{"message": "Later, gator! Catch you around."}`  |
| `GET /haiku`     | `{"message": "<a haiku about DevOps>"}`           |
| `GET /fortune`   | `{"message": "<a software-themed fortune>"}`      |
| `GET /ask?q=...` | `{"message": "<Gemini's answer>"}`                |

Gemini writes the `/haiku`, `/fortune`, and `/ask` text, so it changes on each request. `/haiku` and `/fortune` replies are limited to about 100 output tokens.

Try one with:

```bash
curl http://localhost:8080/hello
```

### Asking a question

`/ask` sends the question in the `q` query parameter to Gemini:

```bash
curl -G http://localhost:8080/ask --data-urlencode "q=What does a load balancer do?"
```

- `q` is required and can be up to 200 characters, not counting spaces at the start or end.
- Gemini is told to answer in three sentences or fewer, though this isn't guaranteed.
- Answers are limited to about 200 output tokens, so a long one may be cut off.

### Errors

The Gemini endpoints return a JSON error if they can't get a reply:

| Status | Meaning                                           | Example response                                                |
| ------ | ------------------------------------------------- | --------------------------------------------------------------- |
| `400`  | `/ask` only: `q` is missing, empty, or too long   | `{"error": "Query parameter 'q' is required and can't be empty."}` |
| `500`  | `GOOGLE_CLOUD_PROJECT` isn't set                  | `{"error": "GOOGLE_CLOUD_PROJECT is not set."}`                 |
| `502`  | The Gemini call failed or returned no text        | `{"error": "The call to Gemini failed. Please try again later."}` |

A rejected `q` never reaches Gemini, so it costs nothing. For a `502`, the server log has the details.

## Deploying to Cloud Run

Cloud Run needs two things for the Gemini endpoints to work:

- Set the `GOOGLE_CLOUD_PROJECT` environment variable on the service.
- Give the service's service account the Vertex AI User role (`roles/aiplatform.user`).

`/ask` is meant to be public and has no rate limiting, so anyone can run up Gemini costs by calling it repeatedly. Set a maximum number of instances on the service and a budget alert on the project.

## Troubleshooting

The URLs only work while the app is running, so keep its terminal open.

If `/hello` returns a "Not Found" page instead of JSON, another program is probably using port 8080. Run the app on a free port and use that port in the URL:

```bash
PORT=8081 poetry run python main.py
```

Then open http://localhost:8081/hello.

## Updating dependencies

`requirements.txt` is exported from Poetry. After any dependency change, export it again:

```bash
poetry export -f requirements.txt --output requirements.txt
```
