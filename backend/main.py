"""Phase 1 parking API and simulation controls."""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
import logging
import os
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.database import Database, InvalidTransitionError, UnknownSpaceError
from backend.schemas import (
    ErrorResponse,
    ParkingEvent,
    ParkingEventRequest,
    ParkingSpace,
    SimulationStatus,
)

logger = logging.getLogger(__name__)
DEFAULT_DATABASE = Path(__file__).resolve().parent.parent / 'data' / 'parking.db'


def create_app(database_path: Path | str | None = None) -> FastAPI:
    database = Database(Path(database_path) if database_path is not None else
                        Path(os.environ.get('PARKPILOT_DB_PATH', str(DEFAULT_DATABASE))))

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database.initialize()
        app.state.simulation_running = False
        yield

    app = FastAPI(title='ParkPilot', lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=['http://localhost:5173'],
        allow_methods=['GET', 'POST'], allow_headers=['Content-Type'],
    )

    @app.get('/parking-spaces', response_model=list[ParkingSpace])
    def parking_spaces() -> list[dict]:
        return database.spaces()

    @app.get('/events', response_model=list[ParkingEvent])
    def events(limit: int = Query(default=50, ge=1, le=1000)) -> list[dict]:
        return database.events(limit)

    @app.post('/webhook/parking-event', status_code=201, response_model=ParkingEvent,
              responses={404: {'model': ErrorResponse}, 409: {'model': ErrorResponse},
                         500: {'model': ErrorResponse}})
    def parking_event(event: ParkingEventRequest) -> dict:
        try:
            return database.record_event(event)
        except UnknownSpaceError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except InvalidTransitionError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except sqlite3.Error as error:
            logger.exception('Unable to persist parking event')
            raise HTTPException(status_code=500, detail='Unable to persist parking event') from error

    @app.post('/simulation/start')
    async def start_simulation() -> SimulationStatus:
        app.state.simulation_running = True
        return SimulationStatus(running=app.state.simulation_running)

    @app.post('/simulation/stop')
    async def stop_simulation() -> SimulationStatus:
        app.state.simulation_running = False
        return SimulationStatus(running=app.state.simulation_running)

    return app


app = create_app()
