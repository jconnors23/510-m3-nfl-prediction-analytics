# The six commands used most often while working on this project. Run them from the project
# folder. PYTHON and NPM can be overridden, for example `make pytest PYTHON=python3.13`.
PYTHON ?= .venv/bin/python
NPM ?= npm

.PHONY: train pytest webtest start start-web docs

# Train the model and log the run to MLflow. Training then writes the readable copy of the run
# to mlflow-reference/latest-run/, so the committed reference always matches the newest run.
# MLFLOW_DISABLE_AGENT_HINT=1 hides a hint line MLflow prints that is not about this project.
train:
	MLFLOW_DISABLE_AGENT_HINT=1 $(PYTHON) -m src.model.train

# Run every Python test. They use made-up data and stand-ins, so they need no AWS account.
pytest:
	$(PYTHON) -m pytest

# Run the web app's tests. The two every-game checks are skipped unless their expected files
# exist in build/.
webtest:
	cd frontend && $(NPM) test

# Start the FastAPI prediction service at http://127.0.0.1:8000. Press Ctrl+C to stop it.
start:
	$(PYTHON) -m uvicorn src.api.app:app --port 8000

# Start the web app's dev server at http://localhost:5173. It forwards /predict and /health to
# the service started by `make start`. The port is fixed, because the live API's CORS list
# allows only this local address.
start-web:
	cd frontend && $(NPM) run dev

# Preview the docs site at http://127.0.0.1:8001, on its own port so it does not take the
# API's. mkdocs is not in the project's packages, so this uses the mkdocs installed on PATH.
docs:
	mkdocs serve -a 127.0.0.1:8001
