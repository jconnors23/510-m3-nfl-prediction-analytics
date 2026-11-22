"""Write the 2026 schedule and the standings before each week, for the frontend to read.

The schedule comes from the raw file and the scores come from the downloaded table. The
browser subtracts one team's stored numbers from the other's and sends the result to the API,
so no number is rounded here. Rounding would make the request differ from the model's inputs.
"""

import json
import os
from pathlib import Path

import pandas as pd

from src.config import load_config, resolve_path, season_window
from src.model.features import load_games, standings_before_week
from src.profiles import TEAM_NAMES


def load_schedule(config: dict) -> pd.DataFrame:
    """Read the 2026 regular-season rows from the raw nflverse file."""
    raw_setting = config["data"]["raw_path"]
    path = resolve_path(raw_setting)
    # The cleaned table has no dates or kickoff times, and it drops unplayed games and ties.
    # The page needs all of those, so the schedule has to come from the raw file.
    if not path.is_file():
        raise ValueError(f"No raw file at {raw_setting}. Run python -m src.data.fetch_raw first.")
    _start_season, end_season, _last_week = season_window(config)
    raw = pd.read_csv(path)
    schedule = raw.loc[(raw["season"] == end_season) & (raw["game_type"] == "REG"), [
        "game_id",
        "week",
        "gameday",
        "weekday",
        "gametime",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "location",
    ]].copy()
    schedule["week"] = schedule["week"].astype(int)
    # Kickoff order, then game id, so the page lists a week's games the same way every time.
    return schedule.sort_values(["week", "gameday", "gametime", "game_id"]).reset_index(drop=True)


def _ids(game_ids: list[str]) -> str:
    """The first five game ids, which is enough to find the failing rows."""
    return ", ".join(game_ids[:5])


def check_schedule(schedule: pd.DataFrame, games: pd.DataFrame, season: int, last_week: int) -> None:
    """Stop when the raw schedule and the downloaded scores do not match."""
    # The page shows a date, a weekday, and a kickoff time for every game, so a blank one would
    # show an empty cell.
    blank = schedule.loc[
        schedule[["gameday", "weekday", "gametime"]].isna().any(axis=1), "game_id"
    ].tolist()
    if blank:
        raise ValueError(f"A game is missing its date, day, or kickoff time: {_ids(blank)}.")
    has_home = schedule["home_score"].notna()
    has_away = schedule["away_score"].notna()
    in_window = schedule["week"] <= last_week
    # Weeks up to last_week are counted, so every game in them needs both scores. A later game
    # with a score means the raw file moved on and the downloaded table and config are behind it.
    missing_score = schedule.loc[in_window & ~(has_home & has_away), "game_id"].tolist()
    if missing_score:
        raise ValueError(f"A counted week is missing a score: {_ids(missing_score)}.")
    late_score = schedule.loc[~in_window & (has_home | has_away), "game_id"].tolist()
    if late_score:
        raise ValueError(f"A game after week {last_week} already has a score: {_ids(late_score)}.")
    season_games = games.loc[games["season"] == season].set_index("game_id")
    # Cleaning removes ties because a tie has no winner to learn from, so a tie is in the raw
    # schedule but not in the downloaded table. Leave ties out of this comparison.
    finished = schedule.loc[has_home & has_away & (schedule["home_score"] != schedule["away_score"])]
    # Every finished game must be in the table with the same teams and scores, so the standings
    # built from the table describe the games the page shows.
    mismatched = []
    for game in finished.itertuples(index=False):
        if game.game_id not in season_games.index:
            mismatched.append(game.game_id)
            continue
        row = season_games.loc[game.game_id]
        same = (
            row["home_team"] == game.home_team
            and row["away_team"] == game.away_team
            and int(row["home_score"]) == int(game.home_score)
            and int(row["away_score"]) == int(game.away_score)
        )
        if not same:
            mismatched.append(game.game_id)
    if mismatched:
        raise ValueError(f"A finished game does not match the downloaded table: {_ids(mismatched)}.")
    # The other direction: a game in the table that the schedule lacks would count in the
    # standings but never appear on the page.
    missing_from_schedule = [game_id for game_id in season_games.index if game_id not in set(schedule["game_id"])]
    if missing_from_schedule:
        raise ValueError(f"A downloaded game is missing from the schedule: {_ids(missing_from_schedule)}.")
    # The page shows a team name for each code, so a code missing from TEAM_NAMES would show blank.
    unknown = schedule.loc[
        ~schedule["home_team"].isin(TEAM_NAMES) | ~schedule["away_team"].isin(TEAM_NAMES), "game_id"
    ].tolist()
    if unknown:
        raise ValueError(f"A game uses a team code with no name: {_ids(unknown)}.")


def _whole(value: object) -> int | None:
    """A score as a whole number, or nothing when the game has not been played."""
    if pd.isna(value):
        return None
    return int(value)


