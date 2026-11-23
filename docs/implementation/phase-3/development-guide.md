---
hide:
  - toc
---

# Phase 3 Development Guide

This guide shows how to run the prediction service on your own computer, how to send it requests, what it answers when the input is wrong, and how to change it. How the service works, and why, is on the [Implementation](./implementation.md) page. The service has nothing to deploy by itself. It runs on AWS through [Phase 4](../phase-4/deployment-guide.md).

## How Do I Run It Locally?

### What Is Needed First?

- **Python 3.13 and the project's virtual environment:** See the [run environment](../phase-1/implementation.md#what-is-the-run-environment).
- **The pinned packages:** `pip install -r requirements.txt`.
- **The saved model `models/model.joblib`:** `python -m src.model.train`. The file is not committed, so a fresh checkout needs this step.

No AWS account, no internet connection, and no Docker are needed.

### Step 1: Open the Project and Activate the Environment

From the project folder, activate the virtual environment so that `python` is the project's Python:

```bash
source .venv/bin/activate
```

Install the packages if this is a new checkout:

```bash
pip install -r requirements.txt
```

Train the model if `models/model.joblib` does not exist:

```bash
python -m src.model.train
```

### Step 2: Start the Service

```bash
python -m uvicorn src.api.app:app --port 8000
```

[`uvicorn`](https://uvicorn.dev/) is the program that runs the service. See [What Is uvicorn?](#what-is-uvicorn) below. Starting it with `python -m` makes sure the one in the project's environment is used, even if the shell cannot find a bare `uvicorn` command.

When the service is ready, the terminal prints these lines and then waits:

```text
INFO:     Started server process [32104]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

- **The terminal stays busy.** The service runs until you stop it. Open a second terminal for the `curl` commands below.
- **Only this computer can reach it.** The address `127.0.0.1` means "this machine", so nobody else on your network can connect.
- **Each request is logged** in that terminal, for example `POST /predict HTTP/1.1" 200 OK`.
- **Port already in use?** If the terminal says `address already in use`, another program owns port 8000. `mkdocs serve` uses port 8000 by default. Either stop that program, or start this service on another port, such as `--port 8001`, and use that port in every command below.

### Step 3: Check That It Is Running

In the second terminal:

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status":"ok","model_version":"v1.0","scikit_learn_version":"1.9.1"}
```

### Step 4: Stop the Service

Press `Ctrl+C` in the terminal where it is running. It prints `Shutting down` and exits.

## How Do I Ask for a Prediction?

### What Are the Two Numbers?

The model uses two numbers, both measured **before** the game from the games already played earlier in the same season. Each one is the home team's value minus the away team's value.

- **`win_pct_differential`:** Home team win percentage minus away team win percentage. A 6-2 team is 0.75, and a 4-4 team is 0.50, so the difference is 0.25. It must be from -1 to 1.
- **`point_diff_per_game_differential`:** Home team points scored minus points allowed per game, minus the same figure for the away team. A team that is +8.0 per game against a team that is -2.0 per game gives 10.0. It must be from -100 to 100.

- **A positive number favors the home team.**
- **Week 1:** no team has played yet, so both numbers are 0.
- **Whole numbers are fine,** for example `0` and `5`. Numbers written as text, such as `"0.5"`, are rejected.
- **The range for the second field is a loose guard.** The real data runs from about -49 to 39.
- The inputs are explained further in [Phase 2 Part 1](../phase-2/implementation-part-1.md).

### Example 1: A Game Where the Away Team Is Stronger

This is game `2025_07_NE_TEN`: the home team (Tennessee) is weaker on both numbers.

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}'
```

```json
{"prediction":0,"predicted_label":"away win","home_win_probability":0.3296,"model_version":"v1.0"}
```

The model gives the home team a **32.96%** chance, which is below 50%, so the pick is an away win. New England won this game, so the pick was correct. This is the same game worked out manually in [Part 2](../phase-2/implementation-part-2.md#what-is-a-worked-example).

What the pieces of the command mean:

- **`-X POST`:** Sends a POST request, which is what `/predict` accepts.
- **`-H "Content-Type: application/json"`:** Tells the service that the body is JSON.
- **`-d '{...}'`:** The body: the two numbers, as JSON. Single quotes outside, double quotes inside.
- **`http://127.0.0.1:8000/predict`:** This computer, port 8000, the `/predict` route.

### Example 2: Two Evenly Matched Teams

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": 0, "point_diff_per_game_differential": 0}'
```

```json
{"prediction":1,"predicted_label":"home win","home_win_probability":0.5364,"model_version":"v1.0"}
```

With no difference between the teams, the model still gives the home team a **53.64%** chance. This is the home-field edge the model learned. See [Part 2](../phase-2/implementation-part-2.md#what-does-the-fit-learn).

### Example 3: The Home Team Is Stronger

A home team that is 6-2 against a 4-4 away team (0.25), and +10.0 points per game better:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": 0.25, "point_diff_per_game_differential": 10.0}'
```

```json
{"prediction":1,"predicted_label":"home win","home_win_probability":0.6467,"model_version":"v1.0"}
```

The model gives the home team a **64.67%** chance, and the pick is a home win.

### Showing the Status Code

Add `-w` to print the HTTP status code after the body, and `-s` to hide curl's progress meter:

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}'
```

```text
{"prediction":0,"predicted_label":"away win","home_win_probability":0.3296,"model_version":"v1.0"}
HTTP 200
```

To print the JSON on several lines, pipe it through Python's formatter. This is one command with two parts, so it stays in one block:

```bash
curl -s -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}' | python -m json.tool
```

### What Is in the Response?

- **`prediction`** (whole number, 1 or 0): 1 is a home win and 0 is an away win. A probability above 0.5 gives 1, and exactly 0.5 gives 0, the same rule as scoring in [Part 2](../phase-2/implementation-part-2.md#how-is-a-game-scored).
- **`predicted_label`** (text): The same pick in words: `home win` or `away win`.
- **`home_win_probability`** (decimal number, 0 to 1): The model's chance that the home team wins, rounded to 4 places. The pick is made from the unrounded value.
- **`model_version`** (text): The `model.version` setting that was saved with the model (`v1.0`).

## What Happens With Bad Input?

A request that fails a check gets status **422** and a JSON error that names the problem. The model is never called. Each example below was sent to the running service.

### Reading an Error

```json
{"detail":[{"type":"less_than_equal","loc":["body","win_pct_differential"],"msg":"Input should be less than or equal to 1","input":1.5,"ctx":{"le":1.0}}]}
```

- **`detail`:** A list with one entry for each problem. A request with two problems has two entries.
- **`type`:** A short code for the kind of problem.
- **`loc`:** Where the problem is: `body`, then the field name.
- **`msg`:** A plain sentence about the problem.
- **`input`:** The value that was sent.
- **`ctx`:** Extra detail, such as the limit that was exceeded.

### Error Examples

**A value out of range, and a missing field.** This one request has two problems:

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": 1.5}'
```

