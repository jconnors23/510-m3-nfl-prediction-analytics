"""Fit the model on the training seasons, score it, record the run, and save the file."""

import hashlib
import json
import os
import tempfile
from pathlib import Path

import joblib

# MLflow prints a hint about its tracing helper the moment it is imported. This project does
# not use tracing, so the hint is switched off here, before the import.
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
import mlflow  # noqa: E402
import mlflow.sklearn  # noqa: E402
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import data_file, load_config, project_root, resolve_path, split_seasons
from src.model.evaluate import plot_confusion_matrix, score_group
from src.model.features import (
    INPUT_COLUMNS,
    build_model_table,
    check_model_table,
    load_games,
    split_games,
)

# The name MLflow uses for its own copy of the pipeline. Project code does not load this copy.
MLFLOW_MODEL_NAME = "pipeline-mlflow-format"


def file_fingerprint(path) -> str:
    """SHA-256 of a file, so two runs can be checked against the same data."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        digest.update(handle.read())
    return digest.hexdigest()


def _rounded(value):
    """Six decimal places, so a rerun writes the same digits."""
    return round(float(value), 6)


def build_pipeline(config: dict):
    """A scaler and a logistic regression, with every setting taken from the config file."""
    logistic = config["model"]["logistic_regression"]
    # The scaler puts both inputs on a common scale (their raw sizes differ about 30 times),
    # then the model learns a weight for each. Keeping them in one pipeline means the saved
    # model can never be used without the scaler. All settings come from config.yaml.
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(
            C=logistic["C"],
            solver=logistic["solver"],
            max_iter=logistic["max_iter"],
            random_state=config["model"]["random_seed"],
        ),
    )


def fit_pipeline(config: dict, training):
    """Fit the scaler and the model on the training games only."""
    pipeline = build_pipeline(config)
    # fit learns the scaler's averages and spreads and the model's weights from these rows alone.
    # Validation and test games stay out of this call, so their results cannot move the weights.
    # The answer column is home_win, which is 1 when the home team won.
    pipeline.fit(training[INPUT_COLUMNS], training["home_win"])
    return pipeline


def save_model(pipeline, config: dict, start_season: int, train_end_season: int) -> Path:
    """Write the fitted pipeline beside the facts needed to load it later."""
    output = resolve_path(config["model"]["output_path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    # The model travels with the facts the API will need to use it safely: the input names in
    # order, which version it is, and which scikit-learn built it (a model saved by one version
    # may fail to load, or answer differently, under another).
    bundle = {
        "pipeline": pipeline,
        "feature_names": INPUT_COLUMNS,
        "model_version": config["model"]["version"],
        "scikit_learn_version": sklearn.__version__,
        "train_start_season": int(start_season),
        "train_end_season": int(train_end_season),
    }
    # Write beside the real file and swap only after the write finishes, so a failed run
    # cannot leave a half-written model in place of a good one.
    partial = output.with_name(output.name + ".partial")
    try:
        # joblib.dump writes a Python object to a file, and is the usual way to save a scikit-learn model.
        joblib.dump(bundle, partial)
        # os.replace swaps the finished file into place in one step, replacing any older model.
        os.replace(partial, output)
    except Exception:
        # Whatever went wrong, remove the half-written file and pass the error on.
        partial.unlink(missing_ok=True)
        raise
    return output


def write_run_summary(config: dict, scores: dict, pipeline) -> Path:
    """Write a small readable summary of the latest run, so the scores can be read without MLflow."""
    start_season, train_end_season, validation_season, test_season = split_seasons(config)
    model = config["model"]
    logistic = model["logistic_regression"]
    estimator = pipeline.named_steps["logisticregression"]
    scaler = pipeline.named_steps["standardscaler"]
    downloaded = data_file(config, "from_s3_path")
    summary = {
        "model_version": model["version"],
        "model_type": type(estimator).__name__,
        "random_seed": int(model["random_seed"]),
        "C": _rounded(logistic["C"]),
        "solver": logistic["solver"],
        "max_iter": int(logistic["max_iter"]),
        "scikit_learn_version": sklearn.__version__,
        "inputs": list(INPUT_COLUMNS),
        "train_start_season": int(start_season),
        "train_end_season": int(train_end_season),
        "validation_season": int(validation_season),
        "test_season": int(test_season),
        "data_file": config["data"]["from_s3_path"],
        "data_sha256": file_fingerprint(downloaded),
        "scores": {
            "training": {
                "games": int(scores["training"]["games"]),
                "correct": int(scores["training"]["correct"]),
                "accuracy": _rounded(scores["training"]["accuracy"]),
                "baseline": _rounded(scores["training"]["baseline"]),
            },
            "validation": {
                "games": int(scores["validation"]["games"]),
                "correct": int(scores["validation"]["correct"]),
                "accuracy": _rounded(scores["validation"]["accuracy"]),
                "baseline": _rounded(scores["validation"]["baseline"]),
                "log_loss": _rounded(scores["validation"]["log_loss"]),
            },
            "test": {
                "games": int(scores["test"]["games"]),
                "correct": int(scores["test"]["correct"]),
                "accuracy": _rounded(scores["test"]["accuracy"]),
                "baseline": _rounded(scores["test"]["baseline"]),
                "log_loss": _rounded(scores["test"]["log_loss"]),
            },
        },
        "learned": {
            "scaler_mean": [_rounded(value) for value in scaler.mean_],
            "scaler_scale": [_rounded(value) for value in scaler.scale_],
            "weights": [_rounded(value) for value in estimator.coef_[0]],
            "intercept": _rounded(estimator.intercept_[0]),
        },
    }
    # Rounding to six places keeps this file identical when the run itself did not change.
    text = json.dumps(summary, indent=2) + "\n"
    output = resolve_path(config["tracking"]["summary_path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.name + ".partial")
    try:
        partial.write_text(text, encoding="utf-8")
        os.replace(partial, output)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return output


def log_run(config: dict, scores: dict, files: dict, pipeline) -> str:
    """Record one run's settings, scores, and files, and return the run name."""
    database = resolve_path(config["tracking"]["database_path"])
    artifacts = resolve_path(config["tracking"]["artifact_folder"])
    # MLflow keeps its records in a local database file. The address is "sqlite://" plus the
    # full path (which starts with "/"), so it has four slashes in a row.
    mlflow.set_tracking_uri(f"sqlite:///{database}")
    experiment_name = config["tracking"]["experiment_name"]
    # An experiment is the named group that holds every run. Its file folder can only be set
    # when it is created, so create it once and let later runs join it.
    if mlflow.get_experiment_by_name(experiment_name) is None:
        artifacts.mkdir(parents=True, exist_ok=True)
        mlflow.create_experiment(experiment_name, artifact_location=artifacts.as_uri())
    mlflow.set_experiment(experiment_name)

    start_season, train_end_season, validation_season, test_season = split_seasons(config)
    model = config["model"]
    logistic = model["logistic_regression"]
    run_name = f"LogisticRegression-{model['version']}"
    # Training log loss is left out. The model is fit by pushing that number down, so it is not a fair check.
    # A run that fails partway is closed by `with` and marked as failed, so it is never left open.
    with mlflow.start_run(run_name=run_name):
        # MLflow keeps every parameter as text. Scores below are numbers, so they can be charted.
        mlflow.log_params(
            {
                "model_version": model["version"],
                "random_seed": model["random_seed"],
                "C": logistic["C"],
                "solver": logistic["solver"],
                "max_iter": logistic["max_iter"],
                "feature_names": ",".join(INPUT_COLUMNS),
                "train_start_season": start_season,
                "train_end_season": train_end_season,
                "validation_season": validation_season,
                "test_season": test_season,
                "n_train": scores["training"]["games"],
                "n_validation": scores["validation"]["games"],
                "n_test": scores["test"]["games"],
                "scikit_learn_version": sklearn.__version__,
                "data_sha256": file_fingerprint(data_file(config, "from_s3_path")),
            }
        )
        # Scores are stored as fractions between 0 and 1 (0.631 means 63.1%). The baseline is the
        # accuracy of always picking the home team, saved beside each accuracy to compare against.
        mlflow.log_metrics(
            {
                "train_accuracy": scores["training"]["accuracy"],
                "validation_accuracy": scores["validation"]["accuracy"],
                "test_accuracy": scores["test"]["accuracy"],
                "validation_log_loss": scores["validation"]["log_loss"],
                "test_log_loss": scores["test"]["log_loss"],
                "baseline_train": scores["training"]["baseline"],
                "baseline_validation": scores["validation"]["baseline"],
                "baseline_test": scores["test"]["baseline"],
            }
        )
        # The three files go in folders named model, plots, and config inside the run's artifacts.
        mlflow.log_artifact(str(files["model"]), artifact_path="model")
        mlflow.log_artifact(str(files["plot"]), artifact_path="plots")
        mlflow.log_artifact(str(files["config"]), artifact_path="config")
        # model/model.joblib is the working copy. It is what the API will load, and it carries
        # the input names, the version, the scikit-learn version, and the training seasons.
        # The MLflow-format copy exists so MLflow's screen and loader can open the model.
        # No project code loads it. Only its test does.
        mlflow.sklearn.log_model(pipeline, name=MLFLOW_MODEL_NAME)
    return run_name


