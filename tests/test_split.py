"""Tests for the season split.

The rows and settings are made up and held in memory, except the one test that reads
config/config.yaml. Nothing calls AWS or the network, and no file is written.
"""

import pandas as pd
import pytest

from src.config import load_config, split_seasons
from src.model.features import split_games


def _settings() -> dict:
    """A four-season window: train 2022-2023, validate 2024, test 2025."""
    # Only the keys that split_seasons reads. The test season is the window's last season.
    return {
        "window": {"start_season": 2022, "end_season": 2025, "test_through_week": 10},
        "split": {"train_end_season": 2023, "validation_season": 2024},
    }


def _table() -> pd.DataFrame:
    """One game in each season the settings cover."""
    return pd.DataFrame(
        {
            "game_id": ["s2022", "s2023", "s2024", "s2025"],
            "season": [2022, 2023, 2024, 2025],
        }
    )


def test_rows_go_to_the_season_group():
    """2022 and 2023 train, 2024 validates, and 2025 is test."""
    groups = split_games(_table(), _settings())
    # Training takes every season from the first one to the last training season, inclusive.
    assert set(groups["training"]["season"]) == {2022, 2023}
    assert set(groups["validation"]["season"]) == {2024}
    assert set(groups["test"]["season"]) == {2025}


def test_every_game_is_in_one_group():
    """The three groups cover the table once, with no game id repeated."""
    table = _table()
    groups = split_games(table, _settings())
    game_ids = []
    for group in groups.values():
        game_ids.extend(group["game_id"])
    # Nothing lost: the groups together hold as many games as the table.
    assert len(game_ids) == len(table)
    # Nothing repeated: no game id appears in two groups.
    assert len(game_ids) == len(set(game_ids))


def test_empty_validation_group_names_validation():
    """Dropping the validation season makes the error name that group."""
    table = _table().loc[_table()["season"] != 2024]
    # The error message must say which group is empty, so the fix is obvious.
    with pytest.raises(ValueError, match="validation"):
        split_games(table, _settings())


def test_validation_must_follow_the_last_training_season():
    """A validation season that is not after the last training season is rejected."""
    settings = _settings()
    settings["split"]["train_end_season"] = 2024
    settings["split"]["validation_season"] = 2024
    # Training would include the validation season, so the model would be scored on games it learned from.
    with pytest.raises(ValueError):
        split_seasons(settings)


def test_real_settings_return_the_four_seasons():
    """The settings file yields training 2020-2024, validation 2025, and test 2026."""
    # This is the only test that reads the real config/config.yaml. It fails if the split
    # changes there, so the change has to be made on purpose along with the docs.
    assert split_seasons(load_config()) == (2020, 2024, 2025, 2026)
