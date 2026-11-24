---
hide:
  - toc
---

# Phase 3: Local Prediction API

!!! success "Delivered in Pull Request #3"
    **[Pull request #3 (`phase-three`)](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/pull/3)** merged the local FastAPI prediction service and its tests into `main`. Its **Files changed** tab shows everything this phase delivered.

**Status: Built and tested.** All 7 steps are done. The phase added 17 API tests in `tests/test_api.py`, and all pass.

**Needs first:** Phase 2, which is built. Its output is the saved model `models/model.joblib`. If that file is missing, run `python -m src.model.train` first.

Phase 3 wraps the trained model in a small web service that runs on your own computer. A person (or a program) sends the two model inputs as JSON, and the service returns the predicted winner and the home win probability as JSON. Nothing in this phase touches AWS or Docker. Those come later, starting with [Phase 4](../phase-4/index.md).

To run it, activate the virtual environment and start the service. The [Development Guide](#how-do-i-run-it-locally) below has `curl` examples and the real output of each.

```bash
python -m uvicorn src.api.app:app --port 8000
```

## How Do the Pieces Fit Together?

Everything runs on one computer. The model file is read once when the service starts, and each request is then answered from memory.

```mermaid
flowchart TB
    A["Caller<br/>(curl or Postman)"] -->|"POST /predict<br/>JSON with the two inputs"| C["Check the input<br/>(Pydantic)"]
    A -->|"GET /health"| E["Health check:<br/>status and model version"]
    C -->|"invalid"| X["422 with error JSON<br/>that names the problem"]
    C -->|"valid"| D["Model in memory:<br/>scaler + logistic regression"]
    D --> R["200 with the prediction<br/>and probability as JSON"]
    F["models/model.joblib<br/>(path from config/config.yaml)"] -->|"loaded once<br/>at start-up"| D
```

## Steps in Order

- [x] **Step 1. Load the saved model once, when the service starts.** Read `models/model.joblib` (the path comes from `model.output_path` in `config/config.yaml`). Compare the scikit-learn version saved inside the file with the installed one, and stop with a clear message if they differ.
- [x] **Step 2. Define the request and the response.** The request holds two decimal numbers. The response holds the prediction and the probability.
- [x] **Step 3. Add the `POST /predict` route.** Put the two numbers in a NumPy array in the saved input order, and return the model's answer.
- [x] **Step 4. Add the `GET /health` route.** It reports that the service is up and which model version it loaded.
- [x] **Step 5. Reject bad input with a clear error.** A missing field, an extra field, a value that is not a number, or a number far outside the possible range returns status 422 with an error that names the problem.
- [x] **Step 6. Write tests** that call both routes with made-up data and no saved model file.
- [x] **Step 7. Run it locally and test it with `curl`.** Start the service with a one-line command, and send the worked example from Phase 2.

## Key Details

- **One route to predict.** `POST /predict` takes JSON like `{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}`. Both fields are required.
- **The response** has four fields:
    - `prediction`: 1 for a home win, 0 for an away win.
    - `predicted_label`: the same answer as text.
    - `home_win_probability`: the model's chance (0 to 1) that the home team wins.
    - `model_version`: the `model.version` setting saved in the file, for example `v1.0`.
- **The pick rule is the same as scoring.** A probability above 0.5 is a home win, and exactly 0.5 is an away win. See [Phase 2, Part 2](../phase-2/index.md#how-is-a-game-scored).
- **Worked example.** The inputs -0.5 and -18.0 (game `2025_07_NE_TEN`) return a home win probability of **0.3296** and the prediction 0, which matches the model's own output in [Phase 2, Part 2](../phase-2/index.md#what-does-the-worked-example-score).
- **Valid ranges:** win percentage difference from -1 to 1, which is the full possible range. Point margin difference from -100 to 100, which is a loose guard, because the real data runs about -49 to 39.
- **Unknown fields are rejected,** so a misspelled name fails loudly and is not ignored.
- **The scaler is inside the model file,** so the API sends raw inputs. The API never standardizes anything itself.
- **FastAPI, not Flask.** FastAPI does the input checks (missing field, extra field, wrong type, out-of-range number) from one request definition, and it gives a test page at `/docs` with no extra code. Flask would need those checks written separately and a different Lambda adapter than Mangum.
- **No cloud code yet.** The adapter that lets AWS Lambda run the same app (Mangum) is added in Phase 4. See [What Is Mangum?](../phase-4/index.md#what-is-mangum).
- **Built so Lambda can reuse it.** Phase 4 runs this same app in Lambda, so Phase 3 keeps four things true:
    - The app is one object named `app` in `src/api/app.py`, with no code that reads the command line on import.
    - The model loads in the start-up step through `load_model`, not inside a route. Phase 4 calls `load_model` once, on the first call.
    - Every file path goes through `resolve_path` in `src/config.py`, and the Lambda zip keeps the same folder layout (`src/`, `config/`, `models/`).
    - Tests call the app in memory (FastAPI's test client), so they need no server and no network.
- **NumPy, not pandas, in the API.** The Lambda zip fits under its size limit only without `pandas`, so no API file may import it. The reason and the test that enforces it are in [Why Does the API Use NumPy Instead of pandas?](#why-does-the-api-use-numpy-instead-of-pandas).
- **Packages:** [`fastapi`](https://fastapi.tiangolo.com/), [`uvicorn`](https://uvicorn.dev/), and [`pydantic`](https://docs.pydantic.dev/latest/) are already pinned in `requirements.txt`. `uvicorn` is the program that runs the service on your machine, and `pydantic` checks that each request has the right fields. See the [Glossary](../extras/glossary.md#phase-3-local-prediction-api) for both.

## What Was Created

- **Code:** `src/api/app.py` and `src/api/schemas.py`, with 17 tests in `tests/test_api.py`.
- **Packages:** one new pinned line in `requirements.txt`, `httpx2`, used only by the tests.
- **Settings:** none new. The service reuses `model.output_path`. Host and port are given on the command line.
- **Nothing committed that is generated.** The saved model stays local, as in Phase 2.

## What Is Not in This Phase

- Docker, built in [Phase 6](../phase-6/index.md).
- AWS Lambda, API Gateway, and CORS, in [Phase 4](../phase-4/index.md).
- The web app, in [Phase 5](../phase-5/index.md).

## Where to Read More

- [Phase 2 Implementation, Part 2](../phase-2/index.md#implementation-part-2) explains what is inside `models/model.joblib` and how the model scores a game.
- [Design Manifest](../design-manifest.md#phase-3-local-prediction-api) lists the API choices already made.

## Development Guide

This section shows how to run the service on your computer, send it requests, read its errors, and change it. The service has nothing to deploy by itself. It runs on AWS through [Phase 4](../phase-4/deployment-guide.md).

### How Do I Run It Locally?

#### What Is Needed First?

- **Python 3.13 and the project's virtual environment:** See the [run environment](../phase-1/index.md#what-is-the-run-environment).
- **The pinned packages:** `pip install -r requirements.txt`.
- **The saved model `models/model.joblib`:** `python -m src.model.train`. The file is not committed, so a fresh checkout needs this step.

No AWS account, no internet connection, and no Docker are needed.

#### Step 1: Open the Project and Activate the Environment

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

#### Step 2: Start the Service

```bash
python -m uvicorn src.api.app:app --port 8000
```

[`uvicorn`](https://uvicorn.dev/) is the program that runs the service. See [What Is uvicorn?](#what-is-uvicorn) below. Starting it with `python -m` uses the copy in the project's environment.

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

#### Step 3: Check That It Is Running

In the second terminal:

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status":"ok","model_version":"v1.0","scikit_learn_version":"1.9.1"}
```

#### Step 4: Stop the Service

Press `Ctrl+C` in the terminal where it is running. It prints `Shutting down` and exits.

### How Do I Ask for a Prediction?

#### What Are the Two Numbers?

The model uses two numbers, both measured **before** the game from the games already played earlier in the same season. Each one is the home team's value minus the away team's value.

- **`win_pct_differential`:** Home team win percentage minus away team win percentage. A 6-2 team is 0.75, and a 4-4 team is 0.50, so the difference is 0.25. It must be from -1 to 1.
- **`point_diff_per_game_differential`:** Home team points scored minus points allowed per game, minus the same figure for the away team. A team that is +8.0 per game against a team that is -2.0 per game gives 10.0. It must be from -100 to 100.

- **A positive number favors the home team.**
- **Week 1:** no team has played yet, so both numbers are 0.
- **Whole numbers are fine,** for example `0` and `5`. Numbers written as text, such as `"0.5"`, are rejected.
- **The range for the second field is a loose guard.** The real data runs from about -49 to 39.
- How the inputs are built is in [Phase 2, Part 1](../phase-2/index.md#implementation-part-1).

#### Example 1: A Game Where the Away Team Is Stronger

This is game `2025_07_NE_TEN`: the home team (Tennessee) is weaker on both numbers.

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}'
```

```json
{"prediction":0,"predicted_label":"away win","home_win_probability":0.3296,"model_version":"v1.0"}
```

The model gives the home team a **32.96%** chance, which is below 50%, so the pick is an away win. New England won this game, so the pick was correct. This is the same game worked out manually in [Phase 2, Part 2](../phase-2/index.md#what-does-the-worked-example-score).

What the pieces of the command mean:

- **`-X POST`:** Sends a POST request, which is what `/predict` accepts.
- **`-H "Content-Type: application/json"`:** Tells the service that the body is JSON.
- **`-d '{...}'`:** The body: the two numbers, as JSON. Single quotes outside, double quotes inside.
- **`http://127.0.0.1:8000/predict`:** This computer, port 8000, the `/predict` route.

#### Example 2: Two Evenly Matched Teams

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": 0, "point_diff_per_game_differential": 0}'
```

```json
{"prediction":1,"predicted_label":"home win","home_win_probability":0.5364,"model_version":"v1.0"}
```

With no difference between the teams, the model still gives the home team a **53.64%** chance. This is the home-field edge the model learned. See [Phase 2, Part 2](../phase-2/index.md#what-does-the-fit-learn).

#### Example 3: The Home Team Is Stronger

A home team that is 6-2 against a 4-4 away team (0.25), and +10.0 points per game better:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": 0.25, "point_diff_per_game_differential": 10.0}'
```

```json
{"prediction":1,"predicted_label":"home win","home_win_probability":0.6467,"model_version":"v1.0"}
```

The model gives the home team a **64.67%** chance, and the pick is a home win.

#### Showing the Status Code

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

#### What Is in the Response?

- **`prediction`** (whole number, 1 or 0): 1 is a home win and 0 is an away win. A probability above 0.5 gives 1, and exactly 0.5 gives 0, the same rule as scoring in [Phase 2, Part 2](../phase-2/index.md#how-is-a-game-scored).
- **`predicted_label`** (text): The same pick in words: `home win` or `away win`.
- **`home_win_probability`** (decimal number, 0 to 1): The model's chance that the home team wins, rounded to 4 places. The pick is made from the unrounded value.
- **`model_version`** (text): The `model.version` setting that was saved with the model (`v1.0`).

### What Happens With Bad Input?

A request that fails a check gets status **422** and a JSON error that names the problem. The model is never called. Each example below was sent to the running service.

#### Reading an Error

```json
{"detail":[{"type":"less_than_equal","loc":["body","win_pct_differential"],"msg":"Input should be less than or equal to 1","input":1.5,"ctx":{"le":1.0}}]}
```

- **`detail`:** A list with one entry for each problem. A request with two problems has two entries.
- **`type`:** A short code for the kind of problem.
- **`loc`:** Where the problem is: `body`, then the field name.
- **`msg`:** A plain sentence about the problem.
- **`input`:** The value that was sent.
- **`ctx`:** Extra detail, such as the limit that was exceeded.

#### Error Examples

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

The `input` shows `"NaN"` as text. FastAPI cannot write a real `NaN` into a JSON response, so the service has its own error handler that swaps it for the string. See [Step 5 in Implementation](#step-5-reject-bad-input-clearly) below.

**A body that is not JSON:**

```bash
curl -s -w "\nHTTP %{http_code}\n" -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d 'not json'
```

```text
{"detail":[{"type":"json_invalid","loc":["body",0],"msg":"JSON decode error","input":{},"ctx":{"error":"Expecting value"}}]}
HTTP 422
```

#### Summary of Rejections

| Request problem | Status | `type` in the error |
| :--- | :--- | :--- |
| A field is missing | 422 | `missing` |
| An unknown field is added | 422 | `extra_forbidden` |
| A value is text, or a true/false | 422 | `float_type` |
| A value is outside its range | 422 | `less_than_equal` or `greater_than_equal` |
| A value is `NaN` or infinity | 422 | `finite_number` |
| The body is not valid JSON | 422 | `json_invalid` |

### How Can I Try It in a Browser?

FastAPI serves a test page, so no `curl` is needed. With the service running, open <http://127.0.0.1:8000/docs>.

1. Click `POST /predict` to open it.
2. Click **Try it out**.
3. Edit the JSON in the box. It starts with an example of the right shape.
4. Click **Execute**. The page shows the status code and the response body, and the `curl` command it sent.

The same page lists `GET /health`, and shows the field descriptions and the allowed ranges. The machine-readable description of the service is at <http://127.0.0.1:8000/openapi.json>. Both pages returned status 200.

### What Is uvicorn?

A FastAPI app is only a Python object, and it does not listen for requests by itself. [`uvicorn`](https://uvicorn.dev/) is the web server that opens a port on your computer, passes each HTTP request to the app, and sends the answer back. The two talk through [ASGI](https://asgi.readthedocs.io/en/latest/), the standard interface between Python web servers and web apps. See the [Glossary](../extras/glossary.md#phase-3-local-prediction-api) for the short definition.

- **Only for the laptop.** On AWS Lambda there is no port to listen on, so `uvicorn` is left out of the Lambda zip and Mangum takes its place. See [What Is Mangum?](../phase-4/index.md#what-is-mangum).
- **It is not part of the API's logic.** The routes, the input checks, and the model call are all in the FastAPI app.

- **`python -m uvicorn`:** Run the `uvicorn` installed in the active environment.
- **`src.api.app:app`:** Import the module `src/api/app.py` and run the object named `app` inside it. The part before the colon is the file, and the part after is the variable.
- **`--port 8000`:** Listen on port 8000. With no `--host`, it listens only on this computer.

### How Do I Develop It?

#### Where Is Each Piece?

- **The app, the start-up step that loads the model, the 0.5 pick rule, and the two routes:** `src/api/app.py` (`create_app`, `load_model`, `label_for`).
- **The request and response shapes, and the input rules:** `src/api/schemas.py`.
- **The port, the host, and the model path:** The port and host are command-line options. The model path is `model.output_path` in `config/config.yaml`.
- **Tests:** `tests/test_api.py` (17 tests).

#### How Do I Run the Tests?

```bash
python -m pytest tests/test_api.py
```

Expected: **17 passed**. The tests build the app in memory with a made-up model in a temporary folder, so they need no server, no network, and no `models/model.joblib`. One test uses the real model and is skipped if the file is missing.

#### How Do I Restart the Service on Every Change?

Add `--reload` and `uvicorn` restarts the service each time a source file changes:

```bash
python -m uvicorn src.api.app:app --port 8000 --reload
```

Each restart runs the start-up step again, so the model file is read again.

#### How Do I Change the Request or the Response?

1. Edit the shapes in `src/api/schemas.py`. The request fields must be exactly the input names saved in the model file. At start-up the service compares the two and refuses to start if they differ, so adding or renaming an input starts in [Phase 2](../phase-2/index.md#how-do-i-add-or-change-an-input).
2. Update the tests in `tests/test_api.py`.
3. Start the service and send the new request with `curl`, using the examples above.
4. Everything that calls the API uses the same shapes: the Phase 4 function, and the Phase 5 web app. The contracts are in [Phase 5: Front-End Web App](../phase-5/index.md#what-does-the-browser-send).

#### How Do I Change a Rule?

- **The pick rule** (a probability above 0.5 is a home win) is in one place, `label_for` in `src/api/app.py`. `test_pick_rule` checks it at 0.0, 0.4999, 0.5, 0.5001, and 1.0. Scoring in `src/model/evaluate.py` uses the same rule, so change both together.
- **The allowed ranges** (-1 to 1 for the win percentage difference, and -100 to 100 for the point margin difference) are in `PredictRequest`.
- **The error body** for a failed check comes from `reject_invalid_request` in `src/api/app.py`. It exists so that a `NaN` in a bad request is sent back as text.

#### What Rules Must the API Files Keep?

- **No `pandas`, `mlflow`, `matplotlib`, or `src/model/` imports** in `src/api/`. The Lambda zip fits under its size limit only without `pandas`, and a test reads the files and checks this. See [Why Does the API Use NumPy Instead of pandas?](#why-does-the-api-use-numpy-instead-of-pandas).
- **The model loads in the start-up step,** and not at import time and not inside a route.
- **Every file path goes through `resolve_path`** in `src/config.py`, so the same paths work on AWS.

#### How Do I Put a Change on AWS?

The Lambda function runs this same app. After you change anything in `src/api/`, rebuild the zip and redeploy with the [Phase 4 Deployment Guide](../phase-4/deployment-guide.md#redeploy-after-a-change).

## Implementation

This section explains how the service works, one step at a time, and why.

**Status: built and tested.** The code is in `src/api/app.py` and `src/api/schemas.py`, and the tests are in `tests/test_api.py`. Every request and response in the Development Guide above was produced by the running service. The whole project now has 95 tests in 14 files, counting those added by later phases.

### How Does the Service Work?

#### How Does It Start?

The model file is read once, in the app's start-up step, and kept in memory. Every request after that reuses it.

```mermaid
flowchart TB
    A["Service starts"] --> B["Read model.output_path<br/>from config.yaml"]
    B --> C{"models/model.joblib<br/>exists?"}
    C -->|"no"| X1["Stop: run<br/>make train first"]
    C -->|"yes"| D["Load the saved file"]
    D --> E{"File readable, with the<br/>four required keys?"}
    E -->|"no"| X3["Stop: name<br/>the problem"]
    E -->|"yes"| F{"Saved scikit-learn version<br/>equals the installed one?"}
    F -->|"no"| X2["Stop: name<br/>both versions"]
    F -->|"yes"| H{"Saved input names match<br/>the two request fields?"}
    H -->|"no"| X4["Stop: name<br/>the input names"]
    H -->|"yes"| G["Ready for requests"]
```

#### How Is a Request Answered?

```mermaid
sequenceDiagram
    participant C as Caller (curl)
    participant A as FastAPI app
    participant V as Input check
    participant M as Model in memory
    C->>A: POST /predict with JSON
    A->>V: check fields,<br/>types, ranges
    alt input is not valid
        V->>C: 422 and error JSON<br/>that names the problem
    else input is valid
        V->>M: the two numbers,<br/>in the saved order
        M->>A: home win probability
        A->>C: 200 with prediction, label,<br/>probability, model version
    end
```

### Which Files Were Added?

- **`src/api/app.py`:** The `app` object, `create_app`, the start-up step (`load_model`), the 0.5 rule (`label_for`), and the two routes.
- **`src/api/schemas.py`:** The three JSON shapes: `PredictRequest`, `PredictResponse`, and `HealthResponse`.
- **`tests/test_api.py`:** 17 tests for both routes, the start-up checks, and the no-pandas rule.
- **`requirements.txt`:** One new pinned line, `httpx2==2.16.2`, used only by the tests.

- **No new settings.** The service reuses `model.output_path` from `config/config.yaml`. The host and port are given on the command line.
- **`httpx2` is test-only.** FastAPI's test client calls the app through it, and the installed Starlette asks for `httpx2` and prints a warning with the older `httpx`. It is not needed in the Lambda zip. It brought in two helper packages, `httpcore2` and `truststore`, which are left unpinned like the project's other indirect packages.
- **No `__init__.py` files,** matching the rest of the project.

### Step 1: Load the Saved Model at Start-Up

!!! abstract "Purpose"
    **Goal:** Read `models/model.joblib` once, check it, and keep it in memory.

    **Why:** Loading on every request would be slow, and a model saved by a different scikit-learn version may fail to load or answer differently. Failing at start-up is clearer than failing on the first request.

    **If skipped:** A missing or mismatched model would show up as an error in the middle of a request.

- **Where the path comes from:** `model.output_path` in `config/config.yaml`, turned into a full path with `resolve_path` from `src/config.py`. That function finds the project folder from the code's own location, so the same path works from any folder, and in the Lambda zip in Phase 4.
- **What is in the file:** a dictionary with `pipeline`, `feature_names`, `model_version`, `scikit_learn_version`, `train_start_season`, and `train_end_season`. See [Step 7 of Phase 2](../phase-2/index.md#what-is-saved).
- **Where the model lives:** in the app's start-up step (FastAPI's `lifespan`), stored on `app.state`. The routes read it from there. Importing `src/api/app.py` builds the app but does not read the file.
- **Why start-up and not import time:** the tests build the app without a real model file, and Lambda (in Phase 4) reuses the same `load_model` function. See [What Is Mangum?](../phase-4/index.md#what-is-mangum) for how Phase 4 calls it.
- **Checks, in this order:** the file exists, it loads, it holds the four keys the API needs (`pipeline`, `feature_names`, `model_version`, `scikit_learn_version`), the scikit-learn version matches, and the saved input names match the request fields.

If any check fails, the service refuses to start, and `uvicorn` prints a traceback that ends with one of these messages (the `RuntimeError` line):

- **The file is missing:** `No saved model at models/model.joblib. Run python -m src.model.train first.`.
- **The file cannot be read, or is not a dictionary, or lacks a key:** `Could not read the saved model at models/model.joblib: <reason>. Run python -m src.model.train to rebuild it.`.
- **Saved scikit-learn version differs:** `Saved model was built with scikit-learn <saved> but <installed> is installed. Retrain with python -m src.model.train, or install scikit-learn==<saved>.`.
- **The saved input names are not the two request fields:** `Could not read the saved model at models/model.joblib: input names [...] do not match the API fields.`.

The real output when the model file is missing ends like this, and the process exits with code 3:

```text
RuntimeError: No saved model at models/model.joblib. Run python -m src.model.train first.

ERROR:    Application startup failed. Exiting.
```

### Step 2: Define the Request and the Response

!!! abstract "Purpose"
    **Goal:** Describe the exact JSON the service accepts and returns, in one place.

    **Why:** One definition gives the input checks, the error messages, and the `/docs` test page together.

    **If skipped:** The checks would be written manually in each route.

The request, from `src/api/schemas.py`:

```python
class PredictRequest(BaseModel):
    """The two pre-game numbers. Extra fields are refused so a typo is not ignored."""

    model_config = ConfigDict(extra="forbid", strict=True)

    win_pct_differential: float = Field(ge=-1, le=1, allow_inf_nan=False, ...)
    # A loose guard, because the real data runs about -49 to 39.
    point_diff_per_game_differential: float = Field(ge=-100, le=100, allow_inf_nan=False, ...)
```

- **`extra="forbid"`** refuses unknown fields.
- **`strict=True`** refuses numbers written as text, and true or false, in place of numbers. Whole numbers such as `0` are still accepted.
- **`allow_inf_nan=False`** refuses `NaN` and infinity.
- **The field names match the model's input names** (`INPUT_COLUMNS` in `src/model/features.py`), but the API does not import that file. At start-up it checks that the names saved in the model file are the same as the two request fields.

The response has four fields (`prediction`, `predicted_label`, `home_win_probability`, `model_version`), described in [What Is in the Response?](#what-is-in-the-response). The health response has three (`status`, `model_version`, `scikit_learn_version`).

### Step 3: Add the `POST /predict` Route

!!! abstract "Purpose"
    **Goal:** Turn a valid request into a prediction.

    **Why:** This is the route the web app calls.

    **If skipped:** There would be no way to ask the model a question.

```python
@app.post("/predict", response_model=PredictResponse, summary="Predict which team wins.")
def predict(request: PredictRequest) -> PredictResponse:
    """Score one game from the two numbers, in the order saved with the model."""
    saved = app.state.model
    row = np.array([[getattr(request, name) for name in saved["feature_names"]]], dtype=float)
    # The scaler was fitted on a table with column names, and this call passes a plain array
    # so the service does not import pandas. The probability is the same either way.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=r"X does not have valid feature names", category=UserWarning)
        probability = float(saved["pipeline"].predict_proba(row)[0, 1])
    prediction, predicted_label = label_for(probability)
    return PredictResponse(
        prediction=prediction,
        predicted_label=predicted_label,
        home_win_probability=round(probability, 4),
        model_version=saved["model_version"],
    )
```

1. FastAPI checks the request against `PredictRequest` before the route code runs.
2. The route looks up each saved input name on the request and builds a numpy array with one row and two columns, **in the order of `feature_names` from the model file.** The order of the fields in the JSON does not matter.
3. The route calls `predict_proba` and takes the probability of class 1 (a home win).
4. `label_for` applies the 0.5 rule: above 0.5 is `(1, "home win")`, and anything else, including exactly 0.5, is `(0, "away win")`. It is applied to the unrounded probability.
5. The response rounds the probability to 4 places.

#### Why Does the API Use NumPy Instead of pandas?

The API uses [NumPy](https://numpy.org/doc/stable/) only. It does not use [pandas](https://pandas.pydata.org/docs/), although training and cleaning do. The two numbers go to the model as a NumPy array and not as a pandas table (a DataFrame).

- **The Lambda zip fits only without `pandas`.** It is 231.3 MB without it and 278.4 MB with it, against a 250 MB limit. See the [Phase 4 Implementation, Step 3](../phase-4/index.md#step-3-measure-the-package-size).
- **`src/model/features.py` imports `pandas` at the top,** so no file in `src/api/` may import from it. The input names come from the model file instead.
- **One warning is expected.** The scaler was fitted on a table with column names, so a plain array makes scikit-learn warn that "X does not have valid feature names". The probability is the same. The route silences this one warning and no others.
- **The answer is unchanged.** With only NumPy installed, the inputs -0.5 and -18.0 give 0.3296, matching [Phase 2, Part 2](../phase-2/index.md#what-does-the-worked-example-score).

### Step 4: Add the `GET /health` Route

!!! abstract "Purpose"
    **Goal:** Report that the service is running and which model it loaded.

    **Why:** It is the quickest way to check a running service, and it shows which model version is answering.

    **If skipped:** A person could not tell a running service from a stopped one without sending a real prediction.

The response is `{"status":"ok","model_version":"v1.0","scikit_learn_version":"1.9.1"}`. The route reads only from memory. It does not open the file or call the model. The `scikit_learn_version` is the one saved in the model file, and start-up has already checked that it equals the installed one.

### Step 5: Reject Bad Input Clearly

!!! abstract "Purpose"
    **Goal:** Make every bad request return an error that names the problem, and never a prediction or a crash.

    **Why:** The web app and a person with `curl` both need to see what to fix.

    **If skipped:** A bad value could reach the model and return a meaningless probability.

```mermaid
flowchart TB
    A["Request arrives"] --> B{"Valid JSON?"}
    B -->|"no"| E["422: json_invalid"]
    B -->|"yes"| C{"Both fields present,<br/>no extra fields?"}
    C -->|"no"| E2["422: missing or extra_forbidden"]
    C -->|"yes"| D{"Both are numbers<br/>inside their ranges?"}
    D -->|"no"| E3["422: float_type, finite_number,<br/>or a range error"]
    D -->|"yes"| F["Run the model"]
```

The checks all come from the request definition in Step 2, and FastAPI answers a failed check with status 422. One piece of extra code was needed. When a value is `NaN`, the error body would contain a real `NaN`, which JSON cannot hold, and FastAPI crashed while writing the 422. The service has its own handler for these errors (`reject_invalid_request` in `src/api/app.py`) that replaces a non-finite number with the text `"NaN"` or `"Infinity"` and then sends the 422. Real examples are shown in [Error Examples](#error-examples).

### Step 6: Run the Tests

!!! abstract "Purpose"
    **Goal:** Check both routes, the start-up checks, and the no-pandas rule, without a real saved model or the internet.

    **Why:** The tests keep the Lambda size result and the input rules from breaking later.

    **If skipped:** A change could pass unnoticed until the deployed function failed.

```bash
python -m pytest tests/test_api.py
```

Expected: **17 passed**, with no warnings. Without `models/model.joblib`, test 17 is skipped instead, and 16 pass. Running `python -m pytest` with no file name runs all 95 project tests: 93 pass and 2 skip until `models/model.joblib` exists.

- **Made-up model.** A fixture fits a tiny pipeline on 40 made-up rows (fixed random seed), saves it in the same dictionary format that training writes, and points the service at it. The tests never touch `models/model.joblib`, except test 17.
- **In-memory calls.** FastAPI's test client calls the app without starting a server. It is used as a context manager (`with TestClient(app)`), because that is what runs the start-up step.

1. `test_prediction_matches_the_pipeline`: The probability from `/predict` equals the pipeline's own answer, rounded to 4 places.
2. `test_pick_rule`: `label_for` gives an away win for 0.0, 0.4999, and exactly 0.5, and a home win for 0.5001 and 1.0.
3. `test_response_fields`: The response has the four fields with the right types, and whole-number inputs are accepted.
4. `test_field_order_does_not_change_the_answer`: The same two values with the JSON fields in the opposite order give the same response.
5. `test_missing_field_is_rejected`: Status 422, and the error names the missing field.
6. `test_extra_field_is_rejected`: Status 422, and the error names the extra field.
7. `test_text_value_is_rejected`: Both `"abc"` and `"0.5"` give 422.
8. `test_out_of_range_value_is_rejected`: 1.5 and 500 are rejected and name the field, and the edge values 1 and -100 are accepted.
9. `test_not_a_number_is_rejected`: A body containing `NaN` gives 422.
10. `test_invalid_json_is_rejected`: A body that is not valid JSON gives 422.
11. `test_health`: Status 200, with the three expected fields.
12. `test_missing_model_file_stops_startup`: Start-up raises an error that says to run the training command.
13. `test_unreadable_model_file_stops_startup`: A file holding plain text stops start-up with "Could not read the saved model".
14. `test_version_mismatch_stops_startup`: A saved scikit-learn version of `0.0.0` stops start-up and names both versions.
15. `test_wrong_feature_names_stop_startup`: Saved input names that are not the two request fields stop start-up.
16. `test_api_files_do_not_import_pandas`: The API files are read as text and checked: none imports `pandas`, `mlflow`, `matplotlib`, or anything from `src/model/`. Checking `sys.modules` would not work, because scikit-learn loads `pandas` on its own when it is installed.
17. `test_real_model_worked_example`: With the real model, the inputs -0.5 and -18.0 return the exact response shown in [Example 1](#example-1-a-game-where-the-away-team-is-stronger). Skipped if `models/model.joblib` does not exist.
