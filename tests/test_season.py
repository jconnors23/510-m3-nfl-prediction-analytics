"""Tests for the 2026 season file the frontend reads.

Five tests build the season from the raw schedule and the downloaded games table on disk, and
they are skipped when either file is missing. The two check_schedule tests use tiny made-up
tables in memory, and the missing-file test uses made-up settings. Nothing calls AWS or the
network, and no test writes a file.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.config import load_config
from src.model.features import build_model_table, load_games
from src.season import build_season, check_schedule, load_schedule, season_text

GAMES = Path(__file__).resolve().parents[1] / "data" / "from-s3" / "nfl_matchups_2020_2026.csv"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "games.csv"
SEASON_FILE = Path(__file__).resolve().parents[1] / "frontend" / "src" / "data" / "season-2026.json"
PROFILES = Path(__file__).resolve().parents[1] / "frontend" / "src" / "data" / "team-profiles.json"
# Both source files are committed, so these tests run on a fresh checkout. They are skipped only
# if one of them has been deleted.
needs_files = pytest.mark.skipif(
    not GAMES.is_file() or not RAW.is_file(),
    reason="the downloaded table or the raw schedule is not on disk",
)

# Games in each of the 18 weeks of the 2026 schedule, counted from the raw file. They add up to 272.
WEEK_COUNTS = [16, 16, 16, 16, 15, 14, 14, 14, 15, 14, 13, 16, 14, 15, 16, 16, 16, 16]


def _document() -> dict:
    """The season document built from the real files."""
    return build_season(load_config())


@needs_files
def test_schedule_counts_match_the_raw_file():
    """272 games, the weekly counts, nine neutral sites, and one tie."""
    document = _document()
    games = [game for week in document["weeks"] for game in week["games"]]
    played = [game for game in games if game["status"] != "upcoming"]
    ties = [game for game in games if game["status"] == "tie"]
    # 150 games are played through week 10 (149 with a winner and 1 tie). The other 122 are upcoming.
    assert len(games) == 272
    assert len(played) == 150
    assert len(games) - len(played) == 122
    assert [len(week["games"]) for week in document["weeks"]] == WEEK_COUNTS
    assert sum(1 for game in games if game["neutral_site"]) == 9
    assert [game["game_id"] for game in ties] == ["2026_05_NYG_WAS"]


@needs_files
def test_inputs_equal_the_model_table_for_every_finished_game():
    """Each finished 2026 game uses the same two differences as the model table."""
    document = _document()
    table = build_model_table(load_games(load_config()))
    finished = table.loc[table["season"] == 2026]
    # 149, not 150: the model table has no tie, and the schedule has one tie (see the test above).
    assert len(finished) == 149
    for game in finished.itertuples(index=False):
        standing = document["standings"][game.week - 1]
        assert standing["before_week"] == game.week
        rows = {row["team"]: row for row in standing["teams"]}
        home = rows[game.home_team]
        away = rows[game.away_team]
        # Exact equality on purpose. The browser subtracts these same numbers, so Python and the
        # browser must produce identical floating-point values, not just close ones.
        assert home["win_pct"] - away["win_pct"] == game.win_pct_differential
        assert home["point_diff_per_game"] - away["point_diff_per_game"] == game.point_diff_per_game_differential


@needs_files
def test_week_11_standings_equal_the_profiles_file():
    """Standings before week 11 are the same numbers the profiles file ships."""
    document = _document()
    profiles = json.loads(PROFILES.read_text(encoding="utf-8"))
    # Week 11 is the first week with no results, so its standings are the final ones the profiles use.
    before_11 = next(entry for entry in document["standings"] if entry["before_week"] == 11)
    profile_rows = {row["team"]: row for row in profiles["teams"]}
    assert [row["team"] for row in before_11["teams"]] == [row["team"] for row in profiles["teams"]]
    # Every field is compared exactly, because the two files are written by different code paths
    # and the page shows both.
    for row in before_11["teams"]:
        profile = profile_rows[row["team"]]
        assert row["games"] == profile["games"]
        assert row["wins"] == profile["wins"]
        assert row["win_pct"] == profile["win_pct"]
        assert row["point_diff_per_game"] == profile["point_diff_per_game"]


@needs_files
def test_upcoming_weeks_use_the_week_11_standings():
    """Weeks 12 to 18 reuse week 11, and week 1 starts every team at 0.5 and 0."""
    document = _document()
    # Games in weeks 12 to 18 have no results to count yet, so they reuse the standings before week 11.
    for week in document["weeks"]:
        if week["week"] <= 10:
            assert week["standings_before_week"] == week["week"]
        else:
            assert week["standings_before_week"] == 11
    week_one = next(entry for entry in document["standings"] if entry["before_week"] == 1)
    # Before week 1 no team has played, so every team counts as 0.5 and 0, as in the model table.
    assert all(
        row["games"] == 0 and row["wins"] == 0 and row["win_pct"] == 0.5 and row["point_diff_per_game"] == 0.0
        for row in week_one["teams"]
    )


@needs_files
def test_the_same_input_writes_the_same_bytes():
    """Two builds match each other and the committed season file."""
    config = load_config()
    first = season_text(build_season(config))
    second = season_text(build_season(config))
    assert first == second
    # Exactly one newline at the end, so editors and diffs show no stray blank line.
    assert first.endswith("\n")
    assert not first.endswith("\n\n")
    # The committed file must be what the current code and data produce, so it cannot go stale.
    assert first == SEASON_FILE.read_text(encoding="utf-8")


def test_a_score_that_differs_from_the_downloaded_table_stops():
    """A schedule score that differs from the downloaded table's score for the same game names that game."""
    # One game in each table. The home score is 20 in the schedule and 13 in the games table.
    schedule = pd.DataFrame(
        [
            {
                "game_id": "2026_01_NE_SEA",
                "week": 1,
                "gameday": "2026-09-09",
                "weekday": "Wednesday",
                "gametime": "20:20",
                "home_team": "SEA",
                "away_team": "NE",
                "home_score": 20,
                "away_score": 10,
                "location": "Home",
            }
        ]
    )
    games = pd.DataFrame(
        [
            {
                "game_id": "2026_01_NE_SEA",
                "season": 2026,
                "week": 1,
                "home_team": "SEA",
                "away_team": "NE",
                "home_score": 13,
                "away_score": 10,
            }
        ]
    )
    with pytest.raises(ValueError, match="2026_01_NE_SEA"):
        check_schedule(schedule, games, 2026, 1)


