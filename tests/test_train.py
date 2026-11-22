"""Tests for fitting, saving, and recording a run.

The games are random but made from a fixed seed, so every run sees the same table. Every file,
including the MLflow database and its artifact folder, goes under the test's temporary folder,
so no test writes into the project or needs a network.
"""

import json
from pathlib import Path
from unittest.mock import patch

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
import pytest
import sklearn
from mlflow.tracking import MlflowClient
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.model.evaluate import score_group
from src.model.features import INPUT_COLUMNS
from src.model.train import (
    build_pipeline,
    file_fingerprint,
    fit_pipeline,
    log_run,
    save_model,
    write_run_summary,
)

# The exact names a run must record. Phase 3 and the README read these names, so a rename or a
# missing entry should fail a test instead of passing unnoticed.
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
    "scikit_learn_version",
    "data_sha256",
}

# Scores stored as fractions. There is no training log loss on purpose: the model is fit by
# pushing that number down, so it would not be a fair check.
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

# The three files stored with each run, as paths inside the run's artifacts.
ARTIFACT_NAMES = {
    "model/model.joblib",
    "plots/confusion_matrix_validation.png",
    "config/config.yaml",
}


@pytest.fixture(autouse=True)
def _restore_tracking_address():
    """log_run points MLflow at a temporary database, so put the earlier address back after each test."""
    # MLflow keeps its tracking address in a global setting. Without this reset, a later test
    # (or a later file) would log into the previous test's deleted folder.
    before = mlflow.get_tracking_uri()
    yield
    mlflow.set_tracking_uri(before)


def _games() -> pd.DataFrame:
    """About 60 rows whose home-win label depends a little on the two inputs."""
    # A generator with a fixed starting number, so every test run builds the same 60 rows.
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
        "data": {"from_s3_path": str(tmp_path / "games.csv")},
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
            "summary_path": str(tmp_path / "results" / "run-summary.json"),
            # The readable MLflow copy goes under tmp_path, so a test never writes into the project's reference folder.
            "reference_folder": str(tmp_path / "mlflow-reference"),
        },
    }


def _write_data_file(settings: dict) -> Path:
    """A stand-in for the downloaded table, so a test can fingerprint a real file."""
    path = Path(settings["data"]["from_s3_path"])
    path.write_bytes(b"abc")
    return path


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
    # Shifting the validation inputs moves their average far from the training average, so a
    # scaler fitted on both tables would give a clearly different mean.
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
    # allclose ignores differences far below anything that could change a displayed probability.
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
    # The file is written under a .partial name and then swapped in, so no .partial file may remain.
    assert not path.with_name(path.name + ".partial").exists()
    assert path.parent.is_dir()


def test_failed_save_keeps_the_old_file(tmp_path):
    """A failed write raises, leaves the existing model unchanged, and removes the partial file."""
    settings = _settings(tmp_path)
    path = Path(settings["model"]["output_path"])
    path.parent.mkdir(parents=True)
    path.write_bytes(b"already saved")
    pipeline = fit_pipeline(settings, _games())
    # Make the write fail partway. The patch is on the name train.py uses, so only this call fails.
    with patch("src.model.train.joblib.dump", side_effect=OSError("disk full")):
        with pytest.raises(OSError, match="disk full"):
            save_model(pipeline, settings, 2020, 2024)
    assert path.read_bytes() == b"already saved"
    assert not path.with_name(path.name + ".partial").exists()


