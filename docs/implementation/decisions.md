---
hide:
  - toc
---

# Decisions

The project-wide choices, and the choices for phases not built yet, with the reason for each and what was turned down. Phase 1 choices are at the end of the [Phase 1 Implementation](./phase-1/implementation.md#which-choices-were-made). Choices still needing the developer's approval are in [Open Decisions](#open-decisions).

## Model Inputs (Decided)

- **Two raw per-game inputs replace the two rank inputs.** They are the home team's win percentage minus the away team's, and the home team's point margin per game minus the away team's. Both use only earlier weeks of the same season. A team with no games counts as 0.5 and 0.0, so week 1 gives 0 for both inputs.
- **Why the change.** Ranks drop the size of a gap (a +14 team and a +2 team can be neighbors), create ties in early weeks, and change when unrelated teams win. Raw values keep the gap, need no tie rule, and read directly ("+7.3 points per game better").
- **Scores were similar,** so the reason is clarity, not accuracy. On the current data, logistic regression with ranks got 169 of 271 validation games right (62.36%, log loss 0.6345) and 92 of 149 test games (61.74%). With raw inputs it got 171 of 271 (63.10%, log loss 0.6451) and 88 of 149 (59.06%).
- **Per game, not season totals,** so a team that has played more games, for example after a bye, is not favored.
- **Home minus away,** so a positive value favors the home team.
- **`rank_gap`, `mismatch`, and `record_ahead_by` are removed.** They were display-only columns for the web app and never model inputs.

## Run Records (Decided)

- **Each run also writes `results/run-summary.json`,** a small readable file with the settings, the data fingerprint, the scores, and the learned weights. It is committed to git, so a reader can check the numbers without MLflow or the saved model.
- **The summary has no run ID, timestamp, git commit, or machine paths.** Each of those changes on every run or commit, so the file would show a change in git when nothing real changed. MLflow keeps the commit for each run.
- **Two parameters were added to every run:** the scikit-learn version and a fingerprint of the data file, so a run can be traced to the exact library and data it used.
- **The model is stored twice in each run, on purpose.** The plain `model.joblib` is the working copy the API will load, and it carries the input names, version, and training seasons. The MLflow-format copy lets MLflow's own screen and loader open the model. MLflow's format alone was not enough: in MLflow 3 it is not in the run's file list, and it does not carry those facts.
- **The MLflow records stay local.** `mlflow.db`, `mlartifacts/`, and `models/` are not committed. The database is a binary file that changes on every run, it records the artifact folder as a full path on one machine, and one command recreates all three with identical scores.

## Phase Boundaries (Decided)

- **Phase 1 is fetch, clean, upload, and download from S3.** It has no feature or front-end work.
- **Phase 2 starts with the features and the split,** then trains and tracks.
- **The team-profile file for the web app belongs to Phase 5,** and its code moves to `src/profiles.py`.
- **Phases 3 to 5 share one high-level page** ([Remaining Phases](./remaining-phases.md)) until they begin.
- **No notebooks.** They repeated the scripts and the docs.
- **Split by season.** Training is 2020 to 2024 (1,339 games), validation is 2025 (271), and test is 2026 weeks 1 to 10 (149). The test games are not used to fit the model.

## Open Decisions

Each shows the proposed answer first.

- **The Phase 3 to 6 choices** (probability field name, zip or container image for Lambda, one Dockerfile or two, no `deploy.yml`, no API key, one standings snapshot, Vite template) are in [Remaining Phases](./remaining-phases.md#open-decisions).

## Model and API

- **Logistic regression only,** with no model comparison. Turned down: a random forest as a second candidate, and XGBoost. One simple model is enough, the two inputs are simple, and an earlier test had the forest and logistic regression within a game or two of each other. Fixing the model type means the 2025 validation season is used only to report the score, so it is never used to choose between models.
- **A standardizing step is kept** and saved with the model as one pipeline, so the API cannot skip it. The two inputs are on different scales: win percentage differences run from -1 to 1 and point margin differences run about -49 to 39.
- **MLflow tracks each run.** See [Run Records](#run-records-decided).
- **The same FastAPI app runs locally and in Lambda, using Mangum.** Turned down: a separate hand-written Lambda function, which would repeat the input checks and the model call in a second place. See [What Is Mangum?](./remaining-phases.md#what-is-mangum).
- **The API takes two decimal numbers** (the win percentage difference and the point margin per game difference), rejects unknown fields, and returns `prediction`, `predicted_label`, `home_win_probability`, and `model_version`. A `GET /health` route is an extra.
- **The API is built and tested locally first,** with no Docker and no AWS (Phase 3).
- **Docker comes last (Phase 6).** Nothing before it needs an image, because Lambda runs the API from a zip file. Turned down: building Docker in Phase 3, which would put a packaging step ahead of the web app without unblocking anything.
- **One Dockerfile with two targets,** `train` and `serve`. The model file is copied in at build time. It is not committed to git and is not downloaded at start-up.
- **A smaller dependency list for serving,** so the zip stays under Lambda's size limit and the function starts faster after idle time.

## Cloud and Front-End (Planned)

- **AWS only:** S3, Lambda behind an API Gateway HTTP API, and CloudFront. ECR is added only if the Lambda zip is over the size limit. Turned down: Google Cloud and Azure.
- **One region, `us-east-1`,** because the data bucket is already there. Decided.
- **Lambda runs from a zip file,** built with Linux packages for the same chip type and Python version (3.13) as the function. Fallback: a container image in ECR, only if the zip is over Lambda's 250 MB unzipped limit. Measured: 231.3 MB unzipped without `pandas`, so the zip fits, and the API must not use `pandas` (278.4 MB with it). See the [Package Size Check](./phase-4/package-size-check.md).
- **CORS is set on the gateway only,** with the CloudFront address and the local Vite address allowed. The CloudFront address is added once the distribution exists (Phase 5). While working locally, the Vite development server can forward requests to the local API instead.
- **The front-end is a Vite app.** The development server is for local work only. The published site is the built static files in a private S3 bucket behind CloudFront. Turned down: Streamlit, and S3's own website hosting (it serves only HTTP and needs a public bucket).
- **The API is public, with no key.** It has a request limit (5 per second, burst of 10) and a budget alert. A key in a browser app would be visible to every visitor.
- **Deployment is a set of written steps,** with no `deploy.yml` workflow.
- **The web app reads one snapshot of the standings,** taken after 2026 week 10.

## Documentation and Process

- **MkDocs with the Material theme** and no right-hand contents list. The theme is light, with sky blue as the main color.
- **The brief and the requirements pages are kept unchanged** in `docs/initial-requirements/`. They are the only two reference documents. The first design draft and the gap list were removed.
- **A phase gets full pages only once it is built.** Phases 1 and 2 have a brief (Phase 1 also has an implementation page). Phase 3 has a brief written before it starts. Phases 4 to 6 share one high-level page.
- **Each implementation step has a purpose block** (Goal, Why, If skipped).
- **Cursor builds the code from a written spec, and the docs are written from the finished code.** Kiro writes a spec in `specs/` with what to build and the numbers to match, Cursor builds it and ends with a deviations report, and the developer, Kiro, and the report are reviewed together before the next spec.
- **Git is run by the developer only.** Phases 1 and 2 go in one branch and one pull request, and the developer names the branch.
