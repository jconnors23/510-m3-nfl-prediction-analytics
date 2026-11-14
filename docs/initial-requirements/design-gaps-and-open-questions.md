---
hide:
  - toc
---

# Design Gaps and Open Questions

This page lists what the [System Architecture Implementation Design](./system-architecture-implementation-design.md) leaves out or leaves unclear, checked against the [Project Requirements](./requirements.md). The design document itself has not been edited, apart from the five commit breakpoint markers. Each item says what is missing and which part of the design it affects.

## Requirements Cross-Check

| Requirement | Covered by the design? | Gap |
| :--- | :--- | :--- |
| 1. Problem and dataset | Yes | No link to the dataset (see G1). |
| 2. Cloud data storage (S3) | Partly | Download is covered. The step that uploads the cleaned file to S3 is not (see G2). |
| 3. Reproducible pipeline | Yes | The validation set has no stated use (see A5). |
| 4. Experiment tracking | Yes | None. |
| 5. Docker | Partly | One image must serve both Lambda and local training, which the design does not explain (see A7). Local build and test steps are not listed (see G5). |
| 6. Prediction API | Partly | Whether the API applies the scaler is not stated (see A4). |
| 7. Cloud deployment (Lambda and API Gateway) | Partly | The roadmap mentions ECR, but the infrastructure section does not. Region, IAM roles, and CORS are not listed (see G3). |
| 8. Front-end | Partly | The ratings lookup table has no script that builds it (see G4). |
| 9. Repository contents | Partly | No branch and pull request plan. A `deploy.yml` file is listed with no description (see G6). |
| 10. README | Partly | No dataset URL, evaluation result, or architecture diagram content is defined (see G1). |

## Missing Items

| ID | Missing item | Affects part | Why it matters |
| :--- | :--- | :--- | :--- |
| G1 | The dataset URL, and a list of what the README must hold (dataset link, evaluation result). | 1, 5 | Requirement 10 asks for a dataset link and the evaluation result. |
| G2 | A script that uploads the cleaned file to S3. The directory tree has `s3_download.py` and `data_loader.py` but no upload script. | 1 | Requirement 2 asks for the upload. Without a script, the step cannot be repeated. |
| G3 | AWS region, IAM permissions for Lambda and for the training job, and CORS settings on API Gateway. | 3, 4 | The web app calls the API from another domain, so the browser request can fail without CORS. |
| G4 | A script that builds the team ratings lookup table used by the front-end. | 5 | The front-end needs ratings for 32 teams, but nothing in the tree produces them. |
| G5 | Steps for building and testing the Docker image and the API locally, before deploying. | 3 | Requirement 5 asks for a local build and run. The roadmap only tests with `curl` after deployment. |
| G6 | What `.github/workflows/deploy.yml` does, or a decision to drop it. | 4 | It is in the tree but not in the roadmap, so it is unclear whether it is required. |
| G7 | A branch and pull request plan. The breakpoint markers suggest one branch per part. | All | Requirement 9 asks for branches and at least one pull request. |
| G8 | `requirements.txt` does not match the design. It lists `google-cloud-storage` and omits `boto3`, `mangum`, and `joblib`. | 1, 3, 4 | The design uses AWS only. The file was created before AWS was chosen. |

## Unclear or Ambiguous Items

| ID | Where | What is unclear |
| :--- | :--- | :--- |
| A1 | Section 1.1, target variable | Ties are "excluded or mapped to 0". The design does not choose one. The choice changes the game counts in Section 2.2. |
| A2 | Section 2.1, features | "Rolling Point Differential" and "Cumulative Season Win %" are described with different words. The rolling window length is not given. Handling of week 1, when no earlier games exist, is not given. It is also not stated whether results carry over from the previous season. |
| A3 | Section 2.1, `home_advantage` | The feature is always `1`. A constant column carries no information for the model and duplicates the intercept in logistic regression. The design does not say why it is included. |
| A4 | Sections 2.2, 3.2, 4.1 | A scaler is fit on the training set and saved as `scaler.joblib`. The API request sends raw differentials. The design does not say that the API loads and applies the scaler. The directory tree lists only `model.joblib`. |
| A5 | Sections 2.2, 3.2 | The validation season (2023) is scored but never used to choose a setting. The design does not say whether it is only reported or used to tune the model. |
| A6 | Section 4.1, response | `win_probability` could mean the chance the home team wins or the chance of the predicted label. When `prediction` is `0`, the meaning changes. |
| A7 | Sections 4.2, 6, 7 | The Dockerfile must run training, run the API locally, and run as an AWS Lambda container image. Lambda images need a specific base image and handler. The design says "multi-stage or entry-point" without choosing. |
| A8 | Section 5.1, lookup table | The front-end uses 2024 end-of-season ratings, but the model was trained on ratings computed before each game. The two are not the same kind of number. Rest days for a future game also have no stated source ("or pre-configured default values"). |
| A9 | Section 5.1, team list | The front-end lists the 32 active teams. The 2016–2024 data includes franchise moves (Oakland to Las Vegas, San Diego to Los Angeles, St. Louis to Los Angeles). The design does not say how old team names are matched to current ones. |
| A10 | Sections 3.1, 4.2 | The S3 bucket name appears as a real name in `config.yaml` and as `<bucket-name>` in Section 1.2. S3 bucket names are unique worldwide, so the real name may already be taken. |
| A11 | Section 4.2 | The route is public with no key, rate limit, or spending cap. The design states "Publicly accessible" but does not say whether this is accepted for the project. |
| A12 | Section 6, `models/model.joblib` | It is not stated whether the model file is committed to git, rebuilt inside the Docker image, or downloaded at start-up. The Lambda image needs the file at build time. |
| A13 | Section 6, `design.md` | The tree calls this file `design.md`. The actual file is `system_architecture_implementation_design.md`. |
| A14 | Section 7, title | The roadmap is titled "for Cursor". The requirements are written for one person. The design does not say who runs each phase. |
| A15 | Section 3.2 | MLflow logs to a local `mlruns` folder. It is not stated where results are kept for the README, or whether the folder is committed. It is currently ignored by git. |
