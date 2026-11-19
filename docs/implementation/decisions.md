---
hide:
  - toc
---

# Decisions

The project-wide choices, and the choices for phases not built yet, with the reason for each and what was turned down. Phase 1 choices are at the end of the [Phase 1 Implementation Details](./phase-1/implementation-details.md#which-choices-were-made). Choices still needing the developer's approval are in [Open Decisions](#open-decisions).

## Model Inputs (Decided, Not Yet Built)

- **Two raw per-game inputs replace the two rank inputs.** They are the home team's win percentage minus the away team's, and the home team's point margin per game minus the away team's. Both use only earlier weeks of the same season. A team with no games counts as 0.5 and 0.0, so week 1 gives 0 for both inputs.
- **Why the change.** Ranks drop the size of a gap (a +14 team and a +2 team can be neighbors), create ties in early weeks, and change when unrelated teams win. Raw values keep the gap, need no tie rule, and read directly ("+7.3 points per game better").
- **Scores were similar,** so the reason is clarity, not accuracy. On the current data, logistic regression with ranks got 169 of 271 validation games right (62.36%, log loss 0.6345) and 92 of 149 live games (61.74%). With raw inputs it got 171 of 271 (63.10%, log loss 0.6451) and 88 of 149 (59.06%).
- **Per game, not season totals,** so a team that has played more games, for example after a bye, is not favored.
- **Home minus away,** so a positive value favors the home team.
- **`rank_gap`, `mismatch`, and `record_ahead_by` are removed.** They were display-only columns for the web app and never model inputs.

## Phase Boundaries (Decided)

- **Phase 1 is fetch, clean, upload, and download from S3.** It has no feature or front-end work.
- **Phase 2 starts with the features and the split,** then trains and tracks.
- **The team-profile file for the web app belongs to Phase 5,** and its code moves to `src/profiles.py`.
- **Phases 3 to 5 share one high-level page** ([Remaining Phases](./remaining-phases.md)) until they begin.
- **No notebooks.** They repeated the scripts and the docs.
- **Split by season.** Training is 2020 to 2024 (1,339 games), validation is 2025 (271), and live is 2026 weeks 1 to 10 (149). The live games are not used to fit or choose the model.

## Open Decisions

Each shows the proposed answer first.

- **How the 2025 validation season is used.** Proposed: it chooses the model type and supplies the reported score, and the live games are reported separately. Alternative: fix logistic regression, or choose using held-out seasons inside 2020 to 2024.
- **Whether to drop week 1 from the model table.** Proposed: keep it for now. Details are in the next section.
- **The Phase 3 to 5 choices** (probability field name, one Dockerfile or two, no `deploy.yml`, no API key, one standings snapshot, Vite template) are in [Remaining Phases](./remaining-phases.md#open-decisions).

## Open Decision: Start From Week 2 (Not Done)

**Status: open. Nothing has been changed.** Week 1 is still kept in the model table.

- **The question:** should the model table drop the 111 week-1 games, so each season starts at week 2?
- **What happens now:** before week 1 no team has a result, so both inputs are 0 for every week-1 game. The trained model then picks the home team in every week-1 game (home win probability 0.537 when both inputs are 0, in the rank version).
- **What the data shows (rank version):**
    - Week 1 has 111 model rows: 79 training, 16 validation, and 16 live (5.9%, 5.9%, and 10.7% of each group).
    - Home teams won 52.25% of week-1 games and 52.97% of games in weeks 2 and later.
    - 2025 validation accuracy on weeks 2 to 18 was 62.7% with week 1 in training and 62.4% without it, a 0.3-point change.
    - 2025 validation accuracy on week 1 alone was 56.2% (16 games), the same as always picking the home team.
- **Effect of dropping it:** the model would stop reporting week-1 scores that come from no information. Row counts become 1,260 training, 255 validation, and 133 live. The cleaned table and the S3 file do not change, because week-1 results still count toward each team's record.
- **Not fixed by dropping it:** early weeks still carry little information. With ranks, there were only 2 distinct record ranks before week 2 of 2025, 3 before week 3, and 8 before week 6.
- **Proposed answer:** keep week 1 for now.
- **Work needed if accepted:** filter week 1 out of the model table in `src/features.py`, update its test, and refresh the expected scores on the [Phase 2 synopsis](./phase-2/synopsis.md).

## Model and API (Planned)

- **Logistic regression,** with a random forest as the only other candidate. XGBoost was dropped to keep the serving image small.
- **A standardizing step is kept** and saved with the model as one pipeline, so the API cannot skip it. The two inputs are on different scales: win percentage differences run from -1 to 1 and point margin differences run about -49 to 39.
- **MLflow tracks each run.** The run record stays local and is not committed. The README's results table is the permanent record.
- **The API takes two decimal numbers** (the win percentage difference and the point margin per game difference), rejects unknown fields, and returns `prediction`, `predicted_label`, `home_win_probability`, and `model_version`. A `GET /health` route is an extra.
- **One Dockerfile with two targets,** `train` and `serve`. The model file is copied in at build time. It is not committed to git and is not downloaded at start-up.
- **A smaller dependency list for serving,** so the image starts faster after idle time.

## Cloud and Front-End (Planned)

- **AWS only:** S3, ECR, Lambda behind an API Gateway HTTP API, and CloudFront. Turned down: the Google Cloud and Azure options in the assignment brief.
- **One region, `us-east-1`,** because the data bucket is already there. Decided.
- **Lambda runs an `arm64` image,** to match the images this Mac builds.
- **CORS is set on the gateway only,** with the CloudFront address and the local Vite address allowed.
- **The front-end is a Vite app.** The development server is for local work only. The published site is the built static files in a private S3 bucket behind CloudFront. Turned down: Streamlit, and S3's own website hosting (it serves only HTTP and needs a public bucket).
- **The API is public, with no key.** It has a request limit (5 per second, burst of 10) and a budget alert. A key in a browser app would be visible to every visitor.
- **Deployment is a set of written steps,** with no `deploy.yml` workflow.
- **The web app reads one snapshot of the standings,** taken after 2026 week 10.

## Documentation and Process

- **MkDocs with the Material theme** and no right-hand contents list. The theme is light, with sky blue as the main color.
- **The assignment brief and the project requirements are kept unchanged** in `docs/initial-requirements/`. They are the only two reference documents. The first design draft and the gap list were removed.
- **A phase gets full pages only once it is built.** Phases 1 and 2 have a synopsis (Phase 1 also has implementation details). Phases 3 to 5 share one high-level page.
- **Each synopsis copies its requirements word for word** from the Project Requirements, next to what the phase does.
- **Each implementation step has a purpose block** (Goal, Why, If skipped).
- **Cursor builds the code from a written spec, and the docs are written from the finished code.** Kiro writes a spec in `specs/` with what to build and the numbers to match, Cursor builds it and ends with a deviations report, and the developer, Kiro, and the report are reviewed together before the next spec.
- **Git is run by the developer only.** Phases 1 and 2 go in one branch and one pull request, and the developer names the branch.
