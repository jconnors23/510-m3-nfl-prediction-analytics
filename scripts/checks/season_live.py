"""Send each 2026 game to the public API and compare it with the local model.

It reads build/expected-season.json and build/season-bodies.json, posts each of the 272
games to the live /predict route, and writes build/season-results.json. It calls the live API.
"""

import json
import sys
from pathlib import Path

import requests

# scripts/checks/ is two folders below the project, so parents[2] is the project folder.
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PATH = ROOT / "build" / "expected-season.json"
BODIES_PATH = ROOT / "build" / "season-bodies.json"
RESULTS_PATH = ROOT / "build" / "season-results.json"
URL = "https://9awodatqc5.execute-api.us-east-1.amazonaws.com/predict"
REQUEST_LIMIT = 300


def post_body(session: requests.Session, body: str) -> tuple[requests.Response | None, int]:
    """Post one body, and try once more only after a timeout or a status of 500 or higher."""
    retries = 0
    response = None
    for attempt in (1, 2):
        try:
            response = session.post(
                URL,
                data=body.encode("utf-8"),
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
        except requests.Timeout:
            response = None
        if response is not None and response.status_code < 500:
            return response, retries
        if attempt == 1:
            retries = 1
            continue
        return response, retries
    return response, retries


def main() -> None:
    """Compare every posted answer with the local model and write the counts."""
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    bodies = json.loads(BODIES_PATH.read_text(encoding="utf-8"))
    if len(expected) != len(bodies) or len(expected) != 272:
        raise SystemExit(f"expected 272 games and found {len(expected)} rows and {len(bodies)} bodies")
    session = requests.Session()
    sent = 0
    retries = 0
    status_200 = 0
    pick_matches = 0
    probability_matches = 0
    mismatches = []
    for row, body in zip(expected, bodies, strict=True):
        if sent >= REQUEST_LIMIT:
            raise SystemExit(f"stopped at {sent} requests")
        response, used_retry = post_body(session, body)
        sent += 1 + used_retry
        retries += used_retry
        if response is None or response.status_code != 200:
            mismatches.append({"game_id": row["game_id"], "status": None if response is None else response.status_code})
            continue
        status_200 += 1
        answer = response.json()
        rounded = round(row["probability"], 4)
        if answer.get("prediction") == row["pick"]:
            pick_matches += 1
        else:
            mismatches.append({"game_id": row["game_id"], "pick": answer.get("prediction"), "expected": row["pick"]})
        if answer.get("home_win_probability") == rounded:
            probability_matches += 1
        else:
            mismatches.append(
                {
                    "game_id": row["game_id"],
                    "probability": answer.get("home_win_probability"),
                    "expected": rounded,
                }
            )
    summary = {
        "requests": sent,
        "retries": retries,
        "status_200": status_200,
        "pick_matches": pick_matches,
        "probability_matches": probability_matches,
        "mismatches": mismatches,
    }
    (ROOT / "build").mkdir(exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "mismatches"}))
    print(f"mismatches: {len(mismatches)}")
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
