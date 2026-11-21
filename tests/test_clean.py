"""Tests for the cleaning step (src/data/clean.py).

They use a few made-up games, so nothing is downloaded and no real data file is read.
"""

import pandas as pd

from src.data.clean import clean_games


def test_drops_tie_playoff_and_out_of_window_season():
    """Cleaning removes a tie, a playoff game, and a pre-window season, and keeps the rest.

    Covers cleaning rules 1, 2, and 4, the 7 saved columns, and whole-number scores.
    """
    # Four made-up games. Only the first one ("kept") should survive cleaning, and each of
    # the other three breaks exactly one rule, so a failure points at the rule that broke.
    raw = pd.DataFrame(
        [
            {
                # A normal regular-season game inside the window: this is the one we keep.
                "game_id": "kept",
                "season": 2022,
                "game_type": "REG",
                "week": 1,
                "home_team": "KC",
                "away_team": "CLE",
                "home_score": 20,
                "away_score": 17,
            },
            {
                # Equal scores: a tie has no winner, so it must be removed.
                "game_id": "tie",
                "season": 2022,
                "game_type": "REG",
                "week": 2,
                "home_team": "BAL",
                "away_team": "MIA",
                "home_score": 21,
                "away_score": 21,
            },
            {
                # A playoff game ("WC" is the wild-card round). Only regular-season games are used.
                "game_id": "playoff",
                "season": 2022,
                "game_type": "WC",
                "week": 19,
                "home_team": "KC",
                "away_team": "JAX",
                "home_score": 27,
                "away_score": 20,
            },
            {
                # A season before the window starts (the window starts in 2020).
                "game_id": "old",
                "season": 2019,
                "game_type": "REG",
                "week": 1,
                "home_team": "GB",
                "away_team": "CHI",
                "home_score": 10,
                "away_score": 3,
            },
        ]
    )

    cleaned, counts = clean_games(raw, start_season=2020, end_season=2026, test_through_week=10)

    # Only the normal game is left.
    assert cleaned["game_id"].tolist() == ["kept"]
    # The saved table has exactly the 7 kept columns, in this order. Anything else
    # (such as the game_type column used for filtering) must have been dropped.
    assert list(cleaned.columns) == [
        "game_id",
        "season",
        "week",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
    ]
    # The counts show where each game left the table, in the order the rules run.
    assert counts["raw"] == 4
    assert counts["regular_season"] == 3  # the playoff game is gone
    assert counts["in_window"] == 2  # the 2019 game is gone
    assert counts["through_completed_weeks"] == 2  # no 2026 games here, so nothing is cut by week
    assert counts["no_ties"] == 1  # the tie is gone
    # "i" means a whole-number column. Scores must not be left as decimals like 20.0.
    assert cleaned["home_score"].dtype.kind == "i"
    assert cleaned["away_score"].dtype.kind == "i"


def test_week_cut_drops_unplayed_games_and_ties():
    """Unplayed weeks of the last season are cut without stopping the step, and ties still go.

    Covers cleaning rule 3. The week cut must run before the blank-score check, because
    unplayed games have blank scores. If the order were swapped, this test would raise an error.
    """
    # Three made-up 2026 games (2026 is the last season in the window, so the week cap applies):
    # a game played in week 10, a game not yet played in week 11, and a tie in week 5.
    raw = pd.DataFrame(
        [
            {
                # Inside the allowed weeks and decided: this is the one we keep.
                "game_id": "played",
                "season": 2026,
                "game_type": "REG",
                "week": 10,
                "home_team": "KC",
                "away_team": "BUF",
                "home_score": 24,
                "away_score": 17,
            },
            {
                # Blank scores because the game has not happened. The week cut must remove it
                # before the blank-score check, or cleaning would stop with an error.
                "game_id": "unplayed",
                "season": 2026,
                "game_type": "REG",
                "week": 11,
                "home_team": "DAL",
                "away_team": "PHI",
                "home_score": None,
                "away_score": None,
            },
            {
                # Inside the allowed weeks, but a tie, so it is removed by the tie rule instead.
                "game_id": "test-tie",
                "season": 2026,
                "game_type": "REG",
                "week": 5,
                "home_team": "GB",
                "away_team": "CHI",
                "home_score": 14,
                "away_score": 14,
            },
        ]
    )

    cleaned, counts = clean_games(raw, start_season=2020, end_season=2026, test_through_week=10)

    assert cleaned["game_id"].tolist() == ["played"]
    assert counts["in_window"] == 3  # all three are regular-season games in the window
    # Week 11 is gone after the week cut, leaving the played game and the tie.
    assert counts["through_completed_weeks"] == 2
    # The tie is gone after the tie rule, leaving only the played game.
    assert counts["no_ties"] == 1
