---
hide:
  - toc
---

# Requirements Rubric

This page lists every requirement in the assignment brief, quoted word for word, and says where the project meets it. The headings follow the brief's own sections and order: the two Deliverables, Steps 1 to 9, and the Learning Goal that asks for a reflection on ethics and limitations. Each entry gives a status, the code that meets the requirement, the docs page that explains it, and the check that proves it, so a reviewer can walk the brief line by line and no requirement goes missing.

The brief itself is on [Assignment Brief](./assignment-brief.md). The longer wording of each requirement is on [Project Requirements](./project-requirements.md). Code links go to the repository on GitHub: `https://github.com/jconnors23/510-m3-nfl-prediction-analytics`. The other Learning Goals describe what the project teaches, and each is covered by the requirements below. The ethics goal asks for something specific in the project, so it is listed as a requirement of its own.

## Summary

The brief holds **48 requirements**, counting the ethics reflection from its Learning Goals. **All 48 are met.** Each one is checked off below and links to its entry.

**[Deliverable 1: GitHub Repository](#deliverable-1-github-repository)**

- [x] [All code for preprocessing, training, serving, and deployment](#all-code-for-preprocessing-training-serving-and-deployment)
- [x] [`config.yaml` for pipeline configuration](#configyaml-for-pipeline-configuration)
- [x] [`requirements.txt` or `environment.yaml`](#requirementstxt-or-environmentyaml)
- [x] [A Dockerfile that can run the full project](#a-dockerfile-that-can-run-the-full-project)
- [x] [How to train the model](#how-to-train-the-model)
- [x] [How to build and test the API locally](#how-to-build-and-test-the-api-locally)
- [x] [How to deploy to the cloud](#how-to-deploy-to-the-cloud)
- [x] [MLFlow or Weights & Biases logging](#mlflow-or-weights-biases-logging)
- [x] [Use of branches and pull requests (each group member must submit at least one PR)](#use-of-branches-and-pull-requests-each-group-member-must-submit-at-least-one-pr)
- [x] [A clear project structure and commit history](#a-clear-project-structure-and-commit-history)

**[Deliverable 2: Front-End Application](#deliverable-2-front-end-application)**

- [x] [Be publicly accessible and linked in the README](#be-publicly-accessible-and-linked-in-the-readme)
- [x] [Send requests to your deployed model API (e.g., using requests or fetch)](#send-requests-to-your-deployed-model-api-eg-using-requests-or-fetch)
- [x] [Display the model's predictions in an interactive, intuitive format](#display-the-models-predictions-in-an-interactive-intuitive-format)
- [x] [Be built with Streamlit, Gradio, NextJS, or a custom web framework](#be-built-with-streamlit-gradio-nextjs-or-a-custom-web-framework)

**[Step 1: Choose a Dataset and Define the Problem](#step-1-choose-a-dataset-and-define-the-problem)**

- [x] [Select a public dataset (e.g., Kaggle, UCI, HuggingFace Datasets).](#select-a-public-dataset-eg-kaggle-uci-huggingface-datasets)
- [x] [Define a supervised learning task (classification or regression).](#define-a-supervised-learning-task-classification-or-regression)
- [x] [Identify your target variable and evaluation metric.](#identify-your-target-variable-and-evaluation-metric)

**[Step 2: Set Up Data Storage in the Cloud](#step-2-set-up-data-storage-in-the-cloud)**

- [x] [Clean and preprocess the dataset locally.](#clean-and-preprocess-the-dataset-locally)
- [x] [Upload your cleaned data to a cloud storage service:](#upload-your-cleaned-data-to-a-cloud-storage-service)
- [x] [Write a script to access and download the data programmatically in your pipeline.](#write-a-script-to-access-and-download-the-data-programmatically-in-your-pipeline)

**[Step 3: Build a Reproducible ML Pipeline](#step-3-build-a-reproducible-ml-pipeline)**

- [x] [Choose a simple model (e.g., logistic regression, random forest, XGBoost).](#choose-a-simple-model-eg-logistic-regression-random-forest-xgboost)
- [x] [Data ingestion (from the cloud)](#data-ingestion-from-the-cloud)
- [x] [Preprocessing and feature engineering](#preprocessing-and-feature-engineering)
- [x] [Train/validation/test split](#trainvalidationtest-split)
- [x] [Model training and evaluation](#model-training-and-evaluation)
- [x] [Control parameters via a `config.yaml` file (e.g., learning rate, split ratio, etc.).](#control-parameters-via-a-configyaml-file-eg-learning-rate-split-ratio-etc)

**[Step 4: Track Experiments](#step-4-track-experiments)**

- [x] [Track experiment runs, model parameters, and evaluation metrics.](#track-experiment-runs-model-parameters-and-evaluation-metrics)
- [x] [Log artifacts (trained model, plots, etc.) for version control and reproducibility.](#log-artifacts-trained-model-plots-etc-for-version-control-and-reproducibility)

**[Step 5: Containerize with Docker](#step-5-containerize-with-docker)**

- [x] [Installs all dependencies.](#installs-all-dependencies)
- [x] [Includes entry points for training and serving.](#includes-entry-points-for-training-and-serving)
- [x] [Build and run your Docker image locally to test reproducibility.](#build-and-run-your-docker-image-locally-to-test-reproducibility)

**[Step 6: Serve Your Model as an API](#step-6-serve-your-model-as-an-api)**

- [x] [Load your trained model.](#load-your-trained-model)
- [x] [Create a `/predict` endpoint that accepts JSON input and returns a prediction.](#create-a-predict-endpoint-that-accepts-json-input-and-returns-a-prediction)
- [x] [Test your API locally using curl or Postman.](#test-your-api-locally-using-curl-or-postman)

**[Step 7: Deploy the API to the Cloud](#step-7-deploy-the-api-to-the-cloud)**

- [x] [Choose a cloud deployment platform:](#choose-a-cloud-deployment-platform)
- [x] [Package your API and deploy it so that the `/predict` endpoint is publicly accessible.](#package-your-api-and-deploy-it-so-that-the-predict-endpoint-is-publicly-accessible)
- [x] [Confirm your endpoint works using an HTTP request with test data.](#confirm-your-endpoint-works-using-an-http-request-with-test-data)

**[Step 8: Build the Front-End Interface](#step-8-build-the-front-end-interface)**

- [x] [Create a lightweight UI using Streamlit, Gradio, or a simple web app.](#create-a-lightweight-ui-using-streamlit-gradio-or-a-simple-web-app)
- [x] [Collect user input, send it to the deployed API using requests or fetch, and display the prediction.](#collect-user-input-send-it-to-the-deployed-api-using-requests-or-fetch-and-display-the-prediction)
- [x] [Host your app on Hugging Face Spaces, Streamlit Cloud, Vercel [all free!], or a custom deployment platform.](#host-your-app-on-hugging-face-spaces-streamlit-cloud-vercel-all-free-or-a-custom-deployment-platform)
- [x] [Include the link to the live front-end in your README.](#include-the-link-to-the-live-front-end-in-your-readme)

**[Step 9: Document Everything and Follow Best Practices](#step-9-document-everything-and-follow-best-practices)**

- [x] [Project overview and goals](#project-overview-and-goals)
- [x] [Dataset description and link](#dataset-description-and-link)
- [x] [Model architecture and evaluation](#model-architecture-and-evaluation)
- [x] [Cloud services used](#cloud-services-used)
- [x] [Setup and usage instructions](#setup-and-usage-instructions)
- [x] [Link to deployed API and front-end app](#link-to-deployed-api-and-front-end-app)

**[Learning Goal: Ethical Implications and Limitations](#learning-goal-ethical-implications-and-limitations)**

- [x] [Reflect on ethical implications and limitations of your ML application](#reflect-on-ethical-implications-and-limitations-of-your-ml-application)

- **Of the 48 met requirements, 12 depend on the README draft.** They are marked "Met (README draft, Phase 7)". They are met once the `README.md` in the repository root is committed. Its sections are written against the brief and linked from each entry.
- **Choices the brief offers, and what this project chose:**
    - **Cloud storage** (Google Cloud Storage, AWS S3, Firebase Storage, or cloud-hosted PostgreSQL): AWS S3.
    - **Experiment tracking** (MLflow or Weights & Biases): MLflow.
    - **API framework** (FastAPI or Flask): FastAPI.
    - **Cloud API platform** (Google Cloud Run or Cloud Functions, AWS Lambda with API Gateway, or Azure Functions): AWS Lambda with API Gateway, in `us-east-1`.
    - **Front-end** (Streamlit, Gradio, NextJS, or a custom web framework): a custom web app built with Vite, React, and TypeScript.
    - **Front-end host** (Hugging Face Spaces, Streamlit Cloud, Vercel, or a custom deployment platform): a custom deployment platform, a private S3 bucket served over HTTPS by CloudFront.

- **Current test counts:** **95 Python tests** pass with a trained model (**93 passed and 2 skipped** without one), and **62 web tests** pass (60 passed and 2 skipped without the files in `build/`). The 14 Python test files in `tests/` cover every module in `src/`. See [Makefile](../extras/makefile.md#make-pytest) for how each count comes about.

## Deliverable 1: GitHub Repository

### "All code for preprocessing, training, serving, and deployment"

- **Status:** Met
- **Where in the code:**
    - **Preprocessing:** the four steps in [`src/data/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/src/data) ([`fetch_raw.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/data/fetch_raw.py), [`clean.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/data/clean.py), [`upload_to_s3.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/data/upload_to_s3.py), [`download_from_s3.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/data/download_from_s3.py)), and [`src/model/features.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/features.py).
    - **Training:** [`src/model/train.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/train.py) and [`src/model/evaluate.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/evaluate.py).
    - **Serving:** [`src/api/app.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/api/app.py) and [`src/api/schemas.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/api/schemas.py).
    - **Deployment:** [`src/api/lambda_handler.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/api/lambda_handler.py), [`requirements-serve.txt`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/requirements-serve.txt), and the written AWS commands on the Phase 4 and Phase 5 Deployment Guides. The [`Dockerfile`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/Dockerfile) and the [`deploy-web-app.yml`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/.github/workflows/deploy-web-app.yml) workflow are deployment code too.
    - **Front-end:** [`frontend/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/frontend) (the web app) and [`src/profiles.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/profiles.py) (writes the team profiles file the web app reads).
- **Docs:** [Phase 1 Development Guide, Where Is Each Piece?](../phase-1/development-guide.md#where-is-each-piece), [Phase 2 Development Guide, Where Is Each Piece?](../phase-2/development-guide.md#where-is-each-piece), [Phase 3 Development Guide, Where Is Each Piece?](../phase-3/development-guide.md#where-is-each-piece), [Phase 4 Development Guide, Where Is Each Piece?](../phase-4/development-guide.md#where-is-each-piece), [Phase 5 Development Guide, Where Is Each Piece?](../phase-5/development-guide.md#where-is-each-piece), and the [Phase 4 Deployment Guide](../phase-4/deployment-guide.md) and [Phase 5 Deployment Guide](../phase-5/deployment-guide.md) for the deployment commands.
- **Evidence:** the file list above is the output of `git ls-files src`. The 14 test files in `tests/` cover every module in `src/`, and the Python tests pass:

```bash
make pytest
```

Result: 95 passed with a trained model, 93 passed and 2 skipped without one.

### "`config.yaml` for pipeline configuration"

- **Status:** Met
- **Where in the code:** [`config/config.yaml`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/config/config.yaml), read through `load_config` in [`src/config.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/config.py). The blocks are covered under Step 3, in the entry on controlling parameters.
- **Docs:** [Step 3: Add the Model and Tracking Settings](../phase-2/implementation-part-1.md#step-3-add-the-model-and-tracking-settings)
- **Evidence:** `git ls-files config` lists `config/config.yaml`. Training reads every setting from it, and `tests/test_train.py` checks the result.

### "`requirements.txt` or `environment.yaml`"

- **Status:** Met
- **Where in the code:** [`requirements.txt`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/requirements.txt), with every package pinned to an exact version. [`requirements-serve.txt`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/requirements-serve.txt) lists the smaller set of packages that go into the AWS Lambda zip.
- **Docs:** [Make Commands, What Must Be Set Up First?](../extras/makefile.md#what-must-be-set-up-first) and [Phase 4 Development Guide, How Do I Change a Package Version?](../phase-4/development-guide.md#how-do-i-change-a-package-version)
- **Evidence:** the Docker `base` stage installs this file with `pip install -r requirements.txt` and the build succeeds. The train container reproduces the run summary byte for byte (see Step 5).

### "A Dockerfile that can run the full project"

- **Status:** Met
- **Where in the code:** [`Dockerfile`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/Dockerfile) in the project folder, with a `train` target and a `serve` target. [`.dockerignore`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/.dockerignore) decides which files enter the image. The details are under Step 5.
- **Docs:** [How Is the Dockerfile Laid Out?](../phase-6/implementation.md#how-is-the-dockerfile-laid-out)
- **Evidence:** see [Step 5: Containerize with Docker](#step-5-containerize-with-docker). Both images build and run locally, and the tests pass inside both.

### "How to train the model"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** `main` in [`src/model/train.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/train.py), run by `make train` from the [`Makefile`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/Makefile).
- **Docs:** [How Do I Do a Training Run?](../phase-2/development-guide.md#how-do-i-do-a-training-run), [make train](../extras/makefile.md#make-train), and the README section [Setup and Usage](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#setup-and-usage).
- **Evidence:** a training run prints the scores and ends with `saved: mlflow-reference/latest-run`. Validation accuracy is 63.10% and test accuracy 59.06%.

```bash
make train
```

### "How to build and test the API locally"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** `create_app` in [`src/api/app.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/api/app.py), started by `make start` from the [`Makefile`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/Makefile). The tests are in [`tests/test_api.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_api.py).
- **Docs:** [Phase 3 Development Guide, How Do I Run It Locally?](../phase-3/development-guide.md#how-do-i-run-it-locally), [How Do I Ask for a Prediction?](../phase-3/development-guide.md#how-do-i-ask-for-a-prediction), [make start](../extras/makefile.md#make-start), and the README section [Setup and Usage](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#setup-and-usage).
- **Evidence:** after `make start`, the worked example returns a home win probability of 0.3296. The 17 tests in `tests/test_api.py` pass as part of `make pytest`.

```bash
make start
```

### "How to deploy to the cloud"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** the Lambda entry point [`src/api/lambda_handler.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/api/lambda_handler.py), the package list [`requirements-serve.txt`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/requirements-serve.txt), and the workflow [`.github/workflows/deploy-web-app.yml`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/.github/workflows/deploy-web-app.yml) that redeploys the web app.
- **Docs:** [Phase 4 Deployment Guide](../phase-4/deployment-guide.md) (the API), [Phase 5 Deployment Guide](../phase-5/deployment-guide.md) (the web app), [Phase 4 Implementation](../phase-4/implementation.md), and the README section [Cloud Services](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#cloud-services).
- **Evidence:** the deployed API answers at the public address given under Step 7, and the live web app answers at the address given under Step 8.

### "MLFlow or Weights & Biases logging"

- **Status:** Met
- **Where in the code:** `log_run` in [`src/model/train.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/train.py), called by `main` in the same file. `python -m src.model.train` therefore logs a run by itself, and then writes the readable copy in [`mlflow-reference/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/mlflow-reference). This project chose MLflow. The details are under Step 4.
- **Docs:** [Step 6: Record the Run in MLflow](../phase-2/implementation-part-2.md#step-6-record-the-run-in-mlflow)
- **Evidence:** every training run adds a run folder to [`mlflow-reference/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/mlflow-reference). The page [`mlflow-logging-reference.md`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/mlflow-reference/mlflow-logging-reference.md) explains the log, and `run-history.md` there lists every run.

### "Use of branches and pull requests (each group member must submit at least one PR)"

- **Status:** Met
- **Where in the code:** not code. The record is in git and on GitHub. This is a one-person project, so the only group member is the repository owner, who submitted all seven pull requests. Pull requests #1 (`phase_one`), #2 (`phase-two`), #3 (`phase-three`), #4 (`phase-four`), #5 (`phase-five`), #6 (`phase-five-p2`), and #7 (`phase-six`) are merged into `main`. They show on the [Pull requests tab](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/pulls?q=is%3Apr+is%3Amerged) of the repository.
- **Docs:** [Phase 7 Brief, Step 6: Pre-Commit Checks and the Final Pull Request](../phase-7/brief.md#step-6-pre-commit-checks-and-the-final-pull-request)
- **Evidence:** the merge commits are listed by this read-only command. It prints seven lines, for pull requests #7 down to #1:

```bash
git log --merges --format='%h %s' main
```

### "A clear project structure and commit history"

- **Status:** Met
- **Where in the code:**
    - **Layout:** [`src/data/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/src/data) (Phase 1 steps), [`src/model/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/src/model) (Phase 2 code), [`src/api/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/src/api) (Phases 3 and 4 code), [`src/profiles.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/profiles.py), [`src/season.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/season.py), and [`frontend/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/frontend) (Phase 5), [`Dockerfile`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/Dockerfile) and [`.dockerignore`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/.dockerignore) (Phase 6), [`Makefile`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/Makefile) and [`.github/workflows/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/.github/workflows) (the [make commands](../extras/makefile.md) and the [three workflows](../extras/github-workflows.md): the Python tests, the docs site, and the web app), [`results/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/results) (the committed run summary), [`mlflow-reference/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/mlflow-reference) (the committed log of every training run), [`src/config.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/config.py) (reads the settings), [`tests/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/tests) (14 test files, which together cover every module in `src/`), [`config/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/config) (settings), and [`docs/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/docs) (these pages).
    - **Workflows:** three GitHub workflows run in [`.github/workflows/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/.github/workflows): `test-python.yml`, `deploy-docs.yml`, and `deploy-web-app.yml`.
    - **Make commands:** the [`Makefile`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/Makefile) has nine commands, each explained on [Makefile](../extras/makefile.md).
    - **Tests:** `pytest` runs all of `tests/`. They use made-up data and a stand-in S3 client, so they need no internet and no AWS account.
- **Docs:** [Makefile](../extras/makefile.md), [GitHub Workflows](../extras/github-workflows.md), and [Design Manifest](../design-manifest.md)
- **Evidence:** the layout above is the output of `git ls-files`. The history is seven phase branches, each merged by a numbered pull request (see the previous entry). The tests pass:

```bash
make pytest
```

Result: 95 passed (93 passed and 2 skipped without a model). The web tests pass too, with 62 passed:

```bash
make web-test
```

## Deliverable 2: Front-End Application

### "Be publicly accessible and linked in the README"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** the live web app is at `https://d1nubiunzfwm0q.cloudfront.net`. The README section [Live Links](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#live-links) carries the link. The hosting is under Step 8.
- **Docs:** [How Is the Page Hosted?](../phase-5/implementation-part-1.md#how-is-the-page-hosted) and the README section [Live Links](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#live-links)
- **Evidence:** the address opens in a browser with no sign-in. Direct requests to the S3 bucket behind it get status 403, so CloudFront is the only public path. See the checks under Step 8.

### "Send requests to your deployed model API (e.g., using requests or fetch)"

- **Status:** Met
- **Where in the code:** the `fetch` call to `POST /predict` in [`frontend/src/api.ts`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/api.ts). The address it calls is set in [`frontend/src/config.ts`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/config.ts). The deployed API is `https://9awodatqc5.execute-api.us-east-1.amazonaws.com`.
- **Docs:** [What Does the Browser Send?](../phase-5/implementation-part-1.md#what-does-the-browser-send) and [The Preflight](../phase-5/implementation-part-1.md#the-preflight)
- **Evidence:** all 992 ordered pairs of teams and all 272 games of the 2026 season were sent to the live API, and every pick and probability equals the local model's. The app tests in `frontend/src/api.test.ts` run under `make web-test`.

### "Display the model's predictions in an interactive, intuitive format"

- **Status:** Met
- **Where in the code:** [`frontend/src/App.tsx`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/App.tsx) (two team lists, the button, the result, and the failure messages), [`frontend/src/Picker.tsx`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/Picker.tsx), and [`frontend/src/matchup.ts`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/matchup.ts) (the two inputs and the chances).
- **Docs:** [How Is the Answer Shown?](../phase-5/implementation-part-1.md#how-is-the-answer-shown) and [What Does Each Tab Do?](../phase-5/implementation-part-2.md#what-does-each-tab-do)
- **Evidence:** each team's record shows under its list, a bar splits the two chances, there is a light and a dark theme, and the text and graphics pass the WCAG contrast minimums in both. The 62 app tests pass.

### "Be built with Streamlit, Gradio, NextJS, or a custom web framework"

- **Status:** Met
- **Where in the code:** a custom web app. It is a React and TypeScript app built with Vite, in [`frontend/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/frontend). The settings are in [`frontend/package.json`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/package.json) and [`frontend/vite.config.ts`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/vite.config.ts). It is not Streamlit or Gradio.
- **Docs:** [Phase 5 Development Guide](../phase-5/development-guide.md) and [Which Choices Were Made?](../phase-5/brief.md#decisions-made)
- **Evidence:** `npm run build` runs the type check and `vite build` into `frontend/dist/`, run from inside `frontend/`:

```bash
npm run build
```

## Step 1: Choose a Dataset and Define the Problem

### "Select a public dataset (e.g., Kaggle, UCI, HuggingFace Datasets)."

- **Status:** Met
- **Where in the code:** the nflverse `games.csv` file, one row per NFL game since 1999. The address is `data.source_url` in [`config/config.yaml`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/config/config.yaml). `fetch_raw` in [`src/data/fetch_raw.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/data/fetch_raw.py) downloads it and saves it as `data/raw/games.csv`.
- **Docs:** [What Is the Source Data?](../phase-1/implementation.md#what-is-the-source-data)
- **Evidence:** the dataset is public, and the fetch step needs no sign-in. The README section [Dataset](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#dataset) gives the link.

### "Define a supervised learning task (classification or regression)."

- **Status:** Met
- **Where in the code:** binary classification. The question is whether the home team won. The answer is the `home_win` column built by `build_model_table` in [`src/model/features.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/features.py).
- **Docs:** [What Is the Prediction Task?](../phase-1/implementation.md#what-is-the-prediction-task) and [Why Binary Classification and Not Regression?](../design-manifest.md#why-binary-classification-and-not-regression)
- **Evidence:** `home_win` holds only 1 and 0, and `check_model_table` in the same file checks the table before training.

### "Identify your target variable and evaluation metric."

- **Status:** Met
- **Where in the code:**
    - **Target:** `home_win` (1 if the home team won, 0 if not), listed in `MODEL_COLUMNS` in [`src/model/features.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/features.py).
    - **Metric:** accuracy, next to the always-pick-home baseline. It is computed by `score_group` in [`src/model/evaluate.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/evaluate.py). Log loss is a second score that checks the win percentages.
- **Docs:** [What Is Accuracy?](../phase-2/implementation-part-2.md#what-is-accuracy) and [Why Accuracy With a Baseline, and Log Loss as a Check?](../design-manifest.md#why-accuracy-with-a-baseline-and-log-loss-as-a-check)
- **Evidence:** validation accuracy is **63.10%** (171 of 271 games) against an always-home baseline of 53.87%. Test accuracy is **59.06%** (88 of 149) against 47.65%. The numbers are in [`results/run-summary.json`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/results/run-summary.json).

## Step 2: Set Up Data Storage in the Cloud

### "Clean and preprocess the dataset locally."

- **Status:** Met
- **Where in the code:** `clean_games` in [`src/data/clean.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/data/clean.py), run with `python -m src.data.clean`. It writes `data/processed/nfl_matchups_2020_2026.csv`.
- **Docs:** [Step 2: Clean the Raw Data](../phase-1/implementation.md#step-2-clean-the-raw-data-and-save-the-cleaned-table)
- **Evidence:** the cleaning tests are in [`tests/test_clean.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_clean.py) and run under `make pytest`.

```bash
python -m src.data.clean
```

### "Upload your cleaned data to a cloud storage service:"

- **Status:** Met
- **Where in the code:** this project chose **AWS S3**. It did not use Google Cloud Storage, Firebase Storage, or cloud-hosted PostgreSQL. `upload` in [`src/data/upload_to_s3.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/data/upload_to_s3.py), run with `python -m src.data.upload_to_s3`. The bucket name and file name are `data.s3_bucket` and `data.s3_key` in [`config/config.yaml`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/config/config.yaml).
    - **The bucket itself:** `510-m3-nfl-dataset` in `us-east-1`. It was created manually in the AWS console, so no file in the repository creates it.
- **Docs:** [Step 3: Upload the Cleaned Table to S3](../phase-1/implementation.md#step-3-upload-the-cleaned-table-to-s3), [How Is the Cloud Storage Set Up?](../phase-1/development-guide.md#how-is-the-cloud-storage-set-up), and the README section [Cloud Services](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#cloud-services)
- **Evidence:** the upload step is tested with a stand-in S3 client in [`tests/test_upload.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_upload.py). Run against the real bucket:

```bash
python -m src.data.upload_to_s3
```

### "Write a script to access and download the data programmatically in your pipeline."

- **Status:** Met
- **Where in the code:** `download` in [`src/data/download_from_s3.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/data/download_from_s3.py), run with `python -m src.data.download_from_s3`. It saves `data/from-s3/nfl_matchups_2020_2026.csv`.
    - **Starting from the S3 copy:** `load_games` in [`src/model/features.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/features.py) reads only that downloaded file, never the local cleaned table.
- **Docs:** [Step 4: Download the Cleaned Table From S3](../phase-1/implementation.md#step-4-download-the-cleaned-table-from-s3-and-save-it)
- **Evidence:** the download step is tested in [`tests/test_download_from_s3.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_download_from_s3.py). Run against the real bucket:

```bash
python -m src.data.download_from_s3
```

## Step 3: Build a Reproducible ML Pipeline

The brief adds a note under this step, which is not a requirement: "NOTE: We are not assessing your ML model. Your model could have terrible accuracy. That is fine! Not the point of the assignment, don't get hung up on your model." The requirement is a clean, repeatable process, and the evidence for it is under the entry on `config.yaml` below.

### "Choose a simple model (e.g., logistic regression, random forest, XGBoost)."

- **Status:** Met
- **Where in the code:** logistic regression behind a standardizing step, kept together as one pipeline. `build_pipeline` and `fit_pipeline` in [`src/model/train.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/train.py).
- **Docs:** [Step 4: Fit the Scaler and the Model](../phase-2/implementation-part-2.md#step-4-fit-the-scaler-and-the-model)
- **Evidence:** the model settings are `model.*` in [`config/config.yaml`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/config/config.yaml), and `tests/test_train.py` fits it.

### "Data ingestion (from the cloud)"

- **Status:** Met
- **Where in the code:** [`src/data/download_from_s3.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/data/download_from_s3.py), then `load_games` in [`src/model/features.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/features.py).
- **Docs:** [Step 4: Download the Cleaned Table From S3](../phase-1/implementation.md#step-4-download-the-cleaned-table-from-s3-and-save-it)
- **Evidence:** `load_games` reads only `data/from-s3/nfl_matchups_2020_2026.csv`. The pipeline order is: the data steps are separate commands (fetch, clean, upload, download). `python -m src.model.train` then runs the rest in order: load the downloaded table, build the inputs, split, fit, score, save, and log.

### "Preprocessing and feature engineering"

- **Status:** Met
- **Where in the code:** preprocessing is [`src/data/clean.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/data/clean.py). Feature engineering is `standings_before_week` and `build_model_table` in [`src/model/features.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/features.py).
- **Docs:** [Step 1: Feature Engineering](../phase-2/implementation-part-1.md#step-1-feature-engineering)
- **Evidence:** the tests are in [`tests/test_features.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_features.py) and [`tests/test_clean.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_clean.py).

### "Train/validation/test split"

- **Status:** Met
- **Where in the code:** `split_games` in [`src/model/features.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/features.py), with `split_seasons` in [`src/config.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/config.py). The split is by season, set by the `split` block in [`config/config.yaml`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/config/config.yaml).
- **Docs:** [Step 2: Split the Games by Season](../phase-2/implementation-part-1.md#step-2-split-the-games-by-season)
- **Evidence:** [`tests/test_split.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_split.py) checks the split. The run summary records 271 validation games and 149 test games.

### "Model training and evaluation"

- **Status:** Met
- **Where in the code:** training is `fit_pipeline` in [`src/model/train.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/train.py). Evaluation is `score_group` and `plot_confusion_matrix` in [`src/model/evaluate.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/evaluate.py).
- **Docs:** [Step 5: Score the Model](../phase-2/implementation-part-2.md#step-5-score-the-model)
- **Evidence:** a training run prints validation accuracy 63.10% and test accuracy 59.06%. [`tests/test_evaluate.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_evaluate.py) and [`tests/test_train.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_train.py) cover this step.

### "Control parameters via a `config.yaml` file (e.g., learning rate, split ratio, etc.)."

- **Status:** Met
- **Where in the code:** [`config/config.yaml`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/config/config.yaml), read through [`src/config.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/config.py). Changing a run means editing that file, not the code. Its blocks are:
    - `data`: paths, bucket, and region.
    - `window`: first and last season, and the last scored week.
    - `split`: last training season and the validation season.
    - `model`: version, seed, output file, and the logistic regression settings.
    - `tracking`: MLflow names and folders.
    - `frontend`: where the web app's team profiles file and season file are written.
    - **Two things live in code, not in the file:** the 0.5 cutoff that turns a probability into a pick, and the list of columns that cleaning keeps.
- **Docs:** [Step 3: Add the Model and Tracking Settings](../phase-2/implementation-part-1.md#step-3-add-the-model-and-tracking-settings), [How Do I Change a Model Setting?](../phase-2/development-guide.md#how-do-i-change-a-model-setting), and [How Do I Change the Split?](../phase-2/development-guide.md#how-do-i-change-the-split)
- **Evidence:** two runs with the same settings give identical scores. `test_same_settings_give_the_same_probabilities` in [`tests/test_train.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_train.py) checks it. [`results/run-summary.json`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/results/run-summary.json) is byte for byte the same on every run with the same settings and data. See [What Makes a Rerun Give the Same Result?](../phase-2/development-guide.md#what-makes-a-rerun-give-the-same-result).

## Step 4: Track Experiments

The brief says "Use MLFlow or Weights & Biases to:". This project chose **MLflow**. Its settings are the `tracking` block in [`config/config.yaml`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/config/config.yaml).

### "Track experiment runs, model parameters, and evaluation metrics."

- **Status:** Met
- **Where in the code:** `log_run` in [`src/model/train.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/train.py).
    - **Parameters (15):** `model_version`, `random_seed`, `C`, `solver`, `max_iter`, `feature_names`, `train_start_season`, `train_end_season`, `validation_season`, `test_season`, `n_train`, `n_validation`, `n_test`, `scikit_learn_version`, and `data_sha256` (a fingerprint of the downloaded table, from `file_fingerprint` in the same file).
    - **Metrics (8):** `train_accuracy`, `validation_accuracy`, `test_accuracy`, `validation_log_loss`, `test_log_loss`, `baseline_train`, `baseline_validation`, `baseline_test`.
    - **Automatic tags:** MLflow also records the git commit, branch, and repository address of each run.
- **Docs:** [What Is Logged for Each Run?](../phase-2/implementation-part-2.md#what-is-logged-for-each-run)
- **Evidence:** each run's 15 parameters and 8 metrics are written to [`mlflow-reference/latest-run/params.json`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/mlflow-reference/latest-run/params.json) and [`metrics.json`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/mlflow-reference/latest-run/metrics.json). The readable log is explained on [`mlflow-logging-reference.md`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/mlflow-reference/mlflow-logging-reference.md).

### "Log artifacts (trained model, plots, etc.) for version control and reproducibility."

- **Status:** Met
- **Where in the code:** `log_run` in [`src/model/train.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/train.py).
    - **Files stored with each run (3):** `model/model.joblib` (the trained model), `plots/confusion_matrix_validation.png` (the one plot), and `config/config.yaml` (a copy of the settings used).
    - **The plot** is drawn by `plot_confusion_matrix` in [`src/model/evaluate.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/evaluate.py).
    - **A second copy of the model, in MLflow's own format:** each run also has one logged model, `pipeline-mlflow-format`, stored under `mlartifacts/models/`. `model/model.joblib` stays the working copy that the API loads.
    - **A readable record outside MLflow:** `results/run-summary.json`, written by `write_run_summary` in the same file. It holds the settings, the data fingerprint, the scores, and the learned weights, and it is committed to git.
- **Docs:** [Why Is the Model Stored Twice?](../phase-2/implementation-part-2.md#why-is-the-model-stored-twice), [What Is the Run Summary File?](../phase-2/implementation-part-2.md#what-is-the-run-summary-file), and [What Does the Confusion Matrix Show?](../phase-2/implementation-part-2.md#what-does-the-confusion-matrix-show)
- **Evidence:** where to find the recorded runs:
    - **In the repository:** [`results/run-summary.json`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/results/run-summary.json) shows the latest run's settings, scores, and learned weights without MLflow.
    - **In the repository:** [`mlflow-reference/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/mlflow-reference), written by `python -m src.model.export_mlflow` ([`src/model/export_mlflow.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/model/export_mlflow.py)), which training calls. It is a log of every training run: each run's id, git commit, 15 parameters, 8 metrics, config copy and plot, and the logged model's text files, with `run-history.md` listing every run and pictures of the MLflow screen. Its page is [`mlflow-logging-reference.md`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/mlflow-reference/mlflow-logging-reference.md).
    - **On this computer only:** the run record `mlflow.db` in the project folder and the run files in `mlartifacts/`. Both are created by training and are not committed, because they store absolute paths on one computer. The saved model file `models/model.joblib` is also not committed.
    - **To browse them:** run `make start-web-ml` and open `http://127.0.0.1:5001`.

```bash
make start-web-ml
```

## Step 5: Containerize with Docker

### "Installs all dependencies."

- **Status:** Met
- **Where in the code:** [`Dockerfile`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/Dockerfile). Its `base` stage installs `requirements.txt` on `python:3.13.14-slim`. [`.dockerignore`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/.dockerignore) decides which files enter the image.
- **Docs:** [How Is the Dockerfile Laid Out?](../phase-6/implementation.md#how-is-the-dockerfile-laid-out) and [What Goes Into the Image?](../phase-6/implementation.md#what-goes-into-the-image)
- **Evidence:** the image builds from the project folder alone, with no virtual environment and no AWS account, and the tests pass inside it.

### "Includes entry points for training and serving."

- **Status:** Met
- **Where in the code:** the `train` target's command is `python -m src.model.train`, and the `serve` target's command is `python -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000`. Both are in the [`Dockerfile`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/Dockerfile). Run them with `make docker-train` and `make docker-serve`.
- **Docs:** [What Does Each Target Do?](../phase-6/brief.md#what-does-each-target-do), [make docker-train](../extras/makefile.md#make-docker-train), and [make docker-serve](../extras/makefile.md#make-docker-serve)
- **Evidence:** both commands run on a computer with Docker Desktop:

```bash
make docker-train
```

```bash
make docker-serve
```

### "Build and run your Docker image locally to test reproducibility."

- **Status:** Met
- **Where in the code:** the `docker-train` and `docker-serve` commands in the [`Makefile`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/Makefile).
- **Docs:** [Phase 6 Implementation, What Was Checked?](../phase-6/implementation.md#what-was-checked) and the [Phase 6 Development Guide](../phase-6/development-guide.md)
- **Evidence:** the train container's run summary is byte for byte `results/run-summary.json`. The serve container answers the worked example with 0.3296, like the local API. The tests pass inside both images: 93 passed and 2 skipped in the train image, and 95 passed in the serve image. The serve image trains its own model during the build, so it needs no file from outside the image. See [Check That It Matches the Project](../phase-6/development-guide.md#check-that-it-matches-the-project).

## Step 6: Serve Your Model as an API

### "Load your trained model."

- **Status:** Met
- **Where in the code:** FastAPI is the framework. The app, the start-up step that loads the saved model once, and the 0.5 pick rule are in [`src/api/app.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/api/app.py) (`create_app`, `load_model`, `label_for`).
- **Docs:** [How Does the Service Work?](../phase-3/implementation.md#how-does-the-service-work) and [Step 1: Load the Saved Model at Start-Up](../phase-3/implementation.md#step-1-load-the-saved-model-at-start-up)
- **Evidence:** without `models/model.joblib` the service stops at start-up with "No saved model at models/model.joblib. Run python -m src.model.train first." The tests are in [`tests/test_api.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_api.py).

### "Create a `/predict` endpoint that accepts JSON input and returns a prediction."

- **Status:** Met
- **Where in the code:** `POST /predict` in [`src/api/app.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/api/app.py), with the request and response shapes in [`src/api/schemas.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/api/schemas.py). The request holds `win_pct_differential` and `point_diff_per_game_differential`. The response holds `prediction`, `predicted_label`, `home_win_probability`, and `model_version`.
- **Docs:** [What Is in the Response?](../phase-3/development-guide.md#what-is-in-the-response) and [Step 3: Add the `POST /predict` Route](../phase-3/implementation.md#step-3-add-the-post-predict-route)
- **Evidence:** the worked example `{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}` returns a home win probability of 0.3296.

### "Test your API locally using curl or Postman."

- **Status:** Met
- **Where in the code:** start it with `make start`, which runs `python -m uvicorn src.api.app:app --port 8000`. Then send requests with `curl` or open the test page at `/docs`. The tests are in [`tests/test_api.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_api.py).
- **Docs:** [How Do I Run It Locally?](../phase-3/development-guide.md#how-do-i-run-it-locally), [How Do I Ask for a Prediction?](../phase-3/development-guide.md#how-do-i-ask-for-a-prediction), and [How Can I Try It in a Browser?](../phase-3/development-guide.md#how-can-i-try-it-in-a-browser)
- **Evidence:** 17 tests in `tests/test_api.py` cover both routes, the input checks, and the start-up checks, and all pass under `make pytest`. A manual request:

```bash
curl -X POST http://127.0.0.1:8000/predict -H "Content-Type: application/json" -d '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}'
```

## Step 7: Deploy the API to the Cloud

### "Choose a cloud deployment platform:"

- **Status:** Met
- **Where in the code:** this project chose **AWS Lambda with API Gateway**, both in `us-east-1`. It did not use Google Cloud Run, Cloud Functions, or Azure Functions. The Lambda function is `510-m3-nfl-predict-api` (entry point [`src/api/lambda_handler.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/api/lambda_handler.py), packages listed in [`requirements-serve.txt`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/requirements-serve.txt)), behind the HTTP API `510-m3-nfl-predict-http-api`.
- **Docs:** [Phase 4 Implementation](../phase-4/implementation.md), [What Was Deployed?](../phase-4/implementation.md#what-was-deployed), the [Phase 4 Deployment Guide](../phase-4/deployment-guide.md), and the README section [Cloud Services](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#cloud-services)
- **Evidence:** the Lambda entry point is tested without AWS in [`tests/test_lambda_handler.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/tests/test_lambda_handler.py) ([Step 2: Test the Entry Point With No AWS](../phase-4/implementation.md#step-2-test-the-entry-point-with-no-aws)). The deployed API answers at the address under the next entry.

### "Package your API and deploy it so that the `/predict` endpoint is publicly accessible."

- **Status:** Met
- **Where in the code:** the zip is built by the steps on the Phase 4 Deployment Guide, and the entry point is `src/api/lambda_handler.py` (see the previous entry). The public address is `https://9awodatqc5.execute-api.us-east-1.amazonaws.com`.
    - **CORS:** it is set on API Gateway, not in the app, so the browser-based front-end can call `/predict`. It allows two origins, the live page `https://d1nubiunzfwm0q.cloudfront.net` and the local dev server `http://localhost:5173`, with the methods `POST`, `GET`, and `OPTIONS`, and the header `content-type`. Other origins get no CORS headers.
- **Docs:** [Step 7: Create the API Gateway HTTP API](../phase-4/implementation.md#step-7-create-the-api-gateway-http-api), [Step 8: Set CORS on the Gateway](../phase-4/implementation.md#step-8-set-cors-on-the-gateway), [The Preflight](../phase-5/implementation-part-1.md#the-preflight), and [Create the HTTP API](../phase-4/deployment-guide.md#create-the-http-api)
- **Evidence:** the address answers a request with no sign-in (see the next entry). The CORS list is checked by the preflight request in [Step 9: Check the Public Address](../phase-4/implementation.md#step-9-check-the-public-address).

### "Confirm your endpoint works using an HTTP request with test data."

- **Status:** Met
- **Where in the code:** the deployed `POST /predict` at `https://9awodatqc5.execute-api.us-east-1.amazonaws.com`.
- **Docs:** [Step 9: Check the Public Address](../phase-4/implementation.md#step-9-check-the-public-address) and [Step 10: Check the Deployed Model Against the Local Model](../phase-4/implementation.md#step-10-check-the-deployed-model-against-the-local-model)
- **Evidence:** a `POST /predict` with the inputs -0.5 and -18.0 returns `{"prediction": 0, "predicted_label": "away win", "home_win_probability": 0.3296, "model_version": "v1.0"}`:

```bash
curl -X POST https://9awodatqc5.execute-api.us-east-1.amazonaws.com/predict -H "Content-Type: application/json" -d '{"win_pct_differential": -0.5, "point_diff_per_game_differential": -18.0}'
```

Checked on every game: all 1,759 games sent through the public address gave the same pick and probability as the local model.

## Step 8: Build the Front-End Interface

### "Create a lightweight UI using Streamlit, Gradio, or a simple web app."

- **Status:** Met
- **Where in the code:** a simple web app built with Vite, using the dev server for local work and `vite build` for the published files. It is the React and TypeScript app in [`frontend/`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/frontend). `npm run dev` starts the dev server on port 5173, and `npm run build` runs the type check and `vite build` into `frontend/dist/`. It is not Streamlit or Gradio.
- **Docs:** [Phase 5 Development Guide](../phase-5/development-guide.md) and [How Do I Run It Locally?](../phase-5/development-guide.md#how-do-i-run-it-locally)
- **Evidence:** `make start-web` opens the dev server at `http://localhost:5173`, and `make web-test` runs 62 tests that pass.

```bash
make web-test
```

### "Collect user input, send it to the deployed API using requests or fetch, and display the prediction."

- **Status:** Met
- **Where in the code:** [`frontend/src/App.tsx`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/App.tsx) (two team lists, the Predict button, the result, and the failure messages), [`frontend/src/matchup.ts`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/matchup.ts) (the two inputs and the chances), and [`frontend/src/api.ts`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/api.ts) (the `fetch` call to `POST /predict`). The standings come from [`frontend/src/data/team-profiles.json`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/frontend/src/data/team-profiles.json), written by `python -m src.profiles` ([`src/profiles.py`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/src/profiles.py)).
- **Docs:** [Phase 5 Implementation, Part 1](../phase-5/implementation-part-1.md) and [Phase 5 Implementation, Part 2](../phase-5/implementation-part-2.md)
- **Evidence:** 62 app tests pass. All 992 ordered pairs of teams, and all 272 games of the 2026 season, were sent to the live API, with every pick and probability equal to the local model. The page is readable and interactive: each team's record under its list, a bar split between the two chances, a light and a dark theme, and text and graphics that pass the WCAG contrast minimums in both.

### "Host your app on Hugging Face Spaces, Streamlit Cloud, Vercel [all free!], or a custom deployment platform."

- **Status:** Met
- **Where in the code:** this project chose **a custom deployment platform**, not Hugging Face Spaces, Streamlit Cloud, or Vercel. The built files sit in a private S3 bucket served over HTTPS through CloudFront. The bucket is `510-m3-nfl-web-app` and the CloudFront distribution is at `https://d1nubiunzfwm0q.cloudfront.net`, with the origin access control `510-m3-nfl-web-app-oac`, all in `us-east-1`. It is redeployed by [`.github/workflows/deploy-web-app.yml`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/.github/workflows/deploy-web-app.yml), on a change under `frontend/` on `main`.
- **Docs:** [How Is the Page Hosted?](../phase-5/implementation-part-1.md#how-is-the-page-hosted), [How Does a Change Reach the Live Web App?](../extras/github-workflows.md#how-does-a-change-reach-the-live-web-app), and the [Phase 5 Deployment Guide](../phase-5/deployment-guide.md)
- **Evidence:** the served files are byte for byte the tested build, and direct requests to the bucket get status 403.

### "Include the link to the live front-end in your README."

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** the README section [Live Links](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#live-links) in `README.md` in the repository root. It gives the live web app, `https://d1nubiunzfwm0q.cloudfront.net`, and the live API, `https://9awodatqc5.execute-api.us-east-1.amazonaws.com`.
- **Docs:** [Phase 7 Brief, Step 1: Write the README](../phase-7/brief.md#step-1-write-the-readme)
- **Evidence:** the link is in the README once the draft is committed. Check it by reading the "Live Links" section.

## Step 9: Document Everything and Follow Best Practices

The README is `README.md` in the repository root. Its sections are "Project Overview and Goals", "Dataset", "Model and Evaluation", "Cloud Services", "Setup and Usage", "Live Links", and "Limitations and Ethics". Each of the six entries below links to the section that meets it. The README links to these docs for detail instead of repeating them.

### "Project overview and goals"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** the README section [Project Overview and Goals](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#project-overview-and-goals).
- **Docs:** [Phase 7 Brief, Step 1: Write the README](../phase-7/brief.md#step-1-write-the-readme)
- **Evidence:** the section states what the project predicts, who it is for, and that it is a coursework project not affiliated with the National Football League.

### "Dataset description and link"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** the README section [Dataset](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#dataset).
- **Docs:** [What Is the Source Data?](../phase-1/implementation.md#what-is-the-source-data)
- **Evidence:** the section links the nflverse games file and names the games used (regular season, 2020 through 2026 week 10).

### "Model architecture and evaluation"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** the README section [Model and Evaluation](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#model-and-evaluation).
- **Docs:** [Step 4: Fit the Scaler and the Model](../phase-2/implementation-part-2.md#step-4-fit-the-scaler-and-the-model) and [What Is Accuracy?](../phase-2/implementation-part-2.md#what-is-accuracy)
- **Evidence:** logistic regression on two inputs. Validation accuracy **63.10%** (171 of 271) against the always-home baseline of 53.87%, and test accuracy **59.06%** (88 of 149) against 47.65%. Each number is recomputed from [`results/run-summary.json`](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/blob/main/results/run-summary.json).

### "Cloud services used"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** the README section [Cloud Services](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#cloud-services).
- **Docs:** [Phase 4 Implementation](../phase-4/implementation.md), [How Is the Page Hosted?](../phase-5/implementation-part-1.md#how-is-the-page-hosted), and [How Are the Docs Published?](../extras/github-workflows.md#how-are-the-docs-published)
- **Evidence:** the section names S3 for the data and the web app, Lambda behind API Gateway for the API, CloudFront for the web app, DynamoDB for the feedback form, and GitHub Pages for the docs.

### "Setup and usage instructions"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** the README section [Setup and Usage](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#setup-and-usage), which gives the run environment and the `make` commands.
- **Docs:** [Makefile](../extras/makefile.md), [What Must Be Set Up First?](../extras/makefile.md#what-must-be-set-up-first), [How Do I Do a Training Run?](../phase-2/development-guide.md#how-do-i-do-a-training-run), and [Phase 3 Development Guide, How Do I Run It Locally?](../phase-3/development-guide.md#how-do-i-run-it-locally)
- **Evidence:** Phase 7 rebuilds the project from a clean copy using only the README ([Step 3: Rebuild From a Clean Copy](../phase-7/brief.md#step-3-rebuild-from-a-clean-copy)). The nine make commands are all documented on [Makefile](../extras/makefile.md).

### "Link to deployed API and front-end app"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** the README section [Live Links](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#live-links). The API is `https://9awodatqc5.execute-api.us-east-1.amazonaws.com` and the web app is `https://d1nubiunzfwm0q.cloudfront.net`.
- **Docs:** [Step 9: Check the Public Address](../phase-4/implementation.md#step-9-check-the-public-address) and [How Is the Page Hosted?](../phase-5/implementation-part-1.md#how-is-the-page-hosted)
- **Evidence:** [Phase 7 Brief, Step 4: Check the Live Services](../phase-7/brief.md#step-4-check-the-live-services) re-checks both addresses before hand-in.

## Learning Goal: Ethical Implications and Limitations

The brief's Learning Goals ask every project to "Reflect on ethical implications and limitations of your ML application". It is a requirement like the others, and it is met.

### "Reflect on ethical implications and limitations of your ML application"

- **Status:** Met (README draft, Phase 7)
- **Where in the code:** the README section [Limitations and Ethics](https://github.com/jconnors23/510-m3-nfl-prediction-analytics#limitations-and-ethics).
- **Docs:** [Design Manifest](../design-manifest.md) records the choices behind the model, and [What Does the Confusion Matrix Show?](../phase-2/implementation-part-2.md#what-does-the-confusion-matrix-show) shows where the model is wrong.
- **Evidence:** the section states that predictions are for reference only, that the model uses two inputs, and that the test accuracy is **59.06%** (88 of 149).
