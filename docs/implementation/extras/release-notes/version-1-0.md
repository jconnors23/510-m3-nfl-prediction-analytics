---
hide:
  - toc
---

# Version 1.0 Release Notes

Version 1.0 is the first complete release of the NFL pre-game winner predictor, built for Duke AIPI 510. It was released on **November 23, 2026**, and it serves model version `v1.0`. The data is a fixed snapshot through 2026 week 10, and nothing in this release updates it.

## What Is in the Release?

| Part | Where it runs | State in version 1.0 |
| :--- | :--- | :--- |
| Data | Amazon S3, and committed in `data/` | nflverse regular-season games, 2020 through 2026 week 10, without ties: 1,759 games |
| Model | Saved in `models/model.joblib`, and inside the Lambda zip | A standard scaler and a logistic regression on two inputs, labeled `v1.0` in `config/config.yaml` |
| Training record | MLflow, and committed in `mlflow-reference/` | Run `49a0841f`, tagged with commit `9562f88` on `main` |
| Prediction API | AWS Lambda behind API Gateway | `POST /predict` and `GET /health` at `https://9awodatqc5.execute-api.us-east-1.amazonaws.com` |
| Web app | Amazon S3 and CloudFront | Five tabs: Overview, Games by Week, Custom Matchup, Team Stats, and Feedback, at `https://d1nubiunzfwm0q.cloudfront.net` |
| Docker images | A laptop only | A `train` image and a `serve` image from one `Dockerfile` |
| Docs site | GitHub Pages | This site |

## How Well Does Version 1.0 Predict?

- **Validation accuracy: 63.10%** (171 of 271 games in 2025), against 53.87% for always picking the home team.
- **Test accuracy: 59.06%** (88 of 149 games in 2026 weeks 1 to 10), against 47.65%.

How the scores are worked out is on [ML Workflow](../architecture/ml-workflow.md).

## How Was the Release Checked?

- **Tests:** 95 Python tests and 62 web app tests pass, as listed on the [Testing Guide](../development/testing-guide.md).
- **The live API matches the local model** on every game (1,759), every ordered pair of teams (992), and every 2026 game (272), with 0 mismatches.
- **Four GitHub workflows** test the Python code and the web app on pull requests, and publish the docs site and the web app. See [GitHub Workflows](../development/github-workflows.md).
- **Every requirement of the assignment is met,** as shown on the [Requirements Rubric](../../requirements/requirements-rubric.md). The final review is on the [Phase 7 Brief](../../phase-7/brief.md).

## What Does Version 1.0 Leave Out?

- **New results after 2026 week 10.** The standings, the web app, and the model all stop at that week.
- **Automatic updates.** Every step, from the download to the deploy, is started manually.
- **Inputs beyond the two standings numbers,** such as injuries, rest days, and weather.

Ideas for a later version are on [Future Considerations](./future-considerations.md).
