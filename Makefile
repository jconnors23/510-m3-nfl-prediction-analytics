# The nine commands used most often while working on this project. Run them from the project
# folder. PYTHON and NPM can be overridden, for example `make pytest PYTHON=python3.13`.
PYTHON ?= .venv/bin/python
NPM ?= npm

.PHONY: train pytest web-test start start-web start-web-ml docs docker-train docker-serve

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
web-test:
	cd frontend && $(NPM) test

# Start the FastAPI prediction service at http://127.0.0.1:8000. Press Ctrl+C to stop it.
start:
	$(PYTHON) -m uvicorn src.api.app:app --port 8000

# Start the web app's dev server at http://localhost:5173. It forwards /predict, /health, and
# /feedback to the service started by `make start`, which has no /feedback route, so the
# Feedback tab works only on the live site. The port is fixed, because the live API's CORS list
# allows only this local address.
start-web:
	cd frontend && $(NPM) run dev

# Start the MLflow screen at http://127.0.0.1:5001, showing every run in this computer's
# mlflow.db. Port 5001, because macOS Control Center often holds MLflow's default, 5000.
# mlflow.db is made by the first `make train`, so run that first. Press Ctrl+C to stop it.
start-web-ml:
	MLFLOW_DISABLE_AGENT_HINT=1 $(PYTHON) -m mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5001

# Preview the docs site at http://127.0.0.1:8001, on its own port so it does not take the
# API's. mkdocs is not in the project's packages, so this uses the mkdocs installed on PATH.
docs:
	mkdocs serve -a 127.0.0.1:8001

# Build the Docker train target and run one training inside it. The container's results/ is
# this computer's build/docker/results/, so the run summary it writes can be compared with
# results/run-summary.json. build/ is git-ignored. The container runs as user 10001. On Linux
# the mounted folder keeps this computer's permissions, so it has to be writable by that user.
docker-train:
	mkdir -p build/docker/results
	chmod a+rwx build/docker/results
	docker build --target train -t 510-m3-nfl-train .
	docker run --rm -v "$(CURDIR)/build/docker/results:/app/results" 510-m3-nfl-train

# Build the Docker serve target and start the API at http://127.0.0.1:8000. It uses the same
# port as `make start`, so stop one before starting the other. Press Ctrl+C to stop it.
docker-serve:
	docker build --target serve -t 510-m3-nfl-serve .
	docker run --rm -p 127.0.0.1:8000:8000 510-m3-nfl-serve
