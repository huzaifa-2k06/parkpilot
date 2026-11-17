"""Train and evaluate arrival forecasts for the simulated ParkPilot lot."""

import argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import json
from math import cos, pi, sin, sqrt
from pathlib import Path
from statistics import median
from tempfile import NamedTemporaryFile
from typing import Literal

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = ROOT / 'data' / 'live_forecast' / 'forecast.json'
GRID_MINUTES = 5
SHORT_MINUTES = 30
DAY_MINUTES = 1440
WEEK_MINUTES = 7 * DAY_MINUTES
LOOKBACK_STEPS = 3
ShortWeights = tuple[float, float, float, float, float, float, float, float]
CalendarWeights = tuple[float, float, float, float, float]
ModelName = Literal['Persistence', 'Recent activity regression', 'Calendar baseline', 'Calendar regression']
CalendarBand = Literal['same_day', 'within_week']


class ForecastPolicy(BaseModel):
    version: Literal[1]
    capacity: int = Field(gt=0)
    short_weights: ShortWeights
    short_intercept: float
    learned_short_minutes: list[int]
    calendar_profile: list[int] = Field(min_length=168, max_length=168)
    calendar_weights: CalendarWeights
    calendar_intercept: float
    calendar_bands: list[CalendarBand]
    learned_calendar_bands: list[CalendarBand]

    @property
    def max_horizon_minutes(self) -> int:
        if 'same_day' not in self.calendar_bands:
            return SHORT_MINUTES
        return WEEK_MINUTES if 'within_week' in self.calendar_bands else DAY_MINUTES


@lru_cache(maxsize=4)
def _read_policy(path: Path, _changed_at: int) -> ForecastPolicy | None:
    try:
        with path.open(encoding='utf-8') as file:
            return ForecastPolicy.model_validate(json.load(file)['policy'])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def load_policy(path: Path) -> ForecastPolicy | None:
    try:
        return _read_policy(path, path.stat().st_mtime_ns)
    except OSError:
        return None


def calendar_slot(target: datetime) -> int:
    utc = target.astimezone(timezone.utc)
    return utc.weekday() * 24 + utc.hour


def calendar_features(target: datetime) -> CalendarWeights:
    utc = target.astimezone(timezone.utc)
    phase = 2 * pi * (utc.hour * 60 + utc.minute) / DAY_MINUTES
    return sin(phase), cos(phase), sin(phase * 2), cos(phase * 2), float(utc.weekday() >= 5)


def calendar_band(minutes: float) -> CalendarBand:
    return 'same_day' if minutes <= DAY_MINUTES else 'within_week'


def short_features(snapshots: list[int], counts: tuple[int, int], lead: int, speed: float) -> ShortWeights:
    current, five, ten, fifteen = snapshots
    arrivals, departures = counts
    return current, five, ten, fifteen, arrivals, departures, lead, speed


def estimated_occupancy(weights: tuple[float, ...], intercept: float,
                        features: tuple[float, ...], capacity: int) -> int:
    return max(0, min(capacity, round(intercept + sum(
        weight * value for weight, value in zip(weights, features, strict=True)
    ))))


def choose_forecast(
    policy: ForecastPolicy | None,
    capacity: int,
    snapshots: list[int],
    counts: tuple[int, int],
    target: datetime,
    minutes: float,
    speed: float | None,
) -> tuple[int, ModelName]:
    if minutes <= SHORT_MINUTES:
        # Fixed five-minute leads match the evaluation grid. Other requests use persistence.
        lead = round(minutes / GRID_MINUTES) * GRID_MINUTES
        if (policy and speed in (0.5, 1, 2) and lead in policy.learned_short_minutes
                and abs(minutes - lead) <= 0.25):
            return estimated_occupancy(
                policy.short_weights, policy.short_intercept,
                short_features(snapshots, counts, lead, speed), capacity,
            ), 'Recent activity regression'
        return snapshots[0], 'Persistence'

    if policy is None or minutes > policy.max_horizon_minutes:
        raise ValueError('This calendar horizon is unavailable')
    if calendar_band(minutes) in policy.learned_calendar_bands:
        return estimated_occupancy(
            policy.calendar_weights, policy.calendar_intercept, calendar_features(target), capacity,
        ), 'Calendar regression'
    return max(0, min(capacity, policy.calendar_profile[calendar_slot(target)])), 'Calendar baseline'


class Scores(BaseModel):
    samples: int
    full_samples: int
    mae: float
    rmse: float
    r2: float | None
    false_availability: float | None


def scores(actual: list[int], predicted: list[int], capacity: int) -> Scores:
    mean = sum(actual) / len(actual)
    squared_error = sum((truth - estimate) ** 2 for truth, estimate in zip(actual, predicted))
    total_variance = sum((truth - mean) ** 2 for truth in actual)
    full = actual.count(capacity)
    false_free = sum(truth == capacity and estimate < capacity
                     for truth, estimate in zip(actual, predicted))
    return Scores(
        samples=len(actual), full_samples=full,
        mae=sum(abs(truth - estimate) for truth, estimate in zip(actual, predicted)) / len(actual),
        rmse=sqrt(squared_error / len(actual)),
        r2=1 - squared_error / total_variance if total_variance else None,
        false_availability=false_free / full if full else None,
    )


def improves(candidate: Scores, baseline: Scores) -> bool:
    return (candidate.mae < baseline.mae
            and candidate.false_availability is not None
            and baseline.false_availability is not None
            and candidate.false_availability <= baseline.false_availability)


