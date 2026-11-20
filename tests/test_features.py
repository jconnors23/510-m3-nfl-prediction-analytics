"""Tests for the two pre-game inputs.

The games are made up, so nothing reads the downloaded table.
"""

import pandas as pd
import pytest

from src.model.features import build_model_table, check_model_table

INPUTS = ["win_pct_differential", "point_diff_per_game_differential"]


def _league() -> pd.DataFrame:
    """Four teams in 2024, with the scores the hand checks use."""
    rows = [
        ("w1a", 1, "A", "B", 30, 0),
        ("w1b", 1, "C", "D", 10, 7),
        ("w2a", 2, "A", "C", 14, 10),
        ("w2b", 2, "B", "D", 21, 3),
        ("w3a", 3, "A", "D", 17, 14),
        ("w3b", 3, "C", "B", 28, 7),
    ]
    return pd.DataFrame(
        rows,
        columns=["game_id", "week", "home_team", "away_team", "home_score", "away_score"],
    ).assign(season=2024)


def _with_new_team(league: pd.DataFrame) -> pd.DataFrame:
    """Add a week-3 game for a team that has not played yet."""
    extra = pd.DataFrame(
        [
            {
                "game_id": "w3c",
                "season": 2024,
                "week": 3,
                "home_team": "E",
                "away_team": "A",
                "home_score": 10,
                "away_score": 20,
            }
        ]
    )
    return pd.concat([league, extra], ignore_index=True)


def _row(table: pd.DataFrame, game_id: str) -> pd.Series:
    """The one row of the model table for a game id."""
    return table.loc[table["game_id"] == game_id].iloc[0]


def test_week_1_differentials_are_zero():
    """Week 1 has no earlier games, so both inputs are exactly 0."""
    table = build_model_table(_league())
    week_one = table.loc[table["week"] == 1, INPUTS]
    assert len(week_one) == 2
    assert (week_one == 0).all().all()


def test_hand_checked_week_2_and_week_3_values():
    """Weeks 2 and 3 match the differentials worked out from the week-1 and week-2 scores."""
    table = build_model_table(_league())
    expected = {
        "w2a": (0.0, 27.0, 1),
        "w2b": (0.0, -27.0, 1),
        "w3a": (1.0, 27.5, 1),
        "w3b": (0.0, 5.5, 1),
    }
    for game_id, (win_pct, margin, home_win) in expected.items():
        row = _row(table, game_id)
        assert row["win_pct_differential"] == win_pct
        assert row["point_diff_per_game_differential"] == margin
        assert row["home_win"] == home_win


def test_sign_follows_which_team_is_stronger():
    """A stronger home team gives positive inputs, and a stronger away team gives negative ones."""
    table = build_model_table(_league())
    stronger_home = _row(table, "w3a")
    assert stronger_home["win_pct_differential"] > 0
    assert stronger_home["point_diff_per_game_differential"] > 0

    with_bye = build_model_table(_with_new_team(_league()))
    stronger_away = _row(with_bye, "w3c")
    assert stronger_away["win_pct_differential"] < 0
    assert stronger_away["point_diff_per_game_differential"] < 0


def test_later_scores_do_not_change_earlier_inputs():
    """Changing week 3 scores leaves the inputs for weeks 1 to 3 the same, because those inputs stop at week 2."""
    original = build_model_table(_league())
    changed = _league()
    later = changed["week"] >= 3
    changed.loc[later, "home_score"] = changed.loc[later, "home_score"] + 9
    changed.loc[later, "away_score"] = 0
    rebuilt = build_model_table(changed)

    left = original.set_index("game_id")
    right = rebuilt.set_index("game_id")
    for game_id in left.index:
        assert left.loc[game_id, "win_pct_differential"] == right.loc[game_id, "win_pct_differential"]
        assert (
            left.loc[game_id, "point_diff_per_game_differential"]
            == right.loc[game_id, "point_diff_per_game_differential"]
        )


def test_margin_is_per_game_and_a_new_team_is_even():
    """A team with no games is 0.5 and 0, and a two-game margin is divided by 2 rather than left as a total."""
    table = build_model_table(_with_new_team(_league()))
    row = _row(table, "w3c")
    assert row["win_pct_differential"] == -0.5
    assert row["point_diff_per_game_differential"] == -17.0
    assert row["home_win"] == 0


def test_model_table_columns_and_no_blanks():
    """The model table has the eight columns in order and no blank cell."""
    table = build_model_table(_league())
    assert list(table.columns) == [
        "game_id",
        "season",
        "week",
        "home_team",
        "away_team",
        "win_pct_differential",
        "point_diff_per_game_differential",
        "home_win",
    ]
    assert not table.isna().any().any()


def test_check_rejects_a_nonzero_week_1_differential():
    """The check stops when a week-1 input is no longer exactly 0."""
    table = build_model_table(_league())
    table.loc[table["week"] == 1, "win_pct_differential"] = 1.0
    with pytest.raises(ValueError):
        check_model_table(table)
