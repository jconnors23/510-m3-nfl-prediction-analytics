---
hide:
  - toc
---

# Glossary

Plain-language meanings of the technical terms used in these docs, grouped by topic. Football terms are not defined here.

## Data

- **Raw data:** the source file exactly as downloaded, `data/raw/games.csv`.
- **Cleaned table:** one row per usable game with only the columns the project uses, `data/processed/nfl_matchups_2020_2026.csv`.
- **S3 copy:** the cleaned table downloaded back from S3 into `data/from-s3/`. Every later step reads this copy.
- **CSV:** a plain text table with one row per line and values separated by commas.
- **Row and column:** a row is one record (here, one game). A column is one named field, such as `home_score`.
- **Feature:** one input number the model uses to decide. This project has two.
- **Feature engineering:** building the features from raw columns. Here: turning scores and weeks into each team's win percentage and point margin per game, and then into the two differentials.
- **Differential:** one team's number minus the other team's. A positive value favors the home team.
- **`win_pct_differential`:** the home team's win percentage minus the away team's, from earlier weeks of the same season. A team with no games counts as 0.5.
- **`point_diff_per_game_differential`:** the home team's average point margin per game minus the away team's, from earlier weeks of the same season. A team with no games counts as 0.0.
- **Target (label):** the known answer the model learns to predict. Here it is `home_win`: 1 if the home team won and 0 if not.
- **Data leakage:** a feature that uses information from after the thing being predicted. It makes scores look better than real use will be. The "earlier weeks only" rule prevents it.
- **Team profiles file:** a small file with each team's record, win percentage, and point margin per game after 2026 week 10, read by the web app.

## Modeling

- **Supervised learning:** learning from examples that come with known answers. Every game has a known winner, so this project is supervised.
- **Classification and regression:** classification predicts a category. Regression predicts a number. They are the two kinds of supervised task.
- **Binary classification:** classification with exactly two categories. Here: home win or away win.
- **Probability and threshold:** the model outputs a probability from 0 to 1 for a home win. The threshold is the cutoff that turns it into a pick. Here a probability above 0.5 picks the home team.
- **Training, validation, and test sets:** training games fit the model (2020 to 2024). Validation games give the reported score (2025). Test games are the 2026 weeks 1 to 10 already played, and they are never used to fit the model.
- **Chronological split:** splitting by date, so the model trains on the past and is scored on later games.
- **Baseline:** a simple rule the model must beat. Here: always pick the home team.
- **Overfitting:** when a model memorizes the training games instead of learning a pattern that carries to new games.
- **Logistic regression:** a simple classification model. It multiplies each feature by a learned weight, adds an intercept, and turns the sum into a probability. Despite its name, it is a classifier.
- **Weight and intercept:** a weight says how much one feature moves the prediction. The intercept is the starting value before any feature is added. Here it holds the average home-team edge.
- **Scaler (standardization):** a step that puts the features on a common scale, by subtracting the training average and dividing by the training spread.
- **Pipeline:** one object that chains the scaler and the model, so the API cannot forget the scaling.
- **Parameter and hyperparameter:** a parameter is learned during training, such as a weight. A hyperparameter is a setting chosen before training, such as `C` (regularization strength) or `max_iter`. The settings file holds them.
- **Random seed:** a starting number for random choices. The same seed gives the same results every run.
- **Inference:** using a trained model to predict new input. The API does this.
- **scikit-learn and joblib:** scikit-learn supplies the scaler and models. joblib saves and loads the trained model as a file.

## Scoring

- **Metric:** any number used to score a model.
- **Accuracy:** the share of games where the predicted winner matches the real winner. This is the main metric.
- **Log loss:** a score that checks whether the model's percentages are honest. High is bad and low is good, like a golf score. Each game gets a penalty that is small when the model gave the real result a high chance and large when it gave that result a low chance, so being confidently wrong costs the most. Lower is better, and saying 50% for every game scores 0.6931.
- **Confusion matrix:** a small table counting correct and wrong predictions for each real outcome.

## Tracking and Configuration

- **MLflow:** a tool that records each training run (settings, scores, and files) so runs can be compared. The project stores it in a local database file, `mlflow.db`.
- **Run, experiment, and artifact:** a run is one execution of training. An experiment is a named group of runs. An artifact is a file saved with a run, such as the model, a plot, or a copy of the settings.
- **`config.yaml`:** the one file that holds every adjustable setting. YAML is a readable text format of indented `name: value` lines.
- **Reproducibility:** getting the same result again from the same inputs on any machine.
- **Pinned version:** an exact library version in `requirements.txt`, such as `scikit-learn 1.9.1`, so installs are identical.
- **Virtual environment:** a private folder of Python libraries for one project, so projects do not interfere.

## API and Web

- **API and endpoint:** an API lets one program ask another for something over a network. An endpoint is one address that does one job, such as `/predict`.
- **Request and response:** the message sent to an API, and the message it sends back. `POST` sends data to be processed, and `GET` only asks for something.
- **JSON:** a plain text format for structured data, written as named fields in braces. The API and the team profiles file use it.
- **Input validation:** checking that incoming data has the right fields, types, and ranges before using it.
- **Status codes:** `200` means it worked, `422` means the request fields were wrong, `429` means too many requests, and `500` means a service error.
- **FastAPI, Pydantic, and Mangum:** FastAPI builds the API, Pydantic checks request fields, and Mangum lets the app run inside AWS Lambda.
- **Health check:** a route that reports whether the service is up and which model version it runs.
- **Cold start:** the extra delay on the first request after Lambda has been idle.
- **CORS:** a browser rule: a web page may call an API at another address only if the API allows that page's address.
- **`curl`:** a command-line tool for sending requests to test an API.
- **Vite:** a tool for building web apps. It has a local development server and a build command (`vite build`) that writes static files to publish.
- **Static files:** files sent to the browser unchanged, such as HTML, CSS, and JavaScript.

## Docker and AWS

- **Docker, image, and container:** Docker packages a program with everything it needs. An image is the packaged snapshot, and a container is a running copy.
- **Dockerfile and build target:** a Dockerfile is the recipe for an image. A build target is a named stage that can be built on its own. This project has `train` and `serve`.
- **Region:** where AWS resources run, such as `us-east-1`.
- **Amazon S3, bucket, object, and key:** S3 stores files. A bucket is a named container for them. An object is one stored file, found by its key (path).
- **`boto3`:** the Python library for calling AWS from code.
- **IAM, policy, and role:** IAM decides who may do what. A policy lists allowed actions. A role is an identity AWS services take on. Least privilege means giving only the access a job needs.
- **Amazon ECR:** AWS storage for Docker images.
- **AWS Lambda:** runs code only when a request arrives, with no server to manage.
- **API Gateway:** gives Lambda a public web address and handles CORS and request limits. The project uses the simpler HTTP API type.
- **Amazon CloudFront:** serves stored copies of files quickly over HTTPS. An origin access control lets only that CloudFront setup read a private bucket.
- **CloudWatch Logs and AWS Budgets:** CloudWatch Logs stores a function's log messages. Budgets emails an alert when spending passes a limit.

## Process

- **Phase:** one build step of the project.
- **Spec:** a file in `specs/` that tells Cursor exactly what to build and which numbers to match.
- **Git, branch, commit, and pull request:** Git records changes. A branch is a separate line of work. A commit is a saved set of changes. A pull request asks to merge a branch after review.
- **README:** the repository front page. It explains the project and links to the live app and API.
- **MkDocs and Mermaid:** MkDocs builds this site from text files. Mermaid draws the diagrams from text.
