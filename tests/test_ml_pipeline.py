"""Check the historical model's time alignment and replay contract."""

from pathlib import Path

import pandas as pd
import pytest

from ml.artifacts import load_bundle
from ml.evaluate import MODEL_NAMES, evaluate
from ml.predict import ReplayInputError, ReplayNotFoundError, ReplayUnavailableError, load_replay
from ml.preprocess import TIMEZONE, build_examples, load_observations
from ml.train import chronological_split, train


def test_clock_grid_and_lags_never_use_future_or_gapped_readings(tmp_path: Path) -> None:
    csv = tmp_path / 'dataset.csv'
    csv.write_text(
        'SystemCodeNumber,Capacity,Occupancy,LastUpdated\n'
        'A,20,2,2016-12-05 07:59:42\n'
        'A,20,3,2016-12-05 08:25:42\n'
        'A,20,4,2016-12-05 08:59:42\n'
        'A,20,5,2016-12-05 09:04:00\n'
        'A,20,6,2016-12-05 09:06:00\n'
        'A,20,7,2016-12-05 09:32:46\n'
        'A,20,22,2016-12-05 10:00:00\n'
        'B,20,11,2016-12-05 07:59:42\n'
        'B,20,12,2016-12-05 08:59:42\n'
        'B,20,16,2016-12-05 09:32:46\n',
        encoding='utf-8',
    )
    observations, audit = load_observations(csv)
    assert audit['out_of_window_rows_removed'] == 1
    assert audit['earlier_same_slot_rows_removed'] == 1
    assert audit['invalid_rows_removed'] == 1
    assert observations['observed_at'].le(observations['timestamp']).all()

    examples = build_examples(observations)
    assert len(examples) == 1
    example = examples.iloc[0]
    assert example['facility_id'] == 'A'
    assert example['reference_at'].isoformat() == '2016-12-05T09:05:00+00:00'
    assert example['target_at'] - example['reference_at'] == pd.Timedelta(minutes=30)
    assert example['current_occupancy'] == 5
    assert example['lag_30_rate'] == 3 / 20
    assert example['lag_60_rate'] == 2 / 20
    assert example['actual_occupancy'] == 7


@pytest.fixture
def readings_csv(tmp_path: Path) -> Path:
    source = tmp_path / 'readings.csv'
    lines = ['SystemCodeNumber,Capacity,Occupancy,LastUpdated']
    for day in range(1, 11):
        for facility, capacity in [('A', 20), ('B', 30)]:
            for slot in range(6):
                reading = f'2016-12-{day:02d} {8 + slot // 2:02d}:{slot % 2 * 30:02d}:00'
                occupancy = min(capacity, day + slot + (capacity - 20))
                lines.append(f'{facility},{capacity},{occupancy},{reading}')
    source.write_text('\n'.join(lines), encoding='utf-8')
    return source


def test_date_splits_exclude_boundary_crossing_labels(readings_csv: Path) -> None:
    observations, _ = load_observations(readings_csv)
    examples = build_examples(observations)
    bridge = examples.iloc[[0]].copy()
    bridge['reference_at'] = pd.Timestamp('2016-12-06T23:45:00', tz=TIMEZONE)
    bridge['target_at'] = pd.Timestamp('2016-12-07T00:15:00', tz=TIMEZONE)
    splits, validation, test = chronological_split(
        pd.concat([examples, bridge], ignore_index=True), observations,
    )
    assert sum(map(len, splits.values())) == len(examples)
    assert splits['train']['target_at'].max() < validation
    assert validation <= splits['validation']['reference_at'].min()
    assert splits['validation']['target_at'].max() < test
    assert test <= splits['test']['reference_at'].min()


def test_training_and_replay_reveal_only_at_target(readings_csv: Path, tmp_path: Path) -> None:
    directory = tmp_path / 'artifacts'
    metadata = train(readings_csv, directory)
    assert set(metadata['test']['overall']) == set(MODEL_NAMES)
    bundle = load_bundle(directory)
    reevaluated = evaluate(bundle['models'], build_examples(bundle['replay_observations']))['overall']
    for model, scores in metadata['test']['overall'].items():
        assert reevaluated[model] == pytest.approx(scores)

    replay = load_replay(directory)
    assert [entry['facility_id'] for entry in replay.catalog()['facilities']] == ['A', 'B']
    forecast = replay.forecast('A')
    assert forecast['source'] == 'uci_parking_birmingham'
    assert forecast['as_of'] == forecast['reference_at']
    assert forecast['actual_occupancy'] is None
    assert forecast['actual_free_spaces'] is None
    assert all(point['timestamp'] <= forecast['reference_at'] for point in forecast['history'])
    premature = (pd.Timestamp(forecast['target_at']) - pd.Timedelta(seconds=1)).isoformat()
    assert replay.forecast('A', forecast['reference_at'], premature)['actual_occupancy'] is None
    comparison = replay.forecast('A', forecast['reference_at'], forecast['target_at'])
    assert comparison['actual_occupancy'] == 12
    assert comparison['predicted_occupancy'] == pytest.approx(forecast['predicted_occupancy'])
    assert comparison['predicted_free_spaces'] == 20 - comparison['predicted_occupancy']
    assert comparison['actual_free_spaces'] == 8

    with pytest.raises(ReplayInputError, match='timezone offset'):
        replay.forecast('A', '2016-12-09T09:05:00')
    with pytest.raises(ReplayInputError, match='cannot precede'):
        replay.forecast('A', forecast['reference_at'], '2016-12-08T09:05:00+00:00')
    with pytest.raises(ReplayNotFoundError, match='No complete'):
        replay.forecast('A', '2016-12-09T23:05:00+00:00')
    with pytest.raises(ReplayNotFoundError, match='No held-out'):
        replay.forecast('unknown')


def test_missing_replay_bundle_raises_an_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(ReplayUnavailableError, match='python -m ml.train'):
        load_replay(tmp_path)
