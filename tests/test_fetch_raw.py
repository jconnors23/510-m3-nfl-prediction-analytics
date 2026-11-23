"""Tests for the games-file download.

They replace requests.get with a stand-in, and every file lives in pytest's temporary folder.
No test uses the internet or touches the project's data folders.
"""

from pathlib import Path

import pytest
import requests

from src.data.fetch_raw import NEEDED_COLUMNS, fetch_raw


def _csv(columns: list[str]) -> bytes:
    """A two-row table whose header is the given columns."""
    header = ",".join(columns)
    row = ",".join("1" for _ in columns)
    return f"{header}\n{row}\n{row}\n".encode()


def _response(content: bytes, fail: bool = False):
    """A stand-in for the object requests.get returns."""

    class Response:
        def raise_for_status(self) -> None:
            if fail:
                raise requests.HTTPError("bad status")

    response = Response()
    response.content = content
    return response


def test_fetch_saves_a_good_file_and_counts_rows(tmp_path, monkeypatch):
    """A complete file is saved, and the row count is the number of data rows."""
    dest = tmp_path / "games.csv"
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _response(_csv(list(NEEDED_COLUMNS))))

    count = fetch_raw("https://example.test/games.csv", dest)

    assert count == 2
    assert dest.read_bytes() == _csv(list(NEEDED_COLUMNS))
    assert not Path(str(dest) + ".partial").exists()


def test_fetch_refuses_a_file_missing_a_season_column(tmp_path, monkeypatch):
    """A file missing gametime is refused, and the previous copy stays as it was."""
    dest = tmp_path / "games.csv"
    dest.write_bytes(b"old")
    columns = [name for name in NEEDED_COLUMNS if name != "gametime"]
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _response(_csv(columns)))

    with pytest.raises(ValueError, match="gametime"):
        fetch_raw("https://example.test/games.csv", dest)

    assert dest.read_bytes() == b"old"
    assert not Path(str(dest) + ".partial").exists()


def test_fetch_keeps_the_old_file_when_the_download_fails(tmp_path, monkeypatch):
    """A failed download leaves the previous copy in place."""
    dest = tmp_path / "games.csv"
    dest.write_bytes(b"old")
    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: _response(b"", fail=True))

    with pytest.raises(requests.HTTPError):
        fetch_raw("https://example.test/games.csv", dest)

    assert dest.read_bytes() == b"old"
    assert not Path(str(dest) + ".partial").exists()
