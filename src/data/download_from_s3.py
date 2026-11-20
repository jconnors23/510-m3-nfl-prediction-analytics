"""Step 4: save the cleaned games table downloaded from S3.

Every later step reads this local copy, so the pipeline always starts from the S3 version.
"""

import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.config import data_file, load_config


def download(config: dict, client=None) -> None:
    """Download the cleaned table from S3 and save it at `from_s3_path`."""
    bucket = config["data"]["s3_bucket"]

    key = config["data"]["s3_key"]
    dest = data_file(config, "from_s3_path")
    dest.parent.mkdir(parents=True, exist_ok=True)
    # A failed download must not replace a good copy, so write beside it and rename after it finishes.
    tmp = dest.with_name(dest.name + ".partial")
    # Tests pass in a fake client. A real run builds one from the machine's AWS credentials.
    if client is None:
        client = boto3.client("s3", region_name=config["data"]["aws_region"])
    try:
        client.download_file(bucket, key, str(tmp))
        # The swap happens only after the whole file arrived. Any older copy is replaced in one step.
        os.replace(tmp, dest)
    except Exception:
        # Anything unexpected: clean up the half-finished file, then pass the error on.
        tmp.unlink(missing_ok=True)
        raise

    # Count lines and subtract the header line. Step 2 already checked the table, so this is
    # only a quick printout to compare with the cleaned table's row count.
    with dest.open(encoding="utf-8") as handle:
        row_count = sum(1 for _ in handle) - 1
    print(f"rows: {row_count}")
    print(f"saved: {config['data']['from_s3_path']}")


def main() -> None:
    """Command for Step 4: download the cleaned table from S3."""
    try:
        download(load_config())
    except (ClientError, BotoCoreError, ValueError, FileNotFoundError) as exc:
        # Expected problems end with a short message, not a traceback.
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    main()
