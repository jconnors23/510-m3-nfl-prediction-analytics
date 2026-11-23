# syntax=docker/dockerfile:1

# One image definition with two targets that share every install step:
#   docker build --target train -t 510-m3-nfl-train .   trains the model and logs the run
#   docker build --target serve -t 510-m3-nfl-serve .   serves the prediction API on port 8000
# Both use the same Python and the exact package pins in requirements.txt, so the container
# trains and answers the same way as the project on a laptop.

# The same minor version as the laptop and the Lambda function (3.13). The patch is pinned so
# a rebuild months later uses the same Python.
ARG PYTHON_VERSION=3.13.14

FROM python:${PYTHON_VERSION}-slim AS base

# No .pyc files in the image, log lines printed at once, no pip cache kept in the image, no pip
# upgrade notice, and no MLflow hint line that is not about this project.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MLFLOW_DISABLE_AGENT_HINT=1

# The code runs as an ordinary user, not root, so a problem in it cannot change the image's
# system files.
RUN useradd --create-home --uid 10001 app

WORKDIR /app
# Training writes models/, mlflow.db, and mlartifacts/ inside /app, so the user must own it.
RUN chown app:app /app

# The package list is copied and installed before the code, so a change to the code reuses
# this slow step from Docker's cache instead of installing every package again.
COPY requirements.txt .
RUN pip install -r requirements.txt

# .dockerignore decides which files arrive here.
COPY --chown=app:app . .

USER app

# Train: fit, score, save the model, and log one MLflow run, all inside the container. The
# files are deleted with the container (docker run --rm removes it when it stops), except in a
# folder mounted from this computer (make docker-train mounts one over results/).
FROM base AS train
CMD ["python", "-m", "src.model.train"]

# Serve: models/model.joblib is not committed, so the model is trained once while the image is
# built. The image then works from a fresh copy of the repository.
FROM base AS serve
RUN python -m src.model.train
EXPOSE 8000
# 0.0.0.0 lets Docker forward a port into the container. The run command publishes it only on
# 127.0.0.1, so only this computer can reach it.
CMD ["python", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
