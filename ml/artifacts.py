"""Read and write the local, versioned model bundle."""

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
import warnings

import joblib
from sklearn.exceptions import InconsistentVersionWarning

from ml.preprocess import ROOT


DEFAULT_ARTIFACT_DIR = ROOT / 'data' / 'ml'
MODEL_FILENAME = 'model.joblib'
METADATA_FILENAME = 'metadata.json'
ARTIFACT_VERSION = 1


class ReplayUnavailableError(RuntimeError):
    """The replay bundle is missing, incompatible, or damaged."""


def save_bundle(directory: Path, bundle: dict[str, Any]) -> None:
    """Publish a fully written bundle without replacing an active partial file."""
    directory.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=directory, suffix='.joblib', delete=False) as file:
        temporary = Path(file.name)
    try:
        joblib.dump(bundle, temporary, compress=3)
        temporary.replace(directory / MODEL_FILENAME)
    finally:
        temporary.unlink(missing_ok=True)

    report = json.dumps(bundle['metadata'], indent=2, allow_nan=False) + '\n'
    (directory / METADATA_FILENAME).write_text(report, encoding='utf-8')


def load_bundle(directory: Path) -> dict[str, Any]:
    """Load a trusted local bundle produced by this project's training command."""
    filename = directory / MODEL_FILENAME
    if not filename.is_file():
        raise ReplayUnavailableError(
            f'No forecast model at {filename}. Run python -m ml.train first.',
        )
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', InconsistentVersionWarning)
            bundle = joblib.load(filename)
    except Exception as error:
        raise ReplayUnavailableError(
            'The forecast bundle could not be loaded. Retrain with the current dependencies.',
        ) from error
    required = {'version', 'models', 'metadata', 'replay_observations'}
    if (
        not isinstance(bundle, dict) or not required.issubset(bundle)
        or bundle['version'] != ARTIFACT_VERSION
    ):
        raise ReplayUnavailableError('The forecast bundle format changed. Run python -m ml.train.')
    return bundle
