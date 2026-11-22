"""Tests for the Lambda entry point, using made-up API Gateway events and a temporary model.

The events are plain dictionaries and the model is fitted on made-up games in a temporary
folder, so no test calls AWS or the network. Only the last test reads models/model.joblib, and
it is skipped when that file is not on disk.
"""

import ast
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.api.app import create_app, load_model
from src.api.lambda_handler import build_handler
import src.api.lambda_handler as lambda_handler

SAVED_MODEL = Path(__file__).resolve().parents[1] / "models" / "model.joblib"
FEATURE_NAMES = ["win_pct_differential", "point_diff_per_game_differential"]
# The model's answer for game 2025_07_NE_TEN (inputs -0.5 and -18.0), the same worked example
# used in the Phase 2 and Phase 3 docs. Only the test that reads the real model file uses it.
WORKED_EXAMPLE = {
    "prediction": 0,
    "predicted_label": "away win",
    "home_win_probability": 0.3296,
    "model_version": "v1.0",
}


@pytest.fixture
def model_config(tmp_path):
    """A tiny saved model in the same dictionary shape as the real file."""
    # Made-up games with a fixed seed, so every run builds the same model and these tests never
    # depend on the real training data or on models/model.joblib.
    generator = np.random.default_rng(0)
    count = 40
    frame = pd.DataFrame(
        {
            "win_pct_differential": generator.normal(0, 0.3, count),
            "point_diff_per_game_differential": generator.normal(0, 8, count),
        }
    )
    # A stronger home team wins more often, so the made-up answers follow the same pattern as real games.
    chance = 1 / (1 + np.exp(-(frame["win_pct_differential"] + 0.05 * frame["point_diff_per_game_differential"])))
    labels = (generator.random(count) < chance).astype(int)
    # Both answers have to appear, or the probability of class 1 is not the second column.
    labels[0] = 0
    labels[1] = 1
    pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=0))
    # Fitted on a table with column names, like the real model, so the handler's plain-array
    # call goes through the same "no valid feature names" path that it does on Lambda.
    pipeline.fit(frame, labels)
    path = tmp_path / "model.joblib"
    joblib.dump(
        {
            "pipeline": pipeline,
            "feature_names": list(FEATURE_NAMES),
            "model_version": "test-1",
            "scikit_learn_version": sklearn.__version__,
            "train_start_season": 2020,
            "train_end_season": 2024,
        },
        path,
    )
    return {"model": {"output_path": str(path)}}


def _event(method, path, body=None):
    """An API Gateway HTTP API event, payload format 2.0, for one method and path."""
    # This is the dictionary API Gateway hands a Lambda function in place of a web request.
    # Mangum recognizes it as an HTTP API event by "version" and "requestContext.http", and builds
    # the request FastAPI sees from the method, the path, the headers, and the body.
    event = {
        "version": "2.0",
        "routeKey": f"{method} {path}",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"content-type": "application/json"},
        "requestContext": {
            "accountId": "123456789012",
            "apiId": "test",
            "domainName": "test.execute-api.us-east-1.amazonaws.com",
            "http": {
                "method": method,
                "path": path,
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "test",
            },
            "requestId": "test",
            "routeKey": f"{method} {path}",
            "stage": "$default",
            "time": "01/Jan/2026:00:00:00 +0000",
            "timeEpoch": 1767225600000,
        },
        "isBase64Encoded": False,
    }
    if body is not None:
        event["body"] = body
    return event


def test_handler_serves_a_predict_event(model_config):
    """A predict event returns 200 and the made-up model's version."""
    # build_handler is the one place the Lambda wiring is written, so calling it with a made-up
    # model tests the same code path that runs on AWS. The body is a JSON string, as in a real event.
    # None stands in for the Lambda context object, which these tests do not need.
    wrapped = build_handler(create_app(model_config), model_config)
    result = wrapped(
        _event(
            "POST",
            "/predict",
            '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}',
        ),
        None,
    )
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert set(body) == {
        "prediction",
        "predicted_label",
        "home_win_probability",
        "model_version",
    }
    assert body["model_version"] == "test-1"


def test_handler_serves_a_health_event(model_config):
    """A health event returns 200 and status ok."""
    wrapped = build_handler(create_app(model_config), model_config)
    result = wrapped(_event("GET", "/health"), None)
    assert result["statusCode"] == 200
    assert json.loads(result["body"])["status"] == "ok"


def test_handler_rejects_a_bad_body(model_config):
    """A body with one out-of-range field and one missing field returns 422 and names both."""
    # win_pct_differential is above its limit of 1, and point_diff_per_game_differential is absent.
    wrapped = build_handler(create_app(model_config), model_config)
    result = wrapped(_event("POST", "/predict", '{"win_pct_differential": 1.5}'), None)
    assert result["statusCode"] == 422
    text = result["body"]
    assert "win_pct_differential" in text
    assert "point_diff_per_game_differential" in text


def test_model_is_loaded_once_across_invocations(model_config, monkeypatch):
    """Three calls to the Lambda handler read the model once."""
    calls = {"count": 0}

    # The handler module looks up load_config and load_model by name, so replacing them on the
    # module points it at the made-up model and counts every read of the model file.
    def counting_load_model(config):
        """Count each read, then load the made-up model."""
        calls["count"] += 1
        return load_model(config)

    monkeypatch.setattr(lambda_handler, "load_config", lambda: model_config)
    monkeypatch.setattr(lambda_handler, "load_model", counting_load_model)
    # The handler keeps its wrapped copy for the life of the module, so it is cleared before the
    # test (to force a fresh first call) and after it (so no later test inherits the made-up model).
    lambda_handler._cached_handler = None
    event = _event(
        "POST",
        "/predict",
        '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}',
    )
    try:
        for _ in range(3):
            lambda_handler.handler(event, None)
    finally:
        lambda_handler._cached_handler = None
    assert calls["count"] == 1


def test_lambda_handler_does_not_import_pandas():
    """The handler file does not import pandas, mlflow, matplotlib, or the training code."""
    # The file is read as text. Looking at sys.modules would not work, because scikit-learn
    # loads pandas on its own when it is installed.
    root = Path(__file__).resolve().parents[1]
    tree = ast.parse((root / "src" / "api" / "lambda_handler.py").read_text(encoding="utf-8"))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    for name in modules:
        assert name not in {"pandas", "mlflow", "matplotlib"}
        assert not name.startswith("src.model")


# models/model.joblib is not committed, so a fresh checkout skips this test until training has run.
@pytest.mark.skipif(not SAVED_MODEL.is_file(), reason="models/model.joblib is not on disk")
def test_real_handler_worked_example():
    """The saved model answers the New England at Tennessee inputs with 0.3296."""
    # This calls the real Lambda handler with the real config and the real model file, so it is
    # the closest test to what runs on AWS. The cache is cleared so the real model is loaded.
    lambda_handler._cached_handler = None
    try:
        result = lambda_handler.handler(
            _event(
                "POST",
                "/predict",
                '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}',
            ),
            None,
        )
    finally:
        lambda_handler._cached_handler = None
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == WORKED_EXAMPLE
