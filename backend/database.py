"""SQLite persistence; state transitions and event history commit together."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Iterator

from backend.schemas import ParkingEventRequest


class UnknownSpaceError(Exception):
    """The requested parking space does not exist."""


class InvalidTransitionError(Exception):
    """The event contradicts the current state."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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

    def record_event(self, event: ParkingEventRequest) -> dict:
        with self.connection() as connection:
            # Reserve the writer before reading, so concurrent requests cannot
            # both validate against the same old state.
            connection.execute('BEGIN IMMEDIATE')
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
            result = dict(connection.execute(
                'SELECT * FROM parking_events WHERE event_id = ?', (cursor.lastrowid,)
            ).fetchone())
        return result
