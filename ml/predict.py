"""Forecast and reveal actuals on the historical Birmingham replay clock."""

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ml.artifacts import DEFAULT_ARTIFACT_DIR, ReplayUnavailableError, load_bundle
from ml.evaluate import predict_spaces
from ml.preprocess import HORIZON_MINUTES, SOURCE, TIMEZONE, build_examples


class ReplayNotFoundError(LookupError):
    """The facility or reference time is absent from the held-out replay."""


class ReplayInputError(ValueError):
    """The replay clock input is invalid."""


def parse_timestamp(value: str, field: str) -> pd.Timestamp:
    """Accept ISO 8601 timestamps with an explicit offset."""
    message = f'{field} must be an ISO 8601 datetime with a timezone offset'
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.utcoffset() is not None:
            return pd.Timestamp(parsed).tz_convert(TIMEZONE)
    except (TypeError, ValueError, OverflowError) as error:
        raise ReplayInputError(message) from error
    raise ReplayInputError(message)


class HistoricalReplay:
    def __init__(self, bundle: dict[str, Any]) -> None:
        metadata = bundle['metadata']
        if metadata['source'] != SOURCE or metadata['horizon_minutes'] != HORIZON_MINUTES:
            raise ValueError('Unexpected model domain or horizon')
        self.observations = bundle['replay_observations']
        examples = build_examples(self.observations)
        if examples.empty:
            raise ValueError('The forecast bundle has no held-out examples')
        self.examples = {
            str(facility): rows.set_index('reference_at', drop=False)
            for facility, rows in examples.groupby('facility_id')
        }
        self.earliest_facility = str(examples.iloc[0]['facility_id'])
        self.model_name = metadata['selected_model']
        self.model = bundle['models'][self.model_name]
        selected_metrics = metadata['test']['overall'][self.model_name]
        self.metrics = {key: selected_metrics[key] for key in ('mae', 'rmse', 'r2')}

    def catalog(self) -> dict[str, Any]:
        facilities = []
        for facility, examples in self.examples.items():
            references = [timestamp.isoformat() for timestamp in examples.index]
            facilities.append({
                'facility_id': facility,
                'first_reference_at': references[0],
                'last_reference_at': references[-1],
                'reference_times': references,
            })
        return {'source': SOURCE, 'timezone': TIMEZONE, 'horizon_minutes': HORIZON_MINUTES,
                'facilities': facilities}

    def forecast(
        self,
        facility_id: str | None = None,
        reference_at: str | None = None,
        as_of: str | None = None,
    ) -> dict[str, Any]:
        """Predict from reference-time features and reveal actuals at the target."""
        facility = self.earliest_facility if facility_id is None else facility_id
        if facility not in self.examples:
            raise ReplayNotFoundError(f'No held-out replay for facility {facility}')
        examples = self.examples[facility]
        reference = (examples.index[0] if reference_at is None
                     else parse_timestamp(reference_at, 'reference_at'))
        replay_clock = reference if as_of is None else parse_timestamp(as_of, 'as_of')
        if replay_clock < reference:
            raise ReplayInputError('as_of cannot precede reference_at')
        if reference not in examples.index:
            raise ReplayNotFoundError(f'No complete held-out example for {facility} at {reference}')

        example = examples.loc[[reference]]
        row = example.iloc[0]
        target = row['target_at']
        capacity = int(row['capacity'])
        predicted = float(predict_spaces(self.model, example)[0])
        actual = int(row['actual_occupancy']) if replay_clock >= target else None

        same_facility = self.observations['facility_id'].eq(facility)
        timestamps = self.observations['timestamp']
        visible = self.observations.loc[
            same_facility & timestamps.le(reference) & timestamps.ge(reference.normalize()),
        ].tail(12)
        history = [
            {'timestamp': item.timestamp.isoformat(), 'occupancy': int(item.occupancy)}
            for item in visible.itertuples(index=False)
        ]
        return {
            'source': SOURCE,
            'timezone': TIMEZONE,
            'facility_id': facility,
            'horizon_minutes': HORIZON_MINUTES,
            'model_name': self.model_name,
            'reference_at': reference.isoformat(),
            'target_at': target.isoformat(),
            'as_of': replay_clock.isoformat(),
            'capacity': capacity,
            'current_occupancy': int(row['current_occupancy']),
            'predicted_occupancy': predicted,
            'predicted_free_spaces': capacity - predicted,
            'actual_occupancy': actual,
            'actual_free_spaces': None if actual is None else capacity - actual,
            'history': history,
            'metrics': self.metrics.copy(),
        }


def load_replay(artifact_dir: Path = DEFAULT_ARTIFACT_DIR) -> HistoricalReplay:
    bundle = load_bundle(artifact_dir)
    try:
        return HistoricalReplay(bundle)
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise ReplayUnavailableError(
            'The forecast bundle is incomplete or incompatible. Run python -m ml.train.',
        ) from error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument('--facility-id')
    parser.add_argument('--reference-at', help='ISO 8601 timestamp with an explicit offset')
    parser.add_argument('--as-of', help='Replay clock. Defaults to the reference time.')
    parser.add_argument('--list-facilities', action='store_true')
    args = parser.parse_args()
    try:
        replay = load_replay(args.artifact_dir)
        result = (replay.catalog() if args.list_facilities
                  else replay.forecast(args.facility_id, args.reference_at, args.as_of))
    except (ReplayUnavailableError, ReplayInputError, ReplayNotFoundError) as error:
        parser.exit(2, f'{error}\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
