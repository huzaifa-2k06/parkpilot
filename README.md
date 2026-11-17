# ParkPilot — Phase 1 backend

FastAPI + SQLite API for a simulated 20-space parking lot. Project rules,
requirements, and design are in `docs/agent.md`, `docs/prd (1).md`, and
`docs/design.md`. Python 3.12 is the tested runtime.

## Setup and run

From the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

The API listens on port 8000; interactive documentation is at `/docs`.
Startup creates `data/parking.db` and seeds P01–P20 automatically. Restarting
preserves occupancy and event history. `PARKPILOT_DB_PATH` optionally selects
another database file. Do not delete an existing database to restart the API.
CORS permits `http://localhost:5173`.

## API

- `GET /parking-spaces`: all spaces ordered by ID; statuses are `available` or `occupied`.
- `GET /events?limit=50`: newest events first; limit must be 1–1000.
- `POST /webhook/parking-event`: accepts the payload below; returns the recorded event with HTTP 201.
- `POST /simulation/start` and `/simulation/stop`: return HTTP 501 with an explicit Phase 2 message. No simulation runs in Phase 1.

```sh
curl -X POST http://localhost:8000/webhook/parking-event \
  -H 'Content-Type: application/json' \
  -d '{"space_id":"P01","event_type":"SPACE_OCCUPIED","vehicle_id":"CAR_104"}'
curl http://localhost:8000/parking-spaces
curl 'http://localhost:8000/events?limit=10'
```

Send `SPACE_AVAILABLE` to record a departure. Both event types require a
nonblank string vehicle ID. An arrival stores it on the space; departure
clears the space's vehicle ID and retains the supplied ID in event history.
Errors use JSON `detail`: 404 for unknown space, 409 for an invalid state
transition, 422 for invalid payload (including unknown event type), and 500
for persistence failure. Each event locks the SQLite writer before reading
state and commits its space update and history insert atomically. Timestamps
are UTC ISO 8601 strings. There are no extra vehicle matching or uniqueness rules.

## Tests

```sh
. .venv/bin/activate
pytest -q
```

Tests use temporary databases, covering automatic seeding, persistence after
restart, valid/duplicate transitions, unknown spaces, payload validation,
forced insert failure rollback, concurrent arrivals, history limits, CORS,
and the Phase 2 endpoint responses. The pinned Starlette release emits an
HTTPX TestClient deprecation warning; tests still run with approved HTTPX.

`requirements.txt` pins the four approved direct dependencies (FastAPI,
Uvicorn, pytest, HTTPX) and their resolved transitive dependencies.

`simulator/`, `frontend/`, and `ml/` are placeholders only. The simulator,
React dashboard, analytics, ML training, evaluation, and forecasts remain for
later phases. No occupancy forecast or evaluation metrics exist yet.
