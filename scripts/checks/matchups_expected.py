"""Score every ordered pair of teams with the saved model, without reading the profiles file.

It reads the downloaded games table and models/model.joblib, scores all 992 ordered pairs, and
writes build/expected-matchups.json. It does not call the live API.
"""

import itertools
import json
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np

# scripts/checks/ is two folders below the project, so parents[2] is the project folder.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_config, resolve_path, season_window
from src.model.features import load_games, standings_before_week

OUTPUT = ROOT / "build" / "expected-matchups.json"


def main() -> None:
    """Write one expected answer for each ordered pair of teams."""
    config = load_config()
    games = load_games(config)
    teams = sorted(set(games["home_team"]) | set(games["away_team"]))
    _start_season, season, _last_week = season_window(config)
    # Week 11 is the first week after the last counted week, so week 10 is included.
    standings = standings_before_week(games, season, 11, teams).set_index("team")
    pipeline = joblib.load(resolve_path(config["model"]["output_path"]))["pipeline"]
    rows = []
    for home_code, away_code in itertools.permutations(teams, 2):
        home = standings.loc[home_code]
        away = standings.loc[away_code]
        win_pct = float(home["win_pct"] - away["win_pct"])
        margin = float(home["point_diff_per_game"] - away["point_diff_per_game"])
        # A plain array has no column names. The warning only says so, and the two numbers are already in order.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="X does not have valid feature names",
                category=UserWarning,
            )
            probability = float(pipeline.predict_proba(np.array([[win_pct, margin]], dtype=float))[0, 1])
        rows.append(
            {
                "home": home_code,
                "away": away_code,
                "win_pct_differential": win_pct,
                "point_diff_per_game_differential": margin,
                "probability": probability,
                "pick": 1 if probability > 0.5 else 0,
            }
        )
    # The written file stays in build/, which a fresh clone does not have yet.
    (ROOT / "build").mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(rows), encoding="utf-8")
    print(f"pairs: {len(rows)}")


if __name__ == "__main__":
    main()
