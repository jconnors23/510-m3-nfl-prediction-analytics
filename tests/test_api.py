"""Tests for the local prediction service.

The made-up model lives in a temporary folder. Only the last test reads models/model.joblib.
"""

import ast
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
import sklearn
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.api.app import create_app, label_for

SAVED_MODEL = Path(__file__).resolve().parents[1] / "models" / "model.joblib"
FEATURE_NAMES = ["win_pct_differential", "point_diff_per_game_differential"]


@pytest.fixture
def model_config(tmp_path):
    """A tiny saved model in the same dictionary shape as the real file."""
    generator = np.random.default_rng(0)
    count = 40
    frame = pd.DataFrame(
        {
            "win_pct_differential": generator.normal(0, 0.3, count),
            "point_diff_per_game_differential": generator.normal(0, 8, count),
        }
    )
    chance = 1 / (1 + np.exp(-(frame["win_pct_differential"] + 0.05 * frame["point_diff_per_game_differential"])))
    labels = (generator.random(count) < chance).astype(int)
    # Both answers have to appear, or the probability of class 1 is not the second column.
    labels[0] = 0
    labels[1] = 1
    pipeline = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, random_state=0))
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
    return {"model": {"output_path": str(path)}}, pipeline


def _client(config: dict) -> TestClient:
    """A client whose start-up step has already loaded the given model."""
    return TestClient(create_app(config))


def test_prediction_matches_the_pipeline(model_config):
    """The route's rounded probability matches the same pipeline called directly."""
    config, pipeline = model_config
    payload = {"win_pct_differential": -0.25, "point_diff_per_game_differential": 6.0}
    with _client(config) as client:
        body = client.post("/predict", json=payload).json()
    table = pd.DataFrame([payload])
    expected = round(float(pipeline.predict_proba(table)[0, 1]), 4)
    assert body["home_win_probability"] == expected


def test_pick_rule():
    """Exactly 0.5 and anything lower is an away win, and anything higher is a home win."""
    assert label_for(0.0) == (0, "away win")
    assert label_for(0.4999) == (0, "away win")
    assert label_for(0.5) == (0, "away win")
    assert label_for(0.5001) == (1, "home win")
    assert label_for(1.0) == (1, "home win")


def test_response_fields(model_config):
    """The response has the four fields, and whole-number inputs are accepted."""
    config, _pipeline = model_config
    with _client(config) as client:
        response = client.post(
            "/predict",
            json={"win_pct_differential": 0, "point_diff_per_game_differential": 5},
        )
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"prediction", "predicted_label", "home_win_probability", "model_version"}
    assert isinstance(body["prediction"], int)
    assert isinstance(body["predicted_label"], str)
    assert isinstance(body["home_win_probability"], float)
    assert body["model_version"] == "test-1"
    if body["home_win_probability"] > 0.5:
        assert body["prediction"] == 1
        assert body["predicted_label"] == "home win"
    else:
        assert body["prediction"] == 0
        assert body["predicted_label"] == "away win"


def test_field_order_does_not_change_the_answer(model_config):
    """The same two values give the same response when the JSON fields are swapped."""
    config, _pipeline = model_config
    first = json.dumps({"win_pct_differential": 0.2, "point_diff_per_game_differential": -4.0})
    second = json.dumps({"point_diff_per_game_differential": -4.0, "win_pct_differential": 0.2})
    headers = {"Content-Type": "application/json"}
    with _client(config) as client:
        left = client.post("/predict", content=first, headers=headers).json()
        right = client.post("/predict", content=second, headers=headers).json()
    assert left == right


def test_missing_field_is_rejected(model_config):
    """A request that leaves out a field is rejected and names that field."""
    config, _pipeline = model_config
    with _client(config) as client:
        response = client.post("/predict", json={"win_pct_differential": 0.1})
    assert response.status_code == 422
    assert "point_diff_per_game_differential" in response.text


def test_extra_field_is_rejected(model_config):
    """A request with an unknown field is rejected and names that field."""
    config, _pipeline = model_config
    with _client(config) as client:
        response = client.post(
            "/predict",
            json={
                "win_pct_differential": 0.1,
                "point_diff_per_game_differential": 1.0,
                "spread": 3,
            },
        )
    assert response.status_code == 422
    assert "spread" in response.text


def test_text_value_is_rejected(model_config):
    """A number written as text is rejected, whether or not the text looks numeric."""
    config, _pipeline = model_config
    with _client(config) as client:
        words = client.post(
            "/predict",
            json={"win_pct_differential": "abc", "point_diff_per_game_differential": 0},
        )
        digits = client.post(
            "/predict",
            json={"win_pct_differential": "0.5", "point_diff_per_game_differential": 0},
        )
    assert words.status_code == 422
    assert digits.status_code == 422


