"""Small, reproducible CRISP-DM walkthrough for Iris classification.

This is intentionally a bounded teaching implementation: one supervised
classification task is carried through all six CRISP-DM phases. It does not
claim to implement the broader curriculum topics (clustering, anomaly
detection, association rules, or LSH).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import sklearn
from sklearn.datasets import load_iris
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


RANDOM_STATE = 42
CV_SPLITS = 5
CV_REPEATS = 3
INPUT_MIN = 0.0
INPUT_MAX = 10.0
FEATURE_UNITS = "cm"


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "tolist"):
        return value.tolist()
    raise TypeError(f"Cannot serialize {type(value)!r}")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def business_understanding() -> dict[str, Any]:
    return {
        "scope": "Bounded Iris supervised-classification walkthrough",
        "objective": "Classify an Iris flower from four measured attributes.",
        "decision": "A student analyst uses the predicted species to demonstrate an auditable classification workflow; no production or clinical decision is implied.",
        "success_criteria": "Beat the majority-class baseline in training-only repeated stratified CV, then report the fixed holdout result with uncertainty and class-level support.",
        "stakeholders": ["student analyst", "course reviewer"],
        "operational_constraints": [
            "Four numeric measurements in centimeters",
            "Local, deterministic execution with no network dependency",
            "Reject malformed or out-of-domain inputs before inference",
        ],
        "error_costs": "All class errors are treated as educationally important; no real-world cost matrix has been validated.",
        "assumptions": [
            "The bundled Iris sample is representative only of this classroom exercise.",
            "The fixed holdout is selected before model fitting and is used once for final reporting.",
        ],
    }


def feature_contract(feature_names: Iterable[str]) -> dict[str, Any]:
    return {
        "feature_names": [str(name) for name in feature_names],
        "units": FEATURE_UNITS,
        "dtype": "finite real number",
        "required_count": 4,
        "allowed_range_per_feature": [INPUT_MIN, INPUT_MAX],
        "invalid_input_policy": "Reject with ValueError; do not impute or reorder caller-provided values.",
    }


def validate_dataset(data) -> dict[str, Any]:
    features = np.asarray(data.data)
    targets = np.asarray(data.target)
    expected_features = tuple(str(name) for name in data.feature_names)
    expected_classes = np.arange(len(data.target_names))
    if features.ndim != 2 or features.shape[1] != len(expected_features):
        raise ValueError("Iris data must be a 2-D matrix with the documented feature count")
    if targets.ndim != 1 or len(targets) != len(features):
        raise ValueError("Iris targets must be a one-dimensional vector aligned to rows")
    if not np.isfinite(features).all():
        raise ValueError("Iris features must contain only finite values")
    if not np.isin(targets, expected_classes).all():
        raise ValueError("Iris targets contain an unknown class label")
    if len(set(expected_features)) != len(expected_features):
        raise ValueError("Feature names must be unique")

    _, counts = np.unique(features, axis=0, return_counts=True)
    return {
        "schema_valid": True,
        "finite_values": True,
        "invalid_labels": 0,
        "duplicate_feature_rows": int((counts > 1).sum()),
        "duplicate_row_instances": int((counts[counts > 1] - 1).sum()),
        "feature_min": [float(value) for value in features.min(axis=0)],
        "feature_max": [float(value) for value in features.max(axis=0)],
        "feature_units": FEATURE_UNITS,
        "label_values": [int(value) for value in sorted(np.unique(targets))],
    }


def dataset_fingerprint(data) -> str:
    payload = {
        "feature_names": [str(name) for name in data.feature_names],
        "target_names": [str(name) for name in data.target_names],
        "data": np.asarray(data.data, dtype="<f8").tolist(),
        "target": np.asarray(data.target, dtype="<i8").tolist(),
    }
    return _sha256_bytes(json.dumps(payload, separators=(",", ":")).encode("utf-8"))


def data_understanding(data) -> dict[str, Any]:
    quality = validate_dataset(data)
    return {
        "dataset": "sklearn.datasets.load_iris",
        "provenance": "Bundled with the installed scikit-learn package; no network download.",
        "dataset_version": sklearn.__version__,
        "license_note": "Review scikit-learn and the upstream UCI Iris terms before redistribution.",
        "content_sha256": dataset_fingerprint(data),
        "rows": int(data.data.shape[0]),
        "features": [str(x) for x in data.feature_names],
        "classes": [str(x) for x in data.target_names],
        "missing_values": int(np.isnan(data.data).sum()),
        "class_counts": {
            str(name): int((data.target == index).sum())
            for index, name in enumerate(data.target_names)
        },
        "quality_checks": quality,
    }


def split_indices(data) -> tuple[np.ndarray, np.ndarray]:
    indices = np.arange(len(data.target))
    return train_test_split(indices, test_size=0.2, random_state=RANDOM_STATE, stratify=data.target)


def prepare_data(data):
    train_indices, test_indices = split_indices(data)
    return data.data[train_indices], data.data[test_indices], data.target[train_indices], data.target[test_indices]


def build_model() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=500, random_state=RANDOM_STATE)),
    ])


def candidate_models() -> dict[str, Any]:
    return {
        "majority_class": DummyClassifier(strategy="most_frequent"),
        "logistic_regression": build_model(),
        "knn": Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", KNeighborsClassifier(n_neighbors=5)),
        ]),
        "decision_tree": DecisionTreeClassifier(max_depth=4, random_state=RANDOM_STATE),
    }


def select_model(x_train, y_train) -> tuple[str, Any, list[dict[str, Any]]]:
    cv = RepeatedStratifiedKFold(n_splits=CV_SPLITS, n_repeats=CV_REPEATS, random_state=RANDOM_STATE)
    results = []
    for name, candidate in candidate_models().items():
        scores = cross_val_score(candidate, x_train, y_train, cv=cv, scoring="accuracy")
        results.append({
            "name": name,
            "algorithm": candidate.__class__.__name__ if name != "logistic_regression" else "StandardScaler + LogisticRegression",
            "cv_scores": [float(score) for score in scores],
            "cv_accuracy_mean": float(scores.mean()),
            "cv_accuracy_std": float(scores.std()),
            "cv_accuracy_min": float(scores.min()),
            "cv_accuracy_max": float(scores.max()),
        })
    # Stable insertion order is the tie-breaker after mean CV accuracy.
    selected = max(enumerate(results), key=lambda pair: (pair[1]["cv_accuracy_mean"], -pair[0]))[1]
    return selected["name"], candidate_models()[selected["name"]], results


def wilson_interval(correct: int, total: int, z: float = 1.96) -> list[float]:
    if total <= 0:
        raise ValueError("An interval requires at least one observation")
    proportion = correct / total
    denominator = 1 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    margin = z * np.sqrt((proportion * (1 - proportion) + z**2 / (4 * total)) / total) / denominator
    return [float(max(0.0, centre - margin)), float(min(1.0, centre + margin))]


def evaluate(model, x_test, y_test, target_names, baseline=None) -> dict[str, Any]:
    predictions = model.predict(x_test)
    report = classification_report(y_test, predictions, target_names=target_names, output_dict=True, zero_division=0)
    correct = int(np.sum(predictions == y_test))
    result = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "correct": correct,
        "total": int(len(y_test)),
        "accuracy_95_wilson_interval": wilson_interval(correct, len(y_test)),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        "classification_report": report,
        "failure_cases": [
            {"row_number_in_holdout": int(index), "actual_class": str(target_names[actual]), "predicted_class": str(target_names[predicted])}
            for index, (actual, predicted) in enumerate(zip(y_test, predictions)) if actual != predicted
        ],
    }
    if baseline is not None:
        baseline_predictions = baseline.predict(x_test)
        baseline_accuracy = accuracy_score(y_test, baseline_predictions)
        result["majority_baseline"] = {
            "accuracy": float(baseline_accuracy),
            "correct": int(np.sum(baseline_predictions == y_test)),
            "accuracy_delta": float(result["accuracy"] - baseline_accuracy),
        }
    return result


def write_csv(path: Path, data) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([*data.feature_names, "target", "target_name"])
        for row, target in zip(data.data, data.target):
            writer.writerow([*map(float, row), int(target), data.target_names[target]])


def runtime_metadata() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
    }


def run(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = load_iris()
    data_report = data_understanding(data)
    train_indices, test_indices = split_indices(data)
    x_train, x_test = data.data[train_indices], data.data[test_indices]
    y_train, y_test = data.target[train_indices], data.target[test_indices]

    selected_name, model, selection_results = select_model(x_train, y_train)
    baseline = candidate_models()["majority_class"]
    baseline.fit(x_train, y_train)
    model.fit(x_train, y_train)
    evaluation = evaluate(model, x_test, y_test, data.target_names, baseline=baseline)

    snapshot_path = output_dir / "iris_snapshot.csv"
    model_path = output_dir / "model.joblib"
    write_csv(snapshot_path, data)
    # Nested estimators are not JSON-native; their stable repr records the
    # fitted model configuration without serializing learned coefficients.
    model_fingerprint = _sha256_bytes(json.dumps(model.get_params(deep=True), default=repr, sort_keys=True).encode("utf-8"))
    cv_means = {result["name"]: result["cv_accuracy_mean"] for result in selection_results}
    model_bundle = {
        "bundle_schema_version": "1.0",
        "model": model,
        "model_name": selected_name,
        "model_fingerprint": model_fingerprint,
        "feature_contract": feature_contract(data.feature_names),
        "target_names": [str(name) for name in data.target_names],
        "dataset_sha256": data_report["content_sha256"],
        "random_state": RANDOM_STATE,
    }
    joblib.dump(model_bundle, model_path)

    report = {
        "report_schema_version": "2.0",
        "runtime": runtime_metadata(),
        "random_state": RANDOM_STATE,
        "business_understanding": business_understanding(),
        "data_understanding": data_report,
        "data_preparation": {
            "train_rows": int(len(x_train)),
            "test_rows": int(len(x_test)),
            "split": "Fixed 80/20 stratified holdout; selected before fitting and used once for final evaluation.",
            "train_test_overlap_rows": int(len(set(train_indices).intersection(set(test_indices)))),
            "preprocessing": "StandardScaler is fit inside each candidate pipeline on each training fold only.",
            "input_contract": feature_contract(data.feature_names),
        },
        "modeling": {
            "selection_protocol": f"{CV_REPEATS} repeats of {CV_SPLITS}-fold stratified CV on training rows only",
            "selection_metric": "accuracy",
            "tie_breaking": "Candidate declaration order after mean CV accuracy",
            "candidates": selection_results,
            "selected_model": selected_name,
            "algorithm": "StandardScaler + multinomial LogisticRegression" if selected_name == "logistic_regression" else selected_name,
            "model_fingerprint": model_fingerprint,
            "baseline_cv_accuracy": cv_means["majority_class"],
            "selected_cv_accuracy": cv_means[selected_name],
            "beats_baseline_in_cv": bool(cv_means[selected_name] > cv_means["majority_class"]),
        },
        "evaluation": evaluation,
        "deployment": {
            "status": "Local inference artifact produced; not production approved.",
            "model_artifact": model_path.name,
            "inference_command": "python3 src/inference.py --model-path artifacts/model.joblib --features 5.1 3.5 1.4 0.2",
            "input_contract": feature_contract(data.feature_names),
            "monitoring_plan": [
                {"signal": "input validation failures", "window": "daily", "action": "inspect caller/schema changes before accepting traffic"},
                {"signal": "feature range and class distribution drift", "window": "weekly", "action": "compare with the checked-in training snapshot"},
                {"signal": "accuracy on reviewed labels", "window": "monthly or every 100 reviewed rows", "action": "retrain and re-run the locked evaluation if it falls below the CV-informed expectation"},
            ],
            "rollback": "Keep the previous model bundle and restore it if a reviewed evaluation or contract check fails.",
            "claim_boundary": "This artifact supports local, schema-validated inference on Iris-like measurements only; it does not establish external or production performance.",
        },
        "artifacts": {
            "iris_snapshot.csv": {"sha256": _sha256_file(snapshot_path)},
            "model.joblib": {"sha256": _sha256_file(model_path)},
        },
    }
    (output_dir / "crispdm_report.json").write_text(json.dumps(report, indent=2, default=_json_default) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    report = run(args.output_dir)
    print(f"Iris CRISP-DM run complete: holdout accuracy={report['evaluation']['accuracy']:.3f}")
    print(f"Selected model: {report['modeling']['selected_model']}")
    print(f"Artifacts written to {args.output_dir}")


if __name__ == "__main__":
    main()
