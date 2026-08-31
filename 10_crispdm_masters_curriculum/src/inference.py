"""Schema-validated inference for the local CRISP-DM model bundle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import joblib
import numpy as np


def load_model_bundle(model_path: Path) -> dict[str, Any]:
    bundle = joblib.load(model_path)
    if not isinstance(bundle, dict) or "model" not in bundle or "feature_contract" not in bundle:
        raise ValueError("Model artifact is not a supported CRISP-DM model bundle")
    return bundle


def validate_features(features: Sequence[float], contract: dict[str, Any]) -> np.ndarray:
    expected = int(contract["required_count"])
    if len(features) != expected:
        raise ValueError(f"Expected exactly {expected} features: {contract['feature_names']}")
    try:
        values = np.asarray(features, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("Features must be finite numeric values in the documented order") from error
    lower, upper = contract["allowed_range_per_feature"]
    if not np.isfinite(values).all() or np.any(values < lower) or np.any(values > upper):
        raise ValueError(f"Features must be finite values in the inclusive range [{lower}, {upper}] {contract['units']}")
    return values.reshape(1, -1)


def predict(model_path: Path, features: Sequence[float]) -> dict[str, Any]:
    bundle = load_model_bundle(model_path)
    values = validate_features(features, bundle["feature_contract"])
    model = bundle["model"]
    prediction = int(model.predict(values)[0])
    probabilities = model.predict_proba(values)[0] if hasattr(model, "predict_proba") else None
    target_names = bundle.get("target_names", [str(value) for value in model.classes_])
    return {
        "predicted_class_index": prediction,
        "predicted_class": str(target_names[prediction]),
        "probabilities": [float(value) for value in probabilities] if probabilities is not None else None,
        "features": [float(value) for value in values[0]],
        "model_name": bundle.get("model_name"),
        "model_fingerprint": bundle.get("model_fingerprint"),
        "dataset_sha256": bundle.get("dataset_sha256"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, default=Path("artifacts/model.joblib"))
    parser.add_argument("--features", nargs=4, type=float, required=True, metavar=("SEPAL_L", "SEPAL_W", "PETAL_L", "PETAL_W"))
    args = parser.parse_args()
    print(json.dumps(predict(args.model_path, args.features), indent=2))


if __name__ == "__main__":
    main()