def test_out_of_range_value_is_rejected(model_config):
    """Values past either limit are rejected, and the two edges are accepted."""
    config, _pipeline = model_config
    with _client(config) as client:
        high = client.post(
            "/predict",
            json={"win_pct_differential": 1.5, "point_diff_per_game_differential": 0},
        )
        far = client.post(
            "/predict",
            json={"win_pct_differential": 0, "point_diff_per_game_differential": 500},
        )
        edge = client.post(
            "/predict",
            json={"win_pct_differential": 1, "point_diff_per_game_differential": -100},
        )
    assert high.status_code == 422
    assert "win_pct_differential" in high.text
    assert far.status_code == 422
    assert "point_diff_per_game_differential" in far.text
    assert edge.status_code == 200


def test_not_a_number_is_rejected(model_config):
    """A body that contains NaN is rejected."""
    config, _pipeline = model_config
    raw = b'{"win_pct_differential": NaN, "point_diff_per_game_differential": 0}'
    with _client(config) as client:
        response = client.post(
            "/predict",
            content=raw,
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 422


def test_invalid_json_is_rejected(model_config):
    """A body that is not JSON is rejected."""
    config, _pipeline = model_config
    with _client(config) as client:
        response = client.post(
            "/predict",
            content=b"{",
            headers={"Content-Type": "application/json"},
        )
    assert response.status_code == 422


def test_health(model_config):
    """Health reports the status and the versions stored in the saved file."""
    config, _pipeline = model_config
    with _client(config) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model_version": "test-1",
        "scikit_learn_version": sklearn.__version__,
    }


def test_missing_model_file_stops_startup(tmp_path):
    """Start-up stops when the model file is not there."""
    config = {"model": {"output_path": str(tmp_path / "missing.joblib")}}
    with pytest.raises(RuntimeError, match="No saved model at") as caught:
        with _client(config):
            pass
    assert "python -m src.model.train" in str(caught.value)


def test_unreadable_model_file_stops_startup(tmp_path):
    """Start-up stops when the file is not a saved model."""
    path = tmp_path / "model.joblib"
    path.write_text("not a model", encoding="utf-8")
    config = {"model": {"output_path": str(path)}}
    with pytest.raises(RuntimeError, match="Could not read the saved model"):
        with _client(config):
            pass


def test_version_mismatch_stops_startup(model_config, tmp_path):
    """Start-up stops when the saved scikit-learn version is not the installed one."""
    config, _pipeline = model_config
    path = Path(config["model"]["output_path"])
    saved = joblib.load(path)
    saved["scikit_learn_version"] = "0.0.0"
    other = tmp_path / "other.joblib"
    joblib.dump(saved, other)
    mismatched = {"model": {"output_path": str(other)}}
    with pytest.raises(RuntimeError, match="0.0.0") as caught:
        with _client(mismatched):
            pass
    assert sklearn.__version__ in str(caught.value)


def test_wrong_feature_names_stop_startup(model_config, tmp_path):
    """Start-up stops when the saved input names are not the API fields."""
    config, _pipeline = model_config
    path = Path(config["model"]["output_path"])
    saved = joblib.load(path)
    saved["feature_names"] = ["x", "y"]
    other = tmp_path / "renamed.joblib"
    joblib.dump(saved, other)
    renamed = {"model": {"output_path": str(other)}}
    with pytest.raises(RuntimeError, match="do not match the API fields"):
        with _client(renamed):
            pass


def test_api_files_do_not_import_pandas():
    """The API files do not import pandas, mlflow, matplotlib, or the training code."""
    root = Path(__file__).resolve().parents[1]
    for relative in ("src/api/app.py", "src/api/schemas.py"):
        tree = ast.parse((root / relative).read_text(encoding="utf-8"))
        modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
        for name in modules:
            assert name not in {"pandas", "mlflow", "matplotlib"}
            assert not name.startswith("src.model")


@pytest.mark.skipif(not SAVED_MODEL.is_file(), reason="models/model.joblib is not on disk")
def test_real_model_worked_example():
    """The saved model answers the New England at Tennessee inputs with 0.3296."""
    with TestClient(create_app()) as client:
        response = client.post(
            "/predict",
            json={"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0},
        )
    assert response.status_code == 200
    assert response.json() == {
        "prediction": 0,
        "predicted_label": "away win",
        "home_win_probability": 0.3296,
        "model_version": "v1.0",
    }
