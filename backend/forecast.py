"""Expose a held-out Birmingham replay through the local REST API."""

from functools import lru_cache
from pathlib import Path
from typing import Literal, TYPE_CHECKING

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ml.explanation import ForecastExplanation

if TYPE_CHECKING:
    from ml.predict import HistoricalReplay


class ForecastSource(BaseModel):
    source: Literal['uci_parking_birmingham']
    horizon_minutes: Literal[30]
    timezone: str = 'Europe/London'


class Facility(BaseModel):
    facility_id: str
    first_reference_at: str
    last_reference_at: str
    reference_times: list[str]


class Facilities(ForecastSource):
    facilities: list[Facility]


class HistoricalPoint(BaseModel):
    timestamp: str
    occupancy: int


class ForecastMetrics(BaseModel):
    mae: float
    rmse: float
    r2: float | None


class Forecast(ForecastSource):
    facility_id: str
    model_name: str
    reference_at: str
    target_at: str
    as_of: str
    capacity: int
    current_occupancy: int
    predicted_occupancy: float
    predicted_free_spaces: float
    actual_occupancy: int | None
    actual_free_spaces: int | None
    history: list[HistoricalPoint]
    metrics: ForecastMetrics
    explanation: ForecastExplanation


def forecast_router(artifact_dir: Path | None = None) -> APIRouter:
    router = APIRouter(prefix='/forecast', tags=['Birmingham forecast replay'])

    @lru_cache(maxsize=1)
    def replay() -> 'HistoricalReplay':
        from ml.predict import ReplayUnavailableError, load_replay

        try:
            return load_replay() if artifact_dir is None else load_replay(artifact_dir)
        except ReplayUnavailableError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

    @router.get('/facilities', response_model=Facilities)
    def forecast_facilities() -> dict:
        return replay().catalog()

    @router.get('', response_model=Forecast)
    def forecast(
        facility_id: str | None = None,
        reference_at: str | None = None,
        as_of: str | None = None,
    ) -> dict:
        from ml.predict import ReplayInputError, ReplayNotFoundError

        try:
            return replay().forecast(facility_id=facility_id, reference_at=reference_at, as_of=as_of)
        except ReplayInputError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except ReplayNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    return router
