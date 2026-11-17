"""Arrival-time forecasts for the simulated facility."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from backend.database import Database
from ml.explanation import ForecastExplanation, ForecastInput
from ml.live_forecast import (
    DEFAULT_POLICY_PATH,
    DAY_MINUTES,
    GRID_MINUTES,
    LOOKBACK_STEPS,
    SHORT_MINUTES,
    WEEK_MINUTES,
    ModelName,
    choose_forecast,
    calendar_slot,
    load_policy,
)

FACILITY_ID = 'parkpilot-demo'
FACILITY_NAME = 'ParkPilot Demo Lot'
STALE_AFTER = timedelta(minutes=1)


class LiveFacility(BaseModel):
    id: str
    name: str
    max_horizon_minutes: int


class ArrivalForecast(BaseModel):
    facility_id: str
    capacity: int
    arrival_at: datetime
    observed_at: datetime
    last_change_at: datetime
    horizon_minutes: float
    current_occupied: int
    estimated_occupied: int
    estimated_free: int
    model: ModelName
    source: Literal['live_simulation', 'simulated_calendar']
    explanation: ForecastExplanation


def live_forecast_router(database: Database, policy_path: Path = DEFAULT_POLICY_PATH) -> APIRouter:
    router = APIRouter(prefix='/live-forecast', tags=['Simulated lot arrival forecast'])

    @router.get('/facilities')
    def facilities() -> list[LiveFacility]:
        policy = load_policy(policy_path)
        return [LiveFacility(
            id=FACILITY_ID,
            name=FACILITY_NAME,
            max_horizon_minutes=policy.max_horizon_minutes if policy else SHORT_MINUTES,
        )]

    @router.get('/{facility_id}')
    def forecast(request: Request, facility_id: str, arrival_at: str) -> ArrivalForecast:
        if facility_id != FACILITY_ID:
            raise HTTPException(status_code=404, detail='Unknown simulated facility.')
        try:
            target = datetime.fromisoformat(arrival_at)
            if target.utcoffset() is None:
                raise ValueError
            target = target.astimezone(timezone.utc)
        except (ValueError, OverflowError):
            raise HTTPException(
                status_code=422, detail='Use an ISO 8601 arrival time with a timezone offset.',
            ) from None

        history = database.occupancy_history(timedelta(minutes=GRID_MINUTES), LOOKBACK_STEPS)
        policy = load_policy(policy_path)
        if policy and policy.capacity != history.capacity:
            policy = None
        minutes = (target - history.observed_at).total_seconds() / 60
        maximum = policy.max_horizon_minutes if policy else SHORT_MINUTES
        if not 0 < minutes <= maximum:
            window = {SHORT_MINUTES: '30 minutes', DAY_MINUTES: '24 hours', WEEK_MINUTES: '7 days'}[maximum]
            raise HTTPException(status_code=422, detail=f'Choose an arrival within the next {window}.')

        started_at = request.app.state.simulation_started_at
        short = minutes <= SHORT_MINUTES
        if short and started_at and history.observed_at - max(started_at, history.last_change_at) > STALE_AFTER:
            raise HTTPException(
                status_code=503,
                detail='The automatic simulator has stopped reporting events. Check the worker or pause it.',
            )
        speed = request.app.state.simulation_speed if started_at and history.has_lookback else None
        occupied, model = choose_forecast(
            policy, history.capacity, history.snapshots,
            (history.arrivals, history.departures), target, minutes, speed,
        )
        inputs = [
            ForecastInput(label='Current occupancy', value=f'{history.snapshots[0]} of {history.capacity}'),
            ForecastInput(label='Arrival (UTC)', value=target.strftime('%A %Y-%m-%d %H:%M')),
            ForecastInput(label='Forecast horizon', value=f'{minutes:.1f} minutes'),
        ]
        if model == 'Persistence':
            steps = [
                'Read the latest accepted occupancy from the simulated lot.',
                'Carry the current occupied count forward to the selected arrival time.',
                f'Subtract {occupied} occupied from {history.capacity} total spaces.',
            ]
        elif model == 'Calendar baseline':
            inputs.append(ForecastInput(
                label='Matching weekday/hour estimate',
                value=f'{policy.calendar_profile[calendar_slot(target)]} occupied',
            ))
            steps = [
                'Use the arrival weekday and hour in UTC.',
                'Look up the median occupancy learned from matching hours in simulated seasonal runs.',
                f'Subtract {occupied} estimated occupied from {history.capacity} total spaces.',
            ]
        else:
            steps = [
                'Build the features used by the selected simulated-lot regression.',
                'Apply the saved coefficients, round the estimate, and bound it to facility capacity.',
                f'Subtract {occupied} estimated occupied from {history.capacity} total spaces.',
            ]
            if short:
                inputs.extend([
                    ForecastInput(label='Occupancy 5 / 10 / 15 minutes ago',
                                  value=' / '.join(map(str, history.snapshots[1:]))),
                    ForecastInput(label='Recent arrivals / departures',
                                  value=f'{history.arrivals} / {history.departures}'),
                ])
        return ArrivalForecast(
            facility_id=facility_id,
            capacity=history.capacity,
            arrival_at=target,
            observed_at=history.observed_at,
            last_change_at=history.last_change_at,
            horizon_minutes=round(minutes, 1),
            current_occupied=history.snapshots[0],
            estimated_occupied=occupied,
            estimated_free=history.capacity - occupied,
            model=model,
            source='live_simulation' if short else 'simulated_calendar',
            explanation=ForecastExplanation(inputs=inputs, steps=steps, raw_occupied=occupied),
        )

    return router
