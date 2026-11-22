# Module Project 3: Data/ML Engineering

## From Data to Decisions: Deploying a Reproducible ML Pipeline

This project is an opportunity to design, build, and deploy a full-stack machine learning system. You and your partner will select a dataset, host it in a cloud storage or database system, and build a reproducible pipeline that trains and tracks a simple ML model. You'll then containerize and deploy your model as an API endpoint on a cloud platform and create a front-end application that consumes this API. The project emphasizes best practices in MLOps, including reproducibility, cloud deployment, and modular design.

## Learning Goals

- Practice sourcing, cleaning, and hosting real-world data in the cloud
- Build reproducible, modular ML pipelines using configuration files and containers
- Track experiments using MLFlow or Weights & Biases
- Deploy a model as an API endpoint using cloud services
- Build a lightweight front-end to consume a live model API
- Follow GitHub best practices for collaboration and version control
- Reflect on ethical implications and limitations of your ML application

## Deliverables

Your final deliverables consist of a GitHub repository and a link to a deployed front-end application.

### 1. GitHub Repository

Your repository must include:

- All code for preprocessing, training, serving, and deployment
- `config.yaml` for pipeline configuration
- `requirements.txt` or `environment.yaml`
- A Dockerfile that can run the full project
- Clear documentation for:
    - How to train the model
    - How to build and test the API locally
    - How to deploy to the cloud
- MLFlow or Weights & Biases logging
- Use of branches and pull requests (each group member must submit at least one PR)
- A clear project structure and commit history

### 2. Front-End Application

Your app must:

- Be publicly accessible and linked in the README
- Send requests to your deployed model API (e.g., using requests or fetch)
- Display the model's predictions in an interactive, intuitive format
- Be built with Streamlit, Gradio, NextJS, or a custom web framework

## Step-by-Step Checklist

### 1. Choose a Dataset and Define the Problem

- Select a public dataset (e.g., Kaggle, UCI, HuggingFace Datasets).
- Define a supervised learning task (classification or regression).
- Identify your target variable and evaluation metric.

### 2. Set Up Data Storage in the Cloud

- Clean and preprocess the dataset locally.
- Upload your cleaned data to a cloud storage service:
    - Google Cloud Storage (GCS)
    - AWS S3
    - Firebase Storage
    - Cloud-hosted PostgreSQL (e.g., via Google Cloud SQL or Supabase)
- Write a script to access and download the data programmatically in your pipeline.

### 3. Build a Reproducible ML Pipeline

- Choose a simple model (e.g., logistic regression, random forest, XGBoost).
- Implement a pipeline that includes:
    - Data ingestion (from the cloud)
    - Preprocessing and feature engineering
    - Train/validation/test split
    - Model training and evaluation
- Control parameters via a `config.yaml` file (e.g., learning rate, split ratio, etc.).

> NOTE: We are not assessing your ML model. Your model could have terrible accuracy. That is fine! Not the point of the assignment, don't get hung up on your model.

### 4. Track Experiments

Use MLFlow or Weights & Biases to:

- Track experiment runs, model parameters, and evaluation metrics.
- Log artifacts (trained model, plots, etc.) for version control and reproducibility.

### 5. Containerize with Docker

Create a Dockerfile that:

- Installs all dependencies.
- Includes entry points for training and serving.

Build and run your Docker image locally to test reproducibility.

### 6. Serve Your Model as an API

Use FastAPI or Flask to:

- Load your trained model.
- Create a `/predict` endpoint that accepts JSON input and returns a prediction.
- Test your API locally using curl or Postman.

### 7. Deploy the API to the Cloud

Choose a cloud deployment platform:

- Google Cloud Run or Cloud Functions
- AWS Lambda with API Gateway
- Azure Functions

Package your API and deploy it so that the `/predict` endpoint is publicly accessible. Confirm your endpoint works using an HTTP request with test data.

### 8. Build the Front-End Interface

- Create a lightweight UI using Streamlit, Gradio, or a simple web app.
- Collect user input, send it to the deployed API using requests or fetch, and display the prediction.
- Host your app on Hugging Face Spaces, Streamlit Cloud, Vercel [all free!], or a custom deployment platform.
- Include the link to the live front-end in your README.

### 9. Document Everything and Follow Best Practices

Your GitHub README must include:

- Project overview and goals
- Dataset description and link
- Model architecture and evaluation
- Cloud services used
- Setup and usage instructions
- Link to deployed API and front-end app
