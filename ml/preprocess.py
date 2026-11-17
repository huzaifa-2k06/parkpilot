"""Build causal, half-hour occupancy snapshots from the Birmingham measurements."""

import argparse
from io import BytesIO
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from zipfile import ZipFile

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = ROOT / 'data' / 'birmingham' / 'dataset.csv'
DATASET_URL = 'https://archive.ics.uci.edu/static/public/482/parking%2Bbirmingham.zip'
DATASET_DOI = 'https://doi.org/10.24432/C51K5Z'
SOURCE = 'uci_parking_birmingham'
TIMEZONE = 'Europe/London'
HORIZON_MINUTES = 30
GRID_OFFSET_MINUTES = 5
MAX_OBSERVATION_AGE_MINUTES = 12
LAG_MINUTES = (30, 60)
SOURCE_COLUMNS = {
    'SystemCodeNumber': 'facility_id',
    'Capacity': 'capacity',
    'Occupancy': 'occupancy',
    'LastUpdated': 'observed_at',
}
NUMERIC_FEATURES = ('capacity', 'occupancy_rate', 'lag_30_rate', 'lag_60_rate', 'hour')
CATEGORICAL_FEATURES = ('facility_id', 'weekday')
FEATURES = list(NUMERIC_FEATURES + CATEGORICAL_FEATURES)


def download_dataset() -> Path:
    """Cache the official archive's CSV once, without a data-client dependency."""
    if DEFAULT_DATASET.is_file():
        return DEFAULT_DATASET
    archive = DEFAULT_DATASET.with_name('uci.zip')
    if archive.is_file():
        payload = archive.read_bytes()
    else:
        with urlopen(DATASET_URL, timeout=45) as response:
            payload = response.read()
    with ZipFile(BytesIO(payload)) as source:
        csv = source.read('dataset.csv')

    DEFAULT_DATASET.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=DEFAULT_DATASET.parent, delete=False) as temporary:
        temporary.write(csv)
    temporary_path = Path(temporary.name)
    try:
        temporary_path.replace(DEFAULT_DATASET)
    finally:
        temporary_path.unlink(missing_ok=True)
    return DEFAULT_DATASET


