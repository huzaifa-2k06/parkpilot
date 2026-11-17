"""Summarize accepted events from the simulated parking lot."""

from collections import deque
from collections.abc import Iterable
from datetime import datetime, timezone
from sqlite3 import Row

from backend.schemas import HourlyActivity, OccupancyPoint, ParkingAnalytics, SpaceActivity

POINT_LIMIT = 240


def summarize_events(space_ids: list[str], events: Iterable[Row]) -> ParkingAnalytics:
    """Replay the full ledger and keep the most recent occupancy points."""
    hourly = [HourlyActivity(hour=f'{hour:02}:00') for hour in range(24)]
    spaces = {space_id: SpaceActivity(space_id=space_id) for space_id in space_ids}
    occupied: set[str] = set()
    points: deque[OccupancyPoint] = deque(maxlen=POINT_LIMIT)
    for event in events:
        space_id = event['space_id']
        timestamp = event['timestamp']
        hour = datetime.fromisoformat(timestamp).astimezone(timezone.utc).hour
        if event['event_type'] == 'SPACE_OCCUPIED':
            occupied.add(space_id)
            spaces[space_id].arrivals += 1
            hourly[hour].arrivals += 1
        else:
            occupied.discard(space_id)
            hourly[hour].departures += 1
        points.append(OccupancyPoint(timestamp=timestamp, occupied=len(occupied)))

    return ParkingAnalytics(
        capacity=len(space_ids),
        points=list(points),
        hourly=hourly,
        spaces=list(spaces.values()),
        total_arrivals=sum(hour.arrivals for hour in hourly),
        total_departures=sum(hour.departures for hour in hourly),
    )
