"""Tests for the S3 download script.

They use a Mock in place of the real S3 client, and every file lives in pytest's temporary
folder. No test calls AWS, needs credentials, or touches the project's data folders.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from src.data.download_from_s3 import download


def _config(bucket: str, from_s3: Path) -> dict:
    """Build a small settings dictionary, with the file path pointing at a temporary folder."""
    return {
        "data": {
            "from_s3_path": str(from_s3),
            "s3_bucket": bucket,
            "s3_key": "data/processed/nfl_matchups_2020_2026.csv",
            "aws_region": "us-east-1",
        }
    }


def test_download_saves_the_file_at_from_s3_path(tmp_path):
    """A finished download replaces the local copy with the bytes S3 sent."""
    dest = tmp_path / "from-s3.csv"
    payload = b"game_id\n1\n"

    def write_file(bucket, key, filename):
        Path(filename).write_bytes(payload)

    client = Mock()
    client.download_file.side_effect = write_file

    download(_config("510-m3-nfl-dataset", dest), client)

    assert dest.read_bytes() == payload
    client.download_file.assert_called_once()
    bucket, key, filename = client.download_file.call_args.args
    assert bucket == "510-m3-nfl-dataset"
    assert key == "data/processed/nfl_matchups_2020_2026.csv"
    assert filename.endswith(".partial")
    assert not Path(str(dest) + ".partial").exists()


def test_download_keeps_the_old_file_when_s3_fails(tmp_path):
    """A failed download leaves the previous copy in place."""
    dest = tmp_path / "from-s3.csv"
    dest.write_bytes(b"old")
    client = Mock()
    client.download_file.side_effect = ClientError(
        {"Error": {"Code": "500", "Message": "down"}},
        "DownloadFile",
    )

    with pytest.raises(ClientError):
        download(_config("510-m3-nfl-dataset", dest), client)

    assert dest.read_bytes() == b"old"
    assert not Path(str(dest) + ".partial").exists()
