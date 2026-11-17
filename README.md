# ParkPilot — Phase 1 backend

FastAPI + SQLite API for a simulated 20-space parking lot. Project rules,
requirements, and design are in `docs/agent.md`, `docs/prd (1).md`, and
`docs/design.md`. Tested with Python 3.11 and 3.12.

## Setup and run

From the repository root on macOS or Linux:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
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
- `POST /simulation/start` and `POST /simulation/stop`: return HTTP 200 with `{"running": true}` and `{"running": false}`, respectively. These routes set an in-memory flag that resets to stopped on restart. Phase 2 will add event generation.

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

On Windows, run `.\.venv\Scripts\python.exe -m pytest -q` from the repository root.

Tests use temporary databases, covering automatic seeding, persistence after
restart, valid/duplicate transitions, unknown spaces, payload validation,
forced insert failure rollback, concurrent arrivals, history limits, CORS,
and the simulation controls. The pinned Starlette release emits an
HTTPX TestClient deprecation warning; tests still run with approved HTTPX.

`requirements.txt` pins the four approved direct dependencies (FastAPI,
Uvicorn, pytest, HTTPX) and their resolved transitive dependencies.

`simulator/`, `frontend/`, and `ml/` are placeholders only. The simulator,
React dashboard, analytics, ML training, evaluation, and forecasts remain for
later phases. No occupancy forecast or evaluation metrics exist yet.
