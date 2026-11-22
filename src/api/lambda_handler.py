"""The function AWS Lambda calls. It loads the saved model once, then hands each request to the API."""

from mangum import Mangum

from src.api.app import app, load_model
from src.config import load_config

# Kept for as long as this copy of the function lives, so later calls do not read the model
# file again. A new copy starts with this empty, so its first call is the one that loads the model.
_cached_handler = None


def build_handler(app, config):
    """Load the saved model once and wrap the API so Lambda can call it."""
    app.state.model = load_model(config)
    # Mangum would otherwise run the start-up step, and so read the model file, on every invocation.
    return Mangum(app, lifespan="off")


def handler(event, context):
    """Build the wrapped handler on the first call, then reuse it for later calls."""
    # The model is loaded here and not when the file is imported, so importing this file works on
    # a machine with no saved model (such as a test run). The Lambda handler setting for the
    # function is src.api.lambda_handler.handler.
    global _cached_handler
    if _cached_handler is None:
        _cached_handler = build_handler(app, load_config())
    return _cached_handler(event, context)
