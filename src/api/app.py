"""A local service that answers one prediction from the saved model.

The service has two routes: POST /predict and GET /health. The saved model is read once, when the
service starts, and every request after that is answered from memory. This file does not train
anything. It reads only config/config.yaml and the saved model file.

Run it with: python -m uvicorn src.api.app:app --port 8000
"""

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

# This file must not import pandas, or anything from src/model/, because features.py imports
# pandas. The Lambda zip only fits under its size limit without pandas.
from src.api.schemas import HealthResponse, PredictRequest, PredictResponse
from src.config import load_config, resolve_path

# The four entries in the saved file that the service reads. If one is missing, the file was not
# written by src/model/train.py, so the service stops at start-up instead of failing on a request.
_REQUIRED_KEYS = ("pipeline", "feature_names", "model_version", "scikit_learn_version")


def load_model(config: dict) -> dict:
    """Read the saved model once, and stop if it is missing or was built by another scikit-learn."""
    output_path = config["model"]["output_path"]
    path = resolve_path(output_path)
    # The messages show the path as written in config.yaml, which is shorter than the full path.
    if not path.is_file():
        raise RuntimeError(f"No saved model at {output_path}. Run python -m src.model.train first.")
    try:
        saved = joblib.load(path)
    except Exception as exc:
        # joblib can raise many kinds of error on a bad file, so any of them becomes one clear message.
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
    # A model saved by one scikit-learn version may fail to load, or answer differently, under
    # another. Stopping here tells the person exactly which version to install.
    saved_version = saved["scikit_learn_version"]
    installed = sklearn.__version__
    if saved_version != installed:
        raise RuntimeError(
            f"Saved model was built with scikit-learn {saved_version} but {installed} is installed. "
            f"Retrain with python -m src.model.train, or install scikit-learn=={saved_version}."
        )
    # The request fields are matched to the model's inputs by name. If the saved names are not
    # the two request fields, the numbers would go to the wrong inputs, so the service refuses to start.
    names = list(saved["feature_names"])
    if set(names) != set(PredictRequest.model_fields):
        raise RuntimeError(
            f"Could not read the saved model at {output_path}: input names {names} do not match the API fields."
        )
    return saved


def _json_safe(value):
    """Replace NaN and infinity so an error body can be sent as JSON."""
    # JSON has no way to write NaN or infinity, so they become text. Lists and dictionaries are
    # walked because the bad value sits inside the error's nested structure.
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else "Infinity"
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def label_for(probability: float) -> tuple[int, str]:
    """A probability above 0.5 is a home win, and exactly 0.5 is an away win."""
    # The same rule as scoring in src/model/evaluate.py, so the service and the reported
    # accuracy always pick the same team for the same probability.
    if probability > 0.5:
        return 1, "home win"
    return 0, "away win"


def create_app(config: dict | None = None) -> FastAPI:
    """Build the service so a test can point it at its own model file."""
    # Tests pass their own settings so they can use a made-up model in a temporary folder.
    # The command line path (uvicorn) passes nothing and reads config/config.yaml.
    if config is None:
        config = load_config()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Load the model when the service starts, so later requests reuse it."""
        # Loading here and not at import time keeps `import src.api.app` fast and file-free, and it
        # runs once each time the service starts. The routes read app.state.model.
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
        # Each value is looked up by name and placed in the order the model was trained with, so
        # the order of the fields in the JSON never matters. The scaler inside the pipeline
        # standardizes the numbers, so they are sent as they arrive.
        row = np.array([[getattr(request, name) for name in saved["feature_names"]]], dtype=float)
        # The scaler was fitted on a table with column names, and this call passes a plain array
        # so the service does not import pandas. The probability is the same either way.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"X does not have valid feature names",
                category=UserWarning,
            )
            # predict_proba gives two columns: the chance of an away win, then of a home win.
            # Index 1 keeps the home-win chance.
            probability = float(saved["pipeline"].predict_proba(row)[0, 1])
        # The pick uses the exact probability. Only the number shown to the caller is rounded.
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
        # Start-up has already checked that the saved scikit-learn version is the installed one,
        # so reporting the saved value is the same as reporting what is running.
        saved = app.state.model
        return HealthResponse(
            status="ok",
            model_version=saved["model_version"],
            scikit_learn_version=saved["scikit_learn_version"],
        )

    return app


# uvicorn runs this object (src.api.app:app). Phase 4 wraps the same object for AWS Lambda.
# Building it reads config.yaml but does not read the model file. That happens at start-up.
app = create_app()
