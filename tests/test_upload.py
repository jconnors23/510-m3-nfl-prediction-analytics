"""Tests for the S3 upload script.

They use a Mock in place of the real S3 client, and every file lives in pytest's temporary
folder. No test calls AWS, needs credentials, or touches the project's data folders.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from src.data.upload_to_s3 import SizeMismatchError, upload


def _config(bucket: str, processed: Path, from_s3: Path) -> dict:
    """Build a small settings dictionary, with the file paths pointing at a temporary folder."""
    return {
        "data": {
            "processed_path": str(processed),
            "from_s3_path": str(from_s3),
            "s3_bucket": bucket,
            "s3_key": "data/processed/nfl_matchups_2020_2026.csv",
            "aws_region": "us-east-1",
        }
    }


def test_upload_stops_when_object_size_differs(tmp_path):
    """Upload fails if the stored object is a different size than the local file.

    The size check is how the script confirms that the file in S3 is the file that was sent.
    """
    path = tmp_path / "games.csv"
    path.write_text("game_id\n1\n", encoding="utf-8")
    # A Mock accepts any call and records it, so the upload runs without a network. Only
    # head_object is given an answer, because the size check is the part under test.
    client = Mock()
    # Pretend S3 reports an object 5 bytes larger than the local file.
    client.head_object.return_value = {"ContentLength": path.stat().st_size + 5}

    # The size check is what proves the upload matches the file, so a difference must stop the step.
    with pytest.raises(SizeMismatchError):
        upload(_config("510-m3-nfl-dataset", path, tmp_path / "from-s3.csv"), client)
