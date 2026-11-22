"""Tests for the team profiles file the frontend reads."""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.config import load_config
from src.config import resolve_path
from src.profiles import TEAM_NAMES, build_profiles, write_profiles

GAMES = Path(__file__).resolve().parents[1] / "data" / "from-s3" / "nfl_matchups_2020_2026.csv"
PROFILES = Path(__file__).resolve().parents[1] / "frontend" / "src" / "data" / "team-profiles.json"
needs_games = pytest.mark.skipif(not GAMES.is_file(), reason="the downloaded games table is not on disk")


def _team_counts(games: pd.DataFrame, team: str) -> tuple[int, int, int, int]:
    """Games, wins, points scored, and points allowed for one team, as whole numbers."""
    home = games.loc[games["home_team"] == team]
    away = games.loc[games["away_team"] == team]
    played = len(home) + len(away)
    wins = int((home["home_score"] > home["away_score"]).sum()) + int(
        (away["away_score"] > away["home_score"]).sum()
    )
    scored = int(home["home_score"].sum() + away["away_score"].sum())
    allowed = int(home["away_score"].sum() + away["home_score"].sum())
    return played, wins, scored, allowed


@needs_games
def test_team_names_match_the_teams_in_the_data():
    """The name list is exactly the 32 team codes in the downloaded table."""
    games = pd.read_csv(GAMES)
    codes = set(games["home_team"]) | set(games["away_team"])
    assert set(TEAM_NAMES) == codes
    assert len(TEAM_NAMES) == 32


@needs_games
def test_profiles_equal_the_standings_before_week_11():
    """Each profile equals a direct count of 2026 games through week 10."""
    games = pd.read_csv(GAMES)
    counted = games.loc[(games["season"] == 2026) & (games["week"] <= 10)]
    document = build_profiles(load_config())
    for team in document["teams"]:
        played, wins, scored, allowed = _team_counts(counted, team["team"])
        assert team["games"] == played
        assert team["wins"] == wins
        assert team["win_pct"] == wins / played
        assert team["point_diff_per_game"] == (scored - allowed) / played


@needs_games
def test_file_layout_and_key_order():
    """The document keys stay in the order the frontend reads."""
    document = build_profiles(load_config())
    assert list(document) == ["as_of", "model", "teams"]
    assert list(document["as_of"]) == ["season", "through_week"]
    assert list(document["model"]) == [
        "version",
        "validation_games",
        "validation_correct",
        "validation_accuracy",
        "validation_baseline",
    ]
    assert document["as_of"] == {"season": 2026, "through_week": 10}
    abbreviations = [team["team"] for team in document["teams"]]
    assert abbreviations == sorted(abbreviations)
    assert len(abbreviations) == 32
    assert len(set(abbreviations)) == 32
    for team in document["teams"]:
        assert list(team) == ["team", "name", "games", "wins", "win_pct", "point_diff_per_game"]


def test_model_block_comes_from_the_run_summary():
    """The model block is the run summary's validation scores, unrounded."""
    config = load_config()
    summary = json.loads(resolve_path(config["tracking"]["summary_path"]).read_text(encoding="utf-8"))
    validation = summary["scores"]["validation"]
    document = build_profiles(config)
    assert document["model"] == {
        "version": summary["model_version"],
        "validation_games": validation["games"],
        "validation_correct": validation["correct"],
        "validation_accuracy": validation["accuracy"],
        "validation_baseline": validation["baseline"],
    }


@needs_games
def test_no_blank_or_non_finite_value():
    """Every number is finite, and the win count fits inside the games played."""
    import math

    document = build_profiles(load_config())
    for team in document["teams"]:
        assert math.isfinite(team["games"])
        assert math.isfinite(team["wins"])
        assert math.isfinite(team["win_pct"])
        assert math.isfinite(team["point_diff_per_game"])
        assert team["games"] >= 1
        assert 0 <= team["wins"] <= team["games"]


@needs_games
def test_the_same_input_writes_the_same_bytes(tmp_path):
    """Writing the file twice produces the same text as the committed profiles file."""
    config = load_config()
    config["frontend"] = {"profiles_path": str(tmp_path / "team-profiles.json")}
    document = build_profiles(config)
    first = write_profiles(config, document).read_text(encoding="utf-8")
    second = write_profiles(config, document).read_text(encoding="utf-8")
    assert first == second
    assert first.endswith("\n")
    assert not first.endswith("\n\n")
    assert first == PROFILES.read_text(encoding="utf-8")


def test_missing_table_stops_with_a_clear_message(tmp_path):
    """A missing games table stops with the path that was configured."""
    config = load_config()
    config["data"]["from_s3_path"] = str(tmp_path / "missing.csv")
    with pytest.raises(ValueError, match="No downloaded table at"):
        build_profiles(config)


def test_failed_write_keeps_the_old_file(tmp_path, monkeypatch):
    """A failed swap leaves the previous file and removes the partial file."""
    destination = tmp_path / "team-profiles.json"
    destination.write_text("old\n", encoding="utf-8")
    config = load_config()
    config["frontend"] = {"profiles_path": str(destination)}

    def fail_replace(_source, _destination):
        """Stand in for a swap that the operating system refuses."""
        raise OSError("replace failed")

    # write_profiles looks up os.replace when it runs, so the stand-in has to sit on that module.
    monkeypatch.setattr("src.profiles.os.replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        write_profiles(config, {"as_of": {"season": 2026, "through_week": 10}})
    assert destination.read_text(encoding="utf-8") == "old\n"
    assert not destination.with_name(destination.name + ".partial").exists()
