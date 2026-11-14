# M3 System Architecture & Implementation Design
**NFL Pre-Game Matchup Predictor (AIPI 510 Milestone 3)**

---

> **▶ PART 1 OF 5 · COMMIT BREAKPOINT: Data Ingestion and Feature Engineering**
> Covers: Sections 1 and 2 (roadmap Phase 1)
> Ready to commit when: the S3 download works and `src/preprocess.py` produces the four features and the chronological split.

## 1. System Overview & Problem Formulation

### 1.1 Objective & Task Definition
* **Problem Type:** Supervised Binary Classification (Pre-game NFL Matchup Winner).
* **Target Variable ($y$):** `home_win` $\in \{0, 1\}$
  * `1` = Home team won.
  * `0` = Away team won (ties excluded or mapped to 0).
* **Evaluation Metric:** **Accuracy** ($\frac{\text{Correct Predictions}}{\text{Total Predictions}}$).
* **Operational Scope:** Predictions are generated strictly prior to kickoff using rolling season performance differentials and rest disparities.

### 1.2 Data Source & Ingestion
* **Public Dataset:** `nflverse` historical schedules and results (`games.csv`).
* **Attributes Utilized:** Season, week, home team, away team, home score, away score, rest days.
* **Storage Architecture:**
  1. Local preprocessing cleans raw schedule records (2016–2024 regular seasons).
  2. Cleaned tabular data is persisted to an **Amazon S3** bucket (`s3://<bucket-name>/data/processed/nfl_matchups_2016_2024.csv`).
  3. The reproducible pipeline begins by pulling the dataset programmatically via `boto3`.

---

## 2. Feature Engineering & Pipeline Integrity

### 2.1 Feature Definitions
Features are constructed strictly using information available prior to kickoff (rolling trailing stats, avoiding within-game data leakage):

| Feature Name | Type | Description |
| :--- | :--- | :--- |
| `point_diff_differential` | `float` | Rolling Point Differential (Home) minus Rolling Point Differential (Away). |
| `win_pct_differential` | `float` | Cumulative Season Win % (Home) minus Cumulative Season Win % (Away). |
| `rest_differential` | `int` | Days of rest (Home) minus days of rest (Away). |
| `home_advantage` | `int` | Constant indicator (`1`) designating home-field presence. |

### 2.2 Chronological Split & Leakage Safeguards
To prevent lookahead bias and temporal leakage:
* **Training Set:** 2016–2022 regular seasons (~$1{,}800$ games).
* **Validation Set:** 2023 regular season (272 games).
* **Test Set:** 2024 regular season (272 games).
* **Transformation Rule:** All scalers (`StandardScaler`) are fit strictly on the training partition and transformed downstream on validation and test partitions.

---

> **▶ PART 2 OF 5 · COMMIT BREAKPOINT: Configuration, Training, and Experiment Tracking**
> Covers: Section 3 (roadmap Phase 2)
> Ready to commit when: `src/train.py` runs from `config/config.yaml` and logs parameters, metrics, and artifacts to MLflow.

## 3. Configuration & Experiment Tracking

### 3.1 Central Configuration (`config.yaml`)
All operational hyperparameters live in a single config file:

```yaml
data:
  s3_bucket: "aipi510-m3-nfl-predictions"
  s3_key: "data/processed/nfl_matchups_2016_2024.csv"
  local_cache_path: "data/raw/nfl_matchups.csv"

split:
  train_start_season: 2016
  train_end_season: 2022
  val_season: 2023
  test_season: 2024

model:
  type: "LogisticRegression" # Options: LogisticRegression, XGBClassifier, RandomForestClassifier
  params:
    C: 1.0
    solver: "lbfgs"
    max_iter: 1000
    random_state: 42

tracking:
  experiment_name: "nfl-pregame-winner-v1"
  tracking_uri: "mlruns" # Local MLflow or remote tracking URI
```

### 3.2 MLflow Tracking Matrix
* **Parameters Logged:** Model type, regular-season training split years, solver, $C$, random seed.
* **Metrics Logged:** Training Accuracy, Validation Accuracy, Test Accuracy, Test ROC-AUC (diagnostic), Test Log Loss.
* **Artifacts Logged:** `model.joblib`, `scaler.joblib`, Confusion Matrix PNG, ROC Curve PNG, and `config.yaml`.

---

> **▶ PART 3 OF 5 · COMMIT BREAKPOINT: Prediction API and Docker Image**
> Covers: Section 4.1, plus the Dockerfile from Section 6 (roadmap Phase 3)
> Ready to commit when: `/predict` answers a local `curl` request and the Docker image builds with training and serving entry points.

## 4. API Design & Cloud Deployment

