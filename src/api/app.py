"""A local service that answers one prediction from the saved model."""

import math
import warnings
from contextlib import asynccontextmanager

import joblib
import numpy as np
import sklearn
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.schemas import HealthResponse, PredictRequest, PredictResponse
from src.config import load_config, resolve_path

_REQUIRED_KEYS = ("pipeline", "feature_names", "model_version", "scikit_learn_version")


def load_model(config: dict) -> dict:
    """Read the saved model once, and stop if it is missing or was built by another scikit-learn."""
    output_path = config["model"]["output_path"]
    path = resolve_path(output_path)
    if not path.is_file():
        raise RuntimeError(f"No saved model at {output_path}. Run python -m src.model.train first.")
    try:
        saved = joblib.load(path)
    except Exception as exc:
        raise RuntimeError(
            f"Could not read the saved model at {output_path}: {exc}. "
            "Run python -m src.model.train to rebuild it."
        ) from exc
    if not isinstance(saved, dict):
        raise RuntimeError(
            f"Could not read the saved model at {output_path}: saved object is not a dictionary. "
            "Run python -m src.model.train to rebuild it."
        )
    for name in _REQUIRED_KEYS:
        if name not in saved:
            raise RuntimeError(
                f"Could not read the saved model at {output_path}: missing key '{name}'. "
                "Run python -m src.model.train to rebuild it."
            )
    saved_version = saved["scikit_learn_version"]
    installed = sklearn.__version__
    if saved_version != installed:
        raise RuntimeError(
            f"Saved model was built with scikit-learn {saved_version} but {installed} is installed. "
            f"Retrain with python -m src.model.train, or install scikit-learn=={saved_version}."
        )
    names = list(saved["feature_names"])
    if set(names) != set(PredictRequest.model_fields):
        raise RuntimeError(
            f"Could not read the saved model at {output_path}: input names {names} do not match the API fields."
        )
    return saved


def _json_safe(value):
    """Replace NaN and infinity so an error body can be sent as JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else "Infinity"
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def label_for(probability: float) -> tuple[int, str]:
    """A probability above 0.5 is a home win, and exactly 0.5 is an away win."""
    if probability > 0.5:
        return 1, "home win"
    return 0, "away win"


def create_app(config: dict | None = None) -> FastAPI:
    """Build the service so a test can point it at its own model file."""
    if config is None:
        config = load_config()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Load the model when the service starts, so later requests reuse it."""
        app.state.model = load_model(config)
        yield

    app = FastAPI(
        title="NFL pre-game winner",
        description="Predict whether the home team wins from two pre-game numbers.",
        lifespan=lifespan,
    )

    @app.exception_handler(RequestValidationError)
    async def reject_invalid_request(_request: Request, exc: RequestValidationError) -> JSONResponse:
        """Send a 422 even when the rejected value is NaN, which JSON cannot carry."""
        # FastAPI puts the bad value in the error. A NaN there makes the 422 response fail to encode.
        return JSONResponse(status_code=422, content=_json_safe(jsonable_encoder({"detail": exc.errors()})))

    @app.post("/predict", response_model=PredictResponse, summary="Predict which team wins.")
    def predict(request: PredictRequest) -> PredictResponse:
        """Score one game from the two numbers, in the order saved with the model."""
        saved = app.state.model
        row = np.array([[getattr(request, name) for name in saved["feature_names"]]], dtype=float)
        # The scaler was fitted on a table with column names, and this call passes a plain array
        # so the service does not import pandas. The probability is the same either way.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"X does not have valid feature names",
                category=UserWarning,
            )
            probability = float(saved["pipeline"].predict_proba(row)[0, 1])
        prediction, predicted_label = label_for(probability)
        return PredictResponse(
            prediction=prediction,
            predicted_label=predicted_label,
            home_win_probability=round(probability, 4),
            model_version=saved["model_version"],
        )

    @app.get("/health", response_model=HealthResponse, summary="Report that the service is up.")
    def health() -> HealthResponse:
        """Read the version already loaded in memory, without calling the model."""
        saved = app.state.model
        return HealthResponse(
            status="ok",
            model_version=saved["model_version"],
            scikit_learn_version=saved["scikit_learn_version"],
        )

    return app


app = create_app()
