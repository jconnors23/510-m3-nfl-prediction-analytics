"""The JSON a caller may send, and the JSON the service sends back.

These definitions are the one place the input rules are written. FastAPI uses them to check each
request, to build the error messages, and to draw the test page at /docs.
"""

from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    """The two pre-game numbers. Extra fields are refused so a typo is not ignored."""

    # extra="forbid" rejects unknown fields. strict=True rejects a number written as text
    # ("0.5") or a true/false, so a mistake in the caller's code is not quietly accepted.
    # Whole numbers such as 0 are still fine.
    model_config = ConfigDict(extra="forbid", strict=True)

    # The full possible range of a win percentage difference is -1 to 1. allow_inf_nan=False
    # also rejects NaN and infinity, which would give the model a meaningless input.
    win_pct_differential: float = Field(
        ge=-1,
        le=1,
        allow_inf_nan=False,
        description="Home win percentage minus away win percentage, before the game.",
    )
    # A loose guard, because the real data runs about -49 to 39. It only stops nonsense such as
    # 500, and it is not a limit the model itself needs.
    point_diff_per_game_differential: float = Field(
        ge=-100,
        le=100,
        allow_inf_nan=False,
        description="Home point margin per game minus the away team's, before the game.",
    )


class PredictResponse(BaseModel):
    """The pick, the same pick in words, the home-win chance, and which model answered."""

    # 1 is a home win and 0 is an away win. predicted_label says the same thing in words.
    prediction: int
    predicted_label: str
    # The model's chance that the home team wins, from 0 to 1, rounded to 4 places.
    home_win_probability: float
    # The model.version setting saved in the model file, so a caller can tell which model answered.
    model_version: str


class HealthResponse(BaseModel):
    """Whether the service is up, and which saved model it loaded."""

    status: str
    model_version: str
    scikit_learn_version: str
