---
hide:
  - toc
---

# Makefile

The `Makefile` in the project folder gives a short name to each of nine commands: training, the two test suites, the local API, the web app, the MLflow screen, the docs preview, and the two Docker images. For each one, this page gives its purpose, the exact command it runs, what it needs first, what it writes, and what you should see. Run every command from the project folder.

## Which Command Do I Use?

| Command | What it is for | Address | Stops by itself? |
| :--- | :--- | :--- | :--- |
| `make train` | Train the model and log the run | none | Yes, in under a minute |
| `make pytest` | Run every Python test | none | Yes, in about 45 seconds |
| `make web-test` | Run the web app's tests | none | Yes, in a few seconds |
| `make start` | Run the prediction API on this computer | `http://127.0.0.1:8000` | No, press Ctrl+C |
| `make start-web` | Run the web app's dev server | `http://localhost:5173` | No, press Ctrl+C |
| `make start-web-ml` | Open the MLflow screen | `http://127.0.0.1:5001` | No, press Ctrl+C |
| `make docs` | Preview this docs site | `http://127.0.0.1:8001` | No, press Ctrl+C |
| `make docker-train` | Train inside a Docker container | none | Yes, in about a minute the first time |
| `make docker-serve` | Run the prediction API inside a Docker container | `http://127.0.0.1:8000` | No, press Ctrl+C |

## What Must Be Set Up First?

- **The Python environment.** The Python commands run `.venv/bin/python`, so create `.venv/` with Python 3.13 and install the pinned packages once:

```bash
python3.13 -m venv .venv
```

```bash
.venv/bin/python -m pip install -r requirements.txt
```

- **The web app's packages.** `make web-test` and `make start-web` need `frontend/node_modules/`. Install them once with Node.js 22.12 or later, using the exact versions in `package-lock.json`. Run this inside `frontend/`:

```bash
npm ci
```

- **MkDocs,** for `make docs` only. It is not one of the project's Python packages, so the command uses the `mkdocs` on your PATH. Install it once with the versions the docs workflow uses:

```bash
pip install mkdocs==1.6.1 mkdocs-material==9.7.7 pymdown-extensions==12.0.1
```

- **Docker Desktop, running,** for the two Docker commands only.

### Changing the Python or npm Program

Two settings at the top of the `Makefile` name the programs used: `PYTHON` (default `.venv/bin/python`) and `NPM` (default `npm`). Either can be changed for one run, for example:

```bash
make pytest PYTHON=python3.13
```

## make train

**What it is for:** one training run. It fits the model on the training seasons, scores it, saves it, records the run in MLflow, and adds the run to the committed log in `mlflow-reference/`. Use it after changing a setting in `config/config.yaml`, after downloading new data, or before `make start` on a fresh copy of the repository.

- **Runs:** `MLFLOW_DISABLE_AGENT_HINT=1 .venv/bin/python -m src.model.train`. The setting turns off a hint line MLflow prints that is not about this project.
- **Needs:** the downloaded table `data/from-s3/nfl_matchups_2020_2026.csv`, which is committed, and `config/config.yaml`.
- **Writes:**
    - `models/model.joblib`, the model the API loads (git-ignored)
    - `mlflow.db` and `mlartifacts/`, MLflow's own record of the run (git-ignored)
    - `results/run-summary.json`, the committed summary of settings, scores, and weights. Its bytes change only when the settings, the data, or the scores change.
    - `mlflow-reference/`: the last run moves into `previous-runs/`, the new run is written to `latest-run/`, and `run-history.md` and `run-history.json` gain a row. These files change on every run, so commit them with the code.
