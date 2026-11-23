"""Score every 2026 game with the saved model, in the season file's order.

It reads the downloaded games table and models/model.joblib, builds the season, scores all
272 games, and writes build/expected-season.json. It does not call the live API.
"""

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

from src.config import load_config, resolve_path
from src.model.features import build_model_table, load_games
from src.season import build_season

OUTPUT = ROOT / "build" / "expected-season.json"


def main() -> None:
    """Write the two inputs, the probability, and the pick for all 272 games."""
    config = load_config()
    document = build_season(config)
    table = build_model_table(load_games(config))
    finished = {
        row.game_id: row
        for row in table.loc[table["season"] == document["season"]].itertuples(index=False)
    }
    standings = {
        entry["before_week"]: {row["team"]: row for row in entry["teams"]} for entry in document["standings"]
    }
    pipeline = joblib.load(resolve_path(config["model"]["output_path"]))["pipeline"]
    rows = []
    for week in document["weeks"]:
        before = standings[week["standings_before_week"]]
        for game in week["games"]:
            home = before[game["home"]]
            away = before[game["away"]]
            win_pct = float(home["win_pct"] - away["win_pct"])
            margin = float(home["point_diff_per_game"] - away["point_diff_per_game"])
            if game["game_id"] in finished:
                model_row = finished[game["game_id"]]
                if win_pct != model_row.win_pct_differential or margin != model_row.point_diff_per_game_differential:
                    raise SystemExit(f"{game['game_id']} does not match the model table")
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore",
                    message="X does not have valid feature names",
                    category=UserWarning,
                )
                probability = float(pipeline.predict_proba(np.array([[win_pct, margin]], dtype=float))[0, 1])
            rows.append(
                {
                    "game_id": game["game_id"],
                    "win_pct_differential": win_pct,
                    "point_diff_per_game_differential": margin,
                    "probability": probability,
                    "pick": 1 if probability > 0.5 else 0,
                }
            )
    if len(finished) != 149:
        raise SystemExit(f"expected 149 finished games and found {len(finished)}")
    (ROOT / "build").mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(rows), encoding="utf-8")
    print(f"games: {len(rows)}")


if __name__ == "__main__":
    main()
