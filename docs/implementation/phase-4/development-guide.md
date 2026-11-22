---
hide:
  - toc
---

# Phase 4 Development Guide

This guide shows how to test the Lambda entry point on your own computer with no AWS account, and how to change it. Every AWS command, for the first deployment, a redeploy, a settings change, or removal, is on the [Deployment Guide](./deployment-guide.md). The reasons and the results are on the [Implementation](./implementation.md) page.

## What Is Needed First?

- **The project's virtual environment with the pinned packages.** The setup commands are in the [Phase 1 guide](../phase-1/development-guide.md#what-is-needed-first).
- **The saved model** `models/model.joblib`. If it is missing, run `python -m src.model.train`.
- **No AWS account.** Everything on this page runs with no AWS account and no internet connection.

## How Do I Run It Locally?

### Step 1: Run the Six Tests

```bash
python -m pytest tests/test_lambda_handler.py
```

Expected: **6 passed**. Five use a made-up model and made-up API Gateway events. The sixth calls the real `handler` function with the real `models/model.joblib`, and it is skipped if that file is missing.

### Step 2: Call the Real Handler by Hand

The handler is the function AWS Lambda calls. It takes an event, which is the dictionary API Gateway builds from a web request. The [Deployment Guide](./deployment-guide.md#stage-the-zip-and-create-the-function) writes three test events into `build/` (step 13), and this command calls the handler with the first of them:

```bash
python -c "import json; from src.api.lambda_handler import handler; r = handler(json.load(open('build/predict-event.json')), None); print(r['statusCode'], r['body'])"
```

```text
200 {"prediction":0,"predicted_label":"away win","home_win_probability":0.3296,"model_version":"v1.0"}
```

This is the same function and the same Mangum wrapper that run on AWS. Only the web server in front of them is missing. The answer is the worked example from the model docs.

### Step 3: Build the Zip

The build commands in the Deployment Guide's [Build the Zip](./deployment-guide.md#build-the-zip) section also need no AWS account. They produce `build/510-m3-nfl-predict-api.zip`, which is **231,252,596 bytes** unzipped and **63,452,500 bytes** zipped when built from the current files.

## How Do I Develop It?

### Where Is Each Piece?

- **The Lambda entry point:** `src/api/lambda_handler.py`.
- **The app it wraps (Phase 3):** `src/api/app.py` and `src/api/schemas.py`.
- **The packages in the zip:** `requirements-serve.txt`.
- **Tests:** `tests/test_lambda_handler.py` (6 tests).
- **The warning filter for tests:** `pytest.ini`.
- **The commands for AWS:** [Deployment Guide](./deployment-guide.md).

### What Rules Does the Entry Point Keep?

- **It imports only `mangum`, `src.api.app`, and `src.config`.** It must not import `pandas`, `mlflow`, `matplotlib`, or anything from `src/model/`, so the zip stays under the size limit. A test reads the file and checks this.
- **Mangum's start-up step is off** (`lifespan="off"`), and `build_handler` loads the model itself, once, on the first call. A test calls the handler three times and checks the model was read once.
- **Importing the file reads no model,** so it works on a machine with no saved model.
- **The zip keeps the project's folder layout** (`src/`, `config/`, `models/`), so `resolve_path` finds the same files on AWS as it does here.

### How Do I Run All the Tests?

```bash
python -m pytest
```

Expected: **88 passed** with no warnings: 3 from Phase 1, 27 from Phase 2, 17 from Phase 3, 6 from Phase 4, and 35 from Phase 5. Without `models/model.joblib`, 86 pass and 2 are skipped.

### How Do I Change a Package Version?

1. Change the pin in `requirements.txt` and the same pin in `requirements-serve.txt`, so the zip and the project agree.
2. Run the tests.
3. Rebuild the zip, and measure it again with the steps in [How Is the Measurement Repeated?](./implementation.md#how-is-the-measurement-repeated). The unzipped size must stay under **262,144,000 bytes** (250 MB). The last build left about 30.9 MB of room, and `pandas` alone would add 46.0 MB.
4. If the change is a new scikit-learn version, retrain first. The saved model records the version that built it, and the service refuses to start if the version in the zip differs.
5. Redeploy with [Redeploy After a Change](./deployment-guide.md#redeploy-after-a-change).