```text
{"detail":[{"type":"less_than_equal","loc":["body","win_pct_differential"],"msg":"Input should be less than or equal to 1","input":1.5,"ctx":{"le":1.0}},{"type":"missing","loc":["body","point_diff_per_game_differential"],"msg":"Field required","input":{"win_pct_differential":1.5}}]}
HTTP 422
```

**An extra field.** A misspelled or unknown name is refused, not ignored:

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": 0.1, "point_diff_per_game_differential": 1.0, "week": 3}'
```

```text
{"detail":[{"type":"extra_forbidden","loc":["body","week"],"msg":"Extra inputs are not permitted","input":3}]}
HTTP 422
```

**A number written as text:**

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": "0.5", "point_diff_per_game_differential": 1.0}'
```

```text
{"detail":[{"type":"float_type","loc":["body","win_pct_differential"],"msg":"Input should be a valid number","input":"0.5"}]}
HTTP 422
```

**Not a number (`NaN`):** standard JSON has no `NaN`, but some tools write it. It is refused:

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": NaN, "point_diff_per_game_differential": 1.0}'
```

```text
{"detail":[{"type":"finite_number","loc":["body","win_pct_differential"],"msg":"Input should be a finite number","input":"NaN"}]}
HTTP 422
```

The `input` shows `"NaN"` as text. FastAPI cannot write a real `NaN` into a JSON response, so the service has its own error handler that swaps it for the string. See [Step 5 of the Implementation](./implementation.md#step-5-reject-bad-input-clearly).

**A body that is not JSON:**

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d 'not json'
```

```text
{"detail":[{"type":"json_invalid","loc":["body",0],"msg":"JSON decode error","input":{},"ctx":{"error":"Expecting value"}}]}
HTTP 422
```

### Summary of Rejections

| Request problem | Status | `type` in the error |
| :--- | :--- | :--- |
| A field is missing | 422 | `missing` |
| An unknown field is added | 422 | `extra_forbidden` |
| A value is text, or a true/false | 422 | `float_type` |
| A value is outside its range | 422 | `less_than_equal` or `greater_than_equal` |
| A value is `NaN` or infinity | 422 | `finite_number` |
| The body is not valid JSON | 422 | `json_invalid` |

## How Can I Try It in a Browser?

FastAPI serves a test page, so no `curl` is needed. With the service running, open <http://127.0.0.1:8000/docs>.

