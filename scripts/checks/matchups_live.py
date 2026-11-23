"""Send each JavaScript request body to the public API and compare it with the local model.

It reads build/expected-matchups.json and build/js-bodies.json, posts each body to the live
/predict route, and writes build/matchups-results.json. It calls the live API.
"""

import json
import sys
from pathlib import Path

import requests

# scripts/checks/ is two folders below the project, so parents[2] is the project folder.
ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PATH = ROOT / "build" / "expected-matchups.json"
BODIES_PATH = ROOT / "build" / "js-bodies.json"
RESULTS_PATH = ROOT / "build" / "matchups-results.json"
URL = "https://9awodatqc5.execute-api.us-east-1.amazonaws.com/predict"
REQUEST_LIMIT = 1100


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
    """Compare every posted answer with the expected file and write the counts."""
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
    bodies = json.loads(BODIES_PATH.read_text(encoding="utf-8"))
    if len(expected) != len(bodies):
        raise SystemExit(f"expected {len(expected)} pairs and {len(bodies)} bodies")
    session = requests.Session()
    sent = 0
    retries = 0
    status_200 = 0
    pick_matches = 0
    probability_matches = 0
    mismatches = []
    largest = 0.0
    for row, body in zip(expected, bodies, strict=True):
        if sent >= REQUEST_LIMIT:
            raise SystemExit(f"stopped at {sent} requests")
        response, used_retry = post_body(session, body)
        sent += 1 + used_retry
        retries += used_retry
        if sent > REQUEST_LIMIT:
            raise SystemExit(f"stopped at {sent} requests")
        if response is None:
            mismatches.append({"home": row["home"], "away": row["away"], "error": "no response"})
            continue
        if response.status_code == 200:
            status_200 += 1
        try:
            answer = response.json()
        except ValueError:
            answer = {}
        rounded = round(row["probability"], 4)
        pick_ok = answer.get("prediction") == row["pick"]
        probability_ok = answer.get("home_win_probability") == rounded
        version_ok = answer.get("model_version") == "v1.0"
        if pick_ok:
            pick_matches += 1
        if probability_ok:
            probability_matches += 1
        if isinstance(answer.get("home_win_probability"), (int, float)):
            largest = max(largest, abs(answer["home_win_probability"] - rounded))
        if response.status_code != 200 or not pick_ok or not probability_ok or not version_ok:
            mismatches.append(
                {
                    "home": row["home"],
                    "away": row["away"],
                    "status": response.status_code,
                    "answer": answer,
                    "pick": row["pick"],
                    "probability": rounded,
                }
            )
    probabilities = [row["probability"] for row in expected]
    picks = [row["pick"] for row in expected]
    results = {
        "requests": sent,
        "retries": retries,
        "status_200": status_200,
        "pick_matches": pick_matches,
        "probability_matches": probability_matches,
        "largest_probability_difference": largest,
        "home_picks": picks.count(1),
        "away_picks": picks.count(0),
        "lowest_probability": min(probabilities),
        "highest_probability": max(probabilities),
        "mismatches": mismatches,
    }
    (ROOT / "build").mkdir(exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in results.items() if key != "mismatches"}))
    print(f"mismatches: {len(mismatches)}")
    if mismatches or sent > REQUEST_LIMIT:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
