"""Generate ParkPilot parking events through the HTTP API."""

import argparse
import os
import random
import sys
from time import sleep
from typing import Literal, TypedDict
from uuid import uuid4

import httpx

DEFAULT_API_URL = 'http://localhost:8000'
POLL_INTERVAL = 0.5
MIN_EVENT_INTERVAL = 2.0
MAX_EVENT_INTERVAL = 5.0


class Space(TypedDict):
    space_id: str
    status: str
    vehicle_id: str | None


class Event(TypedDict):
    space_id: str
    event_type: Literal['SPACE_OCCUPIED', 'SPACE_AVAILABLE']
    vehicle_id: str


def choose_event(spaces: list[Space], mode: str) -> Event | None:
    """Choose a candidate from the current lot state."""
    candidates: list[tuple[str, str | None]] = []
    for space in spaces:
        vehicle_id = space['vehicle_id']
        if space['status'] == 'available' and mode != 'departure':
            candidates.append((space['space_id'], None))
        elif space['status'] == 'occupied' and vehicle_id and mode != 'arrival':
            candidates.append((space['space_id'], vehicle_id))

    if not candidates:
        return None

    space_id, vehicle_id = random.choice(candidates)
    if vehicle_id is None:
        return {
            'space_id': space_id,
            'event_type': 'SPACE_OCCUPIED',
            'vehicle_id': f'CAR_{uuid4().hex[:12].upper()}',
        }
    return {
        'space_id': space_id,
        'event_type': 'SPACE_AVAILABLE',
        'vehicle_id': vehicle_id,
    }


def read_event_candidate(client: httpx.Client, mode: str) -> Event | None:
    spaces = client.get('/parking-spaces').raise_for_status().json()
    return choose_event(spaces, mode)


def send_event(client: httpx.Client, event: Event) -> None:
    client.post('/webhook/parking-event', json=event).raise_for_status()
    print(f"{event['event_type']} {event['space_id']} {event['vehicle_id']}", flush=True)


def simulation_running(client: httpx.Client) -> bool:
    status = client.get('/simulation/status').raise_for_status().json()
    return status['running'] is True


def run_automatic(client: httpx.Client) -> None:
    print('Automatic simulator is waiting for POST /simulation/start.', flush=True)
    while True:
        delay = POLL_INTERVAL
        try:
            if simulation_running(client):
                event = read_event_candidate(client, 'auto')
                # Stop may have been requested while the lot state was fetched.
                if event is not None and simulation_running(client):
                    delay = random.uniform(MIN_EVENT_INTERVAL, MAX_EVENT_INTERVAL)
                    send_event(client, event)
        except httpx.HTTPError as error:
            print(f'ParkPilot API request failed: {error}', file=sys.stderr, flush=True)
            delay = max(delay, MIN_EVENT_INTERVAL)
        sleep(delay)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['auto', 'arrival', 'departure'],
                        nargs='?', default='auto')
    parser.add_argument('--api-url', default=os.getenv('PARKPILOT_API_URL', DEFAULT_API_URL),
                        help='ParkPilot API base URL (default: %(default)s)')
    args = parser.parse_args(argv)
    try:
        with httpx.Client(base_url=args.api_url, timeout=5.0) as client:
            if args.mode == 'auto':
                run_automatic(client)
            else:
                event = read_event_candidate(client, args.mode)
                if event is None:
                    print(f'No eligible space for {args.mode}.', file=sys.stderr)
                    return 1
                send_event(client, event)
    except KeyboardInterrupt:
        return 0
    except (httpx.HTTPError, httpx.InvalidURL) as error:
        print(f'ParkPilot API request failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