1. Click `POST /predict` to open it.
2. Click **Try it out**.
3. Edit the JSON in the box. It starts with an example of the right shape.
4. Click **Execute**. The page shows the status code and the response body, and the `curl` command it sent.

The same page lists `GET /health`, and shows the field descriptions and the allowed ranges. The machine-readable description of the service is at <http://127.0.0.1:8000/openapi.json>. Both pages returned status 200.

## What Is uvicorn?

A FastAPI app is only a Python object. It does not listen for requests by itself, so something has to run it. [`uvicorn`](https://uvicorn.dev/) is that program (a web server). It opens a port on your computer, receives each HTTP request, passes it to the app, and sends the app's answer back to the caller. The two talk through [ASGI](https://asgi.readthedocs.io/en/latest/), the standard interface between Python web servers and web apps. See the [Glossary](../glossary.md#phase-3-local-prediction-api) for the short definition, and the [uvicorn documentation](https://uvicorn.dev/) for its options.

- **Only for the laptop.** `uvicorn` runs the service in Phase 3. On AWS Lambda there is no port to listen on, so it is not used there and is left out of the Lambda zip. Mangum takes its place. See [What Is Mangum?](../phase-4/implementation.md#what-is-mangum).
- **It is not part of the API's logic.** The routes, the input checks, and the model call are all in the FastAPI app. Swapping `uvicorn` for another server would not change an answer.

- **`python -m uvicorn`:** Run the `uvicorn` installed in the active environment.
- **`src.api.app:app`:** Import the module `src/api/app.py` and run the object named `app` inside it. The part before the colon is the file, and the part after is the variable.
- **`--port 8000`:** Listen on port 8000. With no `--host`, it listens only on this computer.

## How Do I Develop It?

### Where Is Each Piece?

- **The app, the start-up step that loads the model, the 0.5 pick rule, and the two routes:** `src/api/app.py` (`create_app`, `load_model`, `label_for`).
- **The request and response shapes, and the input rules:** `src/api/schemas.py`.
- **The port, the host, and the model path:** The port and host are command-line options. The model path is `model.output_path` in `config/config.yaml`.
- **Tests:** `tests/test_api.py` (17 tests).

### How Do I Run the Tests?

```bash
python -m pytest tests/test_api.py
```

Expected: **17 passed**. The tests build the app in memory with a made-up model in a temporary folder, so they need no server, no network, and no `models/model.joblib`. One test uses the real model and is skipped if the file is missing.

### How Do I Restart the Service on Every Change?

Add `--reload` and `uvicorn` restarts the service each time a source file changes:

```bash
python -m uvicorn src.api.app:app --port 8000 --reload
```

Each restart runs the start-up step again, so the model file is read again.

### How Do I Change the Request or the Response?

1. Edit the shapes in `src/api/schemas.py`. The request fields must be exactly the input names saved in the model file. At start-up the service compares the two and refuses to start if they differ, so adding or renaming an input starts in [Phase 2](../phase-2/development-guide.md#how-do-i-add-or-change-an-input).
2. Update the tests in `tests/test_api.py`.
3. Start the service and send the new request with `curl`, using the examples above.
4. Everything that calls the API uses the same shapes: the Phase 4 function, and the Phase 5 web app. The contracts are on the [Phase 5 Implementation](../phase-5/implementation-part-1.md#what-does-the-browser-send) page.

### How Do I Change a Rule?

- **The pick rule** (a probability above 0.5 is a home win) is in one place, `label_for` in `src/api/app.py`. `test_pick_rule` checks it at 0.0, 0.4999, 0.5, 0.5001, and 1.0. Scoring in `src/model/evaluate.py` uses the same rule, so change both together.
- **The allowed ranges** (-1 to 1 for the win percentage difference, and -100 to 100 for the point margin difference) are in `PredictRequest`.
- **The error body** for a failed check comes from `reject_invalid_request` in `src/api/app.py`. It exists so that a `NaN` in a bad request is sent back as text.

### What Rules Must the API Files Keep?

- **No `pandas`, `mlflow`, `matplotlib`, or `src/model/` imports** in `src/api/`. The Lambda zip fits under its size limit only without `pandas`, and a test reads the files and checks this. See [Why Does the API Use NumPy Instead of pandas?](./implementation.md#why-does-the-api-use-numpy-instead-of-pandas).
- **The model loads in the start-up step,** and not at import time and not inside a route.
- **Every file path goes through `resolve_path`** in `src/config.py`, so the same paths work on AWS.

### How Do I Put a Change on AWS?

The Lambda function runs this same app. After you change anything in `src/api/`, rebuild the zip and redeploy with the [Phase 4 Deployment Guide](../phase-4/deployment-guide.md#redeploy-after-a-change).