def main() -> None:
    """Command for Phase 2: fit, score, save the model file, and record one MLflow run."""
    try:
        config = load_config()
        # Same table and split as `python -m src.model.features`, so the two commands agree.
        table = build_model_table(load_games(config))
        check_model_table(table)
        groups = split_games(table, config)
        pipeline = fit_pipeline(config, groups["training"])
        # All three groups are scored with the one fitted pipeline. Only training was used to fit it.
        scores = {
            name: score_group(pipeline, groups[name]) for name in ("training", "validation", "test")
        }
        # The confusion-matrix image is drawn only so the run can store a copy of it. It goes in a
        # temporary folder that is deleted afterward, so no image is left in the project.
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / "confusion_matrix_validation.png"
            plot_confusion_matrix(pipeline, groups["validation"], image)
            start_season, train_end_season, _, _ = split_seasons(config)
            # The model file is saved before logging, because the run stores a copy of it.
            save_model(pipeline, config, start_season, train_end_season)
            write_run_summary(config, scores, pipeline)
            run_name = log_run(
                config,
                scores,
                {
                    "model": resolve_path(config["model"]["output_path"]),
                    "plot": image,
                    "config": project_root() / "config" / "config.yaml",
                },
                pipeline,
            )
    except (ValueError, FileNotFoundError) as exc:
        # Expected problems (no downloaded table, a failed check) end with a short message.
        raise SystemExit(str(exc)) from None

    # One line per group: how many picks were right, and the always-pick-home score beside it.
    for name in ("training", "validation", "test"):
        score = scores[name]
        print(
            f"{name}: {score['correct']} of {score['games']} correct "
            f"({score['accuracy']:.2%}), always-home {score['baseline']:.2%}"
        )
    # Log loss is shown only for games the model did not train on. Lower is better, and 0.6931
    # is the score of saying 50-50 on every game.
    print(f"validation log loss {scores['validation']['log_loss']:.4f}")
    print(f"test log loss {scores['test']['log_loss']:.4f}")
    print(f"saved: {config['model']['output_path']}")
    print(f"summary: {config['tracking']['summary_path']}")
    print(f"MLflow run: {run_name}")


if __name__ == "__main__":
    main()
