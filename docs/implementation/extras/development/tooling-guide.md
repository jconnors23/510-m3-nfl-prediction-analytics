---
hide:
  - toc
---

# Tooling Guide

This page lists every tool the project uses, the version it is pinned to or requires, and where it is used. It covers Python and its packages, the web app's packages, containers, the cloud command line, the docs tools, and the automation. For what each tool is, see the [Glossary](../glossary.md).

## Which Versions Are Exact?

- **Exact (`==`):** every Python package. Another version could change a number, so `requirements.txt` pins each one.
- **Range (`^`, `~`):** the web app's packages in `frontend/package.json`. The file `frontend/package-lock.json` records the exact version installed, and `npm ci` installs exactly those.
- **Pinned in a command or file:** MkDocs and its two add-ons (in the docs workflow), the base image (in the `Dockerfile`), and each GitHub Action (in `.github/workflows/`).
- **Not pinned:** Docker Desktop, GNU Make, and Node.js on a laptop. The versions in the tables below marked "on this laptop" are the ones the project was built with.

## Which Python Version and Packages?

Python **3.13** is required. The Lambda function on AWS and the Docker image use the same minor version, because a saved model can fail to load or answer differently under another one. Create the environment with `python3.13 -m venv .venv`, as in [What Must Be Set Up First?](./makefile.md#what-must-be-set-up-first).

The second column shows whether the package is also in `requirements-serve.txt`, the shorter list for the AWS Lambda zip. Every pin there matches `requirements.txt`.

| Package | Version | In the Lambda zip? | What it does here |
| :--- | :--- | :--- | :--- |
| pandas | 3.1.1 | No | Holds the game tables and does the filtering and grouping |
| numpy | 2.5.4 | Yes | Does the number work under pandas and scikit-learn |
| PyYAML | 6.0.3 | Yes | Reads `config/config.yaml` |
| scikit-learn | 1.9.1 | Yes | Supplies the standardizing step, the logistic regression, and the scores |
| scipy | 1.18.1 | Yes | Used by scikit-learn's solver, pinned so the fitted weights match on every machine |
| mlflow | 3.18.0 | No | Records the settings, scores, and files of each training run |
| matplotlib | 3.11.2 | No | Draws the confusion-matrix image |
| joblib | 1.6.0 | Yes | Writes and reads the saved model file |
| requests | 2.34.2 | No | Downloads the games file |
| boto3 | 1.44.5 | No | Talks to S3 and DynamoDB from code. Lambda supplies its own copy |
| fastapi | 0.162.2 | Yes | Builds the `/predict` and `/health` routes |
| uvicorn[standard] | 0.54.0 | No | Runs the API on a laptop and in the Docker serve image. Mangum replaces it on Lambda |
| pydantic | 2.14.3 | Yes | Checks that each request has the right fields |
| mangum | 0.22.0 | Yes | Lets AWS Lambda call the same FastAPI app |
| pytest | 9.2.0 | No | Runs the Python tests. See the [Testing Guide](./testing-guide.md) |
| httpx2 | 2.16.2 | No | Used only by the API tests, because FastAPI's test client asks for it |

For what the main libraries are, see the Glossary sections for [Phase 2](../glossary.md#phase-2-features-training-and-tracking), [Phase 3](../glossary.md#phase-3-local-prediction-api), and [Phase 4](../glossary.md#phase-4-aws-deployment).

## Which Packages Does the Web App Use?

The web app needs Node.js **`^22.12.0 || ^24.0.0 || >=26.0.0`** (the `engines` range in `frontend/package.json`). The Test Web App and Deploy Web App workflows use Node 24, and the laptop the project was built on has 24.17.0. Install the packages with `npm ci` inside `frontend/`.

| Package | Range in `package.json` | Installed in `package-lock.json` | What it does here |
| :--- | :--- | :--- | :--- |
| react | ^19.3.1 | 19.3.1 | Draws the page |
| react-dom | ^19.3.1 | 19.3.1 | Puts the React page into the browser |
| @fontsource-variable/inter | ^5.3.0 | 5.3.0 | The body font, served from the site's own address |
| @fontsource-variable/oswald | ^5.3.0 | 5.3.0 | The heading font, served the same way |
| vite | ^8.3.6 | 8.3.8 | Runs the dev server and builds the files that are published |
| @vitejs/plugin-react | ^6.1.2 | 6.3.0 | Lets Vite build React code |
| typescript | ~7.0.2 | 7.0.2 | Checks types in `npm run build` (`tsc -b`) |
| vitest | ^5.1.1 | 5.1.1 | Runs the web tests |
| jsdom | ^31.0.1 | 31.0.1 | A browser stand-in for the two tests that draw components |
| @testing-library/react | ^16.3.3 | 16.3.3 | Draws a component in a test and finds things on it |
| @testing-library/user-event | ^14.6.13 | 14.6.13 | Clicks and types in a test the way a visitor would |
| @testing-library/dom | none | 10.4.2 | Installed because `@testing-library/react` needs it |
| @types/node | ^24.19.2 | 24.19.2 | Type definitions for Node, used by the parity tests |
| @types/react | ^19.3.0 | 19.3.0 | Type definitions for React |
| @types/react-dom | ^19.3.0 | 19.3.0 | Type definitions for React DOM |

The four scripts in `package.json` are `dev` (`vite`), `build` (`tsc -b && vite build`), `preview` (`vite preview`), and `test` (`vitest run`). For how to change a package version, see [How Do I Change a Package Version?](../../phase-5/index.md#how-do-i-change-a-package-version). The Glossary entry is [Phase 5: Front-End Web App](../glossary.md#phase-5-front-end-web-app).

## Which Container Tools Are Used?

- **Docker Desktop,** running, for `make docker-train`, `make docker-serve`, and the container test commands. The laptop the project was built on has Docker 29.9.3.
- **Base image `python:3.13.14-slim`,** set by `ARG PYTHON_VERSION=3.13.14` in the `Dockerfile`. The patch version is pinned so a rebuild months later uses the same Python. Both images (`train` and `serve`) start from it and install the same pins as `requirements.txt`.

The Glossary entries are in [Phase 6: Docker](../glossary.md#phase-6-docker).

## Which Cloud Tools Are Used?

- **AWS CLI version 2,** used to deploy the Lambda function, the API gateway, the S3 bucket, and the CloudFront site. The laptop the project was built on has 2.35.9. Credentials for the owning account must be configured, with `us-east-1` as the region.
- **boto3,** for S3 and DynamoDB calls from Python code (see the package table above).

See [Deploy the API](../../phase-4/deployment-guide.md) and [Deploy the Web App](../../phase-5/deployment-guide.md).

## Which Docs Tools Are Used?

| Tool | Version | What it does here |
| :--- | :--- | :--- |
| MkDocs | 1.6.1 | Builds the pages in `docs/` into the site |
| mkdocs-material | 9.7.7 | The theme, with the navigation and the diagram support |
| pymdown-extensions | 12.0.1 | Markdown add-ons, including the code-block setting that draws Mermaid diagrams |
| Mermaid | loaded by the theme | Draws the diagrams written in `mermaid` code blocks |

MkDocs is not in `requirements.txt`. Install the three packages with the versions the docs workflow uses, shown in [What Must Be Set Up First?](./makefile.md#what-must-be-set-up-first). The Glossary entries are in [General Tooling and Reproducibility](../glossary.md#general-tooling-and-reproducibility).

## Which Automation Tools Are Used?

- **GNU Make,** which reads the `Makefile`. The laptop the project was built on has 3.81. Every command is in [Makefile](./makefile.md).
- **GitHub Actions,** which runs the four workflows in `.github/workflows/`. See [GitHub Workflows](./github-workflows.md).

| Workflow | File | Actions and versions used | Runtime set up |
| :--- | :--- | :--- | :--- |
| Test Python | `test-python.yml` | `actions/checkout@v7`, `actions/setup-python@v7` | Python 3.13 |
| Test Web App | `test-web.yml` | `actions/checkout@v7`, `actions/setup-node@v7` | Node 24 |
| Deploy Docs | `deploy-docs.yml` | `actions/checkout@v7`, `actions/setup-python@v7`, `actions/upload-pages-artifact@v5`, `actions/deploy-pages@v5` | Python 3.13 |
| Deploy Web App | `deploy-web-app.yml` | `actions/checkout@v7`, `actions/setup-node@v7`, `aws-actions/configure-aws-credentials@v6` | Node 24 |
