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
- [Phase 5: Web App and Hosting](#phase-5-web-app-and-hosting)
- [Phase 6: Docker, README, and Final Check](#phase-6-docker-readme-and-final-check)
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
- **MLflow UI:** a web page for browsing runs, started with `mlflow ui --backend-store-uri sqlite:///mlflow.db`. See [the tracking UI](https://mlflow.org/docs/latest/ml/tracking/#tracking-ui).
- **Run summary (`results/run-summary.json`):** a small readable record of the latest run, committed to git. It has no run ID, time, or machine path, so it stays identical when the settings and data do not change.

## Phase 3: Local Prediction API

Built. See the [Phase 3 Brief](./phase-3/brief.md) and the [Phase 3 Implementation](./phase-3/implementation.md).

**Docs:** [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/latest/), [Uvicorn](https://uvicorn.dev/), [ASGI](https://asgi.readthedocs.io/en/latest/).

- **FastAPI:** the Python library that builds the web service. It routes each request to a function and returns JSON.
- **Pydantic:** the library FastAPI uses to check each request's fields, types, and ranges, and to describe the response. A request that fails the checks gets an error before any model code runs.
- **Uvicorn and ASGI:** a FastAPI app is only a Python object. It does not listen for requests on its own. Uvicorn is the program that does: it opens a port on the computer, receives each HTTP request, hands it to the app, and sends the app's answer back. They talk through ASGI, the standard interface between Python web servers and Python web apps. Uvicorn is used only on a laptop. On AWS Lambda there is no port to listen on, and Mangum takes its place (Phase 4).
- **Start-up step (lifespan):** code that runs once when the app starts. The API loads the saved model there, so each request reuses it.
- **NumPy, not pandas, in the API:** the API passes the two inputs to the model as a NumPy array. It does not import pandas, which would push the Lambda zip over its 250 MB limit (278.4 MB with pandas, 231.3 MB without). Training and cleaning still use pandas. See [Why Does the API Use NumPy Instead of pandas?](./phase-3/implementation.md#why-does-the-api-use-numpy-instead-of-pandas).
- **Test client:** FastAPI's way to call the app in memory, with no server and no network, so tests run fast.

## Phase 4: AWS Deployment

Planned. See [Remaining Phases](./remaining-phases.md#phase-4-aws-deployment).

**Docs:** [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html), [API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html), [Mangum](https://mangum.fastapiexpert.com/), [Amazon ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html).

- **AWS Lambda:** runs code only when a request arrives, with no server to manage.
- **Cold start:** the first request after a quiet period is slower, because a fresh copy of the function must start and load the model.
- **API Gateway:** gives the function a public web address, routes each request to it, and applies the request limit.
- **Mangum:** a small library that translates between the request format AWS Lambda hands a function (a dictionary) and the format FastAPI expects, so the same app runs on a laptop and in Lambda. It does not carry the request to Lambda. API Gateway does that. See [What Is Mangum?](./remaining-phases.md#what-is-mangum).
- **Lambda zip and size limit:** the function's code and packages are uploaded as a zip. The unzipped size must be 250 MB or less. This project's zip is 231.3 MB without `pandas`. See the [Package Size Check](./phase-4/package-size-check.md).
- **ECR:** stores Docker images. It is used only if the Lambda zip turns out to be too large.

## Phase 5: Web App and Hosting

Planned. See [Remaining Phases](./remaining-phases.md#phase-5-web-app-and-hosting).

**Docs:** [Vite](https://vite.dev/guide/), [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html), [CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html).

- **Vite:** the tool that runs the web app on a laptop during development and builds the files that are published.
- **CloudFront:** serves the built web app's files over HTTPS from a private S3 bucket.

## Phase 6: Docker, README, and Final Check

Planned. See [Remaining Phases](./remaining-phases.md#phase-6-docker-readme-and-final-check).

**Docs:** [Docker](https://docs.docker.com/), [multi-stage builds](https://docs.docker.com/build/building/multi-stage/).

- **Docker:** packages a program with everything it needs, so it runs the same on any machine.
- **Image:** the packaged snapshot that Docker builds.
- **Dockerfile and build target:** a Dockerfile lists the build steps. It can define several build targets, here `train` and `serve`.

## General Machine Learning Ideas

- **Supervised learning:** learning from examples that come with known answers. Every game has a known winner, so the model can be checked against answers it has not seen.
- **Binary classification:** a task with exactly two possible answers. Here: did the home team win (1) or not (0)? The alternative, regression, predicts a number on a scale.
- **Training, validation, and test sets:** training data fits the model, validation data gives the score to report, and test data is a final check on games the model never touched.
- **Data leakage:** a feature that uses information from after the thing being predicted, which inflates scores. Using only earlier weeks prevents it, and a check stops the run if a week-1 feature is not 0.
- **Overfitting:** memorizing the training games instead of learning a pattern that carries over, so the training score is high and the score on unseen games is lower.

## General Tooling and Reproducibility

**Docs:** [pytest](https://docs.pytest.org/en/stable/), [`venv`](https://docs.python.org/3/library/venv.html), [`hashlib`](https://docs.python.org/3/library/hashlib.html), [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation).

- **Reproducibility:** getting the same result again from the same inputs on any machine. Here it comes from pinned versions, a fixed seed, settings in one file, and a data fingerprint. See [Reproducing the Pipeline End to End](./phase-2/reproduce-end-to-end.md).
- **Pinned version:** an exact version in `requirements.txt`, such as `scikit-learn==1.9.1`, so every install is identical. A saved model may fail to load under another scikit-learn version.
- **Virtual environment:** a private folder of Python packages for one project, so projects do not interfere.
- **`config.yaml`:** the one file holding every adjustable setting. YAML is a text format of indented `name: value` lines.
- **Data fingerprint (SHA-256):** a short code worked out from every byte of a file. If one byte changes, the code changes, so two runs with the same fingerprint used the same data.
- **pytest and stand-in objects:** pytest runs the tests in `tests/`. The tests use made-up data and stand-ins for the real S3 client and model, so they need no internet and no AWS account.