def test_file_fingerprint(tmp_path):
    """The fingerprint of the bytes abc is the known SHA-256, and one changed byte differs."""
    path = tmp_path / "sample.txt"
    path.write_bytes(b"abc")
    # The long value is the published SHA-256 test value for the text abc.
    assert file_fingerprint(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    path.write_bytes(b"abd")
    assert file_fingerprint(path) != "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_mlflow_logs_the_run(tmp_path):
    """One run stores the run name, every parameter, every score, and the three files."""
    settings = _settings(tmp_path)
    data_path = _write_data_file(settings)
    pipeline = fit_pipeline(settings, _games())
    run_name = log_run(settings, _scores(), _run_files(tmp_path), pipeline)
    experiment = mlflow.get_experiment_by_name(settings["tracking"]["experiment_name"])
    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    assert len(runs) == 1
    assert runs.iloc[0]["tags.mlflow.runName"] == run_name
    assert run_name == "LogisticRegression-v1.0"
    run_id = runs.iloc[0]["run_id"]
    client = MlflowClient()
    recorded = client.get_run(run_id)
    # Sets are compared, so a missing or an extra name fails the test.
    assert set(recorded.data.params) == PARAMETER_NAMES
    assert recorded.data.params["scikit_learn_version"] == sklearn.__version__
    assert recorded.data.params["data_sha256"] == file_fingerprint(data_path)
    assert set(recorded.data.metrics) == METRIC_NAMES
    # Neither of these scores is recorded on purpose. Training log loss is not a fair check,
    # and the project does not report a ROC AUC.
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
    _write_data_file(settings)
    files = _run_files(tmp_path)
    pipeline = fit_pipeline(settings, _games())
    # The same files are reused, because only the number of runs is under test.
    log_run(settings, _scores(), files, pipeline)
    log_run(settings, _scores(), files, pipeline)
    experiment = mlflow.get_experiment_by_name(settings["tracking"]["experiment_name"])
    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    assert len(runs) == 2


def _summary_scores(pipeline, games: pd.DataFrame) -> dict:
    """Scores for three slices of the made-up table."""
    groups = {
        "training": games.iloc[:40],
        "validation": games.iloc[40:52],
        "test": games.iloc[52:],
    }
    return {name: score_group(pipeline, group) for name, group in groups.items()}


def test_run_summary_contents(tmp_path):
    """The summary lists its keys in order, omits a training log loss, and rounds the weights."""
    settings = _settings(tmp_path)
    data_path = _write_data_file(settings)
    games = _games()
    pipeline = fit_pipeline(settings, games)
    summary_path = write_run_summary(settings, _summary_scores(pipeline, games), pipeline)
    loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    assert list(loaded) == [
        "model_version",
        "model_type",
        "random_seed",
        "C",
        "solver",
        "max_iter",
        "scikit_learn_version",
        "inputs",
        "train_start_season",
        "train_end_season",
        "validation_season",
        "test_season",
        "data_file",
        "data_sha256",
        "scores",
        "learned",
    ]
    assert loaded["scikit_learn_version"] == sklearn.__version__
    assert loaded["data_sha256"] == file_fingerprint(data_path)
    estimator = pipeline.named_steps["logisticregression"]
    # The summary stores the weights rounded to 6 decimals, so the expected values are rounded the same way.
    assert loaded["learned"]["weights"] == [round(float(value), 6) for value in estimator.coef_[0]]
    assert loaded["learned"]["intercept"] == round(float(estimator.intercept_[0]), 6)
    assert "log_loss" not in loaded["scores"]["training"]
    assert "log_loss" in loaded["scores"]["validation"]
    assert "log_loss" in loaded["scores"]["test"]


def test_run_summary_is_identical_on_a_rerun(tmp_path):
    """Writing the same summary twice leaves identical bytes and no partial file."""
    settings = _settings(tmp_path)
    _write_data_file(settings)
    games = _games()
    pipeline = fit_pipeline(settings, games)
    scores = _summary_scores(pipeline, games)
    first = write_run_summary(settings, scores, pipeline)
    # Comparing bytes, not parsed JSON, catches any change in key order or spacing.
    first_bytes = first.read_bytes()
    second = write_run_summary(settings, scores, pipeline)
    assert second.read_bytes() == first_bytes
    assert not second.with_name(second.name + ".partial").exists()


def test_mlflow_format_model_is_logged(tmp_path):
    """The run stores one MLflow-format model, and the run's own file list stays at three files."""
    settings = _settings(tmp_path)
    _write_data_file(settings)
    games = _games()
    pipeline = fit_pipeline(settings, games)
    log_run(settings, _scores(), _run_files(tmp_path), pipeline)
    experiment = mlflow.get_experiment_by_name(settings["tracking"]["experiment_name"])
    logged = MlflowClient().search_logged_models(experiment_ids=[experiment.experiment_id])
    assert len(logged) == 1
    assert logged[0].name == "pipeline-mlflow-format"
    # Loading by the models:/ address proves the stored model is readable by MLflow, not only present.
    reloaded = mlflow.sklearn.load_model(f"models:/{logged[0].model_id}")
    assert np.allclose(
        reloaded.predict_proba(games[INPUT_COLUMNS]),
        pipeline.predict_proba(games[INPUT_COLUMNS]),
    )
    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    assert _artifact_paths(runs.iloc[0]["run_id"]) == ARTIFACT_NAMES
