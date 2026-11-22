---
hide:
  - toc
---

# Remaining Phases

Phases 1 to 5 are built. Each has its own pages, the latest being [Phase 4](./phase-4/brief.md) (AWS deployment) and [Phase 5](./phase-5/brief.md) (the web app, live at [https://d1nubiunzfwm0q.cloudfront.net](https://d1nubiunzfwm0q.cloudfront.net)). Phases 6 to 8 are not started, so this page stays high level. Each phase gets a detailed page when it begins.

The order is: Docker, then the documentation and README, then a final review. Docker comes after the web app because nothing before it needs an image. AWS Lambda runs the API from a zip file, so there is no container registry unless the zip turns out to be too large (see the [Phase 4 Brief](./phase-4/brief.md#what-if-the-zip-is-too-large)). The README and the review come last because they describe and check the finished project.

```mermaid
flowchart LR
    C["Phase 5:<br/>web app + hosting<br/>(built)"] --> D["Phase 6:<br/>Docker"]
    D --> E["Phase 7:<br/>documentation<br/>and README"]
    E --> F["Phase 8:<br/>review"]
```

## Phase 6: Docker

Package the project so it runs from a container.

- **Write one Dockerfile with two targets,** `train` and `serve`, that installs every dependency and gives one entry point for training and one for serving. The image must build and run on a laptop. Both targets use the same Python version and package pins as everything before it.
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
