"""SQLite persistence; state transitions and event history commit together."""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
from typing import Iterator
from uuid import uuid4

from backend.analytics import summarize_events
from backend.schemas import EventType, ParkingAnalytics, ParkingEventRequest


class UnknownSpaceError(Exception):
    """The requested parking space does not exist."""


class InvalidTransitionError(Exception):
    """The event contradicts the current state."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class OccupancyHistory:
    capacity: int
    observed_at: datetime
    last_change_at: datetime
    snapshots: list[int]
    arrivals: int
    departures: int
    has_lookback: bool


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON')
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.execute('''CREATE TABLE IF NOT EXISTS parking_spaces (
                space_id TEXT PRIMARY KEY,
                status TEXT NOT NULL CHECK (status IN ('available', 'occupied')),
                vehicle_id TEXT,
                last_updated TEXT NOT NULL
            )''')
            connection.execute('''CREATE TABLE IF NOT EXISTS parking_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                space_id TEXT NOT NULL REFERENCES parking_spaces(space_id),
                event_type TEXT NOT NULL CHECK (
                    event_type IN ('SPACE_OCCUPIED', 'SPACE_AVAILABLE')),
                vehicle_id TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )''')
            now = utc_now()
            connection.executemany(
                '''INSERT OR IGNORE INTO parking_spaces
                   (space_id, status, vehicle_id, last_updated)
                   VALUES (?, 'available', NULL, ?)''',
                [(f'P{i:02}', now) for i in range(1, 21)],
            )

    def spaces(self) -> list[dict]:
        with self.connection() as connection:
            return [dict(row) for row in connection.execute(
                'SELECT * FROM parking_spaces ORDER BY space_id')]

    def events(self, limit: int) -> list[dict]:
        with self.connection() as connection:
            return [dict(row) for row in connection.execute(
                'SELECT * FROM parking_events ORDER BY event_id DESC LIMIT ?', (limit,))]

    def analytics(self) -> ParkingAnalytics:
        with self.connection() as connection:
            space_ids = [
                row['space_id'] for row in connection.execute(
                    'SELECT space_id FROM parking_spaces ORDER BY space_id')
            ]
            events = connection.execute(
                'SELECT space_id, event_type, timestamp FROM parking_events ORDER BY event_id'
            )
            return summarize_events(space_ids, events)

    def occupancy_history(self, step: timedelta, steps: int) -> OccupancyHistory:
        """Read current occupancy and rewind accepted events from the same SQLite snapshot."""
        with self.connection() as connection:
            connection.execute('BEGIN')
            summary = connection.execute(
                """SELECT COUNT(*) AS capacity, SUM(status = 'occupied') AS occupied,
                          MAX(last_updated) AS last_change, MIN(last_updated) AS earliest_space,
                          (SELECT timestamp FROM parking_events ORDER BY event_id LIMIT 1) AS first_event
                   FROM parking_spaces"""
            ).fetchone()
            observed_at = datetime.now(timezone.utc)
            oldest = observed_at - step * steps
            events = iter(connection.execute(
                """SELECT event_type, timestamp FROM parking_events
                   WHERE timestamp > ? ORDER BY timestamp DESC, event_id DESC""",
                (oldest.isoformat(),),
            ))
            occupied = int(summary['occupied'])
            snapshots = [occupied]
            arrivals = departures = 0
            event = next(events, None)
            for index in range(1, steps + 1):
                boundary = observed_at - step * index
                while event is not None and datetime.fromisoformat(event['timestamp']) > boundary:
                    if event['event_type'] == 'SPACE_OCCUPIED':
                        occupied -= 1
                        arrivals += 1
                    else:
                        occupied += 1
                        departures += 1
                    event = next(events, None)
                snapshots.append(occupied)
            earliest = min(value for value in (summary['earliest_space'], summary['first_event']) if value)
            return OccupancyHistory(
                capacity=summary['capacity'],
                observed_at=observed_at,
                last_change_at=datetime.fromisoformat(summary['last_change']),
                snapshots=snapshots,
                arrivals=arrivals,
                departures=departures,
                has_lookback=datetime.fromisoformat(earliest) <= oldest,
            )

    def record_event(self, event: ParkingEventRequest) -> dict:
        with self.connection() as connection:
            # Reserve the writer before reading, so concurrent requests cannot
            # both validate against the same old state.
            connection.execute('BEGIN IMMEDIATE')
            return self._record_event(connection, event)

    def record_manual_event(self, event_type: EventType) -> dict:
        status = 'available' if event_type == 'SPACE_OCCUPIED' else 'occupied'
        with self.connection() as connection:
            connection.execute('BEGIN IMMEDIATE')
            row = connection.execute(
                '''SELECT space_id, vehicle_id FROM parking_spaces
                   WHERE status = ? ORDER BY RANDOM() LIMIT 1''',
                (status,),
            ).fetchone()
            if row is None:
                raise InvalidTransitionError(f'No {status} space for this event')
            event = ParkingEventRequest(
                space_id=row['space_id'],
                event_type=event_type,
                vehicle_id=row['vehicle_id'] or f'CAR_{uuid4().hex[:12].upper()}',
            )
            return self._record_event(connection, event)

    def _record_event(self, connection: sqlite3.Connection, event: ParkingEventRequest) -> dict:
        row = connection.execute(
            'SELECT status FROM parking_spaces WHERE space_id = ?',
            (event.space_id,),
        ).fetchone()
        if row is None:
            raise UnknownSpaceError(f'Unknown space: {event.space_id}')
        status = 'occupied' if event.event_type == 'SPACE_OCCUPIED' else 'available'
        if row['status'] == status:
            raise InvalidTransitionError(f'{event.space_id} is already {status}')
        now = utc_now()
        connection.execute(
            '''UPDATE parking_spaces SET status = ?, vehicle_id = ?, last_updated = ?
               WHERE space_id = ?''',
            (status, event.vehicle_id if status == 'occupied' else None, now, event.space_id),
        )
        cursor = connection.execute(
            '''INSERT INTO parking_events (space_id, event_type, vehicle_id, timestamp)
               VALUES (?, ?, ?, ?)''',
            (event.space_id, event.event_type, event.vehicle_id, now),
        )
        return dict(connection.execute(
            'SELECT * FROM parking_events WHERE event_id = ?', (cursor.lastrowid,)
        ).fetchone())