def train(output: Path) -> dict:
    from sklearn.linear_model import Ridge
    from simulator.scenarios import DEMO_CAPACITY, fast_run, seasonal_run

    capacity = DEMO_CAPACITY
    short_leads = range(GRID_MINUTES, SHORT_MINUTES + 1, GRID_MINUTES)
    speed_levels = (0.5, 1.0, 2.0)
    short_rows: dict[str, dict[int, list[tuple[ShortWeights, int]]]] = {
        split: defaultdict(list) for split in ('train', 'validation', 'test')
    }
    for split, seeds in [('train', range(24)), ('validation', range(24, 36)),
                         ('test', range(36, 48))]:
        for seed in seeds:
            speed = speed_levels[seed % len(speed_levels)]
            occupied, arrivals, departures = fast_run(seed, 144, speed)
            for offset in range(LOOKBACK_STEPS, len(occupied) - SHORT_MINUTES // GRID_MINUTES):
                snapshots = occupied[offset - LOOKBACK_STEPS:offset + 1][::-1]
                counts = (arrivals[offset] - arrivals[offset - LOOKBACK_STEPS],
                          departures[offset] - departures[offset - LOOKBACK_STEPS])
                for lead in short_leads:
                    short_rows[split][lead].append((
                        short_features(snapshots, counts, lead, speed),
                        occupied[offset + lead // GRID_MINUTES],
                    ))

    short_train = [row for rows in short_rows['train'].values() for row in rows]
    short_model = Ridge().fit([row[0] for row in short_train], [row[1] for row in short_train])
    short_weights = tuple(short_model.coef_.tolist())
    short_intercept = float(short_model.intercept_)
    short_reports = {}
    short_candidates = []
    for lead in short_leads:
        report = {}
        for split in ('validation', 'test'):
            rows = short_rows[split][lead]
            actual = [row[1] for row in rows]
            baseline = scores(actual, [int(row[0][0]) for row in rows], capacity)
            candidate = scores(actual, [
                estimated_occupancy(short_weights, short_intercept, row[0], capacity) for row in rows
            ], capacity)
            report[split] = {'persistence': baseline, 'regression': candidate}
        validation = report['validation']
        if improves(validation['regression'], validation['persistence']):
            short_candidates.append(lead)
        short_reports[lead] = report

    start = datetime(2025, 1, 6, tzinfo=timezone.utc)
    step = timedelta(minutes=GRID_MINUTES)
    calendar_train = seasonal_run(100, start, weeks=4)
    slots: dict[int, list[int]] = defaultdict(list)
    for index, occupancy in enumerate(calendar_train):
        slots[calendar_slot(start + step * index)].append(occupancy)
    profile = [round(median(slots[slot])) for slot in range(168)]
    calendar_model = Ridge().fit(
        [calendar_features(start + step * index) for index in range(len(calendar_train))],
        calendar_train,
    )
    calendar_weights = tuple(calendar_model.coef_.tolist())
    calendar_intercept = float(calendar_model.intercept_)
    calendar_reports: dict[CalendarBand, dict] = {'same_day': {}, 'within_week': {}}
    for split, seed, offset_weeks in [('validation', 101, 4), ('test', 102, 7)]:
        start_at = start + timedelta(weeks=offset_weeks)
        counts = seasonal_run(seed, start_at, weeks=3)
        for band, bounds in [('same_day', (35, DAY_MINUTES)),
                             ('within_week', (DAY_MINUTES + GRID_MINUTES, WEEK_MINUTES))]:
            lower, upper = (bound // GRID_MINUTES for bound in bounds)
            # Give each target a range of leads within the band without reusing training dates.
            indices = range(upper, len(counts))
            timestamps = [start_at + step * index for index in indices]
            actual = list(counts[upper:])
            calendar_reports[band][split] = {
                'persistence': scores(actual, [
                    counts[index - (lower + index % (upper - lower + 1))] for index in indices
                ], capacity),
                'calendar': scores(actual, [profile[calendar_slot(t)] for t in timestamps], capacity),
                'regression': scores(actual, [
                    estimated_occupancy(calendar_weights, calendar_intercept,
                                        calendar_features(t), capacity) for t in timestamps
                ], capacity),
            }
    policy = ForecastPolicy(
        version=1, capacity=capacity,
        short_weights=short_weights, short_intercept=short_intercept,
        learned_short_minutes=[
            lead for lead in short_candidates
            if improves(short_reports[lead]['test']['regression'],
                        short_reports[lead]['test']['persistence'])
        ],
        calendar_profile=profile, calendar_weights=calendar_weights,
        calendar_intercept=calendar_intercept,
        calendar_bands=[
            band for band, report in calendar_reports.items()
            if all(improves(report[split]['calendar'], report[split]['persistence'])
                   for split in ('validation', 'test'))
        ],
        learned_calendar_bands=[
            band for band, report in calendar_reports.items()
            if all(improves(report[split]['regression'], report[split]['calendar'])
                   for split in ('validation', 'test'))
        ],
    )
    report = {
        'source': 'ParkPilot simulated scenarios',
        'short_minutes': short_reports, 'calendar_bands': calendar_reports,
        'policy': policy,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode='w', encoding='utf-8', dir=output.parent,
                            suffix='.tmp', delete=False) as file:
        temporary = Path(file.name)
        json.dump(report, file, indent=2, default=lambda value: value.model_dump(), allow_nan=False)
    try:
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_POLICY_PATH)
    args = parser.parse_args()
    policy = train(args.output)['policy']
    print(f'Wrote {args.output}')
    print(f'Approved recent-activity leads: {policy.learned_short_minutes or "none"}')
    print(f'Approved calendar bands: {policy.calendar_bands or "none"}')
    print(f'Approved calendar regression bands: {policy.learned_calendar_bands or "none"}')


if __name__ == '__main__':
    main()
