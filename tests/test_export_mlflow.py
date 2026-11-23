"""Tests for the readable MLflow copy that export_latest_run writes into the reference folder.

Each test logs a small run with made-up data into a temporary database, the same way the
training tests do, so none of them touch the project's mlflow.db or use the network.
The most important rule checked here is that the copy leaks no user name or absolute path.
"""

import json
from pathlib import Path

import mlflow
import pytest
from mlflow.tracking import MlflowClient

from src.model.export_mlflow import backfill_runs, export_latest_run
from src.model.train import fit_pipeline, log_run
from tests.test_train import _games, _run_files, _scores, _settings, _write_data_file


@pytest.fixture(autouse=True)
def _restore_tracking_address():
    """export_latest_run points MLflow at a temporary database, so put the earlier address back."""
    # The tracking address is process-wide. Without this reset, a later test file would log
    # into the last test's deleted temporary database.
    before = mlflow.get_tracking_uri()
    yield
    mlflow.set_tracking_uri(before)


def _log(tmp_path: Path) -> dict:
    """Log one finished run and return the settings that point at it."""
    # _settings points the database, artifact folder, and reference folder at tmp_path.
    settings = _settings(tmp_path)
    _write_data_file(settings)
    pipeline = fit_pipeline(settings, _games())
    log_run(settings, _scores(), _run_files(tmp_path), pipeline)
    return settings


def test_writes_run_params_and_metrics(tmp_path):
    """run.json, params.json, and metrics.json hold the logged run's id, name, parameters, and metrics."""
    settings = _log(tmp_path)
    saved = export_latest_run(settings)
    client = MlflowClient()
    experiment = client.get_experiment_by_name(settings["tracking"]["experiment_name"])
    run = client.search_runs([experiment.experiment_id])[0]
    document = json.loads((saved / "run.json").read_text(encoding="utf-8"))
    params = json.loads((saved / "params.json").read_text(encoding="utf-8"))
    metrics = json.loads((saved / "metrics.json").read_text(encoding="utf-8"))
    assert document["run_id"] == run.info.run_id
    assert document["run_name"] == run.info.run_name
    assert params == run.data.params
    assert set(metrics) == set(run.data.metrics)
    assert metrics["train_accuracy"]["value"] == run.data.metrics["train_accuracy"]


def test_leaves_out_user_and_absolute_paths(tmp_path):
    """No written file contains the temporary path, a file address, or the mlflow.user value."""
    settings = _log(tmp_path)
    saved = export_latest_run(settings)
    # export_latest_run has already pointed MLflow at the temporary database, so this client reads the same run.
    client = MlflowClient()
    experiment = client.get_experiment_by_name(settings["tracking"]["experiment_name"])
    run = client.search_runs([experiment.experiment_id])[0]
    user_name = run.data.tags["mlflow.user"]
    document = json.loads((saved / "run.json").read_text(encoding="utf-8"))
    assert "mlflow.user" not in document["tags"]
    assert "mlflow.source.name" not in document["tags"]
    # Join every text file so one search covers them all. PNG files are binary and are skipped.
    blob = "\n".join(path.read_text(encoding="utf-8") for path in saved.rglob("*") if path.is_file() and path.suffix != ".png")
    assert str(tmp_path) not in blob
    assert "file:///" not in blob
    assert user_name not in blob


def test_copies_text_and_images_and_lists_binaries(tmp_path):
    """The config copy and the plot are copied. The two binaries are listed and not copied."""
    settings = _log(tmp_path)
    saved = export_latest_run(settings)
    assert (saved / "artifacts" / "config" / "config.yaml").read_text(encoding="utf-8").startswith("model:")
    assert (saved / "artifacts" / "plots" / "confusion_matrix_validation.png").read_bytes() == b"plot"
    listed = json.loads((saved / "artifact-list.json").read_text(encoding="utf-8"))
    binaries = [item for item in listed if item["path"].endswith(("model.joblib", "model.skops"))]
    assert len(binaries) == 2
    assert all(item["copied"] is False for item in binaries)
    assert not (saved / "model.joblib").exists()
    assert not list(saved.rglob("model.skops"))
    assert not list(saved.rglob("model.joblib"))


def test_picks_the_newest_finished_run(tmp_path):
    """With two finished runs and one failed run, the newer finished run is exported."""
    settings = _settings(tmp_path)
    # Build an empty MLflow store manually inside tmp_path: a SQLite file plus an artifact folder.
    database = Path(settings["tracking"]["database_path"])
    artifacts = Path(settings["tracking"]["artifact_folder"])
    artifacts.mkdir(parents=True)
    mlflow.set_tracking_uri(f"sqlite:///{database}")
    mlflow.create_experiment(settings["tracking"]["experiment_name"], artifact_location=artifacts.as_uri())
    mlflow.set_experiment(settings["tracking"]["experiment_name"])
    with mlflow.start_run(run_name="older"):
        mlflow.log_param("model_version", "old")
    with mlflow.start_run(run_name="newer"):
        mlflow.log_param("model_version", "new")
    # Raising inside the run block makes MLflow mark it FAILED. The export must skip it.
    with pytest.raises(RuntimeError):
        with mlflow.start_run(run_name="failed-run"):
            mlflow.log_param("model_version", "bad")
            raise RuntimeError("stop")
    saved = export_latest_run(settings)
    document = json.loads((saved / "run.json").read_text(encoding="utf-8"))
    assert document["run_name"] == "newer"


