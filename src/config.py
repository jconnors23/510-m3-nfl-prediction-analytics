"""Load pipeline settings so the scripts do not hard-code paths or seasons.

Every script reads config/config.yaml through this file. To change a path, a bucket,
or the season window, edit the YAML file and leave the code alone.
"""

from pathlib import Path

import yaml


def project_root() -> Path:
    # This file lives in <project>/src/, so two levels up is the project folder.
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    """Turn a path from the settings file into a full path."""
    candidate = Path(path)
    # Absolute paths let tests point at a temporary file.
    if candidate.is_absolute():
        return candidate
    # Relative paths in config.yaml (such as data/raw/games.csv) are measured from the
    # project folder, so the scripts work no matter which folder they are run from.
    return project_root() / candidate


def load_config() -> dict:
    """Read config/config.yaml and return it as nested dictionaries."""
    config_path = project_root() / "config" / "config.yaml"
    with config_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def data_file(config: dict, key: str) -> Path:
    """Full path of one file listed in the `data` block, such as "raw_path"."""
    return resolve_path(config["data"][key])


def season_window(config: dict) -> tuple[int, int, int]:
    """First season, last season, and the last scored week of that last season."""
    window = config["window"]
    # int() guards against a value written as text in the YAML file.
    return (
        int(window["start_season"]),
        int(window["end_season"]),
        int(window["live_through_week"]),
    )
