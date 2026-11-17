"""Evaluate a saved model and persistence on the held-out Birmingham replay."""

import argparse
import json
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.pipeline import Pipeline

from ml.artifacts import DEFAULT_ARTIFACT_DIR, load_bundle
from ml.preprocess import FEATURES, build_examples


PERSISTENCE = 'Persistence baseline'
LINEAR = 'Linear Regression'
FOREST = 'Random Forest'
MODEL_NAMES = (PERSISTENCE, LINEAR, FOREST)
BUSY_OCCUPANCY_RATE = 0.8
Metrics = dict[str, float | int | None]


def predict_spaces(
    model: Pipeline | None, examples: pd.DataFrame,
) -> NDArray[np.float64]:
    current = examples['current_occupancy'].to_numpy(dtype=float)
    if model is None:
        return current
    capacity = examples['capacity'].to_numpy(dtype=float)
    prediction = model.predict(examples[FEATURES]) * capacity
    return np.clip(prediction, 0, capacity)


def metrics(actual: NDArray[np.float64], predicted: NDArray[np.float64]) -> Metrics:
    return {
        'samples': len(actual),
        'mae': float(mean_absolute_error(actual, predicted)),
        'rmse': float(root_mean_squared_error(actual, predicted)),
        'r2': float(r2_score(actual, predicted)) if len(actual) > 1 and np.ptp(actual) > 0 else None,
    }


def evaluate(
    models: dict[str, Pipeline | None], examples: pd.DataFrame, *, by_group: bool = False,
) -> dict:
    """Report MAE/RMSE in spaces and inspect test errors by observed conditions."""
    actual = examples['actual_occupancy'].to_numpy(dtype=float)
    predictions = {name: predict_spaces(model, examples) for name, model in models.items()}
    result: dict = {'overall': {name: metrics(actual, predicted)
                               for name, predicted in predictions.items()}}
    if by_group:
        busy = np.where(
            examples['actual_occupancy'] / examples['target_capacity'] >= BUSY_OCCUPANCY_RATE,
            'busy', 'below_80_percent',
        )
        groups = examples.assign(target_hour=examples['target_at'].dt.hour, busy_period=busy)
        for column in ('facility_id', 'target_hour', 'busy_period'):
            result[f'by_{column}'] = {
                str(key): {name: metrics(actual[positions], prediction[positions])
                           for name, prediction in predictions.items()}
                for key, positions in groups.groupby(column).indices.items()
            }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact-dir', type=Path, default=DEFAULT_ARTIFACT_DIR)
    args = parser.parse_args()
    bundle = load_bundle(args.artifact_dir)
    examples = build_examples(bundle['replay_observations'])
    report = evaluate(bundle['models'], examples, by_group=True)
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
