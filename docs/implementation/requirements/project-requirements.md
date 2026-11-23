---
hide:
  - toc
---

# Project Requirements

End-to-end requirements for one person building this project, stated as checkable items.

Two things are delivered: a GitHub repository with the full pipeline, and a publicly reachable front-end linked from the repository README.

## 1. Problem and Dataset

- Pick a public dataset (for example from Kaggle, UCI, or Hugging Face Datasets).
- Define a single supervised learning task: either classification or regression.
- Name the target variable and the one evaluation metric used to judge the model.

## 2. Cloud Data Storage

- Clean and preprocess the dataset locally before uploading.
- Upload the cleaned data to an Amazon S3 bucket. S3 is the chosen storage service for this project.
- Include a script that downloads the data from S3 programmatically (for example with boto3), so the pipeline starts from the S3 copy rather than a local file.

## 3. Reproducible Pipeline

- Use one simple model (for example logistic regression, random forest, or XGBoost).
- The pipeline must cover, in order: data ingestion from S3, preprocessing and feature engineering, a train/validation/test split, model training, and evaluation.
- All tunable settings live in a `config.yaml` file (for example the split ratio and model parameters). Changing a run means editing that file, not the code.
- Model accuracy is not graded. A poor score is acceptable; the requirement is a clean, repeatable process.

## 4. Experiment Tracking

- Use MLflow or Weights & Biases.
- Log each run's parameters and evaluation metrics.
- Log artifacts for reproducibility: at minimum the trained model, plus any plots produced.

## 5. Docker

- Provide a Dockerfile that installs every dependency and defines entry points for both training and serving.
- The image must build and run locally so the project is reproducible from the container alone.

## 6. Prediction API

- Serve the trained model with FastAPI or Flask.
- Expose a `/predict` endpoint that accepts JSON input and returns a prediction as JSON.
- The endpoint must be testable locally (for example with curl or Postman).

## 7. Cloud Deployment

- Deploy the API on AWS. AWS is the chosen deployment platform for this project; use AWS Lambda fronted by API Gateway.
- Configure CORS on API Gateway so the browser-based front-end can call `/predict`.
- After deployment, the `/predict` endpoint must be publicly reachable and must return a valid response to an HTTP request with test data.

## 8. Front-End

- Build a lightweight interface with Vite. Use the Vite development server for local work and `vite build` to produce the files that are published.
- The interface collects user input, sends it to the deployed API, and displays the returned prediction in an interactive, readable form.
- Host the built files on AWS: a private S3 bucket served over HTTPS through a CloudFront distribution. CloudFront is the chosen hosting platform for this project.
- Link the live front-end URL in the repository README.

## 9. Repository Contents

The GitHub repository must contain all of the following:

- Code for preprocessing, training, serving, and deployment.
- `config.yaml` for pipeline configuration.
- A dependency file: `requirements.txt` or `environment.yaml`.
- A Dockerfile that runs the full project.
- MLflow or Weights & Biases logging wired into the pipeline.
- A clear project structure and a readable commit history.
- Work done on branches merged through pull requests, with at least one pull request on record.

## 10. README

The repository README must include:

- A project overview and its goals.
- A description of the dataset and a link to it.
- The model used and its evaluation result.
- The cloud services used.
- Setup and usage instructions covering how to train the model, how to build and test the API locally, and how to deploy to the cloud.
- Links to both the deployed API and the live front-end.

## 11. Ethics and Limitations

- Reflect on the ethical implications and limitations of the ML application, in the README: what the model leaves out, how its mistakes lean, how its predictions should and should not be used, and what data the app collects.

## Acceptance Checklist

1. **Problem and dataset.** Done when: Public dataset chosen; task, target, and metric named.
2. **Cloud storage.** Done when: Cleaned data uploaded to Amazon S3; download script pulls it from the bucket.
3. **Pipeline.** Done when: Ingestion → preprocessing → split → train → evaluate, all driven by `config.yaml`.
4. **Tracking.** Done when: Runs, parameters, metrics, and artifacts logged to MLflow or W&B.
5. **Docker.** Done when: Image builds and runs locally with training and serving entry points.
6. **API.** Done when: `/predict` returns a prediction from JSON input, verified locally.
7. **Deployment.** Done when: API runs on AWS Lambda behind API Gateway; `/predict` is publicly reachable, answers test requests, and allows the front-end's origin through CORS.
8. **Front-end.** Done when: Vite app served from S3 through CloudFront calls the live API and shows predictions.
9. **Repository.** Done when: All required files present; branch-and-PR workflow with at least one PR.
10. **README.** Done when: Overview, dataset, model, cloud services, setup/usage, and both live links.
11. **Ethics and limitations.** Done when: The README states the model's limitations and the app's ethical boundaries.
