"""Build the two pre-game inputs and split the games by season.

A game is described only with earlier weeks of its own season, so its own score is never an input.
"""

import pandas as pd

from src.config import data_file, load_config, split_seasons

# The columns of the model table, in order. The first five only identify the game. The next
# two are the model's inputs, and home_win is the answer the model learns to predict.
MODEL_COLUMNS = [
    "game_id",
    "season",
    "week",
    "home_team",
    "away_team",
    "win_pct_differential",
    "point_diff_per_game_differential",
    "home_win",
]

# The only two columns the model sees. A positive value means the home team looks stronger.
# Training, scoring, and saving all use this one list, so the inputs always stay in this order.
INPUT_COLUMNS = [
    "win_pct_differential",
    "point_diff_per_game_differential",
]


def load_games(config: dict) -> pd.DataFrame:
    """Read the cleaned table that was downloaded from S3."""
    # The model always starts from the S3 copy, never from the local cleaned table, so every
    # run uses the shared version of the data.
    path = data_file(config, "from_s3_path")
    if not path.is_file():
        raise ValueError(
            f"No downloaded table at {config['data']['from_s3_path']}. Run the download step first."
        )
    return pd.read_csv(path)


def standings_before_week(
    games: pd.DataFrame,
    season: int,
    week: int,
    teams: list[str],
) -> pd.DataFrame:
    """One row per team from games played earlier in this season."""
    # Same-week games are left out, so a result cannot describe itself or the other game that week.
    earlier = games.loc[(games["season"] == season) & (games["week"] < week)]
    rows = []
    for team in teams:
        home = earlier.loc[earlier["home_team"] == team]
        away = earlier.loc[earlier["away_team"] == team]
        played = len(home) + len(away)
        # No games yet would make a percentage undefined. 0.5 and 0 leave week 1 as a tie.
        if played == 0:
            wins = 0
            win_pct = 0.5
            margin = 0.0
        else:
            wins = int((home["home_score"] > home["away_score"]).sum()) + int(
                (away["away_score"] > away["home_score"]).sum()
            )
            scored = float(home["home_score"].sum() + away["away_score"].sum())
            allowed = float(home["away_score"].sum() + away["home_score"].sum())
            # Divide by games played, not a season total, because bye weeks leave teams on different game counts.
            win_pct = wins / played
            margin = (scored - allowed) / played
        rows.append(
            {
                "team": team,
                "games": played,
                "wins": wins,
                "win_pct": float(win_pct),
                "point_diff_per_game": float(margin),
            }
        )
    return pd.DataFrame(rows)


def build_model_table(games: pd.DataFrame) -> pd.DataFrame:
    """One row per game, with the two pre-game differentials and the home-win answer."""
    # Every team code that appears, so a team with no games yet still gets a row of standings.
    teams = sorted(set(games["home_team"]) | set(games["away_team"]))
    rows = []
    for (season, week), week_games in games.groupby(["season", "week"], sort=False):
        # Once per week, then reused for every game in that week.
        standings = standings_before_week(games, int(season), int(week), teams).set_index("team")
        for game in week_games.itertuples(index=False):
            home = standings.loc[game.home_team]
            away = standings.loc[game.away_team]
            # Home minus away, so a positive value means the home team looks stronger.
            # home_win is the answer to learn. It is the only value that uses this game's score.
            rows.append(
                {
                    "game_id": game.game_id,
                    "season": int(game.season),
                    "week": int(game.week),
                    "home_team": game.home_team,
                    "away_team": game.away_team,
                    "win_pct_differential": float(home["win_pct"] - away["win_pct"]),
                    "point_diff_per_game_differential": float(
                        home["point_diff_per_game"] - away["point_diff_per_game"]
                    ),
                    "home_win": int(game.home_score > game.away_score),
                }
            )
    table = pd.DataFrame(rows, columns=MODEL_COLUMNS)
    return table.sort_values(["season", "week", "game_id"]).reset_index(drop=True)


def check_model_table(table: pd.DataFrame) -> None:
    """Stop if a model input is blank or a week-1 differential is not zero."""
    # A blank input would make the model fail later, so catch it here with a clear message.
    if table[INPUT_COLUMNS].isna().any().any():
        raise ValueError("a model input is blank")
    # Before week 1 no team has played, so every team counts as 0.5 and 0.0. If a week-1 value
    # is anything else, some number used a game it should not have, which would leak the answer.
    week_one = table.loc[table["week"] == 1, INPUT_COLUMNS]
    if (week_one != 0).any().any():
        raise ValueError("a week-1 differential is not 0")


def split_games(table: pd.DataFrame, config: dict) -> dict[str, pd.DataFrame]:
    """Training, validation, and test tables, one season range each."""
    # Whole seasons go to one group, never single games, so a game is never scored by a model
    # that trained on games played after it.
    start_season, train_end_season, validation_season, test_season = split_seasons(config)
    groups = {
        "training": table.loc[table["season"].between(start_season, train_end_season)].copy(),
        "validation": table.loc[table["season"] == validation_season].copy(),
        "test": table.loc[table["season"] == test_season].copy(),
    }
    for name, group in groups.items():
        if group.empty:
            raise ValueError(f"{name} has no rows")
    game_ids = [set(group["game_id"]) for group in groups.values()]
    combined = set.union(*game_ids)
    # A season that falls in a gap, or a game id that lands in two groups, would make the sizes disagree.
    if sum(len(ids) for ids in game_ids) != len(combined) or len(combined) != len(table):
        raise ValueError("every game must be in exactly one split group")
    return groups


def main() -> None:
    """Command: build the model table, run the checks, split it, and print a summary."""
    try:
        config = load_config()
        games = load_games(config)
        table = build_model_table(games)
        check_model_table(table)
        groups = split_games(table, config)
    except ValueError as exc:
        raise SystemExit(str(exc)) from None

    # The home win share is the score of always picking the home team, the baseline to beat.
    for name in ("training", "validation", "test"):
        group = groups[name]
        share = float(group["home_win"].mean())
        print(f"{name}: {len(group)} rows, home win share {share:.2%}")
    # The smallest and largest value of each input, so an odd range is easy to spot.
    for column in INPUT_COLUMNS:
        print(f"{column}: min {float(table[column].min())}, max {float(table[column].max())}")
    print("week 1 differentials are all 0")


if __name__ == "__main__":
    main()
