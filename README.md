# ParkPilot

ParkPilot simulates a 20-space parking lot and displays live occupancy, vehicle
movements, and event analytics in a React dashboard. A separate historical
replay evaluates a 30-minute occupancy forecast on the Birmingham dataset.
See [progress](PROGRESS.md) and the project specs under `docs/`.

## Academic report and viva preparation

- [Final CCA report in Roman Urdu](docs/CCA-REPORT-ROMAN-URDU.md)
- [Printable five-section report](docs/CCA-REPORT-ROMAN-URDU.html)
- [Difficult ML viva questions and baseline/accuracy defence](docs/ML-VIVA-DEFENCE-ROMAN-URDU.md)
- [All 14 labs and mock quiz](docs/QUIZ-GUIDE-ROMAN-URDU.md)

The three integrated lab concepts are preprocessing, Multiple Linear Regression,
and the Random Forest ensemble adapted to a regression target. Persistence is
an additional non-learned benchmark. It is not counted as a lab concept.
Historical regression results use MAE, RMSE and R², not classification accuracy.
Fill the report's team details before submission and rehearse the class demo.

## Setup and run

Use Python 3.11 or 3.12 and Node.js 22.12+ (or 20.19+). From the repository
root on macOS or Linux:

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

In a second terminal, start the dashboard:

```sh
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. The dashboard defaults to
`http://localhost:8000` for its API. Set `VITE_API_URL` in `frontend/.env` to
override it. The dashboard must be served from the configured CORS origin.

## API

- `GET /parking-spaces`: all spaces ordered by ID; statuses are `available` or `occupied`.
- `GET /events?limit=50`: newest events first; limit must be 1–1000.
- `POST /webhook/parking-event`: accepts the payload below; returns the recorded event with HTTP 201.
- `GET /simulation/status` returns whether automatic mode is enabled.
- `POST /simulation/start` and `POST /simulation/stop` enable or pause the simulator. They return `{"running": true}` or `{"running": false}`. The API resets to stopped on restart.
- `POST /simulation/arrival` and `POST /simulation/departure` record one event, or return 409 if no bay is eligible.
- `GET /simulation/speed` returns the worker's speed multiplier. Set it with `POST /simulation/speed` and a body of `{"speed": 1.5}`. The range is 0.5–2 and the default is 1.
- `GET /analytics` returns recorded simulated occupancy, hourly events in UTC, and arrivals per bay.
- `GET /live-forecast/facilities` lists the demo lot and its supported horizon. `GET /live-forecast/parkpilot-demo?arrival_at=...` takes an ISO 8601 timestamp with an offset and returns the arrival estimate, method, and observation time.
- `GET /forecast/facilities` lists held-out Birmingham replay references. `GET /forecast` accepts `facility_id`, `reference_at`, and `as_of` for the replay.

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

Start the API, then run the automatic simulator in another terminal from the repository root:

```sh
python -m simulator.simulator
```

In PowerShell, use `.\.venv\Scripts\python.exe` in place of `python`.
On the dashboard's **Simulate** page, start or pause automatic mode and adjust
its speed. At 1× the worker reads current occupancy and sends events 2–5
seconds apart. A webhook already in flight can still complete after a pause.
Press Ctrl+C in the simulator terminal to exit. Manual controls in the
dashboard are available with just the API running.

To send one event, run either command while the API is up:

```sh
python -m simulator.simulator arrival
python -m simulator.simulator departure
```

Manual commands work while automatic mode is paused. Each command picks an
eligible bay and prints the accepted event. A departure uses the parked
vehicle's ID. The command exits with a message if no eligible bay exists.
Use `--api-url` or `PARKPILOT_API_URL` to override `http://localhost:8000`.

## Forecast an arrival at the demo lot

In **Live Lot → Plan your arrival**, select the facility, date, and time in
your device's timezone. The estimate refreshes as the lot changes. The map
continues to show the current state of each bay.

The arrival result includes a capacity diagram that illustrates the estimated
free and occupied counts. Its positions represent aggregate capacity. The
**How this forecast works** panel shows the inputs and calculation for that
selection. In **Insights**, the Birmingham replay also shows each trained
Random Forest tree's prediction and their average when Random Forest is the
selected model.

For the next 30 minutes, the forecast is available out of the box and uses
persistence, carrying forward occupancy from the current SQLite state. The API
can reconstruct five-minute lags and recent counts from the event ledger.
An enabled simulator feed with no accepted events for one minute returns
a stale-data message. With automatic mode paused, manual events continue to
update the estimate.

To evaluate simulated forecasts and enable calendar estimates, run:

```sh
python -m ml.live_forecast
```

This writes `data/live_forecast/forecast.json` with validation and held-out
metrics. The simulator scenarios approximate the automatic worker's random
event policy for short ranges and use separate seasonal runs with weekday
demand and vehicle dwell times for longer ranges. The latter estimates use
UTC weekday and hour to look up expected occupancy.

The evaluated calendar baseline enables estimates beyond 30 minutes and up
to seven days. It uses simulated calendar demand rather than projecting the
current occupancy forward for days. At the 30-minute mark, regression reduced
MAE from 2.42 to about 1.72 spaces, but the held-out runs contained no full-lot
targets, so persistence remains the live method. For the two longer bands,
calendar MAE was 1.92 and 1.96 spaces. Policy selection uses validation scores
only; test scores are report-only. The earlier test-dependent promotion rule
was corrected on 2026-11-18. Reusing the inspected scenario test set does not
constitute a new untouched evaluation. Calendar forecasts still showed free
spaces in roughly 49% of held-out full-lot cases, so availability is an
estimate. These results describe the scenario generator and do not establish
accuracy on a real facility. The live forecast and the Birmingham replay use
separate artifacts and routes.

## Train and replay a forecast

From the repository root with the virtual environment active:

```sh
python -m ml.train
python -m ml.evaluate
python -m ml.predict
```

Training caches the official [UCI Parking Birmingham dataset](https://archive.ics.uci.edu/dataset/482/parking%2Bbirmingham)
in `data/birmingham/` and saves the trained bundle and evaluation metadata in
`data/ml/`. These files are generated locally. If the API already loaded a
previous bundle, restart it after retraining. See [the ML guide](ml/README.md)
for chronology, sampling, and the evaluation procedure.

In **Insights**, select a Birmingham facility and a held-out reference time.
The dashed forecast estimates occupancy 30 minutes ahead. Advance the replay
to the target to reveal the corresponding recorded observation. The data
cover daytime samples from Birmingham in October–December 2016. The model's
held-out results apply to that dataset. Live occupancy and event analytics
come from the simulated 20-space lot.

## Demo

1. Open **Live Lot** and confirm all 20 bays are shown.
2. Open **Simulate**, start the worker, watch a vehicle arrive, and pause it.
3. Send a manual arrival and departure and check their webhook responses.
4. Open **Insights** and inspect simulated occupancy and arrival counts.
5. Load a Birmingham replay and advance to the target time to compare the
   forecast with the recorded result.

## Tests

```sh
. .venv/bin/activate
pytest -q
```

On Windows, run `.\.venv\Scripts\python.exe -m pytest -q` from the repository root.
Run `npm run build` inside `frontend/` to type-check and build the dashboard.

Tests use temporary databases, covering automatic seeding, persistence after
restart, valid/duplicate transitions, unknown spaces, payload validation,
forced insert failure rollback, concurrent arrivals, history limits, CORS,
simulation controls, and analytics. ML tests cover causal alignment,
chronological splitting, and replay availability. The pinned Starlette
release emits an HTTPX TestClient deprecation warning.
