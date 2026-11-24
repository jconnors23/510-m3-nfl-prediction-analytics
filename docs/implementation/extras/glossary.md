---
hide:
  - toc
---

# Glossary

Key terms and tools, grouped by the phase where they first matter, followed by general ideas that apply across the project. Each phase starts with a **Docs** line that links to the official documentation for its tools. The links go to the latest documentation, and the installed versions are pinned in `requirements.txt`, so a page may describe a newer feature.

- [Phase 1: Data Pipeline](#phase-1-data-pipeline)
- [Phase 2: Features, Training, and Tracking](#phase-2-features-training-and-tracking)
- [Phase 3: Local Prediction API](#phase-3-local-prediction-api)
- [Phase 4: AWS Deployment](#phase-4-aws-deployment)
- [Phase 5: Front-End Web App](#phase-5-front-end-web-app)
- [Phase 6: Docker](#phase-6-docker)
- [Phase 7: Review](#phase-7-review)
- [General Machine Learning Ideas](#general-machine-learning-ideas)
- [General Tooling and Reproducibility](#general-tooling-and-reproducibility)

## Phase 1: Data Pipeline

**Docs:** [nflverse nfldata](https://github.com/nflverse/nfldata), [requests](https://requests.readthedocs.io/en/latest/), [pandas](https://pandas.pydata.org/docs/), [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html), [boto3](https://docs.aws.amazon.com/boto3/latest/), [IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html).

- **nflverse:** the open project that publishes the games file, one row per NFL game since 1999. See the [`games.csv` file](https://github.com/nflverse/nfldata/blob/master/data/games.csv).
- **requests:** the Python library that downloads the games file.
- **pandas:** the Python library that holds the game tables and does the filtering and grouping. It is used in cleaning (Phase 1) and in building the model inputs (Phase 2).
- **NumPy:** the Python library for number work that pandas and scikit-learn are built on. See the [documentation](https://numpy.org/doc/stable/).
- **Amazon S3:** storage for files in the cloud. This project keeps one cleaned table in a private bucket.
- **Bucket and key:** a bucket is a named container in S3, and a key is a file's path inside it.
- **boto3:** the Python library for calling AWS. It finds credentials itself, from environment variables or `~/.aws`, so no key is written in the project.
- **IAM and least privilege:** IAM decides who may do what in AWS, and least privilege gives each identity only the access it needs. See the [best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html).

## Phase 2: Features, Training, and Tracking

**Docs:** [scikit-learn](https://scikit-learn.org/stable/), [MLflow](https://mlflow.org/docs/latest/), [MLflow tracking](https://mlflow.org/docs/latest/ml/tracking/), [MLflow Models](https://mlflow.org/docs/latest/ml/model/), [joblib](https://joblib.readthedocs.io/en/stable/), [skops](https://skops.readthedocs.io/en/stable/), [matplotlib](https://matplotlib.org/stable/), [SQLite](https://www.sqlite.org/docs.html).

### Features and the Split

- **Feature:** one input number the model uses. This project has two, both built from earlier games of the same season: `win_pct_differential` (home win percentage minus away) and `point_diff_per_game_differential` (home point margin per game minus away).
- **Feature engineering:** building features from raw columns. Here, scores and weeks become each team's win percentage and margin so far, then the two differences.
- **Target (label):** the answer the model learns to predict, `home_win` (1 or 0). It is the only column that uses the current game's result.
- **Split by season:** training games (2020 to 2024) fit the model, validation games (2025) give the reported score, and test games (2026 weeks 1 to 10) are a final check. Whole seasons go to one group, so the model never trains on games played after the ones it is scored on.

### The Model

- **Logistic regression:** a simple classifier. It multiplies each feature by a learned weight, adds an intercept, and passes the total through an S-shaped function that gives a probability from 0 to 1. See the [guide](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression) and the [`LogisticRegression` class](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html).
- **Weight and intercept:** a weight says how much one feature moves the prediction. The intercept is the starting value, which here captures the average home-field edge.
- **Probability and threshold:** the model outputs the chance that the home team wins. Above 0.5 picks the home team, and exactly 0.5 picks the away team.
- **Standardization (scaler):** subtracting each feature's average and dividing by its spread, measured on training games only. The two features differ in size by about 30 times, so this lets the model weigh them fairly. See [`StandardScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).
- **Pipeline:** one object chaining the scaler and the model, so a saved model can never be used without its scaling. See [`Pipeline`](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html).
- **Parameter and hyperparameter:** a parameter is learned in training, such as a weight. A hyperparameter is chosen beforehand. Neither is the same as an MLflow parameter, which is a setting written down for a run.
- **Regularization and `C`:** a penalty that holds weights near zero so the model does not memorize the training games. `C` is the inverse of its strength, so a smaller `C` is a stronger penalty. The default is 1.0.
- **Solver (`lbfgs`) and `max_iter`:** the solver finds the best weights by repeatedly adjusting them until the errors stop falling. `max_iter` caps the adjustments. It finishes in about 6 here, so 1000 is a safety margin.
- **Random seed:** a starting number for random choices, so reruns match. The `lbfgs` solver uses no randomness, so the seed only protects later random steps.

### Scoring

- **Accuracy and baseline:** accuracy is the share of games where the pick matches the result. It is shown next to the baseline, the score of always picking the home team. See [`accuracy_score`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html).
- **Log loss:** a score for the probabilities, not just the picks. Each game gets a penalty that is small if the model gave a high chance to what really happened and large if it gave a low one. Lower is better, and saying 50-50 on every game scores 0.6931. It is not logged for training games, because the model is fitted by pushing it down there. See [`log_loss`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html).
- **Calibration:** whether percentages match how often things happen, so 70% should be right about 7 times in 10. Log loss rewards it and accuracy cannot see it. See [probability calibration](https://scikit-learn.org/stable/modules/calibration.html).
- **Confusion matrix:** a 2 by 2 table of picks against results. The diagonal holds the correct picks. See [`confusion_matrix`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html).
- **matplotlib and the Agg backend:** matplotlib draws the confusion-matrix image. The [`Agg` backend](https://matplotlib.org/stable/users/explain/figure/backends.html) draws to a file without opening a window.

### Saving the Model

- **joblib:** saves a Python object to a file and loads it back. It is the usual way to save a scikit-learn model. See [model persistence](https://scikit-learn.org/stable/modules/model_persistence.html).
- **pickle:** the Python format that joblib builds on. Only load a saved file you trust. See [`pickle`](https://docs.python.org/3/library/pickle.html).
- **`model.joblib`:** the working copy of the model, saved with the input names, the model version, the scikit-learn version, and the training seasons. It is the file the API loads.

### MLflow Tracking

- **MLflow:** an open-source tool for keeping a record of machine learning work. This project uses its tracking part only: each run writes down its settings, scores, and files. It does not use the model registry or serving tools.
- **Experiment and run:** an experiment is a named group of runs (`nfl-pregame-winner-v1`). A run is one execution of training, with a run ID, a name (`LogisticRegression-v1.0`), and a status such as FINISHED or FAILED.
- **Parameter (MLflow):** a setting written down for a run as text, such as the seed, `C`, the seasons, the row counts, the scikit-learn version, and the data fingerprint. Each run records 15.
- **Metric:** a number written down for a run, such as an accuracy. Each run records 8.
- **Tag:** a label on a run. MLflow adds the git commit, branch, repository address, script name, and user itself.
- **Artifact:** a file stored with a run. Each run stores three: the saved model file, the confusion-matrix image, and a copy of `config.yaml`.
- **Backend store:** where MLflow keeps experiments, runs, parameters, metrics, and tags. Here it is a database file, `mlflow.db`. See [backend stores](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/).
- **SQLite and the tracking URI:** SQLite is a database that lives in one file and needs no server. The tracking URI is the address MLflow uses to find the store, here `sqlite:///` plus the full path of `mlflow.db`. The path starts with `/`, so the address has four slashes in a row.
- **Artifact store:** where MLflow keeps files. Here it is `mlartifacts/`, with a subfolder per run. The location is set when an experiment is created and cannot be changed afterward. See [artifact stores](https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/).
- **MLflow model format and flavor:** a standard folder layout for a saved model, so MLflow can load it back: a description file (`MLmodel`), the serialized model, and files listing the needed packages. The flavor names the library that built the model, here scikit-learn. See the [scikit-learn flavor](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.sklearn.html).
- **Logged model:** in MLflow 3, a model saved in that format is its own entry linked to the run, stored in a `models/` folder in the artifact store and not in the run's file list.
- **MLflow UI:** a web page for browsing runs, started with `make start-web-ml` at `http://127.0.0.1:5001`. The command runs `mlflow ui --backend-store-uri sqlite:///mlflow.db` on port 5001. See [the tracking UI](https://mlflow.org/docs/latest/ml/tracking/#tracking-ui).
- **Run summary (`results/run-summary.json`):** a small readable record of the latest run, committed to git. It has no run ID, time, or machine path, so it stays identical when the settings and data do not change.

## Phase 3: Local Prediction API

Built. See [Phase 3, Overview](../phase-3/index.md) and [Phase 3, Implementation](../phase-3/index.md#implementation).

**Docs:** [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/latest/), [Uvicorn](https://uvicorn.dev/), [ASGI](https://asgi.readthedocs.io/en/latest/).

- **FastAPI:** the Python library that builds the web service. It routes each request to a function and returns JSON.
- **Pydantic:** the library FastAPI uses to check each request's fields, types, and ranges, and to describe the response. A request that fails the checks gets an error before any model code runs.
- **Uvicorn and ASGI:** a FastAPI app is only a Python object. It does not listen for requests on its own. Uvicorn is the program that does: it opens a port on the computer, receives each HTTP request, hands it to the app, and sends the app's answer back. They talk through ASGI, the standard interface between Python web servers and Python web apps. Uvicorn is used only on a laptop. On AWS Lambda there is no port to listen on, and Mangum takes its place (Phase 4).
- **Start-up step (lifespan):** code that runs once when the app starts. The API loads the saved model there, so each request reuses it.
- **NumPy, not pandas, in the API:** the API passes the two inputs to the model as a NumPy array. It does not import pandas, which would push the Lambda zip over its 250 MB limit (278.4 MB with pandas, 231.3 MB without). Training and cleaning still use pandas. See [Why Does the API Use NumPy Instead of pandas?](../phase-3/index.md#why-does-the-api-use-numpy-instead-of-pandas).
- **Test client:** FastAPI's way to call the app in memory, with no server and no network, so tests run fast.

## Phase 4: AWS Deployment

Built. See [Phase 4, Overview](../phase-4/index.md) and [Phase 4, Implementation](../phase-4/index.md#implementation).

**Docs:** [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html), [API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html), [Mangum](https://mangum.fastapiexpert.com/), [Amazon ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html).

- **AWS Lambda:** runs code only when a request arrives, with no server to manage.
- **API Gateway:** gives the function a public web address, and routes each request to it.
- **Mangum:** a small library that translates between the request format AWS Lambda hands a function (a dictionary) and the format FastAPI expects, so the same app runs on a laptop and in Lambda. It does not carry the request to Lambda. API Gateway does that. See [What Is Mangum?](../phase-4/index.md#what-is-mangum).
- **Lambda zip and size limit:** the function's code and packages are uploaded as a zip. The unzipped size must be 250 MB or less. This project's zip is 231.3 MB without `pandas`. See [Phase 4, Step 3: Measure the Package Size](../phase-4/index.md#step-3-measure-the-package-size).
- **Environment variable:** a named setting passed to the function when it starts. This function has one, `JOBLIB_MULTIPROCESSING=0`, which stops joblib from checking for multiprocessing support that Lambda does not have.
- **CodeSha256:** the SHA-256 fingerprint AWS stores for the zip a function was created from. When it equals the hash of the local zip, Lambda is running the file built here.
- **ECR:** stores Docker images. It is used only if the Lambda zip turns out to be too large.

## Phase 5: Front-End Web App

Built. See [Phase 5, Overview](../phase-5/index.md) and [Phase 5, Implementation Part 1](../phase-5/index.md#implementation-part-1).

**Docs:** [Vite](https://vite.dev/guide/), [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/docs/), [npm](https://docs.npmjs.com/), [Vitest](https://vitest.dev/), [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html), [CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html).

- **Vite:** the tool that runs the web app on a laptop during development and builds the files that are published.
- **React and TypeScript:** React is a JavaScript library that builds a page from small pieces and redraws them when the data changes. TypeScript is JavaScript with types, so a wrong field name in the API's answer is caught when the app is built and not when someone uses it.
- **npm and the lock file:** npm installs the app's JavaScript packages. `package-lock.json` records the exact version of every package, and `npm ci` installs exactly those versions, the way the pinned versions in `requirements.txt` do for Python.
- **Vitest:** the test runner that works with Vite. It does for the web app's code what pytest does for the Python code.
- **`VITE_` variables:** Vite copies only the variables whose names start with `VITE_` into the browser code, and writes their values into the built files, so nothing secret belongs in them. See [Env Variables and Modes](https://vite.dev/guide/env-and-mode).
- **Dev server proxy:** while developing, the Vite server can forward some requests (here `/predict`, `/health`, and `/feedback`) to another address (here the local API). The browser talks only to the dev server. See [server options](https://vite.dev/config/server-options).
- **CloudFront:** serves the built web app's files over HTTPS from a private S3 bucket.
- **Origin access control:** the setting that lets CloudFront, and only CloudFront, read a private S3 bucket. See [restricting access to an S3 origin](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html).
- **Default root object:** the file CloudFront returns when the address has no path. Here it is `index.html`. See [specifying a default root object](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DefaultRootObject.html).
- **Invalidation:** tells CloudFront to drop its saved copy of a file, so the next visitor gets the new one. See [invalidating files](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html).
- **OpenID Connect (OIDC) for GitHub Actions:** a way for a workflow run to sign in to AWS without a stored key. GitHub gives the run a signed token that names the repository and branch, and AWS trades it for a role's short-lived credentials if the role trusts that repository and branch. See [configuring OpenID Connect in AWS](https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services).
- **IAM role:** a set of AWS permissions that something takes on for a short time, in place of a permanent user and key. Here, `510-m3-nfl-web-app-deploy-role` lets the deploy workflow upload the web app and invalidate its distribution.
- **Repository secret:** a value saved in the GitHub repository's settings that a workflow can read but that does not appear in the code or the run logs. Here, `AWS_WEB_APP_DEPLOY_ROLE_ARN` holds the deploy role's address.
- **Fontsource:** npm packages of open-source fonts. Vite copies the font files into the build, so the page loads them from its own address. See [Fontsource](https://fontsource.org/).
- **Contrast ratio:** how far apart two colors are in brightness, from 1 to 1 (the same) to 21 to 1 (black on white). The accessibility guideline WCAG asks for at least 4.5 to 1 for body text and 3 to 1 for graphics. See [understanding contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).

## Phase 6: Docker

Built. See [Phase 6, Overview](../phase-6/index.md) and [Phase 6, Implementation](../phase-6/index.md#implementation).

**Docs:** [Docker](https://docs.docker.com/), [what is a container](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/), [multi-stage builds](https://docs.docker.com/build/building/multi-stage/), [bind mounts](https://docs.docker.com/engine/storage/bind-mounts/), [publishing ports](https://docs.docker.com/engine/network/port-publishing/).

- **Docker:** the tool that builds images and runs containers. On a Mac, Docker Desktop runs a small Linux system in the background, and every container runs inside it. That is why the project's container runs Linux even though this computer runs macOS.
- **Image:** a read-only package of everything a program needs to run: a cut-down Linux system, Python 3.13, the exact packages in `requirements.txt`, and the project's code, settings, and data. Here there are two images, `510-m3-nfl-train` and `510-m3-nfl-serve`.
- **Container:** a running copy of an image, with its own files, Python, programs, and network address, kept apart from this computer's. Every file it writes is deleted when the container is removed (`docker run --rm` removes it when it stops). In this project:
    - **The train container** starts, trains the model, logs one MLflow run inside itself, and stops. It reads the committed data, so it needs no AWS account and no download.
    - **The serve container** runs the prediction API until it is stopped, the same API that `make start` runs on the laptop.
    - **How it differs from a virtual environment:** a virtual environment (`.venv/`) keeps only the Python packages separate, and still uses this computer's Python and system. A container also brings its own Python and system, so it runs the same on any computer with Docker.
- **Dockerfile:** the text file that lists the steps for building an image: which base image to start from, which packages to install, which files to copy in, and which command to run when a container starts.
- **Build target (multi-stage build):** one Dockerfile can define several named stages, and `docker build --target <name>` builds the image up to that stage. Here a shared `base` stage installs everything once, and the `train` and `serve` targets start from it, so both use the same Python and the same pins.
- **Base image:** the image a Dockerfile starts from. Here it is the official `python:3.13.14-slim` image, a small Linux system with Python already installed, pinned to an exact patch version.
- **`.dockerignore`:** lists which files may be copied into an image. This project's file leaves everything out unless it is named, so keys, local databases, and `.git/` never enter the image.
- **Bind mount:** connects a folder on this computer to a folder inside a container, so what the container writes there is kept after it stops. `make docker-train` mounts `build/docker/results/` over the container's `results/`, so its run summary can be compared with the committed one.
- **Published port:** a port on this computer that forwards to a port inside a container. `make docker-serve` publishes `127.0.0.1:8000`, so `curl http://127.0.0.1:8000/health` on the laptop reaches the API inside the container, and nobody else on the network can.
- **Non-root user:** the image runs the code as an ordinary user named `app`, not as the all-powerful `root` user, so a problem in the code cannot change the image's system files.

## Phase 7: Review

Built. See [Phase 7, Overview](../phase-7/index.md). The review adds no code. These are the tools behind the docs site.

**Docs:** [MkDocs](https://www.mkdocs.org/), [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/), [Mermaid](https://mermaid.js.org/), [GitHub Pages](https://docs.github.com/en/pages), [GitHub Actions](https://docs.github.com/en/actions).

- **MkDocs:** builds the pages in `docs/` into a documentation site. A strict build (`mkdocs build --strict`) fails on a broken link, so it doubles as a link check.
- **Material for MkDocs:** the theme that gives the site its layout, navigation, and diagram support.
- **Mermaid:** a text format for diagrams, written inside a code block in a page and drawn by the site.
- **GitHub Pages:** a GitHub feature that serves a built site from a repository. Pages is set to deploy from GitHub Actions, so the workflow uploads the built `site/` folder and Pages serves it. See [deploying your docs](https://www.mkdocs.org/user-guide/deploying-your-docs/).
- **GitHub Actions:** GitHub's built-in way to run a job when something happens in the repository. The workflow `.github/workflows/deploy-docs.yml` runs when docs change on `main`: it installs MkDocs, runs a strict build, and publishes the site. The project has four workflows: `deploy-docs.yml` and `deploy-web-app.yml` publish, and on each pull request `test-python.yml` runs the Python tests and `test-web.yml` runs the web app's tests and build when `frontend/` changes. See [GitHub Workflows](./development/github-workflows.md) and the [documentation](https://docs.github.com/en/actions).
- **README:** the file at the top of the repository that a visitor reads first. It links to the dataset, the live API, and the live web app.

## General Machine Learning Ideas

- **Supervised learning:** learning from examples that come with known answers. Every game has a known winner, so the model can be checked against answers it has not seen.
- **Binary classification:** a task with exactly two possible answers. Here: did the home team win (1) or not (0)? The alternative, regression, predicts a number on a scale. See [Why Binary Classification and Not Regression?](../design-manifest.md#why-binary-classification-and-not-regression).
- **Training, validation, and test sets:** training data fits the model, validation data gives the score to report, and test data is a final check on games the model never touched.
- **Data leakage:** a feature that uses information from after the thing being predicted, which inflates scores. Using only earlier weeks prevents it, and a check stops the run if a week-1 feature is not 0.
- **Overfitting:** memorizing the training games instead of learning a pattern that carries over, so the training score is high and the score on unseen games is lower.

## General Tooling and Reproducibility

**Docs:** [pytest](https://docs.pytest.org/en/stable/), [`venv`](https://docs.python.org/3/library/venv.html), [`hashlib`](https://docs.python.org/3/library/hashlib.html), [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation).

- **Reproducibility:** getting the same result again from the same inputs on any machine. Here it comes from pinned versions, a fixed seed, settings in one file, and a data fingerprint. See [How Do I Reproduce the Result From a Clean Checkout?](../phase-2/index.md#how-do-i-reproduce-the-result-from-a-clean-checkout).
- **Pinned version:** an exact version in `requirements.txt`, such as `scikit-learn==1.9.1`, so every install is identical. A saved model may fail to load under another scikit-learn version.
- **Virtual environment:** a private folder of Python packages for one project, so projects do not interfere.
- **`config.yaml`:** the one file holding every adjustable setting. YAML is a text format of indented `name: value` lines.
- **Data fingerprint (SHA-256):** a short code worked out from every byte of a file. If one byte changes, the code changes, so two runs with the same fingerprint used the same data.
- **pytest and stand-in objects:** pytest runs the tests in `tests/`. The tests use made-up data and stand-ins for the real S3 client and model, so they need no internet and no AWS account.
