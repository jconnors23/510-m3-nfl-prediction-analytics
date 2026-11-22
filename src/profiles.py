"""Write each team's standing after the last counted week, for the frontend to read.

The browser subtracts one team's numbers from the other's, so the values in the file stay
unrounded. Rounding here would make the request sent to the API differ from the model.
"""

import json
import os
from pathlib import Path

from src.config import load_config, resolve_path, season_window
from src.model.features import load_games, standings_before_week

# The 32 abbreviations in the downloaded table, with the name a visitor reads.
TEAM_NAMES = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB": "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs",
    "LA": "Los Angeles Rams",
    "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE": "New England Patriots",
    "NO": "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",
}


def build_profiles(config: dict) -> dict:
    """Build the profiles document from the downloaded games and the run summary."""
    games = load_games(config)
    teams = sorted(set(games["home_team"]) | set(games["away_team"]))
    # A code with no name, or a name with no code, would show the wrong label on the page.
    if set(teams) != set(TEAM_NAMES):
        missing = sorted(set(teams) - set(TEAM_NAMES))
        extra = sorted(set(TEAM_NAMES) - set(teams))
        raise ValueError(
            "Team names do not match the data. "
            f"Teams with no name: {missing}. Names with no team: {extra}."
        )
    _start_season, end_season, last_week = season_window(config)
    # Week last_week + 1 means "before the week after the last counted week", so week 10 is included.
    standings = standings_before_week(games, end_season, last_week + 1, teams).set_index("team")
    summary_setting = config["tracking"]["summary_path"]
    summary_path = resolve_path(summary_setting)
    if not summary_path.is_file():
        raise ValueError(
            f"No run summary at {summary_setting}. Run python -m src.model.train first."
        )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    validation = summary["scores"]["validation"]
    team_rows = []
    for abbreviation in teams:
        row = standings.loc[abbreviation]
        team_rows.append(
            {
                "team": abbreviation,
                "name": TEAM_NAMES[abbreviation],
                "games": int(row["games"]),
                "wins": int(row["wins"]),
                "win_pct": float(row["win_pct"]),
                "point_diff_per_game": float(row["point_diff_per_game"]),
            }
        )
    return {
        "as_of": {"season": int(end_season), "through_week": int(last_week)},
        "model": {
            "version": summary["model_version"],
            "validation_games": validation["games"],
            "validation_correct": validation["correct"],
            "validation_accuracy": validation["accuracy"],
            "validation_baseline": validation["baseline"],
        },
        "teams": team_rows,
    }


def profiles_text(document: dict) -> str:
    """The document as text, with one trailing newline and no non-finite numbers."""
    return json.dumps(document, indent=2, allow_nan=False) + "\n"


def write_profiles(config: dict, document: dict) -> Path:
    """Write the profiles file, swapping it in only after the text is complete."""
    output = resolve_path(config["frontend"]["profiles_path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    # A failed write must not replace a good file with a half-written one.
    partial = output.with_name(output.name + ".partial")
    try:
        partial.write_text(profiles_text(document), encoding="utf-8")
        os.replace(partial, output)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    return output


def main() -> None:
    """Build the profiles file and print where it was saved."""
    try:
        config = load_config()
        document = build_profiles(config)
        write_profiles(config, document)
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from None
    as_of = document["as_of"]
    print(f"teams: {len(document['teams'])}")
    print(f"as of: {as_of['season']} week {as_of['through_week']}")
    print(f"saved: {config['frontend']['profiles_path']}")


if __name__ == "__main__":
    main()
