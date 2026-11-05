# hello_api

A small FastAPI app that says hello and goodbye.

## Install

You need Python 3.12 or newer and [Poetry](https://python-poetry.org/).

```bash
poetry install
```

## Run

```bash
poetry run python main.py
```

The app listens on port 8080 by default. To use a different port, set the `PORT` environment variable:

```bash
PORT=9000 poetry run python main.py
```

## Endpoints

| Endpoint       | Example response                                |
| -------------- | ----------------------------------------------- |
| `GET /hello`   | `{"message": "Hey there! What's up?"}`          |
| `GET /goodbye` | `{"message": "Later, gator! Catch you around."}` |

Try one with:

```bash
curl http://localhost:8080/hello
```

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
