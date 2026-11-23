"""Write a readable log of every MLflow run to mlflow-reference/, with no absolute paths.

mlflow.db and mlartifacts/ stay on this computer, because they store absolute paths. This file
copies what they hold into plain files that can be committed. Training calls export_latest_run
after every run. It moves the last run into previous-runs/, writes the new one to latest-run/,
and rebuilds run-history.md and run-history.json. `--backfill` adds older runs once.
"""

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

import mlflow
from mlflow.tracking import MlflowClient

from src.config import load_config, resolve_path

# The run tags the copy keeps. Only these tags are copied, and mlflow.user and
# mlflow.source.name are left out on purpose because they can hold a user name or an absolute
# path. A list of kept tags, rather than of removed ones, means a tag that a later MLflow
# version adds stays out until someone adds it here.
KEPT_TAGS = (
    "mlflow.runName",
    "mlflow.source.type",
    "mlflow.source.git.commit",
    "mlflow.source.git.branch",
    "mlflow.source.git.repoURL",
)
# File endings read as text when a copied file is not one of the named files below. Each text
# file is checked for absolute paths before it is written.
TEXT_SUFFIXES = {".yaml", ".yml", ".txt", ".json", ".md"}


def _local_path(uri: str) -> Path:
    """Turn an MLflow file address into a local path."""
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    return Path(uri)


