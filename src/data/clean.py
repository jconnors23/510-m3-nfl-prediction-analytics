"""Step 2: keep regular-season games in the season window that have a winner.

Cleaning only removes rows and columns. It never edits a value. It reads the saved raw
file, so the same raw file always gives the same cleaned table.
"""

import pandas as pd

from src.config import data_file, load_config, season_window

# The only columns that are saved. The raw file has 46. The rest (venue, betting lines,
# people, and ids from other data sources) are not used by this project.
KEPT_COLUMNS = [
    "game_id",
    "season",
    "week",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
]


def clean_games(
    raw: pd.DataFrame,
    start_season: int,
    end_season: int,
    test_through_week: int,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Apply the cleaning rules in order.

    Returns the cleaned table and a dictionary with the row count after each rule, so the
    printout shows where games were removed.
    """
    counts = {"raw": len(raw)}

    # Rule 1: regular season only. Playoff games are played under different conditions, and
    # they give some teams extra games, so they stay out of every team's record.
    # .copy() gives us our own table, so later edits cannot touch the raw one.
    regular = raw.loc[raw["game_type"] == "REG"].copy()
    counts["regular_season"] = len(regular)

    # Rule 2: keep only the seasons in the project window (2020 through 2026).
    window = regular.loc[regular["season"].between(start_season, end_season)].copy()
    counts["in_window"] = len(window)

    # Rule 3: cut the unplayed weeks of the last season.
    # Unplayed weeks of the last season have blank scores. Drop them before the
    # blank-score check, or that check would stop the step on games that have not been played.
    later = (window["season"] == end_season) & (window["week"] > test_through_week)
    window = window.loc[~later].copy()
    counts["through_completed_weeks"] = len(window)

    # Every game left should have both scores and both teams. A blank here is a real problem
    # in the source file, so stop and name the first few games instead of guessing a value.
    missing = _missing_score_or_team(window)
    if missing.any():
        sample = ", ".join(window.loc[missing, "game_id"].astype(str).head(5))
        raise ValueError(
            f"{int(missing.sum())} games in the window have a blank score or team"
            f" (first ids: {sample})"
        )

    # Rule 4: remove tied games. A tie has no winner, so it cannot be labeled a home win or an away win.
    decided = window.loc[window["home_score"] != window["away_score"]].copy()
    counts["no_ties"] = len(decided)

    cleaned = decided.loc[:, KEPT_COLUMNS].copy()
    # The raw file stores these as decimals (20.0) because blank scores exist in it. After
    # the checks above none are blank, so whole numbers are the correct type.
    for column in ("season", "week", "home_score", "away_score"):
        cleaned[column] = cleaned[column].astype(int)
    # A fixed order makes the saved file identical every time the same data is cleaned.
    cleaned = cleaned.sort_values(["season", "week", "game_id"]).reset_index(drop=True)
    return cleaned, counts


def require_current_teams(cleaned: pd.DataFrame) -> None:
    """Stop unless exactly 32 team codes appear in the cleaned table."""
    codes = set(cleaned["home_team"]) | set(cleaned["away_team"])
    # Another count would mean a team code changed in the source file or the window moved
    # into seasons with a different set of teams.
    if len(codes) != 32:
        raise ValueError(f"Expected 32 team codes, found {len(codes)}: {sorted(codes)}")


def _missing_score_or_team(window: pd.DataFrame) -> pd.Series:
    """True for each game that has a blank score or a blank team code."""
    missing_score = window["home_score"].isna() | window["away_score"].isna()
    missing_team = window["home_team"].isna() | window["away_team"].isna()
    return missing_score | missing_team


def format_counts(counts: dict[str, int]) -> str:
    """Build the small row-count table printed at the end of a run."""
    # Each pair is (key in `counts`, label shown on screen), in the order the rules run.
    rows = [
        ("raw", "raw"),
        ("regular_season", "regular season"),
        ("in_window", "seasons in window"),
        ("through_completed_weeks", "through completed weeks"),
        ("no_ties", "after removing ties"),
    ]
    lines = [f"{'stage':<24} rows"]
    for key, label in rows:
        lines.append(f"{label:<24} {counts[key]}")
    return "\n".join(lines)


def main() -> None:
    """Command for Step 2: clean the saved raw file and write the cleaned table."""
    try:
        config = load_config()
        start_season, end_season, test_through_week = season_window(config)
        raw_path = data_file(config, "raw_path")
        # Check the input first so a missing file gives a plain "run the fetch step" message.
        if not raw_path.is_file():
            raise ValueError(f"No raw file at {config['data']['raw_path']}. Run the fetch step first.")
        raw = pd.read_csv(raw_path)
        if raw.empty:
            raise ValueError(f"Raw file at {config['data']['raw_path']} is empty. Run the fetch step first.")
        cleaned, counts = clean_games(raw, start_season, end_season, test_through_week)
        require_current_teams(cleaned)
        dest = data_file(config, "processed_path")
        dest.parent.mkdir(parents=True, exist_ok=True)
        cleaned.to_csv(dest, index=False)
    except (ValueError, FileNotFoundError, pd.errors.EmptyDataError) as exc:
        # Expected problems (bad data, no raw file yet) end with a short message, not a traceback.
        raise SystemExit(str(exc)) from None

    print(format_counts(counts))
    print("rows by season:")
    for season, count in cleaned.groupby("season").size().items():
        print(f"  {int(season)} {int(count)}")
    print(f"saved: {config['data']['processed_path']}")


if __name__ == "__main__":
    main()