### 4.1 Prediction API (FastAPI)
The backend exposes a lightweight inference endpoint compliant with the assignment checklist.

* **Method:** `POST`
* **Route:** `/predict`
* **Request Payload (JSON):**
```json
{
  "point_diff_differential": 10.5,
  "win_pct_differential": 0.20,
  "rest_differential": 3,
  "home_advantage": 1
}
```
* **Response Payload (JSON):**
```json
{
  "prediction": 1,
  "predicted_label": "Home Win",
  "win_probability": 0.642,
  "model_version": "v1.0"
}
```

> **▶ PART 4 OF 5 · COMMIT BREAKPOINT: AWS Deployment**
> Covers: Section 4.2 (roadmap Phase 4)
> Ready to commit when: the public API Gateway URL returns a valid prediction to a `curl` request.

### 4.2 Cloud Infrastructure (AWS Serverless)
* **Packaging:** FastAPI wrapped via `Mangum` ASGI adapter, packaged as an AWS Lambda container image.
* **API Gateway:** HTTP API Gateway (v2) routes incoming public requests to the Lambda function.
* **Authentication:** Publicly accessible `POST` route.
* **CORS:** Configured on API Gateway to allow the CloudFront address of the web app and the local Vite development server address, because the browser calls the API directly.

---

> **▶ PART 5 OF 5 · COMMIT BREAKPOINT: Front-End and Documentation**
> Covers: Section 5 (roadmap Phase 5). Sections 6 and 7 are reference material for every part.
> Ready to commit when: the Vite web app, served from S3 through CloudFront, calls the live API and the README holds every required link.

## 5. Front-End UI Architecture

### 5.1 Vite Web App
A lightweight Vite single-page app. The Vite development server is used for local work. `vite build` produces static files that are stored in a private S3 bucket and served over HTTPS through CloudFront:
* **User Input:** Two select boxes (`Home Team`, `Away Team`) populated with the 32 active NFL franchises.
* **Lookup Table:** Front-end caches latest 2024 end-of-season ratings (or pre-configured default values) to calculate differentials automatically.
* **Request Flow:**
  1. User selects teams and clicks **"Predict Matchup"**.
  2. Front-end calculates feature vector $[ \Delta \text{PtDiff}, \Delta \text{WinPct}, \Delta \text{Rest}, 1 ]$.
  3. Calls public AWS API Gateway endpoint via `fetch`.
  4. Renders winning prediction badge, win probability progress bar, and matchup summary cards.

---

## 6. Directory Structure

```text
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD deployment automation
├── api/
│   ├── app.py                  # FastAPI app with /predict endpoint
│   └── mangum_handler.py       # AWS Lambda handler wrapping FastAPI
├── config/
│   └── config.yaml             # Single source of truth for splits & hyperparameters
├── data/
│   ├── processed/              # Preprocessed artifacts prior to S3 upload
│   └── s3_download.py          # Script fetching training data from S3
├── frontend/
│   ├── package.json            # Vite project and its dependencies
│   ├── public/
│   │   └── team-profiles.json  # Team numbers read by the web app
│   └── src/                    # Web app source
├── models/
│   └── model.joblib            # Serialized trained model artifact
├── src/
│   ├── __init__.py
│   ├── data_loader.py          # S3 reader and ingestion logic
│   ├── preprocess.py           # Feature engineering & temporal split
│   ├── train.py                # Pipeline execution with MLflow logging
│   └── evaluate.py             # Accuracy evaluation & artifact generation
├── Dockerfile                  # Multi-stage or entry-point container
├── requirements.txt            # Pinned dependencies
├── README.md                   # Full documentation and public URLs
└── design.md                   # This specification file
```

---

## 7. Implementation Roadmap for Cursor

1. **Phase 1: Ingestion & Feature Engineering**
   * Write `data/s3_download.py` using `boto3`.
   * Implement feature calculations in `src/preprocess.py`.
2. **Phase 2: Training & MLflow Logging**
   * Build `src/train.py` driven strictly by `config/config.yaml`.
   * Log hyperparameters, test accuracy, and model artifacts to MLflow.
3. **Phase 3: FastAPI & Dockerization**
   * Implement `/predict` in `api/app.py`.
   * Write `Dockerfile` supporting both training execution and API serving.
4. **Phase 4: AWS Cloud Deployment**
   * Deploy container image to AWS Lambda via ECR.
   * Attach API Gateway HTTP endpoint and verify using `curl`.
5. **Phase 5: Vite Front-End & Docs**
   * Build the UI in `frontend/` with Vite, connecting to the live Gateway URL.
   * Publish the built files to S3 behind CloudFront.
   * Create README with architecture diagram, test curls, and hosted links.

---

> **■ END OF PART 5 OF 5**
