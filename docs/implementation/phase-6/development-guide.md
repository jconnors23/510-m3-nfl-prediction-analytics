---
hide:
  - toc
---

# Phase 6 Development Guide

This guide shows how to build and run the project's two Docker images on your own computer: the `train` image, which trains the model (and can also run the data steps and the tests), and the `serve` image, which runs the prediction API. With Docker, a copy of the repository is all you need. Python and the packages come inside the image. What goes into the image, and what was checked, is on the [Phase 6 Implementation](./implementation.md) page.

## What Is Needed First?

- **Docker Desktop, running.** Check it with the command below. It must print both a `Client` and a `Server` section. If the server part is missing, start Docker Desktop and try again.

```bash
docker version
```

- **A copy of the repository.** No virtual environment, no trained model, and no AWS account are needed. Training reads the committed data.
- **Port 8000 free,** for the serve image. `make start` and a plain `mkdocs serve` both use it.

Terms such as image, container, bind mount, and published port are in the [Glossary](../extras/glossary.md#phase-6-docker).

## How Do I Train in a Container?

```bash
make docker-train
```

It runs three steps:

1. Makes the folder `build/docker/results/` on your computer, if it is missing, and lets any user write to it. The container runs as user 10001, and on Linux a mounted folder keeps this computer's permissions.
2. Builds the `train` image as `510-m3-nfl-train`. The first build downloads the base image and installs every package, which takes about a minute. Later builds reuse the cache and take about a second, unless `requirements.txt` changed.
3. Runs one container from it. The container trains, prints the same eight scoring lines as `make train`, logs one MLflow run inside itself, and stops. The container is then removed.

- **Expected scores:** validation **63.10%** (171 of 271) and test **59.06%** (88 of 149).
- **Three warnings about `git` are expected.** The image has no `.git/` folder, so MLflow cannot record the commit.
- **Only the run summary is kept.** The container's `results/` folder is your `build/docker/results/` folder, so its `run-summary.json` stays after the container is gone. Everything else it wrote is deleted with the container. Your `mlflow.db`, `models/`, and `mlflow-reference/` are not touched.

### Check That It Matches the Project

Compare the container's run summary with the committed one. The two lines must show the same SHA-256, `bd14becd53dc68dc59da97addb67102e3f2e5a9051b8805ba40537d4d4d56112`:

```bash
shasum -a 256 build/docker/results/run-summary.json results/run-summary.json
```

### Run the Tests in the Container

```bash
docker run --rm 510-m3-nfl-train python -m pytest
```

Expected: **93 passed, 2 skipped**. The two skipped tests need a saved model, and the train image has none until a container trains.

### Run the Data Steps in the Container

The train image also holds the Phase 1 data steps and the two web app data steps, so the whole project can run in Docker. Build the image first (`make docker-train` does this), then run each step in its own container. Each container starts from the committed files inside the image and is removed when it stops, so a file it writes is gone afterward unless a folder from your computer is mounted over it.

Download the nflverse games file. It prints the address, the time, `rows: 7548`, and `saved: data/raw/games.csv`:

```bash
docker run --rm 510-m3-nfl-train python -m src.data.fetch_raw
```

Clean the games into the model's table, with your `build/docker/processed/` folder mounted so the result is kept. Make the folder first, and let the container's user write to it, as `make docker-train` does for its folder:

```bash
mkdir -p build/docker/processed
```

```bash
chmod a+rwx build/docker/processed
```

```bash
docker run --rm -v "$PWD/build/docker/processed:/app/data/processed" 510-m3-nfl-train python -m src.data.clean
```

It prints the row counts at each filter, ending at 1,759 games, and writes `build/docker/processed/nfl_matchups_2020_2026.csv`. Its SHA-256 must be `7219e8a8672b900af9facbb54d8a28f9f2a34df9ede3b8385a735768082517fb`, the same as the committed table:

```bash
shasum -a 256 build/docker/processed/nfl_matchups_2020_2026.csv
```

Print a summary of the two model inputs for each season group (training 1,339 rows, validation 271, test 149):

```bash
docker run --rm 510-m3-nfl-train python -m src.model.features
```

Build the web app's two data files. They print `teams: 32` and `games: 272 (150 final or tie, 122 upcoming)`. The files stay inside the container, so these runs check that the steps work and leave the committed copies alone:

```bash
docker run --rm 510-m3-nfl-train python -m src.profiles
```

```bash
docker run --rm 510-m3-nfl-train python -m src.season
```

The S3 upload and download need AWS credentials, which the image does not hold. To run them, mount your own AWS settings folder, read-only:

```bash
docker run --rm -v ~/.aws:/home/app/.aws:ro 510-m3-nfl-train python -m src.data.upload_to_s3
```

## How Do I Run the API in a Container?

```bash
make docker-serve
```

It builds the `serve` image as `510-m3-nfl-serve`, which trains the model once during the build, then starts the API at `http://127.0.0.1:8000`. The terminal stays busy while it runs. Use a second terminal for the checks below.

### What the Output Means

- **`CACHED` on every build step:** nothing changed since the last build, so Docker reuses the saved image, training step included, and the build takes under a second.
- **`Uvicorn running on http://0.0.0.0:8000`:** that address is inside the container. On your computer, Docker publishes the port only on `127.0.0.1`, so only this machine can reach it.
- **Requests from `172.17.0.1`:** Docker's own address for your computer, as seen from inside the container. Every request from your browser or `curl` shows this address.
- **`GET / HTTP/1.1" 404 Not Found`:** the API has no page at `/`. Its addresses are `/predict`, `/health`, and the test page `/docs`. A browser also asks for `/favicon.ico` by itself, which gets a 404 too.

### Check That It Answers

```bash
curl http://127.0.0.1:8000/health
```

```json
{"status":"ok","model_version":"v1.0","scikit_learn_version":"1.9.1"}
```

The worked example:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}'
```

```json
{"prediction":0,"predicted_label":"away win","home_win_probability":0.3296,"model_version":"v1.0"}
```

The same answer as the local API. More requests, and what each field means, are in [How Do I Ask for a Prediction?](../phase-3/development-guide.md#how-do-i-ask-for-a-prediction). FastAPI's test page is at `http://127.0.0.1:8000/docs`.

### Stop It

Press `Ctrl+C` in the terminal where it runs. The log shows `Shutting down`, the container is removed, and port 8000 is free again.

### Run the Tests in the Serve Image

```bash
docker run --rm 510-m3-nfl-serve python -m pytest
```

Expected: **95 passed**, because this image holds a model.

## How Do I Change the Image?

- **The files:** `Dockerfile` and `.dockerignore` in the project folder.
- **Rebuilding:** both make commands build the image before they run it, so a change shows up the next time either command runs. A plain `docker run` uses the image as it was last built.
- **Adding a file to the image:** add a line starting with `!` to `.dockerignore`. Everything not listed is left out.
- **Changing a package:** change its pin in `requirements.txt`. The next build installs it again. The laptop's `.venv/` and the image then both follow the same file.
- **Changing the Python version:** change `PYTHON_VERSION` at the top of the `Dockerfile`, and keep it on the same minor version as the laptop and the Lambda function (3.13).

## How Do I Remove the Images?

The images use about 1.4 GB each on disk. To remove them:

```bash
docker image rm 510-m3-nfl-train 510-m3-nfl-serve
```

The next make command builds them again.
