---
hide:
  - toc
---

# Extras Brief: Tools and Add-Ons Outside the Phases

Some work in this project does not belong to any one phase. It supports every phase (the make commands and the GitHub workflows), adds a feature beyond the assignment (the feedback form), or improves an output after its phase was done (the confusion-matrix picture). This section collects those pieces in one place, so each phase's pages describe only that phase's work.

**Status:** the make commands, the two workflows, the feedback form, the MLflow run history, the docs site, and the confusion-matrix picture are built. The README is not written yet.

## What Is in This Section?

### Make Commands and GitHub Workflows (Built)

- **The `Makefile`** holds the nine commands used most: training, the two test suites, the API, the web app, the MLflow screen, the docs preview, and the two Docker commands.
- **Two GitHub Actions workflows** publish the project when a change reaches `main`. `deploy-docs.yml` builds and publishes this docs site, and `deploy-web-app.yml` tests, builds, and publishes the web app.
- See [Make Commands and GitHub Workflows](./developer-tools.md).

### The Feedback Form (Built)

- **A Feedback tab** on the web app lets a visitor send a category, an optional 1 to 5 rating, and a message. No personal details are asked for.
- **A separate AWS function and table** save each message, so the prediction function is not touched.
- See [The Feedback Form](./feedback-form.md).

### The Confusion-Matrix Picture (Built)

- **Each training run stores one picture** of the model's picks against the real results for the 2025 validation games.
- **It was redrawn after Phase 2** so the colors mean right and wrong, each cell shows its share of the row, and the axes use plain words.
- See [The Confusion-Matrix Picture](./confusion-matrix.md).

### The MLflow Run History (Built)

- **`mlflow-reference/`** is a committed, readable log of every training run, so the MLflow logging can be read on GitHub without running anything. Each `make train` moves the last run into `previous-runs/` and writes the new one to `latest-run/`.
- See [How Do I Do a Training Run?](../phase-2/development-guide.md#how-do-i-do-a-training-run) and the folder's own [README](https://github.com/jconnors23/510-m3-nfl-prediction-analytics/tree/main/mlflow-reference).

### The Docs Site (Built)

- **These pages** are built with MkDocs and the Material theme, in the web app's colors, with a light and a dark theme. A strict build fails on any broken link.
- **They are published to GitHub Pages** by `deploy-docs.yml`. See [Make Commands and GitHub Workflows](./developer-tools.md#how-are-the-docs-published).

### The README (Not Written Yet)

- **The front page of the repository** will give the project overview, the dataset, the model and its result, the cloud services, setup and usage steps, and links to the live API, the live web app, and this site.
- It is written in [Phase 7](../remaining-phases.md#phase-7-documentation-and-readme), once every phase is built.

## Where to Read More

- [Decisions](../decisions.md) explains the choices behind each piece.
- [Requirements Map](../requirements/requirements-map.md) shows which requirement each piece covers.