def test_no_run_stops_with_a_clear_message(tmp_path):
    """An empty experiment raises ValueError naming the missing run."""
    settings = _settings(tmp_path)
    # An experiment with no runs: the same hand-built store, but nothing is logged into it.
    database = Path(settings["tracking"]["database_path"])
    artifacts = Path(settings["tracking"]["artifact_folder"])
    artifacts.mkdir(parents=True)
    mlflow.set_tracking_uri(f"sqlite:///{database}")
    mlflow.create_experiment(settings["tracking"]["experiment_name"], artifact_location=artifacts.as_uri())
    with pytest.raises(ValueError, match="No MLflow run of"):
        export_latest_run(settings)


def _files(folder: Path) -> dict[str, bytes]:
    """Every file under a run folder, keyed by its path inside that folder."""
    return {
        path.relative_to(folder).as_posix(): path.read_bytes()
        for path in folder.rglob("*")
        if path.is_file()
    }


def _another_run(settings: dict, tmp_path: Path) -> None:
    """Log one more finished run into the same temporary database."""
    pipeline = fit_pipeline(settings, _games())
    log_run(settings, _scores(), _run_files(tmp_path), pipeline)


def test_a_new_run_moves_the_last_one_to_previous_runs(tmp_path):
    """Exporting a second run keeps the first run's files under previous-runs."""
    settings = _log(tmp_path)
    saved = export_latest_run(settings)
    first = json.loads((saved / "run.json").read_text(encoding="utf-8"))
    first_files = _files(saved)
    _another_run(settings, tmp_path)
    saved = export_latest_run(settings)
    second = json.loads((saved / "run.json").read_text(encoding="utf-8"))
    folder = saved.parent
    archived = folder / "previous-runs" / f"{first['start_time'].replace(':', '-')}_{first['run_id'][:8]}"
    assert second["run_id"] != first["run_id"]
    assert json.loads((saved / "run.json").read_text(encoding="utf-8"))["run_id"] == second["run_id"]
    assert _files(archived) == first_files


def test_exporting_the_same_run_twice_archives_nothing(tmp_path):
    """A second export of the same run does not create previous-runs."""
    settings = _log(tmp_path)
    export_latest_run(settings)
    export_latest_run(settings)
    previous = Path(settings["tracking"]["reference_folder"]) / "previous-runs"
    assert not previous.exists() or not any(previous.iterdir())


def test_history_lists_every_run_newest_first(tmp_path):
    """Both history files list the newer run first, with each run's folder, commit, and scores."""
    settings = _log(tmp_path)
    export_latest_run(settings)
    _another_run(settings, tmp_path)
    export_latest_run(settings)
    folder = Path(settings["tracking"]["reference_folder"])
    history = json.loads((folder / "run-history.json").read_text(encoding="utf-8"))
    markdown = (folder / "run-history.md").read_text(encoding="utf-8")
    assert [item["folder"] for item in history] == [
        "latest-run",
        f"previous-runs/{next(folder.joinpath('previous-runs').iterdir()).name}",
    ]
    assert history[0]["run_id"] != history[1]["run_id"]
    for item in history:
        run_folder = folder / item["folder"]
        document = json.loads((run_folder / "run.json").read_text(encoding="utf-8"))
        metrics = json.loads((run_folder / "metrics.json").read_text(encoding="utf-8"))
        assert item["run_id"] == document["run_id"]
        assert item["git_commit"] == document["tags"].get("mlflow.source.git.commit")
        assert item["validation_accuracy"] == round(metrics["validation_accuracy"]["value"], 6)
        assert item["test_log_loss"] == round(metrics["test_log_loss"]["value"], 6)
    assert "Started (UTC)" in markdown
    assert markdown.index(history[0]["run_id"][:8]) < markdown.index(history[1]["run_id"][:8])
    data_rows = [line for line in markdown.splitlines() if line.startswith("| 20")]
    assert len(data_rows) == 2


def test_backfill_adds_older_runs_once(tmp_path):
    """Backfill adds the two older runs, and a second backfill adds nothing."""
    settings = _log(tmp_path)
    _another_run(settings, tmp_path)
    _another_run(settings, tmp_path)
    export_latest_run(settings)
    added = backfill_runs(settings)
    folder = Path(settings["tracking"]["reference_folder"])
    assert len(added) == 2
    assert len(list((folder / "previous-runs").iterdir())) == 2
    assert backfill_runs(settings) == []
    assert len(list((folder / "previous-runs").iterdir())) == 2


def test_a_failed_export_puts_the_archive_back(tmp_path, monkeypatch):
    """When the new run cannot be written, the previous latest run stays where it was."""
    settings = _log(tmp_path)
    saved = export_latest_run(settings)
    first_id = json.loads((saved / "run.json").read_text(encoding="utf-8"))["run_id"]
    _another_run(settings, tmp_path)

    def fail(*_args, **_kwargs):
        raise RuntimeError("stop")

    monkeypatch.setattr("src.model.export_mlflow.export_run", fail)
    with pytest.raises(RuntimeError, match="stop"):
        export_latest_run(settings)
    folder = Path(settings["tracking"]["reference_folder"])
    assert json.loads((folder / "latest-run" / "run.json").read_text(encoding="utf-8"))["run_id"] == first_id
    assert not (folder / "previous-runs").exists()
