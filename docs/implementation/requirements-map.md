---
hide:
  - toc
---

# Requirements Map

This page maps each requirement that is done so far to where it lives in the repository. Each entry gives the requirement as written in [Project Requirements](../initial-requirements/requirements.md), then the file, the function, the setting, or the command that covers it, and the docs page that explains it. A new entry is added when a phase finishes.

## 1. Problem and Dataset

- **Pick a public dataset (for example from Kaggle, UCI, or Hugging Face Datasets).**
    - **What:** the nflverse `games.csv` file, one row per NFL game since 1999.
    - **Where:** the address is `data.source_url` in `config/config.yaml`. `src/data/fetch_raw.py` downloads it and saves it as `data/raw/games.csv`.
    - **Docs:** [What Is the Source Data?](./phase-1/implementation.md#what-is-the-source-data)
- **Define a single supervised learning task: either classification or regression.**
    - **What:** binary classification. Did the home team win?
    - **Where:** the answer is the `home_win` column built in `build_model_table` in `src/model/features.py`.
    - **Docs:** [What Is the Prediction Task?](./phase-1/implementation.md#what-is-the-prediction-task)
- **Name the target variable and the one evaluation metric used to judge the model.**
    - **Target:** `home_win` (1 if the home team won, 0 if not), listed in `MODEL_COLUMNS` in `src/model/features.py`.
    - **Metric:** accuracy, next to the always-pick-home baseline. It is computed by `score_group` in `src/model/evaluate.py`. Log loss is a second score that checks the win percentages.
    - **Docs:** [What Is Accuracy?](./phase-2/implementation-part-2.md#what-is-accuracy)

## 2. Cloud Data Storage

- **Clean and preprocess the dataset locally before uploading.**
    - **Where:** `clean_games` in `src/data/clean.py`, run with `python -m src.data.clean`. It writes `data/processed/nfl_matchups_2020_2026.csv`.
    - **Docs:** [Step 2: Clean the Raw Data](./phase-1/implementation.md#step-2-clean-the-raw-data-and-save-the-cleaned-table)
- **Upload the cleaned data to an Amazon S3 bucket. S3 is the chosen storage service for this project.**
    - **Where:** `upload` in `src/data/upload_to_s3.py`, run with `python -m src.data.upload_to_s3`. The bucket name and file name are `data.s3_bucket` and `data.s3_key` in `config/config.yaml`.
    - **The bucket itself:** `510-m3-nfl-dataset` in `us-east-1`. It was created by hand in the AWS console, so no file in the repository creates it.
    - **Docs:** [Step 3: Upload the Cleaned Table to S3](./phase-1/implementation.md#step-3-upload-the-cleaned-table-to-s3)
- **Include a script that downloads the data from S3 programmatically (for example with boto3), so the pipeline starts from the S3 copy rather than a local file.**
    - **Where:** `download` in `src/data/download_from_s3.py`, run with `python -m src.data.download_from_s3`. It saves `data/from-s3/nfl_matchups_2020_2026.csv`.
    - **Starting from the S3 copy:** `load_games` in `src/model/features.py` reads only that downloaded file, never the local cleaned table.
    - **Docs:** [Step 4: Download the Cleaned Table From S3](./phase-1/implementation.md#step-4-download-the-cleaned-table-from-s3-and-save-it)

## 3. Reproducible Pipeline

- **Use one simple model (for example logistic regression, random forest, or XGBoost).**
    - **What:** logistic regression behind a standardizing step, kept together as one pipeline.
    - **Where:** `build_pipeline` and `fit_pipeline` in `src/model/train.py`.
    - **Docs:** [Step 4: Fit the Scaler and the Model](./phase-2/implementation-part-2.md#step-4-fit-the-scaler-and-the-model)
- **The pipeline must cover, in order: data ingestion from S3, preprocessing and feature engineering, a train/validation/test split, model training, and evaluation.**
    - **Ingestion from S3:** `src/data/download_from_s3.py`, then `load_games` in `src/model/features.py`.
    - **Preprocessing:** `src/data/clean.py`.
    - **Feature engineering:** `standings_before_week` and `build_model_table` in `src/model/features.py`. Docs: [Step 1: Feature Engineering](./phase-2/implementation-part-1.md#step-1-feature-engineering).
    - **Train/validation/test split:** `split_games` in `src/model/features.py`, with `split_seasons` in `src/config.py`. Docs: [Step 2: Split the Games by Season](./phase-2/implementation-part-1.md#step-2-split-the-games-by-season).
    - **Model training:** `fit_pipeline` in `src/model/train.py`.
    - **Evaluation:** `score_group` and `plot_confusion_matrix` in `src/model/evaluate.py`. Docs: [Step 5: Score the Model](./phase-2/implementation-part-2.md#step-5-score-the-model).
    - **How they run:** the data steps are separate commands (fetch, clean, upload, download). `python -m src.model.train` then runs the rest in order: load the downloaded table, build the inputs, split, fit, score, save, and log.
- **All tunable settings live in a `config.yaml` file (for example the split ratio and model parameters). Changing a run means editing that file, not the code.**
    - **Where:** `config/config.yaml`, read through `src/config.py`. Its blocks are `data` (paths, bucket, region), `window` (first and last season, and the last scored week), `split` (last training season and the validation season), `model` (version, seed, output file, and the logistic regression settings), and `tracking` (MLflow names and folders).
    - **Two things live in code, not in the file:** the 0.5 cutoff that turns a probability into a pick, and the list of columns that cleaning keeps.
    - **Docs:** [Step 3: Add the Model and Tracking Settings](./phase-2/implementation-part-1.md#step-3-add-the-model-and-tracking-settings)
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
    - **Docs:** [What Is Logged for Each Run?](./phase-2/implementation-part-2.md#what-is-logged-for-each-run)
- **Log artifacts for reproducibility: at minimum the trained model, plus any plots produced.**
    - **Files stored with each run (3):** `model/model.joblib` (the trained model), `plots/confusion_matrix_validation.png` (the one plot), and `config/config.yaml` (a copy of the settings used).
    - **The plot** is drawn by `plot_confusion_matrix` in `src/model/evaluate.py`.
    - **A second copy of the model, in MLflow's own format:** each run also has one logged model, `pipeline-mlflow-format`, stored under `mlartifacts/models/`. `model/model.joblib` stays the working copy that the API will load.
    - **A readable record outside MLflow:** `results/run-summary.json`, written by `write_run_summary` in `src/model/train.py`. It holds the settings, the data fingerprint, the scores, and the learned weights, and it is committed to git.
- **Where to find the recorded runs:**
    - **In the repository:** `results/run-summary.json` shows the latest run's settings, scores, and learned weights without MLflow.
    - **Run record:** `mlflow.db` in the project folder. **Run files:** `mlartifacts/`. Both are created by training and are not committed.
    - **To browse them:** run `mlflow ui --backend-store-uri sqlite:///mlflow.db` and open the address it prints.
    - **The saved model file:** `models/model.joblib`, also not committed.

## 9. Repository Contents

- **Code for preprocessing, training, serving, and deployment.**
    - **Preprocessing:** `src/data/` (`fetch_raw.py`, `clean.py`, `upload_to_s3.py`, `download_from_s3.py`) and `src/model/features.py`.
    - **Training:** `src/model/train.py` and `src/model/evaluate.py`.
- **`config.yaml` for pipeline configuration.** `config/config.yaml`.
- **A dependency file: `requirements.txt` or `environment.yaml`.** `requirements.txt`, with every package pinned to an exact version.
- **MLflow or Weights & Biases logging wired into the pipeline.** `log_run` is called by `main` in `src/model/train.py`, so `python -m src.model.train` logs a run by itself.
- **A clear project structure and a readable commit history.**
    - **Layout:** `src/data/` (Phase 1 steps), `src/model/` (Phase 2 code), `results/` (the committed run summary), `src/config.py` (reads the settings), `tests/` (one test file per code file), `config/` (settings), and `docs/` (these pages).
    - **Tests:** `pytest` runs all of `tests/`. They use made-up data and a stand-in S3 client, so they need no internet and no AWS account.
- **Work done on branches merged through pull requests, with at least one pull request on record.**
    - **Where:** pull request #1 (branch `phase_one` merged into `main`) is on the GitHub repository's Pull requests tab, and it shows in `git log`. Phase 2 work is on the branch `phase-two`.
