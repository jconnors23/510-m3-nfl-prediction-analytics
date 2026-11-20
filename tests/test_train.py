"""Tests for fitting, saving, and recording a run.

The games are random but fixed, and every file goes under the test's temporary folder.
"""

from pathlib import Path
from unittest.mock import patch

import joblib
import mlflow
import numpy as np
import pandas as pd
import pytest
from mlflow.tracking import MlflowClient
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.model.features import INPUT_COLUMNS
from src.model.train import build_pipeline, fit_pipeline, log_run, save_model

PARAMETER_NAMES = {
    "model_version",
    "random_seed",
    "C",
    "solver",
    "max_iter",
    "feature_names",
    "train_start_season",
    "train_end_season",
    "validation_season",
    "test_season",
    "n_train",
    "n_validation",
    "n_test",
}

METRIC_NAMES = {
    "train_accuracy",
    "validation_accuracy",
    "test_accuracy",
    "validation_log_loss",
    "test_log_loss",
    "baseline_train",
    "baseline_validation",
    "baseline_test",
}

ARTIFACT_NAMES = {
    "model/model.joblib",
    "plots/confusion_matrix_validation.png",
    "config/config.yaml",
}


@pytest.fixture(autouse=True)
def _restore_tracking_address():
    """log_run points MLflow at a temporary database, so put the earlier address back after each test."""
    before = mlflow.get_tracking_uri()
    yield
    mlflow.set_tracking_uri(before)


def _games() -> pd.DataFrame:
    """About 60 rows whose home-win label depends a little on the two inputs."""
    generator = np.random.default_rng(0)
    count = 60
    win_pct = generator.normal(0, 0.3, count)
    margin = generator.normal(0, 8, count)
    chance = 1 / (1 + np.exp(-(0.8 * win_pct + 0.05 * margin)))
    return pd.DataFrame(
        {
            INPUT_COLUMNS[0]: win_pct,
            INPUT_COLUMNS[1]: margin,
            "home_win": (generator.random(count) < chance).astype(int),
        }
    )


def _settings(tmp_path: Path) -> dict:
    """Settings shaped like the config file, with every output inside the temporary folder."""
    return {
        "window": {"start_season": 2020, "end_season": 2026, "test_through_week": 10},
        "split": {"train_end_season": 2024, "validation_season": 2025},
        "model": {
            "version": "v1.0",
            "random_seed": 42,
            "output_path": str(tmp_path / "models" / "model.joblib"),
            "logistic_regression": {"C": 1.0, "solver": "lbfgs", "max_iter": 1000},
        },
        "tracking": {
            "experiment_name": "nfl-pregame-winner-v1",
            "database_path": str(tmp_path / "mlflow.db"),
            "artifact_folder": str(tmp_path / "mlartifacts"),
        },
    }


def _scores() -> dict:
    """Small stand-in scores so a logging test does not need a fitted model."""
    return {
        "training": {"games": 40, "accuracy": 0.6, "baseline": 0.55, "log_loss": 0.6},
        "validation": {"games": 12, "accuracy": 0.5, "baseline": 0.5, "log_loss": 0.7},
        "test": {"games": 8, "accuracy": 0.5, "baseline": 0.4, "log_loss": 0.7},
    }


def _run_files(tmp_path: Path) -> dict:
    """The three files a run stores, written under the temporary folder."""
    model = tmp_path / "model.joblib"
    plot = tmp_path / "confusion_matrix_validation.png"
    config = tmp_path / "config.yaml"
    model.write_bytes(b"model")
    plot.write_bytes(b"plot")
    config.write_text("model:\n  version: v1.0\n", encoding="utf-8")
    return {"model": model, "plot": plot, "config": config}


def _artifact_paths(run_id: str) -> set[str]:
    """Every file path stored on one run."""
    client = MlflowClient()
    found = set()

    def walk(path: str) -> None:
        """Visit one folder of the run's files, going into subfolders."""
        for item in client.list_artifacts(run_id, path):
            if item.is_dir:
                walk(item.path)
            else:
                found.add(item.path)

    walk("")
    return found


def test_pipeline_order_and_settings(tmp_path):
    """The pipeline is a scaler, then logistic regression, using the settings values."""
    settings = _settings(tmp_path)
    pipeline = build_pipeline(settings)
    scaler, model = pipeline.steps[0][1], pipeline.steps[1][1]
    assert isinstance(scaler, StandardScaler)
    assert isinstance(model, LogisticRegression)
    assert model.C == settings["model"]["logistic_regression"]["C"]
    assert model.solver == settings["model"]["logistic_regression"]["solver"]
    assert model.max_iter == settings["model"]["logistic_regression"]["max_iter"]
    assert model.random_state == settings["model"]["random_seed"]


