# ParkPilot — Agent Instructions

Read `prd.md` first. It is the source of truth for scope. If this file and the PRD disagree, ask before choosing.

## Project

Local web app that simulates a 20-space parking lot (P01–P20). Simulator sends HTTP events to a FastAPI backend, SQLite stores state and history, a React frontend shows the dashboard, and an ML module forecasts occupancy 30 minutes ahead.

## Stack

**Backend, simulator, ML:** Python, FastAPI + Uvicorn, SQLite (stdlib `sqlite3`), HTTPX, Pandas, NumPy, Scikit-learn, Joblib.
**Frontend:** React + Vite + TypeScript, Tailwind CSS, Framer Motion, Recharts, TanStack Query. No Streamlit.
Do not add other frameworks or services without asking.

## Structure

```
ParkPilot/
  backend/    main.py, database.py, schemas.py
  simulator/  simulator.py
  frontend/   Vite React app (src/components, src/pages, src/api)
  data/       parking.db (created at runtime, git-ignored)
  ml/         added in the ML phase
  tests/
  requirements.txt
  README.md
  design.md   visual direction, if present
```

## Commands

```
pip install -r requirements.txt
uvicorn backend.main:app --reload          # API on :8000
python -m simulator.simulator              # event generator
cd frontend && npm install && npm run dev   # dashboard on :5173
pytest                                     # tests
```

Keep these working. Update this section if they change.

## Rules that must not be broken

1. **The backend enforces state rules.** Reject arrival on an occupied space, departure from an available space, unknown space IDs, unknown event types. The simulator and dashboard never decide validity.
2. **One transaction per event.** The space update and the event insert succeed or fail together.
3. **Create the 20 spaces automatically** on first run. Never require manual seeding.
4. **Keep components independent.** The simulator talks to the backend only over HTTP, so it can later be replaced by real sensors. The frontend talks only to the backend REST API, never to SQLite or simulator internals.
5. **Never label a forecast as live data.** Always show horizon (30 min), model name, and a "forecast" label.
6. **Keep simulated data and the UCI Birmingham training data separate.** Do not imply the model is validated on the simulated lot.
7. **No time leakage in ML.** Chronological splits only, never random shuffle. Features use only information available at the reference time. Verify timestamp spacing before using row shifts for lags or targets.
8. **Report honestly.** Compare against a persistence baseline. Report MAE, RMSE, R² as measured. Never invent numbers, and write `[add after evaluation]` where results do not exist yet.

## API (proposed names, implement as such)

- `POST /webhook/parking-event` body `{space_id, event_type, vehicle_id}`; `event_type` is `SPACE_OCCUPIED` or `SPACE_AVAILABLE`
- `GET /parking-spaces`
- `GET /events?limit=N`
- `POST /simulation/start`, `POST /simulation/stop`

Return clear JSON errors with a meaningful HTTP status (404 unknown space, 409 invalid transition, 422 bad payload).

## Data model

`parking_spaces(space_id PK, status, vehicle_id, last_updated)`
`parking_events(event_id, space_id, event_type, vehicle_id, timestamp)`

## Code style

- Type hints on all functions. Pydantic models for request and response bodies.
- Small functions, plain names, docstrings for anything non-obvious.
- No secrets in code. No network calls other than simulator to backend, dashboard to backend, and the one-time dataset download.
- Handle failures explicitly (backend down, empty database, no history yet) and show a useful message in the dashboard.

## Frontend

Pages: **Live lot**, **Simulate**, **Insights** (analytics + prediction). Follow `design.md` when it exists.

- Build the lot as SVG or absolutely positioned divs. Animate cars with Framer Motion: drive in from the Entry gate, turn into the bay, and reverse out toward the Exit. Trigger animations from state changes between polls (diff the previous and current space list), not from timers alone.
- Poll `GET /parking-spaces` and `GET /events` every 1 to 2 seconds with TanStack Query. Show a visible "last updated" time and a clear message if the backend is unreachable.
- Charts with Recharts. Draw the forecast as a dashed line with its own legend entry and a "Forecast, not live" badge.
- Keep API calls in `src/api/` with typed responses. Read the base URL from `VITE_API_URL`.
- Respect `prefers-reduced-motion` by replacing car movement with simple fades.
- Accessibility: never use color alone to show status, keep contrast readable, label charts, make controls real buttons.
- Add CORS middleware to FastAPI for `http://localhost:5173`.

## Workflow

1. Work phase by phase in the PRD milestone order. Finish and test one phase before starting the next.
2. Before writing code for a phase, state the plan in a few lines.
3. Write tests for backend rules first (valid arrival, valid departure, duplicate arrival, duplicate departure, unknown space, transaction rollback).
4. After each phase, run the tests and the relevant command, then summarize what changed and what is left.
5. Ask before adding dependencies, changing the data model, or changing scope.
6. Do not refactor unrelated code, and do not delete `data/parking.db` without asking.

## ML phase notes

- Place code in `ml/`: `preprocess.py`, `train.py`, `evaluate.py`, `predict.py`, plus a notebook for exploration.
- Save the trained pipeline with Joblib and record the training period, features, and metrics next to it.
- Models: persistence baseline, Linear Regression, Random Forest. K-Means is descriptive only, never the prediction target.
- Inspect errors by facility, time of day, and busy periods.
- Document limits in the README: limited period and location, not Karachi, not live, not the simulated lot.

## Definition of done

All items in the PRD acceptance checklist pass, tests pass, README explains setup, run steps, limitations, and data sources, and the demo script in the PRD runs end to end.
