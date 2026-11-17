"""Serializable facts about one forecast computation."""

from pydantic import BaseModel, Field


class ForecastInput(BaseModel):
    label: str
    value: str


class ForecastExplanation(BaseModel):
    inputs: list[ForecastInput]
    steps: list[str]
    tree_predictions: list[float] = Field(default_factory=list)
    raw_occupied: float
