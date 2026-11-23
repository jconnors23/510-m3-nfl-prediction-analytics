"""Tests for scoring and the confusion-matrix image.

The probabilities come from a stand-in object and the games are made up, so nothing is trained
and no file in the project is written. The picture goes to pytest's temporary folder.
"""

import matplotlib
import numpy as np
import pandas as pd
import pytest

from src.model.evaluate import confusion_cell_labels, plot_confusion_matrix, score_group
from src.model.features import INPUT_COLUMNS


class _FixedProbabilities:
    """Return one home-win probability per row, ignoring the table values."""

    def __init__(self, probabilities):
        """Keep the home-win probabilities to hand back, one per game."""
        self.probabilities = probabilities

    def predict_proba(self, frame):
        """Return [away chance, home chance] for each game, the way a scikit-learn model does."""
        positive = np.asarray(self.probabilities, dtype=float)
        return np.column_stack([1 - positive, positive])


def _group(probabilities, results, season=2025) -> pd.DataFrame:
    """A small group with the two input columns, a result, and a season."""
    frame = pd.DataFrame(
        {
            INPUT_COLUMNS[0]: [0.0] * len(results),
            INPUT_COLUMNS[1]: [0.0] * len(results),
            "home_win": results,
            "season": [season] * len(results),
        }
    )
    return frame


def test_hand_checked_scores():
    """Probabilities 0.9, 0.6, 0.5, and 0.2 with results 1, 0, 0, 0 score 3 of 4."""
    # Home picks are 0.9 and 0.6 (0.5 is an away pick), so the picks are 1, 1, 0, 0 against
    # results 1, 0, 0, 0. Three match. The baseline is the share of home wins, 1 of 4.
    group = _group([0.9, 0.6, 0.5, 0.2], [1, 0, 0, 0])
    scores = score_group(_FixedProbabilities([0.9, 0.6, 0.5, 0.2]), group)
    assert scores["correct"] == 3
    assert scores["games"] == 4
    # Exact comparison is fine for 3/4 and 1/4, which a float stores exactly. Log loss uses
    # logarithms, so it is compared to four decimals. The hand value is the average of
    # -ln(0.9), -ln(0.4), -ln(0.5), and -ln(0.8), which is 0.4845.
    assert scores["accuracy"] == 0.75
    assert scores["baseline"] == 0.25
    assert scores["log_loss"] == pytest.approx(0.4845, abs=0.0001)


def test_exact_half_is_an_away_pick():
    """A probability of exactly 0.5 is an away pick: right when the away team wins, wrong when the home team does."""
    away_won = score_group(_FixedProbabilities([0.5]), _group([0.5], [0]))
    home_won = score_group(_FixedProbabilities([0.5]), _group([0.5], [1]))
    assert away_won["correct"] == 1
    assert home_won["correct"] == 0


def test_one_outcome_still_has_a_log_loss():
    """A group where every game has the same result still returns a log loss."""
    # Some log-loss functions need both classes present in the results and fail otherwise.
    # Here the hand value is the average of -ln(0.9) and -ln(0.8), which is 0.1643.
    group = _group([0.9, 0.8], [1, 1])
    scores = score_group(_FixedProbabilities([0.9, 0.8]), group)
    assert scores["log_loss"] == pytest.approx(0.1643, abs=0.0001)


def test_plot_writes_a_png_without_a_window(tmp_path):
    """The confusion matrix is a non-empty PNG, drawn without opening a window."""
    group = _group([0.9, 0.2], [1, 0])
    destination = tmp_path / "confusion_matrix_validation.png"
    saved = plot_confusion_matrix(_FixedProbabilities([0.9, 0.2]), group, destination)
    assert saved == destination
    assert destination.is_file()
    assert destination.stat().st_size > 0
    # Agg draws to a file only. A window-based backend would fail on a computer with no display.
    assert matplotlib.get_backend().lower() == "agg"


def test_cell_labels_give_counts_row_shares_and_right_or_wrong():
    """The 2025 validation counts name each cell's share and whether the pick was right."""
    labels = confusion_cell_labels([[62, 63], [37, 109]])
    assert labels == [
        [
            {"count": "62", "share": "49.6% of away wins", "verdict": "Correct"},
            {"count": "63", "share": "50.4% of away wins", "verdict": "Wrong"},
        ],
        [
            {"count": "37", "share": "25.3% of home wins", "verdict": "Wrong"},
            {"count": "109", "share": "74.7% of home wins", "verdict": "Correct"},
        ],
    ]


def test_cell_labels_handle_a_row_with_no_games():
    """A row with no games says so, and the other row still gives its shares."""
    # A small group can have no away wins at all. Its share would divide by zero, so it reads
    # "no games" instead.
    labels = confusion_cell_labels([[0, 0], [1, 1]])
    assert [cell["share"] for cell in labels[0]] == ["no games", "no games"]
    assert [cell["share"] for cell in labels[1]] == ["50.0% of home wins", "50.0% of home wins"]
    assert [cell["verdict"] for row in labels for cell in row] == ["Correct", "Wrong", "Wrong", "Correct"]
