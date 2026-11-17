# ParkPilot — backend and simulator

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
- `GET /simulation/status` returns whether automatic mode is enabled.
- `POST /simulation/start` and `POST /simulation/stop` enable or pause the simulator. They return `{"running": true}` or `{"running": false}`. The API resets to stopped on restart.

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

## Simulator

Start the API, then run the automatic simulator in a second terminal from the repository root:

```sh
python -m simulator.simulator
```

In PowerShell, use `.\.venv\Scripts\python.exe` in place of `python`.
The simulator waits for the API to enable automatic mode. Use the interactive
API docs at `http://localhost:8000/docs` to send `POST /simulation/start` and
`POST /simulation/stop`. While enabled, it reads current occupancy and sends
events 2–5 seconds apart. Stop pauses the worker. A webhook already in flight
can still complete. Press Ctrl+C in the simulator terminal to exit.

To send one event, run either command while the API is up:

```sh
python -m simulator.simulator arrival
python -m simulator.simulator departure
```

Manual commands work while automatic mode is paused. Each command picks an
eligible bay and prints the accepted event. A departure uses the parked
vehicle's ID. The command exits with a message if no eligible bay exists.
Use `--api-url` or `PARKPILOT_API_URL` to override `http://localhost:8000`.

## Tests

```sh
. .venv/bin/activate
pytest -q
```

On Windows, run `.\.venv\Scripts\python.exe -m pytest -q` from the repository root.

Tests use temporary databases, covering automatic seeding, persistence after
restart, valid/duplicate transitions, unknown spaces, payload validation,
forced insert failure rollback, concurrent arrivals, history limits, CORS,
and the simulation controls. Simulator tests exercise candidate selection and
automatic pause/resume over mocked HTTP. The pinned Starlette release emits an
HTTPX TestClient deprecation warning; tests still run with approved HTTPX.

`requirements.txt` pins the four approved direct dependencies (FastAPI,
Uvicorn, pytest, HTTPX) and their resolved transitive dependencies.

`frontend/` and `ml/` are placeholders. The React dashboard, analytics, ML
training, evaluation, and forecasts remain for later phases.
