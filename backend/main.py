"""Parking API and simulation controls."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
import logging
import os
import sqlite3

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.database import Database, InvalidTransitionError, UnknownSpaceError
from backend.forecast import forecast_router
from backend.schemas import (
    ErrorResponse,
    ParkingAnalytics,
    ParkingEvent,
    ParkingEventRequest,
    ParkingSpace,
    SimulationSpeed,
    SimulationStatus,
)

logger = logging.getLogger(__name__)
DEFAULT_DATABASE = Path(__file__).resolve().parent.parent / 'data' / 'parking.db'
EVENT_WRITE_ERRORS = {409: {'model': ErrorResponse}, 500: {'model': ErrorResponse}}


def create_app(
    database_path: Path | str | None = None,
    forecast_artifact_dir: Path | None = None,
) -> FastAPI:
    database = Database(Path(database_path) if database_path is not None else
                        Path(os.environ.get('PARKPILOT_DB_PATH', str(DEFAULT_DATABASE))))

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database.initialize()
        app.state.simulation_running = False
        app.state.simulation_speed = 1.0
        yield

    app = FastAPI(title='ParkPilot', lifespan=lifespan)
    app.include_router(forecast_router(forecast_artifact_dir))
    app.add_middleware(
        CORSMiddleware, allow_origins=['http://localhost:5173'],
        allow_methods=['GET', 'POST'], allow_headers=['Content-Type'],
    )

    @app.exception_handler(UnknownSpaceError)
    async def unknown_space(_request: Request, error: UnknownSpaceError) -> JSONResponse:
        return JSONResponse(status_code=404, content={'detail': str(error)})

    @app.exception_handler(InvalidTransitionError)
    async def invalid_transition(_request: Request, error: InvalidTransitionError) -> JSONResponse:
        return JSONResponse(status_code=409, content={'detail': str(error)})

    @app.exception_handler(sqlite3.Error)
    async def database_error(request: Request, error: sqlite3.Error) -> JSONResponse:
        detail = (
            'Unable to persist parking event' if request.method == 'POST'
            else 'Unable to read parking data'
        )
        logger.error(detail, exc_info=error)
        return JSONResponse(status_code=500, content={'detail': detail})

    @app.get('/parking-spaces', response_model=list[ParkingSpace])
    def parking_spaces() -> list[dict]:
        return database.spaces()

    @app.get('/events', response_model=list[ParkingEvent])
    def events(limit: int = Query(default=50, ge=1, le=1000)) -> list[dict]:
        return database.events(limit)

    @app.get('/analytics')
    def analytics() -> ParkingAnalytics:
        return database.analytics()

    @app.post('/webhook/parking-event', status_code=201, response_model=ParkingEvent,
              responses={404: {'model': ErrorResponse}, **EVENT_WRITE_ERRORS})
    def parking_event(event: ParkingEventRequest) -> dict:
        return database.record_event(event)

    @app.post('/simulation/arrival', status_code=201, response_model=ParkingEvent,
              responses=EVENT_WRITE_ERRORS)
    def manual_arrival() -> dict:
        return database.record_manual_event('SPACE_OCCUPIED')

    @app.post('/simulation/departure', status_code=201, response_model=ParkingEvent,
              responses=EVENT_WRITE_ERRORS)
    def manual_departure() -> dict:
        return database.record_manual_event('SPACE_AVAILABLE')

    @app.get('/simulation/status')
    async def simulation_status() -> SimulationStatus:
        return SimulationStatus(running=app.state.simulation_running)

    @app.post('/simulation/start')
    async def start_simulation() -> SimulationStatus:
        app.state.simulation_running = True
        return await simulation_status()

    @app.post('/simulation/stop')
    async def stop_simulation() -> SimulationStatus:
        app.state.simulation_running = False
        return await simulation_status()

    @app.get('/simulation/speed')
    async def simulation_speed() -> SimulationSpeed:
        return SimulationSpeed(speed=app.state.simulation_speed)

    @app.post('/simulation/speed')
    async def set_simulation_speed(speed: SimulationSpeed) -> SimulationSpeed:
        app.state.simulation_speed = speed.speed
        return speed

    return app


app = create_app()
