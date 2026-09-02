"""Schema-validated inference for the local CRISP-DM model bundle."""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np

SUPPORTED_BUNDLE_SCHEMA_VERSION = "1.1"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _normalise_state(value: Any) -> Any:
    """Convert fitted estimator state into deterministic JSON-compatible data."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _normalise_state(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_normalise_state(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def fitted_model_fingerprint(model: Any) -> str:
    """Fingerprint learned estimator state separately from configuration."""
    if not hasattr(model, "predict"):
        raise ValueError("Model bundle must contain a fitted estimator")
    state: dict[str, Any] = {"estimator": model.__class__.__name__}
    if hasattr(model, "named_steps"):
        state["steps"] = {
            str(name): fitted_model_fingerprint_payload(step)
            for name, step in model.named_steps.items()
        }
    else:
        state["fitted_attributes"] = {
            key: _normalise_state(value)
            for key, value in sorted(vars(model).items())
            if key.endswith("_") and not key.startswith("__")
        }
    return _sha256_bytes(json.dumps(state, separators=(",", ":"), sort_keys=True, default=repr).encode("utf-8"))


def fitted_model_fingerprint_payload(model: Any) -> dict[str, Any]:
    return {
        "estimator": model.__class__.__name__,
        "fitted_attributes": {
            key: _normalise_state(value)
            for key, value in sorted(vars(model).items())
            if key.endswith("_") and not key.startswith("__")
        },
    }


def model_configuration_fingerprint(model: Any) -> str:
    if not hasattr(model, "get_params"):
        raise ValueError("Model bundle must contain an estimator with configuration")
    payload = _normalise_state(model.get_params(deep=True))
    return _sha256_bytes(json.dumps(payload, separators=(",", ":"), sort_keys=True, default=repr).encode("utf-8"))


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _validate_contract(contract: Any) -> dict[str, Any]:
    if not isinstance(contract, dict):
        raise ValueError("Model bundle feature_contract must be an object")
    required = {"feature_names", "units", "dtype", "required_count", "allowed_range_per_feature", "invalid_input_policy"}
    if not required.issubset(contract):
        raise ValueError(f"Model bundle feature_contract is missing: {sorted(required - set(contract))}")
    names = contract["feature_names"]
    if not isinstance(names, list) or not names or len(set(names)) != len(names):
        raise ValueError("Model bundle feature_contract feature_names must be a unique non-empty list")
    if int(contract["required_count"]) != len(names):
        raise ValueError("Model bundle feature_contract required_count does not match feature_names")
    bounds = contract["allowed_range_per_feature"]
    if not isinstance(bounds, list) or len(bounds) != 2:
        raise ValueError("Model bundle feature_contract must declare two input bounds")
    lower, upper = (float(value) for value in bounds)
    if not np.isfinite([lower, upper]).all() or lower > upper:
        raise ValueError("Model bundle feature_contract bounds are invalid")
    if not isinstance(contract["units"], str) or not isinstance(contract["dtype"], str):
        raise ValueError("Model bundle feature_contract units and dtype must be strings")
    if contract["units"] != "cm":
        raise ValueError("Model bundle feature_contract units must be cm")
    if contract["dtype"] != "finite real number":
        raise ValueError("Model bundle feature_contract dtype must be finite real number")
    return contract


def load_model_bundle(model_path: Path) -> dict[str, Any]:
    bundle = joblib.load(model_path)
    if not isinstance(bundle, dict) or "model" not in bundle or "feature_contract" not in bundle:
        raise ValueError("Model artifact is not a supported CRISP-DM model bundle")
    if bundle.get("bundle_schema_version") != SUPPORTED_BUNDLE_SCHEMA_VERSION:
        raise ValueError(f"Unsupported model bundle schema: {bundle.get('bundle_schema_version')!r}")
    contract = _validate_contract(bundle["feature_contract"])
    target_names = bundle.get("target_names")
    model = bundle["model"]
    if not isinstance(target_names, list) or not target_names or len(set(target_names)) != len(target_names):
        raise ValueError("Model bundle target_names must be a unique non-empty list")
    if not hasattr(model, "predict") or not hasattr(model, "classes_"):
        raise ValueError("Model bundle model must be a fitted classifier with classes_")
    classes = np.asarray(model.classes_)
    expected_classes = np.arange(len(target_names))
    if classes.shape != expected_classes.shape or not np.array_equal(classes, expected_classes):
        raise ValueError("Model classes_ must be ordered as target_names indices")
    if not _is_sha256(bundle.get("dataset_sha256")):
        raise ValueError("Model bundle dataset_sha256 must be a SHA-256 fingerprint")
    snapshot_name = bundle.get("dataset_snapshot")
    if not isinstance(snapshot_name, str) or Path(snapshot_name).name != snapshot_name:
        raise ValueError("Model bundle dataset_snapshot must be a filename")
    if not _is_sha256(bundle.get("dataset_snapshot_sha256")):
        raise ValueError("Model bundle dataset_snapshot_sha256 is missing or invalid")
    snapshot_path = model_path.parent / snapshot_name
    if snapshot_path.exists() and _sha256_file(snapshot_path) != bundle["dataset_snapshot_sha256"]:
        raise ValueError("Model bundle dataset snapshot hash does not match the local snapshot")
    if not _is_sha256(bundle.get("model_configuration_fingerprint")):
        raise ValueError("Model bundle model_configuration_fingerprint is missing or invalid")
    if not _is_sha256(bundle.get("fitted_model_fingerprint")):
        raise ValueError("Model bundle fitted_model_fingerprint is missing or invalid")
    if model_configuration_fingerprint(model) != bundle["model_configuration_fingerprint"]:
        raise ValueError("Model bundle configuration fingerprint does not match the estimator")
    if fitted_model_fingerprint(model) != bundle["fitted_model_fingerprint"]:
        raise ValueError("Model bundle fitted-artifact fingerprint does not match the estimator")
    if contract["required_count"] != getattr(model, "n_features_in_", contract["required_count"]):
        raise ValueError("Model bundle feature count does not match the estimator")
    return bundle


def validate_features(features: Sequence[float], contract: dict[str, Any]) -> np.ndarray:
    contract = _validate_contract(contract)
    expected = int(contract["required_count"])
    if len(features) != expected:
        raise ValueError(f"Expected exactly {expected} features: {contract['feature_names']}")
    try:
        values = np.asarray(features, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("Features must be finite numeric values in the documented order") from error
    lower, upper = contract["allowed_range_per_feature"]
    if not np.isfinite(values).all() or np.any(values < lower) or np.any(values > upper):
        raise ValueError(f"Features must be finite numeric values in the inclusive range [{lower}, {upper}] {contract['units']}")
    return values.reshape(1, -1)


def validate_named_features(features: Mapping[str, Any], contract: dict[str, Any]) -> np.ndarray:
    """Validate a name-to-value payload and canonicalise it to contract order."""
    contract = _validate_contract(contract)
    names = contract["feature_names"]
    if not isinstance(features, Mapping):
        raise ValueError("Named features must be an object keyed by the documented feature names")
    provided = set(features)
    expected = set(names)
    if provided != expected:
        missing = sorted(expected - provided)
        extra = sorted(provided - expected)
        raise ValueError(f"Named features must match the contract; missing={missing}, extra={extra}")
    return validate_features([features[name] for name in names], contract)


def predict(model_path: Path, features: Sequence[float]) -> dict[str, Any]:
    bundle = load_model_bundle(model_path)
    values = validate_features(features, bundle["feature_contract"])
    return _predict_loaded_bundle(bundle, values)


def predict_named(model_path: Path, features: Mapping[str, Any]) -> dict[str, Any]:
    bundle = load_model_bundle(model_path)
    values = validate_named_features(features, bundle["feature_contract"])
    return _predict_loaded_bundle(bundle, values)


def _predict_loaded_bundle(bundle: dict[str, Any], values: np.ndarray) -> dict[str, Any]:
    model = bundle["model"]
    prediction = int(model.predict(values)[0])
    probabilities = model.predict_proba(values)[0] if hasattr(model, "predict_proba") else None
    target_names = bundle["target_names"]
    if prediction < 0 or prediction >= len(target_names):
        raise ValueError("Model returned a class outside the bundle target_names")
    return {
        "predicted_class_index": prediction,
        "predicted_class": str(target_names[prediction]),
        "probabilities": [float(value) for value in probabilities] if probabilities is not None else None,
        "features": [float(value) for value in values[0]],
        "model_name": bundle.get("model_name"),
        "model_fingerprint": bundle.get("fitted_model_fingerprint"),
        "model_configuration_fingerprint": bundle.get("model_configuration_fingerprint"),
        "fitted_model_fingerprint": bundle.get("fitted_model_fingerprint"),
        "dataset_sha256": bundle.get("dataset_sha256"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, default=Path("artifacts/model.joblib"))
    feature_group = parser.add_mutually_exclusive_group(required=True)
    feature_group.add_argument("--features", nargs=4, type=float, metavar=("SEPAL_L", "SEPAL_W", "PETAL_L", "PETAL_W"))
    feature_group.add_argument("--named-features", type=json.loads, metavar="JSON_OBJECT", help="JSON object keyed by the contract feature names")
    args = parser.parse_args()
    result = predict(args.model_path, args.features) if args.features is not None else predict_named(args.model_path, args.named_features)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
