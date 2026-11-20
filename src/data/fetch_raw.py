"""Step 1: download the games file and keep the previous copy if the download fails.

The saved file is never edited. Cleaning (Step 2) reads it and writes a separate table.
"""

import os
from datetime import datetime, timezone

import pandas as pd
import requests

from src.config import data_file, load_config

# Cleaning reads these columns. The downloaded file may have more, and that is fine.
NEEDED_COLUMNS = [
    "game_id",
    "season",
    "game_type",
    "week",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
]


def fetch_raw(url: str, dest) -> int:
    """Download `url` to `dest` and return the number of rows in the file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    # A failed download must not replace a good file, so write beside it and rename after the checks.
    tmp = dest.with_name(dest.name + ".partial")
    try:
        response = requests.get(url, timeout=120)
        # Stops on a 404 or a server error, so an error page is never saved as data.
        response.raise_for_status()
        tmp.write_bytes(response.content)
        # Read the file back to prove it is a real table with the columns cleaning needs.
        frame = pd.read_csv(tmp)
        missing = [name for name in NEEDED_COLUMNS if name not in frame.columns]
        if missing:
            raise ValueError(f"Downloaded file is missing columns: {', '.join(missing)}")
        if frame.empty:
            raise ValueError("Downloaded file has no rows")
        row_count = len(frame)
    except Exception:
        # Remove the half-finished file, then pass the original error on to the caller.
        tmp.unlink(missing_ok=True)
        raise
    # Only a file that passed every check reaches this line. os.replace swaps it in one step.
    os.replace(tmp, dest)
    return row_count


def main() -> None:
    """Command for Step 1: download the games file and save it unchanged."""
    try:
        config = load_config()
        url = config["data"]["source_url"]
        dest = data_file(config, "raw_path")
        row_count = fetch_raw(url, dest)
    except (requests.RequestException, ValueError, pd.errors.EmptyDataError, OSError) as exc:
        # An expected problem (no internet, bad file) ends with a short message, not a traceback.
        raise SystemExit(str(exc)) from None

    # Print what was downloaded and when, so a run can be traced later.
    print(url)
    print(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
    print(f"rows: {row_count}")
    print(f"saved: {config['data']['raw_path']}")


if __name__ == "__main__":
    main()
