---
hide:
  - toc
---

# Running Locally

Do these steps in order, from the project folder, in macOS Terminal or a Linux shell such as Ubuntu on WSL. Windows PowerShell is not supported. When they are done, the model is trained, the API has answered on this computer, and a Docker container has returned the same prediction. The sections after that are for changing one part of the project. Each command is described on [Makefile](./makefile.md). Tool versions are on the [Tooling Guide](./tooling-guide.md).

## Set Up

Install Python 3.13, `make`, and Docker Desktop. For the web app, install Node.js 22.12 or later.

```bash
python3.13 -m venv .venv
```

```bash
.venv/bin/python -m pip install -r requirements.txt
```

The first command creates the environment and the second installs the packages. If a `.venv` folder already exists, delete it and run both again.

Start Docker Desktop. On Windows, use the Ubuntu terminal, not PowerShell, and turn on WSL integration for that distro (Docker Desktop: Settings, Resources, WSL Integration). Open a new terminal there. This check should print a Client section and a Server section:

```bash
docker version
```

If it says permission denied, run `wsl --shutdown` from Windows, then open a new terminal and run `docker version` again.

From inside `frontend/`, install the web app's packages:

```bash
npm ci
```

## Train

```bash
make train
```

This writes `models/model.joblib`. The local API loads that file.

## Test the API Locally

Start the API on this computer and call its `/predict` route. Leave this terminal running.

```bash
make start
```

In a second terminal, send the worked example:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}'
```

The home win probability is **0.3296**. FastAPI's test page is `http://127.0.0.1:8000/docs`.

## Test the Same API in Docker

The Docker image installs its own packages and has entry points for training and serving, so it runs with no virtual environment. Its prediction must match the local API's.

In the terminal where `make start` is running, press Ctrl+C. The container uses `http://127.0.0.1:8000` too.

```bash
make docker-train
```

```bash
make docker-serve
```

`make docker-train` trains inside the image and writes `build/docker/results/run-summary.json`. `make docker-serve` serves the API from the image's own model. In the second terminal, send the same `curl` as above. The home win probability is **0.3296**.

This prints nothing when the container's training summary matches the project's:

```bash
diff build/docker/results/run-summary.json results/run-summary.json
```

Press Ctrl+C in the serve terminal. The container stops and port 8000 is free.

## Run the Web App

Start the local API again with `make start`. In another terminal:

```bash
make start-web
```

Open `http://localhost:5173`. The page sends predictions to the local API.

## How Do I Work on the Model?

Use this when changing a setting, the split, an input, or the data. [Phase 2 Development Guide](../../phase-2/development-guide.md) has the detail.

1. Edit `config/config.yaml`, or the code under `src/model/`.
2. Train the model:

```bash
make train
```

3. Open the MLflow screen to compare this run with earlier ones:

```bash
make start-web-ml
```

4. Run the Python tests:

```bash
make pytest
```

5. Commit the changed files in `results/` and `mlflow-reference/` with the code. See [What Is Kept in Git After a Retrain?](../../phase-2/development-guide.md#what-is-kept-in-git-after-a-retrain).

## How Do I Work on the API?

Use this when changing a route, a rule, or what a response holds. [Phase 3 Development Guide](../../phase-3/development-guide.md) has the detail.

1. Train the model once, if `models/model.joblib` does not exist:

```bash
make train
```

2. Start the service:

```bash
make start
```

3. In another terminal, check that it answers:

```bash
curl http://127.0.0.1:8000/health
```

4. Send the worked example, which should return a home win probability of 0.3296:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}'
```

5. To restart the service on every code change, see [How Do I Restart the Service on Every Change?](../../phase-3/development-guide.md#how-do-i-restart-the-service-on-every-change).
6. Run the Python tests:

```bash
make pytest
```

## How Do I Work on the Web App?

Use this when changing the page, the tabs, or the matchup code. [Phase 5 Development Guide](../../phase-5/development-guide.md) has the detail.

1. Start the local API in one terminal:

```bash
make start
```

2. Start the dev server in a second terminal:

```bash
make start-web
```

3. Open `http://localhost:5173`. The page reloads each time a file in `frontend/src/` is saved.
4. Run the web tests:

```bash
make web-test
```

5. Before finishing, check that the production build compiles. Run it inside `frontend/`:

```bash
npm run build
```

The Feedback tab does not work against the local API, which has no `/feedback` route. See [make start-web](./makefile.md#make-start-web).

## How Do I Work on the Docs?

Use this when editing a page under `docs/`. [Phase 6 Development Guide](../../phase-6/development-guide.md) covers the Docker side, and the docs workflow is in [GitHub Workflows](./github-workflows.md#how-are-the-docs-published).

1. Start the preview:

```bash
make docs
```

2. Open `http://127.0.0.1:8001/510-m3-nfl-prediction-analytics/`. The page reloads on each save.
3. The preview prints a broken link as a warning and keeps running. Before committing, run the same strict build the docs workflow runs:

```bash
mkdocs build --strict
```

## How Do I Check the Container?

Follow [Test the Same API in Docker](#test-the-same-api-in-docker). To run the tests inside the images, see [Where Do the Tests Run?](./testing-guide.md#where-do-the-tests-run). The image layout is in the [Phase 6 Development Guide](../../phase-6/development-guide.md).
