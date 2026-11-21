---
hide:
  - toc
---

# Phase 2 Synopsis: Features, Training, and Tracking

**Status: Built and tested.** All 7 steps are done, and `pytest` passes 26 tests.
**Needs first:** Phase 1, which is built. Its output is the downloaded table `data/from-s3/nfl_matchups_2020_2026.csv`.

Phase 2 turns the cleaned games into two inputs per game, trains the model, and keeps a record of every run. It fits a logistic regression on the 2020 to 2024 games, scores it on the 2025 season and on the 2026 test games, and saves the settings, scores, and files of each run in MLflow.

## Steps in Order

- [x] **Step 1. Feature engineering:** build the two inputs in `src/model/features.py`: home minus away win percentage, and home minus away point margin per game, both from earlier weeks of the same season.
- [x] **Step 2. Split the games by season.** Training 2020 to 2024, validation 2025, test 2026 weeks 1 to 10.
- [x] **Step 3. Add the model and tracking settings** to `config/config.yaml`.
- [x] **Step 4. Fit the scaler and the model** on the training seasons only. Save both as one scikit-learn pipeline.
- [x] **Step 5. Score the model.** Accuracy on the training, validation, and test games, next to the baseline. Also log loss and one plot.
- [x] **Step 6. Record the run in MLflow:** settings, scores, and files.
- [x] **Step 7. Save the final pipeline** as `models/model.joblib`, and add `models/`, `mlflow.db`, and `mlartifacts/` to `.gitignore`.

## Details in Brief

- **Inputs:** a team with no games yet counts as win percentage 0.5 and margin 0.0, so week 1 gives 0 for both inputs. Reasons for raw values over ranks are in [Decisions](../decisions.md#model-inputs-decided).
- **Split:** training is 1,339 games, validation is 271, and test is 149. The test games never fit anything. With only 149 of them, their accuracy can move by about 4 points by chance.
- **Baseline:** always picking the home team scores 53.32% on training, 53.87% on 2025, and 47.65% on the test games. The model must beat this.
- **One saved object:** the scaler and the model travel together in one pipeline, so the API cannot apply the model without the scaler. The scaler learns its averages from training rows only.
- **Tracking:** a local database file `mlflow.db`, with run files in `mlartifacts/`.
- **Logistic regression only.** There is no model comparison. Random forest and XGBoost are left out, which keeps the model simple to explain and the serving image small.

## Done When

- [x] One training command, `python -m src.model.train`, runs after the download step with only `config.yaml`.
- [x] Changing a model setting in `config.yaml` (`C`, `solver`, `max_iter`, or the random seed) changes the run with no code edit.
- [x] Two runs with the same settings give identical scores.
- [x] The scaler's saved average comes from the training rows only.
- [x] The MLflow run lists the settings, the scores, and all three kinds of files.

## What Was Created

- **Settings:** new `split`, `model`, and `tracking` blocks in `config/config.yaml`.
- **Code:** `src/model/features.py`, `src/model/train.py`, and `src/model/evaluate.py`, next to the Phase 1 folder `src/data/`, with tests in `tests/`. Packages `matplotlib` and `joblib` are pinned in `requirements.txt`.
- **Local only, not committed:** `mlflow.db`, the `mlartifacts/` folder, and `models/model.joblib`.

## Where to Read More

- [Implementation Part 1](./implementation-part-1.md) explains Steps 1 to 3: feature engineering, the split by season, and the new settings.
- [Implementation Part 2](./implementation-part-2.md) explains Steps 4 to 7: fitting the model, scoring it, recording the run in MLflow, and saving the model.
