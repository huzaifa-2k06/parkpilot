*Reviewed with [ml-system-design-review](https://github.com/ML-SystemDesign/MLSystemDesign/tree/main/skills) · [ML System Design](https://arseny.info/ml_design_book) by Kravchenko and Babushkin*

**Follow-up, 2026-11-18:** Validation-only live-policy selection is now implemented.
Regression tests verify that reversing test rankings does not change selected
horizons and that missing full-lot validation cases prevent promotion. The
corrected scenario artifact was regenerated and the Python suite passed 36
tests. This resolves the test-dependent selection code in finding 1; it does
not provide a new untouched evaluation, change the original audit grade, or
resolve findings 2–4. The original review below remains a record of the audited
version. See the [CCA report](CCA-REPORT-ROMAN-URDU.md) for current behavior.

## ML System Design Scorecard: ParkPilot

**Verdict:** Approve with concerns (2.73/4.00) · local prototype, parking availability, advisory use  
**Critical findings:** 1  
**Author verdict:** Valerii and Arseny would recognize the value of retaining persistence when evidence runs thin and ask for an untouched evaluation before endorsing the live policy.

| Dimension | Grade | Evidence |
|---|---|---|
| Problem framing, goals & antigoals | B | The PRD names the driver’s decision and distinguishes simulation from historical replay. The minimum useful forecast improvement is open. |
| Cost of mistakes & risk | B− | False availability explicitly counts a wasted trip. The team has yet to specify a tolerable rate. |
| Prior work, build/buy & baselines | B+ | Persistence competes with regression, forest and a calendar profile in their respective domains and serves as fallback. |
| Metrics, loss & measurement | C+ | Errors use parking-space units. A relative gate accepts a calendar forecast that promises room in roughly half the full-lot cases. |
| Data, labels & features | B | Historical snapshots have a freshness limit and causal lags. Long-horizon scenarios assume a demand process distinct from the automatic worker. |
| Validation & leakage | C | Birmingham selection respects time boundaries. The live policy consults test outcomes when enabling horizons. |
| Error analysis | B | Facility, hour and busy-period slices expose different winners. Full-lot short-horizon behavior remains unmeasured. |
| Training pipeline & reproducibility | B | Scripted training reproduced historical scores and the simulated policy. Artifact metadata lacks a raw dataset digest. |
| Serving, integration & release | B | Typed APIs expose model, horizon and source. Missing policy narrows the supported horizon and the replay gates actuals on its clock. |
| Monitoring, ownership & maintenance | C | The dashboard exposes data freshness and failures. Forecast outcomes still need an owner and a recurring comparison before a pilot. |

**Top fix:** Freeze the live policy using validation runs, then score that fixed policy once on fresh independent seeds.  
**Takeaway:** A full-lot forecast needs two counts beside its average error: how often the lot filled and how often the forecast promised a space on those occasions.

## Evidence and reproduction

**Doc and repo.** Reviewed the [MVP requirements](prd%20(1).md), [ML guide](../ml/README.md), [delivery record](../PROGRESS.md), preprocessing, training, evaluation, artifacts, serving, simulator scenarios, and regression tests on the combined candidate. This grade covers a local demo; real-facility deployment needs additional evidence.

Fresh runs of `python -m ml.train` and `python -m ml.live_forecast` reproduced the following results. The Birmingham CSV SHA-256 was `f1e28b9c697769a1a05cd20148241b60b1a73fee4907611163efc6fd9d12770a`. Training, validation and holdout had 15,917, 5,095 and 5,210 examples respectively. All 29 facilities in the holdout were observed during training.

| Birmingham model | Holdout MAE (spaces) | RMSE (spaces) | R² |
|---|---:|---:|---:|
| Persistence | 50.96 | 91.44 | 0.9861 |
| Linear regression | 20.09 | 36.26 | 0.9978 |
| Random forest | 19.68 | 35.81 | 0.9979 |

Forest MAE ranged from 3.69 at BHMEURBRD02 to 75.78 at Others-CCCPS133. On the 1,071 targets at or above 80% capacity, linear regression achieved 15.27 spaces MAE versus 15.97 for the forest. Report per-facility errors relative to capacity alongside these absolute errors. [Evaluation](../ml/evaluate.py)

## Findings and fix order

1. **Critical · Live model selection reuses test results.** The policy builder filters validation-qualified short leads using test scores and checks both splits before enabling calendar and regression bands. In this run, a validation-only rule would make the same choices across six short leads and two calendar bands. That agreement does not restore independence. Freeze all eligibility decisions on validation, persist the policy, then evaluate it once on new seeds. Add a regression check that changing test labels cannot change the saved policy. [Policy construction](../ml/live_forecast.py)
2. **Major · Full-lot failures pass the current gate.** Each short lead has 1,620 test targets and zero full lots, making false availability unmeasurable. Persistence remains in service. On seasonal same-day targets the selected calendar profile promised space on 49.09% of 929 full targets. On longer targets it did so on 49.08% of 654. Its respective MAEs of 1.92 and 1.96 spaces hide the consequence for a driver. Agree on an absolute false-availability limit, add saturated and near-capacity runs, and report independent-run uncertainty. Keep stress-case and naturally occurring rates separate. [Scoring and gates](../ml/live_forecast.py)
3. **Major · Calendar accuracy depends on a different demand process.** Long-horizon evaluation generates rush hours and vehicle stays. The running automatic worker varies events by eligible bay and speed. The API identifies calendar scenarios as their own source. Preserve that disclosure and evaluate the same frozen policy against recorded worker sessions before promising arrival-time accuracy there. [Scenarios](../simulator/scenarios.py) · [Worker](../simulator/simulator.py) · [Serving](../backend/live_forecast.py)
4. **Minor · Make published scores easier to trace.** Add the CSV digest, training commit and policy identifier to evaluation metadata. Before a pilot, assign an owner to review forecast-versus-observed counts by horizon, full-lot sample size, false availability and fallback frequency. [Training metadata](../ml/train.py)

## Decisions to preserve

The Birmingham splitter excludes labels that cross date partitions. Preprocessing caps reading age at 12 minutes and joins exact facility/time lags, which prevents an overnight gap from masquerading as a half-hour transition. The replay reveals the actual only when the replay clock reaches its target. These choices make the driver-facing comparison reproducible. [Preprocessing](../ml/preprocess.py) · [Chronological split](../ml/train.py) · [Replay](../ml/predict.py)

**Team decision before a pilot.** What false-availability rate would make an arrival forecast worth showing, and who can disable a horizon when measured outcomes exceed it?