- **What you see:** the scores, ending with `saved: mlflow-reference/latest-run`. The expected lines are in [Step 2: Train the Model](../../phase-2/development-guide.md#step-2-train-the-model). Validation accuracy is 63.10% and test accuracy 59.06%.
- **If the table is missing or a check fails,** it stops with one short message and writes nothing more.
- **More:** [How Do I Do a Training Run?](../../phase-2/development-guide.md#how-do-i-do-a-training-run).

## make pytest

**What it is for:** checking that the Python code still works after a change. It runs every test in `tests/`.

- **Runs:** `.venv/bin/python -m pytest`, with the settings in `pytest.ini`.
- **Needs:** nothing else. The tests use made-up data and stand-ins for S3, DynamoDB, and the model, so they need no AWS account and no internet.
- **Writes:** nothing in the project. Tests that write files use a temporary folder.
- **What you see:** **95 passed** once a model has been trained. Without `models/model.joblib`, for example on a fresh copy, **93 passed and 2 skipped**: the last test in `tests/test_api.py` and the last in `tests/test_lambda_handler.py` need the saved model.
- **To run one file:** `.venv/bin/python -m pytest tests/test_features.py`.
- **On GitHub:** the Test Python workflow runs this same command on every pull request. See [How Are the Python Tests Run?](./github-workflows.md#how-are-the-python-tests-run).

## make web-test

**What it is for:** checking the web app's code: the matchup math, the schedule labels, the team table, the feedback check, the tabs, and each page.

- **Runs:** `npm test` inside `frontend/`, which runs `vitest run` once and exits.
- **Needs:** `frontend/node_modules/` (see [What Must Be Set Up First?](#what-must-be-set-up-first)).
- **Writes:** nothing in the project, except the two every-game checks below.
- **What you see:** **65 passed** in 12 test files. On a fresh copy, **63 passed and 2 skipped**: `matchups.parity.test.ts` and `season.parity.test.ts` compare the browser's numbers with expected files in the git-ignored `build/` folder, and skip when those files are missing. When they run, they write `build/js-bodies.json` and `build/season-bodies.json`.

## make start

**What it is for:** running the prediction API on this computer, to try requests with `curl` or to give `make start-web` an API to call.

- **Runs:** `.venv/bin/python -m uvicorn src.api.app:app --port 8000`. uvicorn listens on `127.0.0.1` by default, so only this computer can reach it.
- **Needs:** `models/model.joblib`. Without it the service stops at start-up with "No saved model at models/model.joblib. Run python -m src.model.train first." Run `make train` once.
- **Port 8000 must be free.** `make docker-serve` and a plain `mkdocs serve` also use it.
- **Addresses:** `POST /predict`, `GET /health`, and FastAPI's test page at `http://127.0.0.1:8000/docs`. `/` has no page and returns 404.
- **What you see:** `Uvicorn running on http://127.0.0.1:8000`, then one line per request.
- **Try it:** [How Do I Ask for a Prediction?](../../phase-3/development-guide.md#how-do-i-ask-for-a-prediction). The worked example returns a home win probability of 0.3296.

## make start-web

**What it is for:** working on the web app. The page reloads as soon as a file in `frontend/src/` is saved.

- **Runs:** `npm run dev` inside `frontend/`, which starts Vite's dev server.
- **Needs:** `frontend/node_modules/`. For predictions, it also needs the API from `make start` running in another terminal. Without it, the page loads but every Analyze shows an error message.
- **Address:** `http://localhost:5173`. The port is fixed (`strictPort` in `vite.config.ts`): the live API's CORS list allows only this local address, so Vite stops instead of moving to another port when 5173 is taken.
- **How it reaches the API:** the page calls its own address, and Vite forwards `/predict`, `/health`, and `/feedback` to `http://127.0.0.1:8000`. To forward to another address, set `API_PROXY_TARGET` before the command.
- **The Feedback tab does not work locally.** The local API has no `/feedback` route, so sending the form gets status 404. The route exists only on AWS. See [Feedback Path](../features/feedback-path.md).
- **More:** [How Do I Run It Locally?](../../phase-5/development-guide.md#how-do-i-run-it-locally).

## make start-web-ml

**What it is for:** browsing training runs in MLflow's own screen: each run's 15 settings, 8 scores, saved files, and logged model, with charts to compare runs.

- **Runs:** `MLFLOW_DISABLE_AGENT_HINT=1 .venv/bin/python -m mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5001`.
- **Address:** `http://127.0.0.1:5001`. Port 5001, because macOS Control Center often holds MLflow's default, 5000.
- **Needs:** `mlflow.db`, made by the first `make train`. Without it, MLflow makes an empty database and the screen shows only its empty `Default` experiment.
- **What you see:** the list of experiments. Open `nfl-pregame-winner-v1` to see the runs. `Default` is created by MLflow in every database and is never used.
- **It shows only this computer's runs.** `mlflow.db` is git-ignored, so another copy of the repository shows only its own runs. The record every copy shares is [`mlflow-reference/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/mlflow-reference).
- **Expected warnings:** MLflow starts four worker processes, and each prints a `StarletteDeprecationWarning` about MLflow's own code. They are harmless.

## make docs

**What it is for:** previewing this docs site while editing it. The page reloads when a file in `docs/` or `mkdocs.yml` is saved.

- **Runs:** `mkdocs serve -a 127.0.0.1:8001`.
- **Needs:** MkDocs on your PATH (see [What Must Be Set Up First?](#what-must-be-set-up-first)).
- **Address:** `http://127.0.0.1:8001`, which redirects to `http://127.0.0.1:8001/510-m3-nfl-prediction-analytics/`, the same path as the published site (set by `site_url` in `mkdocs.yml`). Port 8001, because MkDocs' default, 8000, is the API's port.
- **Note:** the preview prints a broken link as a warning and keeps running. The published build stops on one. Before committing docs, run `mkdocs build --strict`, the same check the docs workflow runs.

## make docker-train

**What it is for:** checking that the project trains the same way inside a container, with its own Python and packages, as on this computer.

- **Runs four steps:**
    1. `mkdir -p build/docker/results`
    2. `chmod a+rwx build/docker/results`, because the container runs as user 10001, and on Linux the mounted folder keeps this computer's permissions.
    3. `docker build --target train -t 510-m3-nfl-train .`
    4. `docker run --rm -v "$(CURDIR)/build/docker/results:/app/results" 510-m3-nfl-train`
- **Needs:** Docker Desktop, running. No AWS account, no virtual environment, and no trained model.
- **Writes:** only `build/docker/results/run-summary.json` on this computer, through the mounted folder. Everything else the container writes (its model, MLflow database, and run log) is deleted with the container. Your `mlflow.db`, `models/`, and `mlflow-reference/` are not touched.
- **What you see:** the first build takes about a minute, most of it installing packages. Later builds take under a second unless `requirements.txt` changed. Then the same scores as `make train`, three warnings that `git` is not in the image (expected), and `saved: mlflow-reference/latest-run` inside the container.
- **Check it:** `build/docker/results/run-summary.json` should be byte for byte `results/run-summary.json`. See [Check That It Matches the Project](../../phase-6/development-guide.md#check-that-it-matches-the-project).

## make docker-serve

**What it is for:** running the prediction API from a container, to check that the packaged project answers the same as the local one.

- **Runs two steps:**
    1. `docker build --target serve -t 510-m3-nfl-serve .`. The build trains the model once, so the image carries its own `models/model.joblib`.
    2. `docker run --rm -p 127.0.0.1:8000:8000 510-m3-nfl-serve`
- **Needs:** Docker Desktop, running, and port 8000 free, so stop `make start` first.
- **Address:** `http://127.0.0.1:8000`, the same addresses as `make start`. Docker publishes the port on `127.0.0.1` only.
- **What you see:** `Uvicorn running on http://0.0.0.0:8000`. That address is inside the container. Requests show as coming from `172.17.0.1`, Docker's address for this computer. See [What the Output Means](../../phase-6/development-guide.md#what-the-output-means).
- **To stop it:** press Ctrl+C. Uvicorn prints `Shutting down`, and `--rm` removes the container.

## What Is Not a Make Command?

These are run rarely, so they stay as plain commands in their phase's guide:

- **Rebuilding the web app's data files** from the downloaded table: `python -m src.profiles` and `python -m src.season`. See the [Phase 5 Development Guide](../../phase-5/development-guide.md#how-do-i-rebuild-the-profiles-file).
- **The web app's production build:** `npm run build` in `frontend/`. See [How Do I Build and Preview the Site?](../../phase-5/development-guide.md#how-do-i-build-and-preview-the-site).
- **The data pipeline's four steps** (download, clean, upload to S3, download back). See the [Phase 1 Development Guide](../../phase-1/development-guide.md).
- **Adding older MLflow runs to the log:** `python -m src.model.export_mlflow --backfill`.
- **Deploying to AWS.** See the [Phase 4](../../phase-4/deployment-guide.md) and [Phase 5](../../phase-5/deployment-guide.md) Deployment Guides.
