"""Fit the model on the training seasons, score it, record the run, and save the file."""

import os
import tempfile
from pathlib import Path

import joblib

# MLflow prints a hint about its tracing helper the moment it is imported. This project does
# not use tracing, so the hint is switched off here, before the import.
os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")
import mlflow  # noqa: E402
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.config import load_config, project_root, resolve_path, split_seasons
from src.model.evaluate import plot_confusion_matrix, score_group
from src.model.features import (
    INPUT_COLUMNS,
    build_model_table,
    check_model_table,
    load_games,
    split_games,
)


def build_pipeline(config: dict):
    """A scaler and a logistic regression, with every setting taken from the config file."""
    logistic = config["model"]["logistic_regression"]
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
    # Validation and test games stay out of this call, so their results cannot move the weights.
    pipeline.fit(training[INPUT_COLUMNS], training["home_win"])
    return pipeline


def save_model(pipeline, config: dict, start_season: int, train_end_season: int) -> Path:
    """Write the fitted pipeline beside the facts needed to load it later."""
    output = resolve_path(config["model"]["output_path"])
    output.parent.mkdir(parents=True, exist_ok=True)
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
        joblib.dump(bundle, partial)
        os.replace(partial, output)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return output


def log_run(config: dict, scores: dict, files: dict) -> str:
    """Record one run's settings, scores, and files, and return the run name."""
    database = resolve_path(config["tracking"]["database_path"])
    artifacts = resolve_path(config["tracking"]["artifact_folder"])
    # The path already starts with /, so this address has four slashes.
    mlflow.set_tracking_uri(f"sqlite:///{database}")
    experiment_name = config["tracking"]["experiment_name"]
    # The artifact folder is fixed at creation, so a later run must join the same experiment.
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
            }
        )
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
        # The image exists only so the run can store it. The temporary folder removes it afterward.
        with tempfile.TemporaryDirectory() as folder:
            image = Path(folder) / "confusion_matrix_validation.png"
            plot_confusion_matrix(pipeline, groups["validation"], image)
            start_season, train_end_season, _, _ = split_seasons(config)
            # The model file is saved before logging, because the run stores a copy of it.
            save_model(pipeline, config, start_season, train_end_season)
            run_name = log_run(
                config,
                scores,
                {
                    "model": resolve_path(config["model"]["output_path"]),
                    "plot": image,
                    "config": project_root() / "config" / "config.yaml",
                },
            )
    except (ValueError, FileNotFoundError) as exc:
        # Expected problems (no downloaded table, a failed check) end with a short message.
        raise SystemExit(str(exc)) from None

    for name in ("training", "validation", "test"):
        score = scores[name]
        print(
            f"{name}: {score['correct']} of {score['games']} correct "
            f"({score['accuracy']:.2%}), always-home {score['baseline']:.2%}"
        )
    print(f"validation log loss {scores['validation']['log_loss']:.4f}")
    print(f"test log loss {scores['test']['log_loss']:.4f}")
    print(f"saved: {config['model']['output_path']}")
    print(f"MLflow run: {run_name}")


if __name__ == "__main__":
    main()