def test_scaler_uses_training_rows_only(tmp_path):
    """The scaler's average matches the training rows and not the training and validation rows together."""
    settings = _settings(tmp_path)
    games = _games()
    training = games.iloc[:40].copy()
    validation = games.iloc[40:].copy()
    validation[INPUT_COLUMNS] = validation[INPUT_COLUMNS] + 5
    pipeline = fit_pipeline(settings, training)
    learned = pipeline.named_steps["standardscaler"].mean_
    training_mean = training[INPUT_COLUMNS].mean().to_numpy()
    combined_mean = pd.concat([training, validation])[INPUT_COLUMNS].mean().to_numpy()
    assert np.allclose(learned, training_mean)
    assert not np.allclose(learned, combined_mean)


def test_same_settings_give_the_same_probabilities(tmp_path):
    """Two fits on the same table and the same settings give identical probabilities."""
    settings = _settings(tmp_path)
    training = _games()
    first = fit_pipeline(settings, training)
    second = fit_pipeline(settings, training)
    assert np.allclose(
        first.predict_proba(training[INPUT_COLUMNS]),
        second.predict_proba(training[INPUT_COLUMNS]),
    )


def test_saved_file_round_trip(tmp_path):
    """The saved dictionary reloads to the same probabilities, and the parent folder is created."""
    settings = _settings(tmp_path)
    training = _games()
    pipeline = fit_pipeline(settings, training)
    path = save_model(pipeline, settings, 2020, 2024)
    loaded = joblib.load(path)
    assert list(loaded) == [
        "pipeline",
        "feature_names",
        "model_version",
        "scikit_learn_version",
        "train_start_season",
        "train_end_season",
    ]
    assert np.allclose(
        loaded["pipeline"].predict_proba(training[INPUT_COLUMNS]),
        pipeline.predict_proba(training[INPUT_COLUMNS]),
    )
    assert not path.with_name(path.name + ".partial").exists()
    assert path.parent.is_dir()


def test_failed_save_keeps_the_old_file(tmp_path):
    """A failed write raises, leaves the existing model unchanged, and removes the partial file."""
    settings = _settings(tmp_path)
    path = Path(settings["model"]["output_path"])
    path.parent.mkdir(parents=True)
    path.write_bytes(b"already saved")
    pipeline = fit_pipeline(settings, _games())
    with patch("src.model.train.joblib.dump", side_effect=OSError("disk full")):
        with pytest.raises(OSError, match="disk full"):
            save_model(pipeline, settings, 2020, 2024)
    assert path.read_bytes() == b"already saved"
    assert not path.with_name(path.name + ".partial").exists()


def test_mlflow_logs_the_run(tmp_path):
    """One run stores the run name, every parameter, every score, and the three files."""
    settings = _settings(tmp_path)
    run_name = log_run(settings, _scores(), _run_files(tmp_path))
    experiment = mlflow.get_experiment_by_name(settings["tracking"]["experiment_name"])
    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    assert len(runs) == 1
    assert runs.iloc[0]["tags.mlflow.runName"] == run_name
    assert run_name == "LogisticRegression-v1.0"
    run_id = runs.iloc[0]["run_id"]
    client = MlflowClient()
    recorded = client.get_run(run_id)
    assert set(recorded.data.params) == PARAMETER_NAMES
    assert set(recorded.data.metrics) == METRIC_NAMES
    assert "validation_roc_auc" not in recorded.data.metrics
    assert "train_log_loss" not in recorded.data.metrics
    assert _artifact_paths(run_id) == ARTIFACT_NAMES
    artifact_root = Path(settings["tracking"]["artifact_folder"])
    stored = {path.name for path in artifact_root.rglob("*") if path.is_file()}
    # The files must land under the temporary artifact folder, not under the project.
    assert {"model.joblib", "confusion_matrix_validation.png", "config.yaml"} <= stored


def test_second_run_joins_the_same_experiment(tmp_path):
    """Logging again adds a second run to the same experiment."""
    settings = _settings(tmp_path)
    files = _run_files(tmp_path)
    log_run(settings, _scores(), files)
    log_run(settings, _scores(), files)
    experiment = mlflow.get_experiment_by_name(settings["tracking"]["experiment_name"])
    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    assert len(runs) == 2
