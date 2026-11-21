---
hide:
  - toc
---

# Remaining Phases

Phases 3 to 5 are not started, so this page stays high level. Each phase gets a detailed page when it begins.

## Phase 3: API and Docker

Wrap the trained model in a small web service and package the project in Docker.

- **Serve the model with FastAPI.** One `POST /predict` route takes the two model inputs as JSON and returns the prediction and the home win probability as JSON. A `GET /health` route reports the model version.
- **Reject bad input.** A missing, unknown, or out-of-range field returns a clear error.
- **Test it locally** with `curl` or Postman before Docker and before AWS.
- **Write a Dockerfile** that installs every dependency and has entry points for both training and serving. The image must build and run on a laptop.
- **Make the service Lambda-ready** with the Mangum adapter, which lets FastAPI run inside AWS Lambda.
- **Keep the serving image small.** Use a shorter dependency list, and the same scikit-learn version as training, so the saved model loads.

## Phase 4: AWS Deployment

Put the API on the internet.

- **Store the serving image** in a private Amazon ECR repository, tagged with the model version.
- **Run it on AWS Lambda** as a container image, behind an API Gateway HTTP API in `us-east-1` (already decided).
- **Set CORS on the gateway** so the browser web app can call `/predict`.
- **Check the public endpoint** with real test requests. It must return a valid response.
- **Limit permissions and cost.** Each AWS identity gets only the access its job needs. Set a request limit and a budget alert.
- **Write the deployment steps down** so they can be repeated by hand.

## Phase 5: Web App, README, and Final Check

Build the part a person uses, and finish the repository.

- **Build a Vite web app.** The user picks a home team and an away team, the app calls the live API, and it shows the predicted winner and probability.
- **Build the team profiles file** (`python -m src.profiles`), which holds each team's record, win percentage, and point margin per game, so the browser can compute the two inputs.
- **Host the built files** in a private S3 bucket served over HTTPS through CloudFront.
- **Write the README** with the project overview, the dataset and its link, the model and its result, the cloud services used, setup and usage steps, and links to the live API and the live web app.
- **Run a final check** that the repository holds code, `config.yaml`, a dependency file, a Dockerfile, MLflow logging, a clear structure, and at least one merged pull request.

## Open Decisions

Each shows the proposed answer first.

- **Probability field name.** Proposed: `home_win_probability`. Alternative: `win_probability`, with a written rule that it is the home team's chance.
- **Dockerfile layout.** Proposed: one file with `train` and `serve` targets. Alternative: two Dockerfiles.
- **Repeating the deployment.** Proposed: written command-line steps, no `deploy.yml`. Alternative: a GitHub Actions workflow.
- **API key.** Proposed: no key, with a request limit and a budget alert, because a key in a browser app is visible to every visitor. Alternative: an API key.
- **Standings in the app.** Proposed: one snapshot after 2026 week 10. Alternative: standings for each of weeks 1 to 10 with a week picker.
- **Vite template.** Proposed: React with TypeScript. Alternative: plain TypeScript or JavaScript.

The settled hosting and API choices are in [Decisions](./decisions.md).
