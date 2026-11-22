---
hide:
  - toc
---

# Remaining Phases

Phases 1 to 4 are built. Each has its own pages, the latest being [Phase 3](./phase-3/brief.md) (local API) and [Phase 4](./phase-4/brief.md) (AWS deployment, with an [implementation page](./phase-4/implementation.md)). Phases 5 to 8 are not started, so this page stays high level. Each phase gets a detailed page when it begins.

The order is: the web app, then Docker, then the documentation and README, then a final review. Docker is after the web app because nothing before it needs an image. AWS Lambda runs the API from a zip file, so there is no container registry unless the zip turns out to be too large (see the [Phase 4 Brief](./phase-4/brief.md#what-if-the-zip-is-too-large)). The README and the review come last because they describe and check the finished project.

```mermaid
flowchart LR
    C["Phase 5:<br/>web app + hosting"] --> D["Phase 6:<br/>Docker"]
    D --> E["Phase 7:<br/>documentation<br/>and README"]
    E --> F["Phase 8:<br/>review"]
```

## Phase 5: Web App and Hosting

Build the part a person uses.

- **Build a Vite web app.** The user picks a home team and an away team, the app calls the API, and it shows the predicted winner and probability.
- **Build the team profiles file** (`python -m src.profiles`), which holds each team's record, win percentage, and point margin per game, so the browser can compute the two inputs.
- **Develop against the local API first.** The Vite development server can forward `/predict` requests to the local API, which avoids needing CORS while working locally. Then point the app at the live API.
- **Host the built files** in a private S3 bucket served over HTTPS through CloudFront. Add the CloudFront address to the gateway's CORS settings.

## Phase 6: Docker

Package the project so it runs from a container.

- **Write a Dockerfile** that installs every dependency and has entry points for both training and serving. The image must build and run on a laptop. It uses the same Python version and package pins as everything before it.
- **Check the image gives the same answers.** The container must return the same probability as the local API for the worked example.

## Phase 7: Documentation and README

Write the front door of the repository, and make the docs match the finished project.

- **Write the README** with the project overview and goals, the dataset and its link, the model and its result, the cloud services used, setup and usage steps (how to train the model, how to build and test the API locally, and how to deploy to the cloud), and links to the live API and the live web app.
- **Check the docs against the finished code.** Every page describes what exists, every number is recomputed from the data or the code, and every link resolves in a strict docs build.
- **Complete the requirements map** so every requirement has the file, function, setting, or command that covers it, and the docs page that explains it.
- **Check the comments and docstrings** in the code read plainly and match what the code does.
- **Keep the docs site published on GitHub Pages** by the `deploy-docs.yml` workflow, and link it from the README.

## Phase 8: Review

Check the finished project against the requirements before it is handed in.

- **Walk the acceptance checklist** item by item, and write down the evidence for each one.
- **Rebuild from a clean checkout,** following only the README. Train, run the tests, and start the API locally, and note anything the README leaves out.
- **Run the pre-commit checks:** no secrets or generated files are tracked, local-only files are ignored, relative links resolve, and the docs match the latest code.
- **Review the code and configuration independently,** and fix or note each finding.
- **Check the repository contents:** code, `config.yaml`, a dependency file, a Dockerfile, MLflow logging, a clear structure, and at least one merged pull request.
- **Check the live API and the live web app** with real requests.

## Open Decisions

Each shows the proposed answer first.

- **Dockerfile layout.** Proposed: one file with `train` and `serve` targets. Alternative: two Dockerfiles.
- **Standings in the app.** Proposed: one snapshot after 2026 week 10. Alternative: standings for each of weeks 1 to 10 with a week picker.
- **Vite template.** Proposed: React with TypeScript. Alternative: plain TypeScript or JavaScript.

The settled hosting and API choices are in [Decisions](./decisions.md).
