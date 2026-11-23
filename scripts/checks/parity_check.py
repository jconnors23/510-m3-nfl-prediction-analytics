"""Send every game to the public API and compare each answer with the local model.

It reads the downloaded games table, models/model.joblib, and the run summary, posts each of
the 1,759 games to the live /predict route, and writes build/parity-results.json. It calls
the live API.
"""

import json
import sys
import time
from pathlib import Path

import joblib
import requests

# scripts/checks/ is two folders below the project, so parents[2] is the project folder.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_config, resolve_path
from src.model.features import (
    INPUT_COLUMNS,
    build_model_table,
    check_model_table,
    load_games,
    split_games,
)

URL = "https://9awodatqc5.execute-api.us-east-1.amazonaws.com/predict"
GROUP_ORDER = ("training", "validation", "test")
RESULTS_PATH = ROOT / "build" / "parity-results.json"


def local_rows(config):
    """Score every game with the saved pipeline, in training, validation, then test order."""
    games = load_games(config)
    table = build_model_table(games)
    check_model_table(table)
    groups = split_games(table, config)
    bundle = joblib.load(resolve_path(config["model"]["output_path"]))
    pipeline = bundle["pipeline"]
    rows = []
    for name in GROUP_ORDER:
        group = groups[name]
        # The same column list the training score uses, so the local probability is that score.
        probability = pipeline.predict_proba(group[INPUT_COLUMNS])[:, 1]
        for game, chance in zip(group.itertuples(index=False), probability, strict=True):
            chance = float(chance)
            rows.append(
                {
                    "game_id": game.game_id,
                    "group": name,
                    "home_win": int(game.home_win),
                    "win_pct_differential": float(getattr(game, INPUT_COLUMNS[0])),
                    "point_diff_per_game_differential": float(getattr(game, INPUT_COLUMNS[1])),
                    "local_probability": chance,
                    "local_pick": 1 if chance > 0.5 else 0,
                }
            )
    return rows


def expected_correct(config):
    """The correct counts already written in the run summary."""
    path = resolve_path(config["tracking"]["summary_path"])
    summary = json.loads(path.read_text(encoding="utf-8"))
    return {name: int(summary["scores"][name]["correct"]) for name in GROUP_ORDER}


def post_game(session, row):
    """Send one game, and try once more only after a timeout or a status of 500 or higher."""
    payload = {
        "win_pct_differential": row["win_pct_differential"],
        "point_diff_per_game_differential": row["point_diff_per_game_differential"],
    }
    retries = 0
    times = []
    response = None
    for attempt in (1, 2):
        started = time.perf_counter()
        try:
            response = session.post(URL, json=payload, timeout=30)
        except requests.Timeout:
            times.append(time.perf_counter() - started)
            if attempt == 1:
                retries = 1
                continue
            return None, retries, times
        times.append(time.perf_counter() - started)
        if response.status_code >= 500 and attempt == 1:
            retries = 1
            continue
        return response, retries, times
    return response, retries, times


def main():
    """Compare every deployed answer with the local model and write the results file."""
    config = load_config()
    rows = local_rows(config)
    wanted = expected_correct(config)
    session = requests.Session()
    mismatches = []
    times = []
    retries = 0
    requests_sent = 0
    status_200 = 0
    exact = 0
    picks_matched = 0
    largest = 0.0
    correct = {name: 0 for name in GROUP_ORDER}
    games = {name: 0 for name in GROUP_ORDER}
    failed = False

    for index, row in enumerate(rows, start=1):
        response, used_retry, attempt_times = post_game(session, row)
        retries += used_retry
        requests_sent += len(attempt_times)
        times.extend(attempt_times)
        if retries > 10:
            print(f"stopped: {retries} retries, more than 10")
            failed = True
            break
        if response is None or response.status_code != 200:
            status = None if response is None else response.status_code
            print(f"stopped: {row['game_id']} status {status} after {used_retry} retry")
            failed = True
            break
        status_200 += 1
        body = response.json()
        deployed_probability = float(body["home_win_probability"])
        deployed_pick = int(body["prediction"])
        rounded = round(row["local_probability"], 4)
        difference = abs(deployed_probability - rounded)
        largest = max(largest, difference)
        pick_ok = deployed_pick == row["local_pick"]
        exact_ok = deployed_probability == rounded
        version_ok = body["model_version"] == "v1.0"
        if pick_ok:
            picks_matched += 1
        if exact_ok:
            exact += 1
        if deployed_pick == row["home_win"]:
            correct[row["group"]] += 1
        games[row["group"]] += 1
        if not pick_ok or not exact_ok or not version_ok or difference > 0.0001:
            mismatches.append(
                {
                    "game_id": row["game_id"],
                    "local_probability": rounded,
                    "deployed_probability": deployed_probability,
                    "difference": difference,
                    "local_pick": row["local_pick"],
                    "deployed_pick": deployed_pick,
                    "model_version": body["model_version"],
                }
            )
            if not pick_ok or not version_ok or difference > 0.0001:
                failed = True
        if index % 500 == 0:
            print(f"sent {index}", file=sys.stderr)

    group_report = {}
    for name in GROUP_ORDER:
        count = games[name]
        hits = correct[name]
        group_report[name] = {
            "games": count,
            "correct": hits,
            "accuracy": None if count == 0 else hits / count,
            "summary_correct": wanted[name],
        }
        if hits != wanted[name] or count == 0:
            failed = True

    report = {
        "requests": requests_sent,
        "retries": retries,
        "status_200": status_200,
        "exact_probability_matches": exact,
        "pick_matches": picks_matched,
        "largest_probability_difference": largest,
        "mismatches": mismatches,
        "groups": group_report,
        "slowest_seconds": None if not times else max(times),
        "average_seconds": None if not times else sum(times) / len(times),
    }
    (ROOT / "build").mkdir(exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"requests {requests_sent}")
    print(f"retries {retries}")
    print(f"status 200 {status_200}")
    print(f"picks matched {picks_matched}")
    print(f"probabilities exact {exact}")
    print(f"largest difference {largest}")
    for name in GROUP_ORDER:
        item = group_report[name]
        print(f"{name}: {item['correct']} of {item['games']} correct")
    if times:
        print(f"slowest {max(times):.3f}s average {sum(times) / len(times):.3f}s")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
