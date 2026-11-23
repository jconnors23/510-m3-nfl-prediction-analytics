"""Save one piece of feedback. This file is the whole Lambda zip, so it imports nothing from the project.

boto3 is not in the zip because the Lambda Python runtime already provides it. Any import from
src/ would fail in Lambda, since only this file is uploaded. The table client is created on the
first call, so importing this file needs no AWS access.
"""

import base64
import json
import os
import uuid
from datetime import datetime, timezone

import boto3

# Created on first use. Tests can set this to a stand-in before the handler runs.
_table = None

# The choices the form offers, and the only fields a body may hold. "website" is the hidden
# field that real visitors never fill in.
CATEGORIES = ("general", "predictions", "site", "broken")
KEYS = {"category", "rating", "message", "website"}
# The largest body that is read, in bytes. A full form with a 1,000-character message in plain
# English is a little over 1 KB, so a larger body is refused before it is parsed or stored.
# Note: a character can take up to 4 bytes, so a long message written mostly in emoji or other
# multi-byte characters can go over 4,096 bytes and be refused even though it is a real form.
MAX_BODY_BYTES = 4096


def check_feedback(body: dict) -> dict:
    """Return the cleaned fields, or raise ValueError with a message a visitor can read."""
    # Exactly these four fields. A missing or extra field means the caller is not the site's form.
    if set(body) != KEYS:
        raise ValueError("Send exactly category, rating, message, and website.")
    category = body["category"]
    if category not in CATEGORIES:
        raise ValueError("Choose one of the listed categories.")
    rating = body["rating"]
    # bool is a subclass of int, and a checkbox value is not a rating.
    if rating is not None and (isinstance(rating, bool) or not isinstance(rating, int) or rating < 1 or rating > 5):
        raise ValueError("The rating must be a whole number from 1 to 5, or empty.")
    message = body["message"]
    # The length is measured after trimming, so a message of only spaces is too short.
    if not isinstance(message, str) or not 10 <= len(message.strip()) <= 1000:
        raise ValueError("The message must be 10 to 1,000 characters.")
    # Any text is allowed here, because a bot fills this field and handler() turns it away
    # without an error. Only a value that is not text is refused.
    website = body["website"]
    if not isinstance(website, str):
        raise ValueError("Send exactly category, rating, message, and website.")
    return {"category": category, "rating": rating, "message": message.strip(), "website": website}


def _client():
    """The DynamoDB table, created once and reused on later calls."""
    # Reusing the table across calls avoids rebuilding the AWS client on every request while the
    # same Lambda copy stays warm. The table name comes from the environment, not from code.
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["FEEDBACK_TABLE"])
    return _table


def _answer(status: int, body: dict) -> dict:
    """One API Gateway version 2.0 answer. CORS headers are added by the API, not here."""
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event, context) -> dict:
    """Check one feedback body and save it when the hidden field is empty."""
    raw = event.get("body") or ""
    # API Gateway sends the body as base64 text for some requests, so decode it before measuring.
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    # The size is checked in bytes, not characters, because a character can take several bytes.
    # It is checked before parsing so an oversized body is never parsed or saved.
    if len(raw.encode("utf-8")) > MAX_BODY_BYTES:
        return _answer(400, {"detail": "The request body must be a JSON object under 4 KB."})
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        return _answer(400, {"detail": "The request body must be a JSON object under 4 KB."})
    # Valid JSON can still be a list or a number, and check_feedback needs an object.
    if not isinstance(body, dict):
        return _answer(400, {"detail": "The request body must be a JSON object under 4 KB."})
    try:
        clean = check_feedback(body)
    except ValueError as exc:
        return _answer(422, {"detail": str(exc)})
    feedback_id = str(uuid.uuid4())
    # A real visitor never sees the hidden field, so a filled one is a bot. It gets the same
    # success answer as a real visitor, so it cannot tell the entry was dropped, and nothing is stored.
    if clean["website"] != "":
        return _answer(201, {"status": "received", "feedback_id": feedback_id})
    # The time is in UTC with no fraction, so entries sort the same way no matter where they came from.
    item = {
        "feedback_id": feedback_id,
        "submitted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "category": clean["category"],
        "message": clean["message"],
    }
    # An empty rating is left out of the item, because DynamoDB would store None as a null value.
    if clean["rating"] is not None:
        item["rating"] = clean["rating"]
    # A random id should never repeat. The condition makes a repeat fail the save instead of
    # silently overwriting an earlier entry.
    try:
        _client().put_item(Item=item, ConditionExpression="attribute_not_exists(feedback_id)")
    except Exception as exc:
        # The error text can contain part of the item, which holds what the visitor wrote. The log
        # keeps only the error type, so that text never reaches the logs.
        print(type(exc).__name__)
        return _answer(500, {"detail": "The feedback could not be saved."})
    return _answer(201, {"status": "received", "feedback_id": feedback_id})
