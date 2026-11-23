"""Tests for the feedback Lambda function, with a stand-in for the DynamoDB table.

The events are made-up API Gateway dictionaries and the table is a small class that records
what the handler tries to save. No test calls AWS, uses credentials, or touches the network.
"""

import base64
import json
import uuid

import pytest

from src.api import feedback_handler


class Table:
    """Records put_item calls, or raises when the test asks it to."""
    # Only put_item is needed, because that is the one table method the handler calls.

    def __init__(self, fail: bool = False):
        self.calls = []
        self.fail = fail

    def put_item(self, **kwargs):
        """Save the call, or raise the storage error the handler turns into a 500."""
        if self.fail:
            raise RuntimeError("table unavailable")
        self.calls.append(kwargs)


def _event(body, encoded: bool = False) -> dict:
    """An API Gateway version 2.0 event, with the body as text or base64."""
    # A string is sent as is, so a test can send text that is not JSON. Anything else becomes JSON.
    text = body if isinstance(body, str) else json.dumps(body)
    if encoded:
        return {"body": base64.b64encode(text.encode("utf-8")).decode("ascii"), "isBase64Encoded": True}
    return {"body": text, "isBase64Encoded": False}


def _use_table(monkeypatch, table: Table) -> None:
    """Point the handler at the stand-in and name the table, without calling AWS."""
    # Lambda sets this name in its settings. The handler reads it only when it builds a real table client.
    monkeypatch.setenv("FEEDBACK_TABLE", "510-m3-nfl-feedback")
    # The handler keeps its table in a module variable and builds one only when it is empty.
    # Setting it first means boto3 is never called. monkeypatch puts the old value back after the test.
    monkeypatch.setattr(feedback_handler, "_table", table)


def _valid(**overrides) -> dict:
    """A body the check accepts."""
    body = {"category": "general", "rating": 4, "message": "The week list is clear.", "website": ""}
    body.update(overrides)
    return body


def test_valid_feedback_is_saved(monkeypatch):
    """A valid body is stored with the five fields, the trimmed message, and the condition."""
    table = Table()
    _use_table(monkeypatch, table)
    answer = feedback_handler.handler(_event(_valid(message="  The week list is clear.  ")), None)
    body = json.loads(answer["body"])
    assert answer["statusCode"] == 201
    assert body["status"] == "received"
    # UUID() raises ValueError when the text is not a valid id.
    uuid.UUID(body["feedback_id"])
    assert len(table.calls) == 1
    call = table.calls[0]
    item = call["Item"]
    assert set(item) == {"feedback_id", "submitted_at", "category", "message", "rating"}
    assert item["message"] == "The week list is clear."
    assert item["rating"] == 4
    assert item["category"] == "general"
    # The condition makes DynamoDB refuse to overwrite an existing item with the same id.
    assert call["ConditionExpression"] == "attribute_not_exists(feedback_id)"
    assert answer["headers"]["Content-Type"] == "application/json"


def test_rating_is_left_out_when_empty(monkeypatch):
    """An empty rating is not stored as a key."""
    table = Table()
    _use_table(monkeypatch, table)
    answer = feedback_handler.handler(_event(_valid(rating=None)), None)
    assert answer["statusCode"] == 201
    assert "rating" not in table.calls[0]["Item"]


def test_hidden_field_saves_nothing(monkeypatch):
    """A filled website field still says received, and the table is not called."""
    # The website field is not shown to people on the page, so only a bot fills it in. The bot
    # gets the same success answer, so it learns nothing, and nothing is stored.
    table = Table()
    _use_table(monkeypatch, table)
    answer = feedback_handler.handler(_event(_valid(website="https://spam.example")), None)
    body = json.loads(answer["body"])
    assert answer["statusCode"] == 201
    # The answer still carries an id, so it looks the same as a real save. The id is not stored.
    uuid.UUID(body["feedback_id"])
    assert table.calls == []


def test_extra_or_missing_keys_are_refused(monkeypatch):
    """An extra key and a missing key both name the four required keys."""
    table = Table()
    _use_table(monkeypatch, table)
    extra = _valid(note="no")
    missing = _valid()
    del missing["message"]
    # The same message is expected for both, because the check compares the whole set of keys.
    for body in (extra, missing):
        answer = feedback_handler.handler(_event(body), None)
        assert answer["statusCode"] == 422
        assert json.loads(answer["body"])["detail"] == "Send exactly category, rating, message, and website."
    assert table.calls == []


def test_bad_category_and_rating_are_refused(monkeypatch):
    """A category or a rating outside the list is refused."""
    _use_table(monkeypatch, Table())
    # 2.5 is not a whole number. True is refused because Python counts a bool as an int.
    for body in (
        _valid(category="other"),
        _valid(rating=0),
        _valid(rating=6),
        _valid(rating=2.5),
        _valid(rating=True),
    ):
        answer = feedback_handler.handler(_event(body), None)
        assert answer["statusCode"] == 422


def test_message_length_is_checked_after_trimming(monkeypatch):
    """Spaces do not count toward the 10 character minimum."""
    table = Table()
    _use_table(monkeypatch, table)
    # Nine characters between spaces, one short of the minimum. Without trimming, the spaces would pass it.
    short = feedback_handler.handler(_event(_valid(message="   123456789   ")), None)
    assert short["statusCode"] == 422
    assert json.loads(short["body"])["detail"] == "The message must be 10 to 1,000 characters."
    # Exactly 10 characters is the shortest message that is accepted. 1001 is one over the longest.
    ok = feedback_handler.handler(_event(_valid(message="1234567890")), None)
    assert ok["statusCode"] == 201
    long = feedback_handler.handler(_event(_valid(message="x" * 1001)), None)
    assert long["statusCode"] == 422


def test_large_or_non_json_body_gives_400(monkeypatch):
    """A body over 4 KB, a body that is not JSON, and a JSON list are all refused."""
    _use_table(monkeypatch, Table())
    # 4097 characters is one byte over the 4096 limit. The list is valid JSON but not an object.
    for body in ("x" * 4097, "not json", json.dumps(["general"])):
        answer = feedback_handler.handler(_event(body), None)
        assert answer["statusCode"] == 400
        assert json.loads(answer["body"])["detail"] == "The request body must be a JSON object under 4 KB."


def test_base64_body_is_decoded(monkeypatch):
    """A valid body sent base64-encoded is saved."""
    # API Gateway marks a body as base64 text when it cannot send it as plain text.
    table = Table()
    _use_table(monkeypatch, table)
    answer = feedback_handler.handler(_event(_valid(), encoded=True), None)
    assert answer["statusCode"] == 201
    assert len(table.calls) == 1


def test_storage_error_gives_500(monkeypatch):
    """A table error gives a 500 with a fixed message that does not repeat the visitor's text."""
    _use_table(monkeypatch, Table(fail=True))
    # The stand-in raises on put_item, as DynamoDB would on a throttle or an outage.
    answer = feedback_handler.handler(_event(_valid()), None)
    assert answer["statusCode"] == 500
    assert json.loads(answer["body"])["detail"] == "The feedback could not be saved."