def build_season(config: dict) -> dict:
    """Build the season document from the raw schedule and the downloaded scores."""
    _start_season, season, last_week = season_window(config)
    schedule = load_schedule(config)
    games = load_games(config)
    check_schedule(schedule, games, season, last_week)
    teams = sorted(TEAM_NAMES)
    standings = []
    # One standings table for each week from 1 to last_week + 1. Week 1 has no earlier games, so
    # every team has 0.5 for win_pct and 0.0 for point_diff_per_game, matching what the model
    # saw for week 1 in training. The last table, before week last_week + 1, holds the
    # standings after the last scored week, which is the latest that exists.
    for before_week in range(1, last_week + 2):
        rows = standings_before_week(games, season, before_week, teams)
        standings.append(
            {
                "before_week": before_week,
                "teams": [
                    {
                        "team": row.team,
                        "games": int(row.games),
                        "wins": int(row.wins),
                        "win_pct": float(row.win_pct),
                        "point_diff_per_game": float(row.point_diff_per_game),
                    }
                    for row in rows.itertuples(index=False)
                ],
            }
        )
    # Look up a team's row by week and code, for the totals check below.
    by_week = {entry["before_week"]: {row["team"]: row for row in entry["teams"]} for entry in standings}
    weeks = []
    for week_number, week_games in schedule.groupby("week", sort=True):
        game_rows = []
        for game in week_games.itertuples(index=False):
            home_score = _whole(game.home_score)
            away_score = _whole(game.away_score)
            # A tie is a played game with equal scores. It is in the schedule but not in the
            # standings, because the downloaded table has no ties.
            if home_score is None or away_score is None:
                status = "upcoming"
            elif home_score == away_score:
                status = "tie"
            else:
                status = "final"
            game_rows.append(
                {
                    "game_id": game.game_id,
                    "gameday": str(game.gameday),
                    "weekday": str(game.weekday),
                    "gametime": str(game.gametime),
                    "home": game.home_team,
                    "away": game.away_team,
                    "neutral_site": game.location == "Neutral",
                    "status": status,
                    "home_score": home_score,
                    "away_score": away_score,
                }
            )
        days = [row["gameday"] for row in game_rows]
        weeks.append(
            {
                "week": int(week_number),
                "first_day": min(days),
                "last_day": max(days),
                "status": "final" if all(row["home_score"] is not None for row in game_rows) else "upcoming",
                # Games after week last_week have no score, so the newest standings are the ones
                # before week last_week + 1. Weeks 12 to 18 reuse the standings before week 11
                # because no table exists for them.
                "standings_before_week": min(int(week_number), last_week + 1),
                "games": game_rows,
            }
        )
    counted = games.loc[(games["season"] == season) & (games["week"] <= last_week)]
    latest = by_week[last_week + 1]
    team_totals = []
    # The team totals add up the downloaded games directly, not through standings_before_week.
    # Both routes must give the same win_pct and point_diff_per_game for every team, so a
    # difference means one of them counted the wrong games.
    for team in teams:
        home = counted.loc[counted["home_team"] == team]
        away = counted.loc[counted["away_team"] == team]
        played = len(home) + len(away)
        wins = int((home["home_score"] > home["away_score"]).sum()) + int(
            (away["away_score"] > away["home_score"]).sum()
        )
        points_for = int(home["home_score"].sum() + away["away_score"].sum())
        points_against = int(home["away_score"].sum() + away["home_score"].sum())
        # Same rule as standings_before_week: a team with no games counts as 0.5 and 0.0, so the
        # percentage is never a division by zero.
        if played == 0:
            win_pct = 0.5
            margin = 0.0
        else:
            win_pct = wins / played
            margin = (points_for - points_against) / played
        standing = latest[team]
        # The comparison is exact, with no tolerance, because both sides do the same division on the
        # same whole numbers.
        if win_pct != standing["win_pct"] or margin != standing["point_diff_per_game"]:
            raise ValueError(f"{team} totals do not match the standings before week {last_week + 1}.")
        team_totals.append(
            {
                "team": team,
                "games": played,
                "wins": wins,
                "losses": played - wins,
                "points_for": points_for,
                "points_against": points_against,
                "point_diff": points_for - points_against,
                "win_pct": float(win_pct),
                "point_diff_per_game": float(margin),
            }
        )
    return {
        "season": int(season),
        "through_week": int(last_week),
        "weeks": weeks,
        "standings": standings,
        "team_totals": team_totals,
    }


def season_text(document: dict) -> str:
    """The document as text, with one trailing newline and no non-finite numbers."""
    # allow_nan=False makes a NaN or infinity raise an error, because the browser cannot parse
    # either one from JSON.
    return json.dumps(document, indent=2, allow_nan=False) + "\n"


def write_season(config: dict, document: dict) -> Path:
    """Write the season file, swapping it in only after the text is complete."""
    output = resolve_path(config["frontend"]["season_path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    # A failed write must not replace a good file with a half-written one.
    partial = output.with_name(output.name + ".partial")
    try:
        partial.write_text(season_text(document), encoding="utf-8")
        os.replace(partial, output)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return output


def main() -> None:
    """Build the season file and print the counts a developer can check."""
    try:
        config = load_config()
        document = build_season(config)
        write_season(config, document)
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from None
    games = [game for week in document["weeks"] for game in week["games"]]
    played = sum(1 for game in games if game["status"] != "upcoming")
    print(f"games: {len(games)} ({played} final or tie, {len(games) - played} upcoming)")
    print(f"weeks: {len(document['weeks'])}, standings through {document['season']} week {document['through_week']}")
    print(f"saved: {config['frontend']['season_path']}")


if __name__ == "__main__":
    main()
