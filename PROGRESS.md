# ParkPilot progress

Updated 2026-11-17 (Asia/Karachi). Current branch is `feat/forecast-visualization`.

| Workstream | Owner | Status |
| --- | --- | --- |
| Phase 1 · Backend and SQLite | Root | Implemented and verified. [PR #1](https://github.com/huzaifa-2k06/parkpilot/pull/1) |
| Phase 2 · Manual and automatic simulator | Root | Implemented and verified. [PR #2](https://github.com/huzaifa-2k06/parkpilot/pull/2) |
| Phases 3–4 · Live lot, simulation controls, event analytics | `live_parking` | Implemented and verified in Chrome. The dashboard shows 20 bays, animated transitions, manual and automatic controls, history, and recorded analytics. |
| Phases 5–6 · ML pipeline and forecast comparison | `ml_pipeline` | Implemented and verified on official UCI data. Models, evaluation, replay, notebook, and [ML guide](ml/README.md) are ready. |
| Phase 7 · Setup, demo, and integration checks | Root | [Setup and demo instructions](README.md) verified. All planned checks passed. [Integration PR #3](https://github.com/huzaifa-2k06/parkpilot/pull/3) is open for review. |
| Arrival-time forecast | Root | Live Lot picker and API verified. Persistence serves up to 30 minutes. Held-out seasonal scenarios cleared both calendar horizons through seven days. [PR #4](https://github.com/huzaifa-2k06/parkpilot/pull/4) |
| Forecast visualization | Root | Added an illustrative capacity diagram for arrival estimates and input-to-output explanations for both forecasting paths. Birmingham explanations include actual predictions from all 120 trees. 34 tests, production build, and desktop/mobile Chrome checks passed. |

## Verification

- [x] Phase 1 · 17 tests passed and five endpoints exercised over HTTP.
- [x] Phase 2 · 22 tests passed and a live worker verified manual arrival/departure and automatic start, pause, and resume.
- [x] Live API integration · 25 backend and simulator tests passed before the forecast routes were added.
- [x] ML training · Birmingham holdout contains 5,210 snapshots across 29 facilities. Validation MAE selected Random Forest.
- [x] Run the complete Python test suite with the pinned dependencies. 30 passed with the existing Starlette TestClient warning.
- [x] Reproduce the held-out scores from the saved bundle in the project virtual environment.
- [x] Type-check and build the frontend for production.
- [x] Verify the live lot, manual events, speed, start/stop, reduced motion, analytics, and historical comparison in Chrome. Verify the layout at desktop size and 390 px.
- [x] Verify live controls, occupancy analytics, and the saved forecast over HTTP, including actual reveal at the historical target time.
- [x] Document setup and the demo sequence.
- [x] Complete the demo checks and open the integration PR.
- [x] Arrival forecast · 34 Python tests, Vite build, and Chrome checks including a two-day estimate and 390 px layout.
- [x] Reproduce simulated forecast metrics with `python -m ml.live_forecast`. Persistence remains in service through 30 minutes because the held-out observations contained zero full-lot targets. The calendar baseline serves both longer bands.

PR #3 includes the commits from Phase 1 and Phase 2 while those PRs are open.
The downloaded dataset, saved model bundle, and evaluation metadata are
generated locally with `python -m ml.train`.

## Held-out Birmingham evaluation

| Model | MAE (spaces) | RMSE (spaces) | R² |
| --- | ---: | ---: | ---: |
| Persistence | 50.96 | 91.44 | 0.98613 |
| Linear Regression | 20.09 | 36.26 | 0.99782 |
| Random Forest | 19.68 | 35.81 | 0.99787 |

These measurements cover the Birmingham held-out period of 2016-12-05 to
2016-12-19. The simulated lot has its own event history and analytics.
The forecast page uses a Birmingham historical replay.
