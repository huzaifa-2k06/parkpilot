"""Fit and compare the Birmingham 30-minute occupancy forecasts."""

import argparse
from importlib.metadata import version
import json
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.artifacts import ARTIFACT_VERSION, DEFAULT_ARTIFACT_DIR, save_bundle
from ml.evaluate import FOREST, LINEAR, PERSISTENCE, evaluate
from ml.preprocess import (
    CATEGORICAL_FEATURES,
    DATASET_DOI,
    FEATURES,
    HORIZON_MINUTES,
    NUMERIC_FEATURES,
    SOURCE,
    TIMEZONE,
    build_examples,
    download_dataset,
    load_observations,
)


def chronological_split(
    examples: pd.DataFrame, observations: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], pd.Timestamp, pd.Timestamp]:
    """Split by dates and discard any label that crosses a split boundary."""
    days = sorted(observations['timestamp'].dt.normalize().unique())
    if len(days) < 5:
        raise ValueError('Need observations on at least five days for chronological splitting')
    validation_start, test_start = days[int(len(days) * 0.6)], days[int(len(days) * 0.8)]
    reference, target = examples['reference_at'], examples['target_at']
    splits = {
        'train': examples.loc[reference.lt(validation_start) & target.lt(validation_start)],
        'validation': examples.loc[reference.ge(validation_start) & target.lt(test_start)],
        'test': examples.loc[reference.ge(test_start)],
    }
    if any(rows.empty for rows in splits.values()):
        raise ValueError('A chronological split has no complete 30-minute examples')
    return splits, validation_start, test_start


def fit_candidates(train: pd.DataFrame) -> dict[str, Pipeline | None]:
    target = train['actual_occupancy'] / train['capacity']
    models: dict[str, Pipeline | None] = {PERSISTENCE: None}
    for name, estimator in (
        (LINEAR, LinearRegression()),
        (FOREST, RandomForestRegressor(
            n_estimators=120, max_depth=16, min_samples_leaf=4, random_state=42, n_jobs=2,
        )),
    ):
        columns = ColumnTransformer([
            ('numeric', 'passthrough', list(NUMERIC_FEATURES)),
            ('categorical', OneHotEncoder(handle_unknown='ignore'), list(CATEGORICAL_FEATURES)),
        ])
        pipeline = Pipeline([('features', columns), ('model', estimator)])
        models[name] = pipeline.fit(train[FEATURES], target)
    return models


def train(dataset: Path, artifact_dir: Path) -> dict:
    observations, audit = load_observations(dataset)
    examples = build_examples(observations)
    splits, validation_start, test_start = chronological_split(examples, observations)
    models = fit_candidates(splits['train'])
    validation = evaluate(models, splits['validation'])
    scores = validation['overall']
    selected = min(models, key=lambda name: (scores[name]['mae'], scores[name]['rmse']))
    # The model choice is fixed before any test metrics are computed.
    test = evaluate(models, splits['test'], by_group=True)
    metadata = {
        'source': SOURCE,
        'dataset': 'UCI Parking Birmingham',
        'dataset_doi': DATASET_DOI,
        'timezone': TIMEZONE,
        'horizon_minutes': HORIZON_MINUTES,
        'features': FEATURES,
        'prediction_units': 'spaces',
        'selected_model': selected,
        'selection_rule': 'Lowest validation MAE in spaces, then validation RMSE',
        'dependency_versions': {name: version(name) for name in
                                ('pandas', 'numpy', 'scikit-learn', 'joblib')},
        'audit': {**audit, 'supervised_examples': len(examples)},
        'split_policy': {
            'validation_start': validation_start.isoformat(),
            'test_start': test_start.isoformat(),
            'fractions_by_local_date': [0.6, 0.2, 0.2],
        },
        'splits': {
            name: {
                'rows': len(rows),
                'facilities': int(rows['facility_id'].nunique()),
                'first_reference_at': rows['reference_at'].min().isoformat(),
                'last_reference_at': rows['reference_at'].max().isoformat(),
                'last_target_at': rows['target_at'].max().isoformat(),
            }
            for name, rows in splits.items()
        },
        'validation': validation,
        'test': test,
    }
    save_bundle(artifact_dir, {
        'version': ARTIFACT_VERSION,
        'models': models,
        'metadata': metadata,
        'replay_observations': observations.loc[observations['timestamp'].ge(test_start)].copy(),
    })
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, help='Local UCI CSV. Defaults to the official cache.')
    parser.add_argument('--artifact-dir', type=Path, default=DEFAULT_ARTIFACT_DIR)
    args = parser.parse_args()
    metadata = train(args.dataset or download_dataset(), args.artifact_dir)
    print(json.dumps({
        'selected_model': metadata['selected_model'],
        'splits': metadata['splits'],
        'test_metrics': metadata['test']['overall'],
    }, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
