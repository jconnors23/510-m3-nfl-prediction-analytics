---
hide:
  - toc
---

# Confusion Matrix

Every training run stores one picture in MLflow: the model's picks against the real results for the 2025 validation games. It is drawn by `plot_confusion_matrix` in `src/model/evaluate.py`, saved as `confusion_matrix_validation.png`, and copied into each run's folder in `mlflow-reference/`. The table the picture shows, and why validation is the season scored, are in [What Does the Confusion Matrix Show?](../phase-2/implementation-part-2.md#what-does-the-confusion-matrix-show).

![The validation confusion matrix for 2025: correct picks in purple and wrong picks in orange, each cell with its count, its share of the row, and the word Correct or Wrong, under the title Model Picks vs Actual Results](./images/confusion-matrix.png){ width="520" }

## How Do I Read It?

- **Color means right or wrong.** Correct-pick cells are purple (`#5b21b6`) and wrong-pick cells are orange (`#c2410c`), the site's link and action colors. Both carry white text, at contrast ratios of 9.0 to 1 and 5.2 to 1, above the 4.5 to 1 minimum for text.
- **Rows are what actually happened,** and columns are what the model picked. Each row label carries its game count: the away team won 125 games and the home team won 146.
- **Each cell gives three things:** the count in large bold type, the share of that row, and the word "Correct" or "Wrong".
- **Each row's share uses that row's games.** "49.6% of away wins" means 62 of the 125 games the away team won. The model got 74.7% of home wins right (109 of 146) but only 49.6% of away wins.
- **The title block** states the accuracy ("171 of 271 games picked correctly (63.1%).") and the main pattern: the model picked the home team in 172 games, while the home team won 146.
- **A legend** under the grid names the two colors.
- **Every number comes from the data,** never typed in: the season, the counts, the shares, the correct total, and the home picks.

## How Is It Drawn?

- **`confusion_cell_labels(matrix)`** in `src/model/evaluate.py` returns each cell's count, share, and verdict as text. A row with no games gets the share "no games". It reads nothing and draws nothing, so the wording is tested without opening the image.
- **`plot_confusion_matrix(pipeline, group, path)`** counts the picks with the same 0.5 rule as the scores, draws the four cells as rectangles, writes the text from `confusion_cell_labels`, and saves the picture at 150 dots per inch. It is 1004 by 1008 pixels and 87,311 bytes. It uses matplotlib's non-window drawing mode (`Agg`), so no window opens.
- **The two colors** are set once, as `CORRECT_COLOR` and `WRONG_COLOR`.
- **Tests in `tests/test_evaluate.py`:** `test_cell_labels_give_counts_row_shares_and_right_or_wrong` checks all four cells for the real validation counts, `test_cell_labels_handle_a_row_with_no_games` checks the empty-row case, and `test_plot_writes_a_png_without_a_window` checks that the picture is a non-empty PNG.
- **The picture does not affect the model.** It is drawn after the model is fit, so the scores, `results/run-summary.json`, and `models/model.joblib` do not depend on it.
