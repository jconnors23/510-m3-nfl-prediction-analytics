"""Score a fitted model and draw the validation confusion matrix.

The picture says which picks were right and which were wrong. This file does not
record runs and does not read any file.
"""

from pathlib import Path

import matplotlib

# A training machine may have no display. Agg draws the image without opening a window.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from sklearn.metrics import confusion_matrix, log_loss

from src.model.features import INPUT_COLUMNS

# The site's link color for a correct pick, and its action color for a wrong pick.
CORRECT_COLOR = "#5b21b6"
WRONG_COLOR = "#c2410c"


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


def confusion_cell_labels(matrix) -> list[list[dict]]:
    """Each cell's count, its share of that row, and whether the pick was right."""
    labels = []
    for row_index, row in enumerate(matrix):
        total = int(sum(row))
        # Row 0 is the games the away team won. Row 1 is the games the home team won.
        outcome = "away wins" if row_index == 0 else "home wins"
        cells = []
        for column_index, count in enumerate(row):
            count = int(count)
            if total == 0:
                share = "no games"
            else:
                share = f"{100 * count / total:.1f}% of {outcome}"
            cells.append(
                {
                    "count": str(count),
                    "share": share,
                    # The diagonal is a right pick: the model chose the team that won.
                    "verdict": "Correct" if row_index == column_index else "Wrong",
                }
            )
        labels.append(cells)
    return labels


def plot_confusion_matrix(pipeline, group, path) -> Path:
    """Save the group's picks against the real results as a 2 by 2 picture, and return its path.

    Correct picks are purple and wrong picks are orange. Each cell shows its count, its share of
    the row, and the word Correct or Wrong, and the title states the accuracy and how often the
    model picked the home team.
    """
    probability = pipeline.predict_proba(group[INPUT_COLUMNS])[:, 1]
    # The same 0.5 rule as the score, so the picture counts the same picks.
    picked_home = (probability > 0.5).astype(int)
    happened = group["home_win"].to_numpy()
    # A 2 by 2 table of counts: the rows are what really happened (away win, home win) and the
    # columns are what the model picked. The diagonal cells are the correct picks.
    matrix = confusion_matrix(happened, picked_home, labels=[0, 1])
    labels = confusion_cell_labels(matrix)
    # The year comes from the games in this group, so a different validation season renames the figure.
    season = int(group["season"].iloc[0])
    games = int(len(group))
    correct = int((picked_home == happened).sum())
    home_picks = int(picked_home.sum())
    home_wins = int((happened == 1).sum())
    figure, axes = plt.subplots(figsize=(8.4, 6.6))
    # The grid is drawn by hand in a 2 by 2 space, one unit per cell, so the color can mean right
    # or wrong. scikit-learn's standard drawing colors a cell by the size of its count.
    axes.set_xlim(0, 2)
    axes.set_ylim(0, 2)
    # Square cells, whatever the figure's shape.
    axes.set_aspect("equal")
    for row_index, row in enumerate(labels):
        # Row 0 is drawn at the top, so the away-win row is read first.
        bottom = 1 - row_index
        for column_index, cell in enumerate(row):
            color = CORRECT_COLOR if row_index == column_index else WRONG_COLOR
            # A white edge on each cell makes one 2-point line where two cells meet.
            axes.add_patch(
                Rectangle(
                    (column_index, bottom),
                    1,
                    1,
                    facecolor=color,
                    edgecolor="white",
                    linewidth=2,
                )
            )
            center_x = column_index + 0.5
            axes.text(
                center_x,
                bottom + 0.62,
                cell["count"],
                ha="center",
                va="center",
                color="white",
                fontsize=22,
                fontweight="bold",
            )
            axes.text(
                center_x,
                bottom + 0.40,
                cell["share"],
                ha="center",
                va="center",
                color="white",
                fontsize=9.5,
            )
            axes.text(
                center_x,
                bottom + 0.24,
                cell["verdict"],
                ha="center",
                va="center",
                color="white",
                fontsize=9.5,
                fontweight="bold",
            )
    # Ticks at each cell's center. The column labels go above the grid, and the axis name below it.
    axes.set_xticks([0.5, 1.5])
    axes.set_xticklabels(["Picked away win", "Picked home win"])
    axes.xaxis.tick_top()
    row_totals = [int(sum(row)) for row in matrix]
    axes.set_yticks([1.5, 0.5])
    axes.set_yticklabels(
        [
            f"Away team won\n({row_totals[0]} games)",
            f"Home team won\n({row_totals[1]} games)",
        ]
    )
    axes.tick_params(length=0, labelsize=11)
    for spine in axes.spines.values():
        spine.set_visible(False)
    axes.set_xlabel("What the model picked", fontweight="bold", labelpad=12)
    axes.set_ylabel("What actually happened", fontweight="bold")
    # The legend sits under the axis name, in one row, and has no frame of its own.
    axes.legend(
        handles=[
            Patch(facecolor=CORRECT_COLOR, edgecolor="none", label="Correct pick"),
            Patch(facecolor=WRONG_COLOR, edgecolor="none", label="Wrong pick"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.16),
        ncol=2,
        frameon=False,
        handlelength=1.4,
        handleheight=1.1,
    )
    # The three title lines sit against each other, and the grid starts just below them. Figure
    # text is placed in fractions of the figure (0 to 1). x=0.58 is halfway between left=0.18 and
    # right=0.98, so the title is centered over the plot area and not over the row labels.
    figure.subplots_adjust(top=0.84, bottom=0.16, left=0.18, right=0.98)
    figure.text(
        0.58,
        0.99,
        f"Validation {season}: Model Picks vs Actual Results",
        ha="center",
        va="top",
        fontsize=13,
        fontweight="bold",
    )
    figure.text(
        0.58,
        0.948,
        f"{correct} of {games} games picked correctly ({100 * correct / games:.1f}%).",
        ha="center",
        va="top",
        fontsize=10,
    )
    figure.text(
        0.58,
        0.908,
        f"The model picked the home team in {home_picks} games, and the home team won {home_wins}.",
        ha="center",
        va="top",
        fontsize=10,
    )
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(destination, dpi=150, bbox_inches="tight")
    plt.close(figure)
    return destination