def load_observations(path: Path) -> tuple[pd.DataFrame, dict]:
    """Audit native spacing, clean counts, and standardize the sampling clock."""
    raw = pd.read_csv(path, dtype={'SystemCodeNumber': 'string'})
    missing_columns = SOURCE_COLUMNS.keys() - set(raw.columns)
    if missing_columns:
        raise ValueError(f'Missing source columns: {", ".join(sorted(missing_columns))}')

    readings = raw[list(SOURCE_COLUMNS)].rename(columns=SOURCE_COLUMNS)
    readings['facility_id'] = readings['facility_id'].str.strip()
    readings['observed_at'] = pd.to_datetime(
        readings['observed_at'], format='%Y-%m-%d %H:%M:%S', errors='coerce',
    )
    for column in ('capacity', 'occupancy'):
        readings[column] = pd.to_numeric(readings[column], errors='coerce')
    readings = readings.sort_values(['facility_id', 'observed_at'])

    gaps = readings.groupby('facility_id')['observed_at'].diff().dt.total_seconds().div(60)
    gap_histogram = gaps.dropna().round().astype(int).value_counts().head(10)
    valid = (
        readings['facility_id'].notna() & readings['facility_id'].ne('')
        & readings['observed_at'].notna()
        & readings['capacity'].gt(0)
        & readings['occupancy'].between(0, readings['capacity'])
        & readings['capacity'].mod(1).eq(0) & readings['occupancy'].mod(1).eq(0)
    )
    cleaned = readings.loc[valid].copy()
    unique = cleaned.drop_duplicates()
    conflicts = unique.duplicated(['facility_id', 'observed_at'], keep=False)
    reliable = unique.loc[~conflicts].copy()

    observed = reliable['observed_at']
    offset = pd.Timedelta(minutes=GRID_OFFSET_MINUTES)
    slot = (observed - offset).dt.ceil('30min') + offset
    local_minutes = slot.dt.hour * 60 + slot.dt.minute
    in_window = (
        (slot - observed).le(pd.Timedelta(minutes=MAX_OBSERVATION_AGE_MINUTES))
        & slot.dt.normalize().eq(observed.dt.normalize())
        & local_minutes.between(8 * 60 + 5, 16 * 60 + 35)
    )
    aligned = reliable.loc[in_window].assign(timestamp=slot.loc[in_window])
    # The latest observed measurement in a slot was already available at its endpoint.
    aligned = aligned.drop_duplicates(['facility_id', 'timestamp'], keep='last').copy()
    for column in ('observed_at', 'timestamp'):
        aligned[column] = aligned[column].dt.tz_localize(TIMEZONE)
    aligned = aligned.astype({'capacity': int, 'occupancy': int}).reset_index(drop=True)
    if aligned.empty:
        raise ValueError('No valid in-hours observations could be aligned to the 30-minute clock')

    audit = {
        'raw_rows': len(raw),
        'raw_facilities': int(readings['facility_id'].nunique()),
        'native_gap_median_minutes': None if gaps.dropna().empty else float(gaps.median()),
        'native_gap_top_rounded_minutes': {str(gap): int(count) for gap, count in gap_histogram.items()},
        'invalid_rows_removed': len(readings) - len(cleaned),
        'exact_duplicates_removed': len(cleaned) - len(unique),
        'conflicting_timestamp_rows_removed': int(conflicts.sum()),
        'out_of_window_rows_removed': len(reliable) - int(in_window.sum()),
        'earlier_same_slot_rows_removed': int(in_window.sum()) - len(aligned),
        'aligned_observations': len(aligned),
        'aligned_facilities': int(aligned['facility_id'].nunique()),
        'grid_minutes': HORIZON_MINUTES,
        'grid_offset_minutes': GRID_OFFSET_MINUTES,
        'max_observation_age_minutes': MAX_OBSERVATION_AGE_MINUTES,
    }
    return aligned, audit


def build_examples(observations: pd.DataFrame) -> pd.DataFrame:
    """Join observations by facility and exact clock time, dropping gaps."""
    examples = observations.rename(columns={
        'timestamp': 'reference_at', 'occupancy': 'current_occupancy',
    }).copy()
    reference = examples['reference_at']
    examples['occupancy_rate'] = examples['current_occupancy'] / examples['capacity']
    examples['hour'] = reference.dt.hour + reference.dt.minute / 60
    examples['weekday'] = reference.dt.dayofweek

    for minutes in LAG_MINUTES:
        lag = observations[['facility_id']].copy()
        lag['reference_at'] = observations['timestamp'] + pd.Timedelta(minutes=minutes)
        lag[f'lag_{minutes}_rate'] = observations['occupancy'] / observations['capacity']
        examples = examples.merge(lag, on=['facility_id', 'reference_at'], validate='one_to_one')

    examples['target_at'] = examples['reference_at'] + pd.Timedelta(minutes=HORIZON_MINUTES)
    targets = observations[['facility_id', 'timestamp', 'occupancy', 'capacity', 'observed_at']].rename(
        columns={'timestamp': 'target_at', 'occupancy': 'actual_occupancy',
                 'capacity': 'target_capacity', 'observed_at': 'actual_observed_at'},
    )
    examples = examples.merge(targets, on=['facility_id', 'target_at'], validate='one_to_one')
    examples = examples.loc[examples['target_capacity'].eq(examples['capacity'])]
    return examples.sort_values(['reference_at', 'facility_id']).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, help='Local UCI CSV. Defaults to the official cache.')
    args = parser.parse_args()
    observations, audit = load_observations(args.dataset or download_dataset())
    audit['supervised_examples'] = len(build_examples(observations))
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
