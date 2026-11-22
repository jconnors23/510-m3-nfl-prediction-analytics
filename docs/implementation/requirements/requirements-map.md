---
hide:
  - toc
---

# Requirements Map

This page maps each requirement that is done so far to where it lives in the repository. Each entry gives the requirement as written in [Project Requirements](./project-requirements.md), then the file, the function, the setting, or the command that covers it, and the docs page that explains it. A new entry is added when a phase finishes.

## 1. Problem and Dataset

- **Pick a public dataset (for example from Kaggle, UCI, or Hugging Face Datasets).**
    - **What:** the nflverse `games.csv` file, one row per NFL game since 1999.
    - **Where:** the address is `data.source_url` in `config/config.yaml`. `src/data/fetch_raw.py` downloads it and saves it as `data/raw/games.csv`.
    - **Docs:** [What Is the Source Data?](../phase-1/implementation.md#what-is-the-source-data)
- **Define a single supervised learning task: either classification or regression.**
    - **What:** binary classification. Did the home team win?
    - **Where:** the answer is the `home_win` column built in `build_model_table` in `src/model/features.py`.
    - **Docs:** [What Is the Prediction Task?](../phase-1/implementation.md#what-is-the-prediction-task)
- **Name the target variable and the one evaluation metric used to judge the model.**
    - **Target:** `home_win` (1 if the home team won, 0 if not), listed in `MODEL_COLUMNS` in `src/model/features.py`.
    - **Metric:** accuracy, next to the always-pick-home baseline. It is computed by `score_group` in `src/model/evaluate.py`. Log loss is a second score that checks the win percentages.
    - **Docs:** [What Is Accuracy?](../phase-2/implementation-part-2.md#what-is-accuracy)

## 2. Cloud Data Storage

- **Clean and preprocess the dataset locally before uploading.**
    - **Where:** `clean_games` in `src/data/clean.py`, run with `python -m src.data.clean`. It writes `data/processed/nfl_matchups_2020_2026.csv`.
    - **Docs:** [Step 2: Clean the Raw Data](../phase-1/implementation.md#step-2-clean-the-raw-data-and-save-the-cleaned-table)
- **Upload the cleaned data to an Amazon S3 bucket. S3 is the chosen storage service for this project.**
    - **Where:** `upload` in `src/data/upload_to_s3.py`, run with `python -m src.data.upload_to_s3`. The bucket name and file name are `data.s3_bucket` and `data.s3_key` in `config/config.yaml`.
    - **The bucket itself:** `510-m3-nfl-dataset` in `us-east-1`. It was created by hand in the AWS console, so no file in the repository creates it.
    - **Docs:** [Step 3: Upload the Cleaned Table to S3](../phase-1/implementation.md#step-3-upload-the-cleaned-table-to-s3)
- **Include a script that downloads the data from S3 programmatically (for example with boto3), so the pipeline starts from the S3 copy rather than a local file.**
    - **Where:** `download` in `src/data/download_from_s3.py`, run with `python -m src.data.download_from_s3`. It saves `data/from-s3/nfl_matchups_2020_2026.csv`.
    - **Starting from the S3 copy:** `load_games` in `src/model/features.py` reads only that downloaded file, never the local cleaned table.
    - **Docs:** [Step 4: Download the Cleaned Table From S3](../phase-1/implementation.md#step-4-download-the-cleaned-table-from-s3-and-save-it)

## 3. Reproducible Pipeline

- **Use one simple model (for example logistic regression, random forest, or XGBoost).**
    - **What:** logistic regression behind a standardizing step, kept together as one pipeline.
    - **Where:** `build_pipeline` and `fit_pipeline` in `src/model/train.py`.
    - **Docs:** [Step 4: Fit the Scaler and the Model](../phase-2/implementation-part-2.md#step-4-fit-the-scaler-and-the-model)
- **The pipeline must cover, in order: data ingestion from S3, preprocessing and feature engineering, a train/validation/test split, model training, and evaluation.**
    - **Ingestion from S3:** `src/data/download_from_s3.py`, then `load_games` in `src/model/features.py`.
    - **Preprocessing:** `src/data/clean.py`.
    - **Feature engineering:** `standings_before_week` and `build_model_table` in `src/model/features.py`. Docs: [Step 1: Feature Engineering](../phase-2/implementation-part-1.md#step-1-feature-engineering).
    - **Train/validation/test split:** `split_games` in `src/model/features.py`, with `split_seasons` in `src/config.py`. Docs: [Step 2: Split the Games by Season](../phase-2/implementation-part-1.md#step-2-split-the-games-by-season).
    - **Model training:** `fit_pipeline` in `src/model/train.py`.
    - **Evaluation:** `score_group` and `plot_confusion_matrix` in `src/model/evaluate.py`. Docs: [Step 5: Score the Model](../phase-2/implementation-part-2.md#step-5-score-the-model).
    - **How they run:** the data steps are separate commands (fetch, clean, upload, download). `python -m src.model.train` then runs the rest in order: load the downloaded table, build the inputs, split, fit, score, save, and log.
- **All tunable settings live in a `config.yaml` file (for example the split ratio and model parameters). Changing a run means editing that file, not the code.**
    - **Where:** `config/config.yaml`, read through `src/config.py`. Its blocks are `data` (paths, bucket, region), `window` (first and last season, and the last scored week), `split` (last training season and the validation season), `model` (version, seed, output file, and the logistic regression settings), and `tracking` (MLflow names and folders).
    - **Two things live in code, not in the file:** the 0.5 cutoff that turns a probability into a pick, and the list of columns that cleaning keeps.
    - **Docs:** [Step 3: Add the Model and Tracking Settings](../phase-2/implementation-part-1.md#step-3-add-the-model-and-tracking-settings)
- **Model accuracy is not graded. A poor score is acceptable; the requirement is a clean, repeatable process.**
    - **Where:** two runs with the same settings give identical scores. `test_same_settings_give_the_same_probabilities` in `tests/test_train.py` checks it, and `results/run-summary.json` is byte for byte the same on every run with the same settings and data.

## 4. Experiment Tracking

- **Use MLflow or Weights & Biases.**
    - **What:** MLflow. Its settings are the `tracking` block in `config/config.yaml`.
    - **Where:** `log_run` in `src/model/train.py`.
- **Log each run's parameters and evaluation metrics.**
    - **Parameters (15):** `model_version`, `random_seed`, `C`, `solver`, `max_iter`, `feature_names`, `train_start_season`, `train_end_season`, `validation_season`, `test_season`, `n_train`, `n_validation`, `n_test`, `scikit_learn_version`, and `data_sha256` (a fingerprint of the downloaded table, from `file_fingerprint` in `src/model/train.py`).
    - **Metrics (8):** `train_accuracy`, `validation_accuracy`, `test_accuracy`, `validation_log_loss`, `test_log_loss`, `baseline_train`, `baseline_validation`, `baseline_test`.
    - **Automatic tags:** MLflow also records the git commit, branch, and repository address of each run.
    - **Docs:** [What Is Logged for Each Run?](../phase-2/implementation-part-2.md#what-is-logged-for-each-run)
- **Log artifacts for reproducibility: at minimum the trained model, plus any plots produced.**
    - **Files stored with each run (3):** `model/model.joblib` (the trained model), `plots/confusion_matrix_validation.png` (the one plot), and `config/config.yaml` (a copy of the settings used).
    - **The plot** is drawn by `plot_confusion_matrix` in `src/model/evaluate.py`.
    - **A second copy of the model, in MLflow's own format:** each run also has one logged model, `pipeline-mlflow-format`, stored under `mlartifacts/models/`. `model/model.joblib` stays the working copy that the API will load.
    - **A readable record outside MLflow:** `results/run-summary.json`, written by `write_run_summary` in `src/model/train.py`. It holds the settings, the data fingerprint, the scores, and the learned weights, and it is committed to git.
- **Where to find the recorded runs:**
    - **In the repository:** `results/run-summary.json` shows the latest run's settings, scores, and learned weights without MLflow.
    - **Run record:** `mlflow.db` in the project folder. **Run files:** `mlartifacts/`. Both are created by training and are not committed, because they store absolute paths on one computer.
    - **In the repository:** [`mlflow-reference/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/mlflow-reference), written by `python -m src.model.export_mlflow`, which training calls. It is a log of every training run: each run's id, git commit, 15 parameters, 8 metrics, config copy and plot, and the logged model's text files, with `run-history.md` listing every run and pictures of the MLflow screen.
    - **To browse them:** run `mlflow ui --backend-store-uri sqlite:///mlflow.db` and open the address it prints.
    - **The saved model file:** `models/model.joblib`, also not committed.

## 6. Prediction API

- **Serve the trained model with FastAPI or Flask.**
    - **What:** FastAPI. The app, the start-up step that loads the saved model once, and the 0.5 pick rule are in `src/api/app.py` (`create_app`, `load_model`, `label_for`).
    - **Docs:** [How Does the Service Work?](../phase-3/implementation.md#how-does-the-service-work)
- **Expose a /predict endpoint that accepts JSON input and returns a prediction as JSON.**
    - **Where:** `POST /predict` in `src/api/app.py`, with the request and response shapes in `src/api/schemas.py`. The request holds `win_pct_differential` and `point_diff_per_game_differential`. The response holds `prediction`, `predicted_label`, `home_win_probability`, and `model_version`.
    - **Docs:** [What Is in the Response?](../phase-3/development-guide.md#what-is-in-the-response)
- **The endpoint must be testable locally (for example with curl or Postman).**
    - **How:** start it with `python -m uvicorn src.api.app:app --port 8000`, then send requests with `curl` or open the test page at `/docs`. 17 tests in `tests/test_api.py` cover both routes, the input checks, and the start-up checks.
    - **Docs:** [How Do I Run It Locally?](../phase-3/development-guide.md#how-do-i-run-it-locally)

## 7. Cloud Deployment

- **Deploy the API on AWS; use AWS Lambda fronted by API Gateway.**
    - **Where:** the Lambda function `510-m3-nfl-predict-api` (entry point `src/api/lambda_handler.py`, packages listed in `requirements-serve.txt`) behind the HTTP API `510-m3-nfl-predict-http-api`, both in `us-east-1`. The commands are on [Deployment Guide](../phase-4/deployment-guide.md).
    - **Docs:** [Phase 4 Implementation](../phase-4/implementation.md)
- **Configure CORS on API Gateway so the browser-based front-end can call /predict.**
    - **Where:** set on the gateway, not in the app. It allows two origins, the live page `https://d1nubiunzfwm0q.cloudfront.net` and the local dev server `http://localhost:5173`, with the methods `POST`, `GET`, and `OPTIONS`, and the header `content-type`. Other origins get no CORS headers.
    - **Docs:** [Step 8: Set CORS on the Gateway](../phase-4/implementation.md#step-8-set-cors-on-the-gateway) and [The Preflight](../phase-5/implementation-part-1.md#the-preflight)
- **After deployment, /predict must be publicly reachable and must return a valid response to an HTTP request with test data.**
    - **Public address:** `https://9awodatqc5.execute-api.us-east-1.amazonaws.com`. `POST /predict` with the inputs -0.5 and -18.0 returns `{"prediction": 0, "predicted_label": "away win", "home_win_probability": 0.3296, "model_version": "v1.0"}`.
    - **Checked on every game:** all 1,759 games sent through the public address gave the same pick and probability as the local model.
    - **Docs:** [Step 9: Check the Public Address](../phase-4/implementation.md#step-9-check-the-public-address) and [Step 10](../phase-4/implementation.md#step-10-check-the-deployed-model-against-the-local-model)

## 8. Front-End

- **Build a lightweight interface with Vite, using the dev server for local work and `vite build` for the published files.**
    - **Where:** the React and TypeScript app in `frontend/`. `npm run dev` starts the dev server on port 5173, and `npm run build` runs the type check and `vite build` into `frontend/dist/`.
    - **Docs:** [Phase 5 Development Guide](../phase-5/development-guide.md)
- **Collect user input, send it to the deployed API, and display the prediction in a readable form.**
    - **Where:** `frontend/src/App.tsx` (two team lists, the Predict button, the result, and the failure messages), `frontend/src/matchup.ts` (the two inputs and the chances), and `frontend/src/api.ts` (the `fetch` call to `POST /predict`). The standings come from `frontend/src/data/team-profiles.json`, written by `python -m src.profiles`.
    - **Checked:** 62 app tests, all 992 ordered pairs of teams, and all 272 games of the 2026 season sent to the live API, with every pick and probability equal to the local model.
    - **Interactive and readable:** each team's record under its list, a bar split between the two chances, a light and a dark theme, and text and graphics that pass the WCAG contrast minimums in both.
    - **Docs:** [Phase 5 Implementation](../phase-5/implementation-part-1.md)
- **Host the built files in a private S3 bucket served over HTTPS through CloudFront.**
    - **Where:** the bucket `510-m3-nfl-web-app` and the CloudFront distribution at `https://d1nubiunzfwm0q.cloudfront.net`, with the origin access control `510-m3-nfl-web-app-oac`, all in `us-east-1`. The served files are byte for byte the tested build, and direct requests to the bucket get status 403.
    - **Redeployed by:** `.github/workflows/deploy-web-app.yml`, on a change under `frontend/` on `main`.
    - **Docs:** [How Is the Page Hosted?](../phase-5/implementation-part-1.md#how-is-the-page-hosted), [How Does a Change Reach the Live Page?](../phase-5/implementation-part-1.md#how-does-a-change-reach-the-live-page), and the [Phase 5 Deployment Guide](../phase-5/deployment-guide.md)
- **Link the live front-end URL in the README.** Not done yet. It comes in [Phase 7](../remaining-phases.md#phase-7-documentation-and-readme).

## 9. Repository Contents

- **Code for preprocessing, training, serving, and deployment.**
    - **Preprocessing:** `src/data/` (`fetch_raw.py`, `clean.py`, `upload_to_s3.py`, `download_from_s3.py`) and `src/model/features.py`.
    - **Training:** `src/model/train.py` and `src/model/evaluate.py`.
    - **Serving:** `src/api/app.py` and `src/api/schemas.py`.
    - **Deployment:** `src/api/lambda_handler.py`, `requirements-serve.txt`, and the written commands on the [Phase 4 Deployment Guide](../phase-4/deployment-guide.md) and the [Phase 5 Deployment Guide](../phase-5/deployment-guide.md).
    - **Front-end:** `frontend/` (the web app) and `src/profiles.py` (the team profiles file it reads).
- **`config.yaml` for pipeline configuration.** `config/config.yaml`.
- **A dependency file: `requirements.txt` or `environment.yaml`.** `requirements.txt`, with every package pinned to an exact version.
- **MLflow or Weights & Biases logging wired into the pipeline.** `log_run` is called by `main` in `src/model/train.py`, so `python -m src.model.train` logs a run by itself, and then writes the readable copy in [`mlflow-reference/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/mlflow-reference).
- **A clear project structure and a readable commit history.**
    - **Layout:** `src/data/` (Phase 1 steps), `src/model/` (Phase 2 code), `src/api/` (Phases 3 and 4 code), `src/profiles.py` and `frontend/` (Phase 5), `results/` (the committed run summary), `.github/workflows/` (the docs site publishing workflow and the web app deploy workflow), `src/config.py` (reads the settings), `tests/` (one test file per code file), `config/` (settings), and `docs/` (these pages).
    - **Tests:** `pytest` runs all of `tests/`. They use made-up data and a stand-in S3 client, so they need no internet and no AWS account.
- **Work done on branches merged through pull requests, with at least one pull request on record.**
    - **Where:** pull requests #1 (`phase_one`), #2 (`phase-two`), and #3 (`phase-three`) are merged into `main`, and show in `git log` and on the GitHub repository's Pull requests tab. Phase 4 is on the branch `phase-four`.