def _iso(milliseconds: int) -> str:
    """Format an MLflow timestamp as UTC text."""
    return datetime.fromtimestamp(milliseconds / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _guard(text: str) -> None:
    """Stop if a text file would publish this computer's path or a file address."""
    home = str(Path.home())
    if home in text or "file:///" in text:
        raise ValueError("The export would contain an absolute path.")


def _json_text(payload: object) -> str:
    """JSON with sorted keys and one trailing newline."""
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    _guard(text)
    return text


def _copied(relative: str) -> bool:
    """True for the text and image files the reference folder keeps."""
    return relative.endswith(
        (
            "/config/config.yaml",
            "/plots/confusion_matrix_validation.png",
            "/MLmodel",
            "/requirements.txt",
            "/python_env.yaml",
            "/conda.yaml",
        )
    )


# The history table keeps these five scores. The other three metrics stay in each run's metrics.json.
HISTORY_METRICS = (
    "train_accuracy",
    "validation_accuracy",
    "test_accuracy",
    "validation_log_loss",
    "test_log_loss",
)


def _run_folder_name(start_time: str, run_id: str) -> str:
    """Name a previous-run folder from its UTC start time and the first 8 characters of its id."""
    # The colon in the time is written as a hyphen so the name is a valid folder on every computer.
    return f"{start_time.replace(':', '-')}_{run_id[:8]}"


def _finished_runs(config: dict, client: MlflowClient):
    """Return the experiment and its finished runs, newest first."""
    tracking = config["tracking"]
    experiment = client.get_experiment_by_name(tracking["experiment_name"])
    runs = []
    # Only a finished run is exported. A run that failed partway has missing scores or files.
    if experiment is not None:
        runs = client.search_runs(
            [experiment.experiment_id],
            filter_string="attributes.status = 'FINISHED'",
            order_by=["attributes.start_time DESC"],
        )
    return experiment, runs


def _require_runs(config: dict, experiment, runs) -> None:
    """Raise the same message when the experiment is missing and when it has no finished run."""
    # Both are fixed the same way: train once.
    if experiment is None or not runs:
        tracking = config["tracking"]
        raise ValueError(
            f"No MLflow run of {tracking['experiment_name']} in {tracking['database_path']}. "
            "Run python -m src.model.train first."
        )


def _open_client(config: dict) -> MlflowClient:
    """Point MLflow at this project's database and return a client for it."""
    database = resolve_path(config["tracking"]["database_path"])
    # The same local database training writes to, so the export reads exactly what was logged.
    mlflow.set_tracking_uri(f"sqlite:///{database}")
    return MlflowClient()


def export_run(config: dict, client: MlflowClient, run, destination: Path) -> None:
    """Write one run's files into destination, swapping them in by a rename."""
    tracking = config["tracking"]
    artifact_root = resolve_path(tracking["artifact_folder"])
    info = run.info
    # MLflow 3 keeps the logged model apart from the run, so it is found by the run id it came from.
    models = [
        model
        for model in client.search_logged_models(experiment_ids=[info.experiment_id])
        if model.source_run_id == info.run_id
    ]
    model = models[0] if models else None
    # Only the listed tags are kept, so a tag MLflow adds in a later version cannot leak a private value.
    tags = {key: run.data.tags[key] for key in KEPT_TAGS if key in run.data.tags}
    # MLflow stores times in milliseconds.
    duration = (info.end_time - info.start_time) / 1000
    run_document = {
        "experiment_name": tracking["experiment_name"],
        "experiment_id": info.experiment_id,
        "run_id": info.run_id,
        "run_name": info.run_name,
        "status": info.status,
        "start_time": _iso(info.start_time),
        "end_time": _iso(info.end_time),
        "duration_seconds": duration,
        "tags": tags,
    }
    metrics = {}
    # run.data.metrics holds values only. The history adds the step each value was logged at.
    for key in sorted(run.data.metrics):
        history = client.get_metric_history(info.run_id, key)
        latest = history[-1]
        metrics[key] = {"step": latest.step, "value": latest.value}
    # Every file MLflow holds for this run and its logged model. All of them are listed, and only
    # the text and image files are copied.
    sources: list[Path] = []
    run_root = _local_path(info.artifact_uri)
    if run_root.exists():
        sources.extend(path for path in run_root.rglob("*") if path.is_file())
    model_root = _local_path(model.artifact_location) if model is not None else None
    if model_root is not None and model_root.exists():
        sources.extend(path for path in model_root.rglob("*") if path.is_file())
    listed = []
    copies: dict[str, bytes] = {}
    for source in sources:
        # Paths are written relative to mlartifacts/, so the list never names this computer's folders.
        relative = source.resolve().relative_to(artifact_root.resolve()).as_posix()
        copied = _copied(relative)
        listed.append({"copied": copied, "path": relative, "size": source.stat().st_size})
        if not copied:
            continue
        # MLmodel records the model's folder as a full file:/// address. The copy names the same
        # folder relative to the project, which is the only line that changes.
        if source.name == "MLmodel" and model is not None:
            text = source.read_text(encoding="utf-8")
            replacement = f"artifact_path: mlartifacts/models/{model.model_id}/artifacts"
            lines = [replacement if line.startswith("artifact_path:") else line for line in text.splitlines()]
            rewritten = "\n".join(lines) + "\n"
            _guard(rewritten)
            copies["logged-model/MLmodel"] = rewritten.encode("utf-8")
            continue
        if source.name == "confusion_matrix_validation.png":
            copies["artifacts/plots/confusion_matrix_validation.png"] = source.read_bytes()
            continue
        if source.name == "config.yaml":
            text = source.read_text(encoding="utf-8")
            _guard(text)
            copies["artifacts/config/config.yaml"] = text.encode("utf-8")
            continue
        if source.suffix in TEXT_SUFFIXES or source.name in {"MLmodel", "requirements.txt", "python_env.yaml", "conda.yaml"}:
            text = source.read_text(encoding="utf-8")
            _guard(text)
            copies[f"logged-model/{source.name}"] = text.encode("utf-8")
    documents = {
        "run.json": _json_text(run_document),
        "params.json": _json_text(dict(sorted(run.data.params.items()))),
        "metrics.json": _json_text(metrics),
        "artifact-list.json": _json_text(sorted(listed, key=lambda item: item["path"])),
    }
    # A last check over every text file before anything is written: the run's user name must not
    # appear anywhere, even inside a copied file. Images are skipped, because they are not text.
    user_name = run.data.tags.get("mlflow.user", "")
    readable = list(documents.values())
    for payload in copies.values():
        try:
            readable.append(payload.decode("utf-8"))
        except UnicodeDecodeError:
            continue
    if user_name and any(user_name in text for text in readable):
        raise ValueError("The export would contain a user name or an absolute path.")
    # The new copy is built beside the old one and swapped in by renaming, so a failure partway
    # leaves the old copy whole, and a file from an older run can never linger in the new one.
    partial = destination.parent / f"{destination.name}.partial"
    if partial.exists():
        shutil.rmtree(partial)
    partial.mkdir(parents=True)
    for name, text in documents.items():
        (partial / name).write_text(text, encoding="utf-8")
    for relative, payload in copies.items():
        copied_path = partial / relative
        copied_path.parent.mkdir(parents=True, exist_ok=True)
        copied_path.write_bytes(payload)
    if destination.exists():
        previous = destination.parent / f"{destination.name}.previous"
        if previous.exists():
            shutil.rmtree(previous)
        os.rename(destination, previous)
        os.rename(partial, destination)
        shutil.rmtree(previous)
    else:
        os.rename(partial, destination)


def _archive_latest(folder: Path, run_id: str) -> Path | None:
    """Move the current latest run into previous-runs when a different run replaces it."""
    latest = folder / "latest-run"
    document_path = latest / "run.json"
    # The first export has nothing to keep.
    if not document_path.is_file():
        return None
    document = json.loads(document_path.read_text(encoding="utf-8"))
    # Exporting the same run again rewrites its folder and must not make a second copy.
    if document["run_id"] == run_id:
        return None
    name = _run_folder_name(document["start_time"], document["run_id"])
    archived = folder / "previous-runs" / name
    # A run id belongs in one folder. A name that is already there means the history is wrong.
    if archived.exists():
        raise ValueError(f"previous-runs/{name} already exists.")
    archived.parent.mkdir(parents=True, exist_ok=True)
    os.rename(latest, archived)
    return archived


def _restore_archive(archived: Path, latest: Path) -> None:
    """Put the archived run back so a failed export leaves the folder as it was."""
    # Anything the failed write left behind is removed before the archived run moves back.
    if latest.exists():
        shutil.rmtree(latest)
    os.rename(archived, latest)
    # A previous-runs/ folder made only for this archive is removed, so the folder is as it was.
    parent = archived.parent
    if parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()


def _history_entry(run_folder: Path, label: str) -> dict:
    """One history row, read from that run's exported files."""
    document = json.loads((run_folder / "run.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_folder / "metrics.json").read_text(encoding="utf-8"))
    entry = {
        "folder": label,
        "git_commit": document["tags"].get("mlflow.source.git.commit"),
        "run_id": document["run_id"],
        "run_name": document["run_name"],
        "start_time": document["start_time"],
        "status": document["status"],
    }
    for name in HISTORY_METRICS:
        recorded = metrics.get(name)
        entry[name] = None if recorded is None else round(recorded["value"], 6)
    return entry


def _history_markdown(entries: list[dict]) -> str:
    """The history table, newest first, with one relative link per run."""
    header = (
        "| Started (UTC) | Run | Commit | Validation accuracy | Test accuracy | Validation log loss | Folder |"
    )
    separator = "| --- | --- | --- | --- | --- | --- | --- |"
    rows = [header, separator]
    for entry in entries:
        commit = entry["git_commit"]
        commit_cell = "none" if not commit else commit[:7]
        validation = _percent(entry["validation_accuracy"])
        test = _percent(entry["test_accuracy"])
        loss = "none" if entry["validation_log_loss"] is None else f"{entry['validation_log_loss']:.4f}"
        folder = entry["folder"]
        rows.append(
            "| "
            + " | ".join(
                [
                    entry["start_time"],
                    entry["run_id"][:8],
                    commit_cell,
                    validation,
                    test,
                    loss,
                    f"[{folder}]({folder}/)",
                ]
            )
            + " |"
        )
    text = (
        "# MLflow Run History\n\n"
        "Every training run of this project, newest first. Each row links to that run's folder.\n\n"
        + "\n".join(rows)
        + "\n\nGenerated by python -m src.model.export_mlflow. Do not edit it manually.\n"
    )
    _guard(text)
    return text


def _percent(value: float | None) -> str:
    """Format an accuracy fraction as a percentage with two decimals."""
    if value is None:
        return "none"
    return f"{value * 100:.2f}%"


def _collect_entries(folder: Path) -> list[dict]:
    """Read latest-run and every previous run, newest first."""
    entries = []
    latest = folder / "latest-run"
    if (latest / "run.json").is_file():
        entries.append(_history_entry(latest, "latest-run"))
    previous = folder / "previous-runs"
    if previous.is_dir():
        for child in previous.iterdir():
            if (child / "run.json").is_file():
                entries.append(_history_entry(child, f"previous-runs/{child.name}"))
    # The start time is UTC text, so sorting it puts the newest run first.
    entries.sort(key=lambda entry: entry["start_time"], reverse=True)
    return entries


def _rebuild_history(folder: Path) -> list[dict]:
    """Rewrite both history files from the run folders already in the reference folder."""
    entries = _collect_entries(folder)
    # The history is built from those folders, so it is checked by the same path guard as a run.
    (folder / "run-history.json").write_text(_json_text(entries), encoding="utf-8")
    (folder / "run-history.md").write_text(_history_markdown(entries), encoding="utf-8")
    return entries


def export_latest_run(config: dict) -> Path:
    """Archive the current latest run, write the newest finished run, and rebuild the history."""
    folder = resolve_path(config["tracking"]["reference_folder"])
    client = _open_client(config)
    experiment, runs = _finished_runs(config, client)
    _require_runs(config, experiment, runs)
    run = runs[0]
    # Archive first, then write. If the write fails, the archived run goes back to latest-run/,
    # so a failed export never loses a run or leaves latest-run/ empty.
    archived = _archive_latest(folder, run.info.run_id)
    try:
        export_run(config, client, run, folder / "latest-run")
    except Exception:
        if archived is not None:
            _restore_archive(archived, folder / "latest-run")
        raise
    _rebuild_history(folder)
    return folder / "latest-run"


def _known_run_ids(folder: Path) -> set[str]:
    """Run ids already stored under previous-runs."""
    previous = folder / "previous-runs"
    if not previous.is_dir():
        return set()
    found = set()
    for document_path in previous.glob("*/run.json"):
        found.add(json.loads(document_path.read_text(encoding="utf-8"))["run_id"])
    return found


def backfill_runs(config: dict) -> list[str]:
    """Export every older finished run that is not already in previous-runs."""
    folder = resolve_path(config["tracking"]["reference_folder"])
    client = _open_client(config)
    experiment, runs = _finished_runs(config, client)
    _require_runs(config, experiment, runs)
    known = _known_run_ids(folder)
    added = []
    # runs is newest first. Skip that one, and add the older runs from earliest to latest.
    for run in reversed(runs[1:]):
        if run.info.run_id in known:
            continue
        name = _run_folder_name(_iso(run.info.start_time), run.info.run_id)
        destination = folder / "previous-runs" / name
        if destination.exists():
            raise ValueError(f"previous-runs/{name} already exists.")
        export_run(config, client, run, destination)
        added.append(f"previous-runs/{name}")
    _rebuild_history(folder)
    return added


def main() -> None:
    """Print the newest run, or the runs a backfill added."""
    # With no flag, the newest run is exported, as training does. --backfill adds the older runs
    # in the local database that the reference does not have yet, and is safe to run again.
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill", action="store_true")
    args = parser.parse_args()
    try:
        config = load_config()
        if args.backfill:
            added = backfill_runs(config)
            for name in added:
                print(f"added: {name}")
            folder = resolve_path(config["tracking"]["reference_folder"])
            count = len(json.loads((folder / "run-history.json").read_text(encoding="utf-8")))
            print(f"history: {count} runs")
            return
        saved = export_latest_run(config)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    document = json.loads((saved / "run.json").read_text(encoding="utf-8"))
    params = json.loads((saved / "params.json").read_text(encoding="utf-8"))
    metrics = json.loads((saved / "metrics.json").read_text(encoding="utf-8"))
    print(f"run: {document['run_name']} ({document['run_id']})")
    print(f"params: {len(params)}, metrics: {len(metrics)}")
    print(f"saved: {config['tracking']['reference_folder']}/latest-run")


if __name__ == "__main__":
    main()
