---
hide:
  - toc
---

# Glossary

The machine learning ideas and the tools used in this project, with how each is used here. Tools link to their official documentation, and the first section lists all of them in one place. The links go to the latest documentation, and the installed versions are pinned in `requirements.txt`, so a page may describe a newer feature.

## Tool Documentation

- **Tracking:** [MLflow](https://mlflow.org/docs/latest/), [MLflow tracking](https://mlflow.org/docs/latest/ml/tracking/), [MLflow Models](https://mlflow.org/docs/latest/ml/model/), [SQLite](https://www.sqlite.org/docs.html).
- **Modeling and data:** [scikit-learn](https://scikit-learn.org/stable/), [pandas](https://pandas.pydata.org/docs/), [NumPy](https://numpy.org/doc/stable/), [joblib](https://joblib.readthedocs.io/en/stable/), [skops](https://skops.readthedocs.io/en/stable/), [matplotlib](https://matplotlib.org/stable/), [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation).
- **Data source and download:** [nflverse nfldata](https://github.com/nflverse/nfldata), [requests](https://requests.readthedocs.io/en/latest/).
- **AWS storage and access:** [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html), [boto3](https://docs.aws.amazon.com/boto3/latest/), [IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html).
- **Serving and deployment (later phases):** [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/latest/), [Mangum](https://mangum.fastapiexpert.com/), [Docker](https://docs.docker.com/), [Amazon ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html), [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html), [API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html), [CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html), [Vite](https://vite.dev/guide/).
- **Testing and environment:** [pytest](https://docs.pytest.org/en/stable/), Python's [`venv`](https://docs.python.org/3/library/venv.html), [`hashlib`](https://docs.python.org/3/library/hashlib.html), and [`pickle`](https://docs.python.org/3/library/pickle.html).

## Machine Learning Ideas

- **Supervised learning:** learning from examples that come with known answers. Every game has a known winner, so the model can be checked against answers it has not seen.
- **Binary classification:** a task with exactly two possible answers. Here: did the home team win (1) or not (0)? The alternative, regression, predicts a number on a scale.
- **Feature:** one input number the model uses. This project has two, both built from earlier games of the same season: `win_pct_differential` (home win percentage minus away) and `point_diff_per_game_differential` (home point margin per game minus away). A positive value favors the home team, and a team with no games counts as 0.5 and 0.0.
- **Feature engineering:** building features from raw columns. Here, scores and weeks become each team's win percentage and margin so far, then the two differentials.
- **Target (label):** the answer the model learns to predict, `home_win`. It is the only column that uses the current game's result.
- **Data leakage:** a feature that uses information from after the thing being predicted, which inflates scores. Using only earlier weeks prevents it, and a check stops the run if a week-1 feature is not 0.
- **Training, validation, and test sets:** training games (2020 to 2024) fit the model, validation games (2025) give the reported score, and test games (2026 weeks 1 to 10) are a final check. The split is by season, not at random, so the model never trains on games played after the ones it is scored on.
- **Overfitting:** memorizing the training games instead of learning a pattern that carries over, so the training score is high and the score on unseen games is lower.

## The Model and Training

- **Logistic regression:** a simple classifier. It multiplies each feature by a learned weight, adds an intercept, and passes the total through the logistic (S-shaped) function, which gives a probability from 0 to 1. A weight says how much one feature moves the prediction, and the intercept is the starting value, which here captures the average home-field edge. See the scikit-learn [guide](https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression) and the [`LogisticRegression` class](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html).
- **Probability and threshold:** the model outputs the chance that the home team wins. Above 0.5 picks the home team, and exactly 0.5 picks the away team.
- **Standardization (scaler):** subtracting each feature's average and dividing by its spread, measured on training games only. The two features differ in size by about 30 times, so this lets the model weigh them fairly. See [`StandardScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).
- **Pipeline:** one object chaining the scaler and the model, so a saved model can never be used without its scaling. See [`Pipeline`](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html).
- **Parameter and hyperparameter:** a parameter is learned in training, such as a weight. A hyperparameter is chosen beforehand. Neither is the same as an MLflow parameter, which is a setting written down for a run.
- **Regularization and `C`:** a penalty that holds weights near zero so the model does not memorize the training games. `C` is the inverse of its strength, so a smaller `C` is a stronger penalty. The default is 1.0.
- **Solver (`lbfgs`) and `max_iter`:** the solver finds the best weights. `lbfgs` repeatedly adjusts them to lower the errors until they stop improving, and it suits a small table. `max_iter` caps the adjustments. It finishes in about 6 here, so 1000 is a safety margin.
- **Random seed:** a starting number for random choices, so reruns match. The `lbfgs` solver uses no randomness, so it only protects later random steps.

## Scoring

- **Accuracy and baseline:** accuracy is the share of games where the pick matches the result. It is shown next to the baseline, the score of always picking the home team. See [`accuracy_score`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.accuracy_score.html).
- **Log loss:** a score for the probabilities, not just the picks. Each game gets a penalty that is small if the model gave a high chance to what really happened and large if it gave a low one, so being confidently wrong costs the most. Lower is better, and saying 50-50 on every game scores 0.6931. It is not logged for training games, because the model is fitted by pushing it down there. See [`log_loss`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html).
- **Calibration:** whether percentages match how often things happen, so 70% should be right about 7 times in 10. Log loss rewards it and accuracy cannot see it. See [probability calibration](https://scikit-learn.org/stable/modules/calibration.html).
- **Confusion matrix:** a 2 by 2 table of picks against results. The diagonal holds the correct picks. See [`confusion_matrix`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.confusion_matrix.html).

## MLflow

- **MLflow:** an open-source tool for keeping a record of machine learning work. This project uses its tracking part: the training code calls `log_params`, `log_metrics`, and `log_artifact` so each run writes down its settings, scores, and files. It does not use the model registry or serving tools. See the [documentation](https://mlflow.org/docs/latest/), the [tracking guide](https://mlflow.org/docs/latest/ml/tracking/), and the [tracking API](https://mlflow.org/docs/latest/ml/tracking/tracking-api/).
- **Experiment and run:** an experiment is a named group of runs (`nfl-pregame-winner-v1`). A run is one execution of training, with a unique run ID, a name (`LogisticRegression-v1.0`), and a status such as FINISHED or FAILED. A run that fails partway is closed and marked failed.
- **Parameter (MLflow):** a setting written down for a run as text, such as the seed, `C`, the seasons, the row counts, the scikit-learn version, and the data fingerprint. Each run records 15.
- **Metric, tag, and artifact:** a metric is a number written down for a run, such as an accuracy (here each is logged once). A tag is a label on a run, and MLflow adds the git commit, branch, repository address, script name, and user itself. An artifact is a file stored with a run. Each run stores three: the saved model file, the confusion-matrix image, and a copy of `config.yaml`.
- **Backend store:** where MLflow keeps experiments, runs, parameters, metrics, and tags. Here it is a database file, `mlflow.db`. See [backend stores](https://mlflow.org/docs/latest/self-hosting/architecture/backend-store/).
- **SQLite and the tracking URI:** SQLite is a database that lives in one file and needs no server. The tracking URI is the address MLflow uses to find the store, here `sqlite:///` plus the full path of `mlflow.db`. The path starts with `/`, so the address has four slashes in a row. See the [SQLite documentation](https://www.sqlite.org/docs.html).
- **Artifact store:** where MLflow keeps files. Here it is `mlartifacts/`, with a subfolder per run. The location is set when an experiment is created and cannot be changed afterward. See [artifact stores](https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/).
- **MLflow model format and flavor:** a standard folder layout for a saved model, so MLflow can load it back: a description file (`MLmodel`), the serialized model, and files listing the needed packages. The flavor names the library that built the model, here scikit-learn. The installed version writes the model with [`skops`](https://skops.readthedocs.io/en/stable/). See [MLflow Models](https://mlflow.org/docs/latest/ml/model/) and the [scikit-learn flavor](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.sklearn.html).
- **Logged model:** in MLflow 3, a model saved in that format is its own entry linked to the run, stored in a `models/` folder in the artifact store and not in the run's file list. Each run also keeps the plain `model.joblib` file, the copy the API will load.
- **MLflow UI:** a web page for browsing runs, started with `mlflow ui --backend-store-uri sqlite:///mlflow.db`. See [the tracking UI](https://mlflow.org/docs/latest/ml/tracking/#tracking-ui).

## Python Tooling and Reproducibility

- **Reproducibility:** getting the same result again from the same inputs on any machine. Here it comes from pinned versions, a fixed seed, settings in one file, and a data fingerprint. Each run also writes `results/run-summary.json`, a small readable record of its settings, scores, and learned weights.
- **Data fingerprint (SHA-256):** a short code worked out from every byte of a file. If one byte changes, the code changes, so two runs with the same fingerprint used the same data. See [`hashlib`](https://docs.python.org/3/library/hashlib.html).
- **Pinned version:** an exact version in `requirements.txt`, such as `scikit-learn==1.9.1`, so every install is identical. A saved model may fail to load under another scikit-learn version.
- **Virtual environment:** a private folder of Python packages for one project, so projects do not interfere. See [`venv`](https://docs.python.org/3/library/venv.html).
- **`config.yaml`:** the one file holding every adjustable setting. YAML is a text format of indented `name: value` lines, and [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation) reads it.
- **pandas, NumPy, scikit-learn, and requests:** pandas holds the game tables, NumPy does the number work underneath, scikit-learn supplies the scaler, model, pipeline, and scoring functions, and requests downloads the games file.
- **joblib and pickle:** [joblib](https://joblib.readthedocs.io/en/stable/) saves a Python object to a file and loads it back, and it is the usual way to save a scikit-learn model. It builds on [pickle](https://docs.python.org/3/library/pickle.html), so only load a saved file you trust. See [model persistence](https://scikit-learn.org/stable/modules/model_persistence.html).
- **matplotlib and the Agg backend:** [matplotlib](https://matplotlib.org/stable/) draws the confusion-matrix image. The `Agg` [backend](https://matplotlib.org/stable/users/explain/figure/backends.html) draws to a file without opening a window, so it works with no display.
- **pytest and stand-in objects:** [pytest](https://docs.pytest.org/en/stable/) runs `tests/`. The tests use made-up data and stand-ins for the real S3 client and model, so they need no internet and no AWS account.

## Data Source and Storage

- **nflverse:** the open project that publishes the games file, one row per NFL game since 1999. See the [repository](https://github.com/nflverse/nfldata) and [`games.csv`](https://github.com/nflverse/nfldata/blob/master/data/games.csv).
- **Amazon S3, bucket, and key:** S3 stores files in the cloud. A bucket is a named container, and a key is a file's path inside it. This project keeps one cleaned table in a private bucket. See the [S3 documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html).
- **boto3:** the Python library for calling AWS. It finds credentials itself, from environment variables or `~/.aws`, so no key is written in the project. See the [documentation](https://docs.aws.amazon.com/boto3/latest/).
- **IAM and least privilege:** IAM decides who may do what in AWS, and least privilege gives each identity only the access it needs. See [IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html) and its [best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html).

## Serving and Deployment Tools

Used in the later phases.

- **FastAPI, Pydantic, and Mangum:** [FastAPI](https://fastapi.tiangolo.com/) builds the web service, [Pydantic](https://docs.pydantic.dev/latest/) checks each request's fields and types, and [Mangum](https://mangum.fastapiexpert.com/) lets the app run inside AWS Lambda.
- **Docker, image, and build target:** Docker packages a program with everything it needs. An image is the packaged snapshot, and a Dockerfile can define several build targets, here `train` and `serve`. See [Docker](https://docs.docker.com/) and [multi-stage builds](https://docs.docker.com/build/building/multi-stage/).
- **AWS Lambda and cold start:** Lambda runs code only when a request arrives. The first request after a quiet period is slower because a fresh copy must start and load the model. See the [documentation](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html).
- **ECR, API Gateway, CloudFront, and Vite:** [ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html) stores Docker images, [API Gateway](https://docs.aws.amazon.com/apigateway/latest/developerguide/welcome.html) gives the function a public address, [CloudFront](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html) serves the web app's files over HTTPS, and [Vite](https://vite.dev/guide/) builds the web app.
