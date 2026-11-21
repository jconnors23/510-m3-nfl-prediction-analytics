# Phase 2 Pull Request Notes

## Summary

This pull request adds the Phase 2 model pipeline. It turns the cleaned games from Phase 1 into two inputs per game, splits them by season, trains a logistic regression, scores it, records each run in MLflow, and saves the trained model. It also renames one Phase 1 setting and adds explanatory docstrings and comments to Phase 1 code.

## What Was Added

- **Feature engineering** (`src/model/features.py`): two inputs per game, built from earlier weeks of the same season only: the home team's win percentage minus the away team's, and the same for point margin per game.
- **Split by season:** training 2020 to 2024 (1,339 games), validation 2025 (271), and test 2026 weeks 1 to 10 (149).
- **Settings** (`config/config.yaml`, `src/config.py`): new `split`, `model`, and `tracking` blocks, including `tracking.summary_path`.
- **Scoring** (`src/model/evaluate.py`): accuracy next to the always-pick-home baseline, log loss, and one confusion-matrix image.
- **Training and saving** (`src/model/train.py`): a scaler and a logistic regression kept as one pipeline, fitted on training games only, and saved to `models/model.joblib`.
- **MLflow tracking:** each run records 15 parameters (including the scikit-learn version and a SHA-256 of the training data), 8 scores, 3 files, and one MLflow-format logged model.
- **Run summary** (`results/run-summary.json`): a small committed file with the run's settings, scores, and learned weights. It has no run id, timestamp, or machine paths, so it stays identical when the command is rerun.
- **Tests:** 27 new tests with mock data.
- **Docs:** new Phase 2 briefs and implementation pages, and updated glossary, decisions, and requirements map.

## Key Decisions

- **Raw per-game inputs, not ranks.** They keep the size of a gap, need no tie rule, and read directly.
- **Logistic regression only.**
- **Two scores and one plot.** Accuracy and log loss.
- **The live group is called the test set.** The Phase 1 setting `live_through_week` is now `test_through_week`.
- **The model is stored twice per run.** `model/model.joblib` is the working copy the API will load, and it carries the input names, version, and seasons. The MLflow-format copy is for MLflow's own tools.
- **MLflow records stay local.** `mlflow.db`, `mlartifacts/`, and `models/` are git-ignored. The database is binary, records an absolute machine path, and one command rebuilds it. `results/run-summary.json` is the committed record.

## Results

The command ran twice with identical scores. Log loss is lower-is-better, and 0.6931 is the score of saying 50-50 on every game.

- **Training:** 61.24% correct (820 of 1,339), against 53.32% for always picking the home team.
- **Validation (2025):** **63.10%** (171 of 271), against 53.87%. Log loss 0.6451.
- **Test (2026 weeks 1 to 10):** 59.06% (88 of 149), against 47.65%. Log loss 0.6815. With 149 games, accuracy can move about 4 points by chance.
- **Tests:** 30 pass (3 from Phase 1 and 27 new).

## Heads-Up

- The MLflow run tags the git commit that was checked out when training ran. If that was before these changes were committed, retrain after committing to make the tag match. The scores will not change.

## Not in This Pull Request

- Phases 3 to 5 (see `docs/implementation/remaining-phases.md`).
