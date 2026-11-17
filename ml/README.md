# Birmingham occupancy forecast

This pipeline forecasts the occupancy of a historical Birmingham car park 30
minutes ahead. The live ParkPilot demo uses an independent, simulated 20-space
lot. Birmingham history, predictions, and accuracy measures describe the
historical replay only.

## Run locally

Install the repository requirements, then run the commands from the repository
root.

```sh
python -m ml.preprocess
python -m ml.train
python -m ml.evaluate
python -m ml.predict
```

The first preprocessing or training run downloads the official archive and
caches `data/birmingham/dataset.csv`. Use `--dataset path/to/dataset.csv` for a
local copy. Training writes `data/ml/model.joblib` and `data/ml/metadata.json`.
The bundle contains the fitted candidates and held-out observations. Load
bundles generated locally by the training command. Set `--artifact-dir` to
choose a different local directory.

Run `python -m ml.predict --list-facilities` to list eligible reference
times. The default forecast starts at the earliest eligible held-out reference.
Advance the replay clock to the returned target to compare against the recorded
actual. ISO 8601 times require an explicit offset.

```sh
python -m ml.predict --facility-id BHMBCCMKT01 --reference-at 2016-12-05T09:05:00+00:00 --as-of 2016-12-05T09:35:00+00:00
```

## Data and evaluation

The source is Daniel Stolfi's *Parking Birmingham* from the UCI Machine
Learning Repository (2017). UCI attributes the underlying parking measurements
to Birmingham City Council and publishes the dataset under CC BY 4.0.
[DOI 10.24432/C51K5Z](https://doi.org/10.24432/C51K5Z)

The source covers daytime readings from October through December 2016. The
most frequent native intervals are about 26–27 and 33–34 minutes, with larger
gaps and overnights. Preprocessing and training follow four steps.

1. Excludes missing or impossible counts (including negative and overcapacity
   readings) and invalid timestamps. Collapses exact duplicates and excludes
   conflicting readings for the same facility and timestamp.
2. Builds half-hour snapshots at :05 and :35 Birmingham time. Each snapshot
   uses the latest valid reading available at that instant, at most 12 minutes
   old. Out-of-window readings and earlier readings mapped to the same
   snapshot are excluded.
3. Joins the same facility on exact snapshot times for the 30- and 60-minute
   lags and the 30-minute target. It excludes incomplete samples and targets
   across capacity changes. The replay actual is the snapshot at the target.
4. Splits local dates chronologically 60/20/20 and removes labels that cross
   partition boundaries. Learns from the facility, current capacity,
   current and lagged occupancy fractions, hour, and day of week. Fits both
   regressors on training data and selects the deployment candidate by
   validation MAE, using validation RMSE to break ties.

The published run used 34,247 aligned observations and 26,222 complete
examples. It had 15,917 training, 5,095 validation, and 5,210 held-out
test examples. The test references run from December 5 through December 19,
2016, across 29 facilities.

| Model | Validation MAE (spaces) | Test MAE (spaces) | Test RMSE (spaces) | Test R² |
| --- | ---: | ---: | ---: | ---: |
| Persistence baseline | 49.46 | 50.96 | 91.44 | 0.9861 |
| Linear Regression | 19.73 | 20.09 | 36.26 | 0.9978 |
| Random Forest (selected) | 18.21 | 19.68 | 35.81 | 0.9979 |

`metadata.json` records exact metrics, split periods, features, model selection,
dependency versions, and the cleaning audit. It also reports test metrics by
facility, Birmingham target hour, and busy period (actual target occupancy at
least 80% of capacity). In this run, the selected Random Forest's highest hourly
MAE was 27.42 spaces during the 10:00 hour, compared with 13.96 during the
13:00 hour. Linear Regression had lower MAE in the busy subgroup (15.27
spaces versus 15.97). Pooled R² includes differences between facility sizes,
so the per-facility errors provide additional context.

These results apply to the recorded Birmingham facilities, sampling schedule,
and short 2016 period. They establish no accuracy for Karachi, the simulated
lot, unseen seasons, or present-day operations.
