# MLflow Logging Reference

This folder is a readable log of every MLflow training run of this project. Anyone can see what was logged without installing or running anything. The full MLflow records stay on the developer's computer, because they store absolute paths that would not open anywhere else.

Training writes this folder by itself. `make train` (or `python -m src.model.train`) logs the run to MLflow, then calls the export in `src/model/export_mlflow.py`. The export does three things:

1. **Archives the last run.** The current `latest-run/` moves into `previous-runs/`, with its files unchanged.
2. **Writes the new run** to `latest-run/`.
3. **Rebuilds `run-history.md` and `run-history.json`** from every run folder here.

The folder grows by one run each time the model is trained, so it is a lasting log. The pictures in `screenshots/` are taken by hand and are not rewritten by training.

## Where Do I Start?

- **[`run-history.md`](run-history.md)** lists every run, newest first, with its start time, git commit, scores, and a link to its folder. Open this first.
- **[`latest-run/`](latest-run/)** is the newest run.
- **[`previous-runs/`](previous-runs/)** holds every earlier run, one folder each.
- **[`screenshots/`](screenshots/)** shows the MLflow screen for the newest run when the pictures were taken.

## What Is in This Folder

```text
mlflow-reference/
  README.md                  this page, written by hand
  run-history.md             every run, newest first (generated)
  run-history.json           the same list, as data (generated)
  latest-run/                the newest run (generated)
    run.json                   the run's id, name, status, times, and git commit
    params.json                the 15 settings the run used
    metrics.json               the 8 scores the run recorded
    artifact-list.json         every file MLflow holds for the run, with sizes
    artifacts/
      config/config.yaml         the settings file as it was for this run
      plots/confusion_matrix_validation.png
    logged-model/
      MLmodel                    MLflow's description of the saved model
      requirements.txt           the packages the model needs
      python_env.yaml            the Python version and packages
      conda.yaml                 the same, for conda
  previous-runs/             one folder per earlier run (generated)
    <start time>_<run id>/     the same files as latest-run/
  screenshots/
    runs.png                   the MLflow screen: the experiment and its runs
    run-overview.png           one run's settings and scores
    run-artifacts.png          one run's saved files
```

- **A previous run's folder name** is the run's start time in UTC, then the first 8 characters of its run id, for example `2026-11-22T21-40-33Z_0086979f`. The `:` in the time is written as `-`, so the name works on every computer. The names sort in time order.
- **Each run adds about 40 KB.** Most of that is the confusion-matrix picture.
- **The history is built from the folders here,** not from MLflow's database. It reads the same in any copy of the repository.
- **Running the export twice on the same run changes nothing.** The run is archived only when a newer run replaces it.
- **Runs from before the history began** are added once with `python -m src.model.export_mlflow --backfill`.

## What MLflow Logs on Each Run

Each run of training is one MLflow run named `LogisticRegression-v1.0`, in the experiment `nfl-pregame-winner-v1`.

### Parameters (15)

These are the settings the run used. MLflow stores every parameter as text.

- **The model:** `model_version`, `C`, `solver`, `max_iter`, and `random_seed`.
- **The inputs:** `feature_names` (`win_pct_differential,point_diff_per_game_differential`).
- **The split:** `train_start_season`, `train_end_season`, `validation_season`, and `test_season`.
- **The group sizes:** `n_train`, `n_validation`, and `n_test`.
- **What it ran on:** `scikit_learn_version`, and `data_sha256`, the fingerprint of the data file. A different fingerprint means different data.

### Metrics (8)

These are what the run scored. Accuracy is a fraction from 0 to 1, so 0.631 means 63.1%.

- **Accuracy:** `train_accuracy`, `validation_accuracy`, and `test_accuracy`.
- **Baselines:** `baseline_train`, `baseline_validation`, and `baseline_test`. Each is the accuracy of always picking the home team, the score the model has to beat.
- **Log loss:** `validation_log_loss` and `test_log_loss`. It is lower when the model gives a high chance to the team that wins. Training log loss is left out, because the model is fit by pushing that number down.

### Tags

- **Kept here:** `mlflow.runName`, `mlflow.source.type`, `mlflow.source.git.commit`, `mlflow.source.git.branch`, and `mlflow.source.git.repoURL`. The commit says which version of the code made the run.
- **Left out:** `mlflow.user` and `mlflow.source.name`, because they can hold a user name and an absolute file path.
- **The run's owner** is set to `510-m3-pipeline` when the run is logged, so the MLflow screen shows that and not a computer's user name. Runs logged before this was added kept the older value, which is never copied here.

### Files

- **Copied here:** the settings file and the confusion-matrix picture for the validation games, and the logged model's text files.
- **Listed but not copied:** `model/model.joblib` and the logged model's `model.skops`. They are binary files that training rebuilds, so `artifact-list.json` records their names and sizes instead.

## How Do I See the Full MLflow Screen?

Train once, then start the MLflow screen from the project folder:

```bash
make train
```

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

Open the address it prints (`http://127.0.0.1:5000`, or add `--port 5001` if 5000 is taken, as it is by macOS Control Center), and choose the experiment `nfl-pregame-winner-v1`. The screen lists every run in your local database. This folder lists every run that was exported.

## Where to Read More

- [Phase 2 Implementation Part 2](../docs/implementation/phase-2/implementation-part-2.md) explains each logged value and why it is logged.
- [Phase 2 Development Guide](../docs/implementation/phase-2/development-guide.md) explains each output file: the model, `mlflow.db`, `mlartifacts/`, and the run summary.
- [`results/run-summary.json`](../results/run-summary.json) is the other committed record of the latest run: its settings, scores, and learned weights, rounded so the file stays the same when nothing changes.
