"""Load pipeline settings so the scripts do not hard-code paths or seasons.

Every script reads config/config.yaml through this file. To change a path, a bucket,
or the season window, edit the YAML file and leave the code alone.
"""

from pathlib import Path

import yaml


def project_root() -> Path:
    """The project folder, found from the location of this file."""
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
        int(window["test_through_week"]),
    )


def split_seasons(config: dict) -> tuple[int, int, int, int]:
    """First training season, last training season, validation season, and test season."""
    start_season, test_season, _test_week = season_window(config)
    train_end_season = int(config["split"]["train_end_season"])
    validation_season = int(config["split"]["validation_season"])
    # A later season inside training would let the model learn from games played
    # after the seasons it is scored on.
    if start_season > train_end_season:
        raise ValueError(
            f"first training season {start_season} is after last training season {train_end_season}"
        )
    if train_end_season >= validation_season:
        raise ValueError(
            f"validation season {validation_season} is not after last training season {train_end_season}"
        )
    if validation_season >= test_season:
        raise ValueError(
            f"validation season {validation_season} is not before test season {test_season}"
        )
    return start_season, train_end_season, validation_season, test_season
