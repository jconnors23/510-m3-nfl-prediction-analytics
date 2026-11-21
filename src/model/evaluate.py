"""Score a fitted model and draw the validation confusion matrix.

This file does not record runs and does not read any file.
"""

from pathlib import Path

import matplotlib

# A training machine may have no display. Agg draws the image without opening a window.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix, log_loss

from src.model.features import INPUT_COLUMNS


def score_group(pipeline, group) -> dict:
    """Accuracy, the always-home baseline, and log loss for one group."""
    # Keep the column names so the pipeline applies the inputs in the saved order.
    # predict_proba gives two columns per game: the chance of an away win, then of a home win.
    # [:, 1] keeps the home-win chance, a number from 0 to 1.
    probability = pipeline.predict_proba(group[INPUT_COLUMNS])[:, 1]
    # Exactly 0.5 is an away pick. Only a higher probability picks the home team.
    picked_home = (probability > 0.5).astype(int)
    home_win = group["home_win"].to_numpy()
    games = int(len(group))
    correct = int((picked_home == home_win).sum())
    # baseline is the accuracy of always picking the home team. log_loss grades the percentages,
    # not just the picks, and lower is better.
    return {
        "games": games,
        "correct": correct,
        "accuracy": correct / games,
        "baseline": float((home_win == 1).mean()),
        # labels=[0, 1] tells log_loss both outcomes exist even if a small group has only one.
        "log_loss": float(log_loss(home_win, probability, labels=[0, 1])),
    }


def plot_confusion_matrix(pipeline, group, path) -> Path:
    """Save the group's confusion matrix and return the image path."""
    probability = pipeline.predict_proba(group[INPUT_COLUMNS])[:, 1]
    # The same 0.5 rule as the score, so the picture counts the same picks.
    picked_home = (probability > 0.5).astype(int)
    # A 2 by 2 table of counts: the rows are what really happened (away win, home win) and the
    # columns are what the model picked. The diagonal cells are the correct picks.
    matrix = confusion_matrix(group["home_win"], picked_home, labels=[0, 1])
    figure, axes = plt.subplots(figsize=(5, 4.5))
    ConfusionMatrixDisplay(matrix, display_labels=["Away win", "Home win"]).plot(
        ax=axes,
        colorbar=False,
        cmap="Blues",
        values_format="d",
    )
    # The year comes from the games in this group, so a different validation season renames the figure.
    season = int(group["season"].iloc[0])
    correct = int((picked_home == group["home_win"].to_numpy()).sum())
    figure.suptitle(f"Validation {season}: Predicted vs Actual", fontweight="bold")
    axes.set_title(f"{correct} of {len(group)} games were picked correctly")
    axes.set_xlabel(axes.get_xlabel(), fontweight="bold")
    axes.set_ylabel(axes.get_ylabel(), fontweight="bold")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return destination