def test_an_upcoming_game_with_a_score_stops():
    """A score after the last counted week names that game."""
    # A week 12 game that already has a score, while only weeks through 10 are counted.
    schedule = pd.DataFrame(
        [
            {
                "game_id": "2026_12_NE_SEA",
                "week": 12,
                "gameday": "2026-11-29",
                "weekday": "Sunday",
                "gametime": "13:00",
                "home_team": "SEA",
                "away_team": "NE",
                "home_score": 1,
                "away_score": 0,
                "location": "Home",
            }
        ]
    )
    # An empty games table with the right columns, because no counted game matches this schedule row.
    games = pd.DataFrame(columns=["game_id", "season", "week", "home_team", "away_team", "home_score", "away_score"])
    with pytest.raises(ValueError, match="2026_12_NE_SEA"):
        check_schedule(schedule, games, 2026, 10)


def test_missing_raw_file_stops_with_a_clear_message():
    """A missing raw file says where it was expected."""
    # Only the settings load_schedule reads, with a raw path that does not exist.
    config = {
        "data": {"raw_path": "data/raw/missing-games.csv"},
        "window": {"start_season": 2020, "end_season": 2026, "test_through_week": 10},
    }
    with pytest.raises(ValueError, match="No raw file at"):
        load_schedule(config)
