"""The JSON a caller may send, and the JSON the service sends back."""

from pydantic import BaseModel, ConfigDict, Field


class PredictRequest(BaseModel):
    """The two pre-game numbers. Extra fields are refused so a typo is not ignored."""

    model_config = ConfigDict(extra="forbid", strict=True)

    win_pct_differential: float = Field(
        ge=-1,
        le=1,
        allow_inf_nan=False,
        description="Home win percentage minus away win percentage, before the game.",
    )
    # A loose guard, because the real data runs about -49 to 39.
    point_diff_per_game_differential: float = Field(
        ge=-100,
        le=100,
        allow_inf_nan=False,
        description="Home point margin per game minus the away team's, before the game.",
    )


class PredictResponse(BaseModel):
    """The pick, the same pick in words, the home-win chance, and which model answered."""

    prediction: int
    predicted_label: str
    home_win_probability: float
    model_version: str


class HealthResponse(BaseModel):
    """Whether the service is up, and which saved model it loaded."""

    status: str
    model_version: str
    scikit_learn_version: str
