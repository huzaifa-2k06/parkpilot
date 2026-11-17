"""Typed webhook payloads and public API responses."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Identifier = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
EventType = Literal['SPACE_OCCUPIED', 'SPACE_AVAILABLE']


class ParkingEventRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    space_id: Identifier
    event_type: EventType
    vehicle_id: Identifier


class ParkingSpace(BaseModel):
    space_id: str
    status: Literal['available', 'occupied']
    vehicle_id: str | None
    last_updated: str


class ParkingEvent(BaseModel):
    event_id: int
    space_id: str
    event_type: EventType
    vehicle_id: str
    timestamp: str


class SimulationStatus(BaseModel):
    running: bool


class SimulationSpeed(BaseModel):
    speed: float = Field(strict=True, ge=0.5, le=2.0)


class OccupancyPoint(BaseModel):
    timestamp: str
    occupied: int


class HourlyActivity(BaseModel):
    hour: str
    arrivals: int = 0
    departures: int = 0


class SpaceActivity(BaseModel):
    space_id: str
    arrivals: int = 0


class ParkingAnalytics(BaseModel):
    capacity: int
    points: list[OccupancyPoint]
    hourly: list[HourlyActivity]
    spaces: list[SpaceActivity]
    total_arrivals: int
    total_departures: int


class ErrorResponse(BaseModel):
    detail: str
