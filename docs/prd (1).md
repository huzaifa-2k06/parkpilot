# ParkPilot — Product Requirements Document (MVP)

Smart parking management and availability prediction system. Academic MVP.

## 1. Summary

ParkPilot simulates a 20-space parking facility (P01–P20). A simulator sends vehicle arrival and departure events to a FastAPI webhook. The backend validates each event, updates SQLite, and records history. A React web dashboard shows live occupancy, analytics, and a machine-learning forecast of occupancy 30 minutes ahead.

**Core value:** show how many spaces are free now, and estimate how availability will change soon.

## 2. Problem

Drivers waste time looking for parking because they cannot see which spaces are taken. Operators lack a single view of occupancy and usage patterns. ParkPilot demonstrates how event-based updates, one central database, and a dashboard solve this.

## 3. Goals and non-goals

**Goals**
- Simulate realistic arrival/departure flow for 20 spaces.
- Enforce valid state transitions in the backend only.
- Persist state and event history across restarts.
- Show live status, analytics, and a clearly labeled forecast.
- Evaluate ML models honestly against baselines using chronological splits.

**Non-goals (out of scope)**
Physical IoT sensors, camera recognition, payments, user accounts, GPS navigation, multiple real facilities, cloud infrastructure.

## 4. Users

| User | Need |
|---|---|
| Driver (demo persona) | See free spaces now and what to expect in 30 minutes |
| Parking operator (demo persona) | See occupancy, busy periods, and event history |
| Evaluator (academic) | See a working end-to-end flow, honest ML evaluation, and documented limits |

## 5. Functional requirements

### FR1 Live occupancy
- Show 20 spaces with status: available, occupied, optional unavailable.
- Show capacity, occupied, available, occupancy %.
- Show last update time. Refresh by polling.
- Status must not rely on color alone (occupied spaces also show a car and label).

### FR2 Vehicle simulator
- Automatic mode: generate valid arrivals and departures at random intervals.
- Manual mode: buttons to send one arrival or one departure.
- Generate vehicle IDs (e.g. `CAR_104`).
- Pick only spaces whose state allows the event; the backend still enforces rules.

### FR3 Webhook and backend
- `POST /webhook/parking-event` accepts `{space_id, event_type, vehicle_id}` where `event_type` is `SPACE_OCCUPIED` or `SPACE_AVAILABLE`.
- Reject unknown `space_id`, unknown `event_type`, arrival on occupied space, departure from available space.
- Update space row and insert event row in one transaction.
- `GET /parking-spaces` returns all 20 spaces.
- `GET /events?limit=N` returns recent events.
- `POST /simulation/start` and `POST /simulation/stop` control the simulation if exposed through the backend.
- Initialize 20 spaces automatically on first run.
- Enable CORS for the frontend dev origin (`http://localhost:5173`).

### FR4 Analytics
- Occupancy over time, arrival/departure counts, most-used spaces, peak periods.
- Computed from recorded events. Label as simulated data.

### FR5 ML prediction
- Predict facility-level occupancy 30 minutes ahead; show estimated free spaces.
- Compare forecast with actual occupancy once the target time arrives.
- Show horizon, model name, metrics, and a "forecast, not live" label.

## 6. Data model

**parking_spaces**: `space_id` (PK), `status`, `vehicle_id`, `last_updated`
**parking_events**: `event_id`, `space_id`, `event_type`, `vehicle_id`, `timestamp`

Space update and event insert run in one transaction.

## 7. Architecture

```
Simulator --HTTP--> FastAPI --> SQLite
                       ^
                       | REST (polling)
                 React dashboard
                                   ^
                              ML module (reads history, supplies forecast)
```

Components are independent so the simulator can later be replaced by real sensors.

**Frontend stack:** React + Vite + TypeScript, Tailwind CSS, Framer Motion (animated cars and lot), Recharts (charts), TanStack Query (polling). The frontend talks only to the FastAPI REST API. Streamlit is not used.

## 8. ML plan

- **Data:** UCI Parking Birmingham (historical, not live, not the simulated lot).
- **Target:** facility occupancy 30 minutes after a reference timestamp.
- **Features:** only information available at the reference time (current occupancy, lags, hour, day of week).
- **Checks:** verify timestamp intervals before shifting rows for lags or targets.
- **Split:** chronological train / validation / test. No random shuffling.
- **Models:** persistence baseline, Linear Regression, Random Forest. K-Means for descriptive usage clusters only.
- **Metrics:** MAE, RMSE, R². Inspect errors by facility, time of day, busy periods.
- **Limitation:** results do not prove performance for Karachi, other seasons, or the simulated lot. Do not imply validation on simulated data without a matching and evaluation plan.

## 9. UI screens

Design reference: [ParkPilot 3-screen reference](https://claude.ai/artifact/Jv2VeG3zs9mTHiUQ4jMbgr). The final build is a React app, so match the layout, motion, and visual style closely.

1. **Live lot:** top-down lot, 20 bays, animated cars entering and leaving, availability panel, recent activity.
2. **Simulate:** entry/exit lane animation, start/stop and manual controls, last webhook response, event history.
3. **Insights:** occupancy chart with dashed 30-minute forecast, arrivals/departures by hour, usage clusters, forecast card.

## 10. Non-functional requirements

- Runs locally with `pip install -r requirements.txt`, `npm install`, and a few start commands.
- Recovers state after restart.
- Dashboard shows staleness (last update time).
- Clear separation of simulated data and historical training data.

## 11. Acceptance criteria

- [ ] Exactly 20 spaces initialized.
- [ ] Automatic simulation produces only valid events.
- [ ] Manual arrival and departure work.
- [ ] Backend rejects duplicate or invalid transitions.
- [ ] Every accepted event is persisted.
- [ ] Dashboard reflects backend state.
- [ ] Analytics come from recorded data and are labeled.
- [ ] Models compared with baselines on chronological splits.
- [ ] Forecast visibly distinct from live occupancy.
- [ ] README covers setup, run steps, limitations, data sources.

## 12. Milestones

| Phase | Deliverable |
|---|---|
| 1 | Backend, SQLite, schemas, transaction logic, tests |
| 2 | Simulator (auto + manual) |
| 3 | React app: live lot with animated cars, event history |
| 4 | Analytics |
| 5 | ML notebook/scripts, evaluation, saved pipeline (`ml/`) |
| 6 | Prediction page, forecast-vs-actual comparison |
| 7 | README, demo rehearsal |

## 13. Risks

| Risk | Mitigation |
|---|---|
| Duplicate or out-of-order events | Validate state; consider event IDs and timestamps |
| Stale dashboard | Polling and visible last-update time |
| Simulator/ML data mismatch | Keep separate and document model domain |
| Misleading prediction claims | Show horizon, metrics, limitations |
| Time leakage | Chronological splits, features known at prediction time |

## 14. Demo script

1. Open dashboard, show 20 spaces.
2. Start simulation, watch cars arrive and leave.
3. Manual arrival, show space turn occupied.
4. Show webhook response and database event.
5. Manual departure, space becomes available.
6. Open analytics.
7. Run 30-minute prediction, explain forecast vs current.
8. Compare forecast with actual once the target time is reached.
