"""Small, reproducible CRISP-DM demonstration using sklearn's Iris dataset.

The script keeps each CRISP-DM phase explicit and writes inspectable JSON/CSV
artifacts so it can be run as a classroom example without notebooks.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.datasets import load_iris
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


RANDOM_STATE = 42


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "tolist"):
        return value.tolist()
    raise TypeError(f"Cannot serialize {type(value)!r}")


def business_understanding() -> dict[str, Any]:
    return {
        "objective": "Classify Iris flowers from four measured attributes.",
        "success_criteria": "Holdout accuracy >= 0.90 and a documented evaluation.",
        "stakeholders": ["student analyst", "course reviewer"],
        "assumptions": ["The labeled sample is representative of the intended use."],
    }


def data_understanding(data) -> dict[str, Any]:
    return {
        "dataset": "sklearn.datasets.load_iris",
        "rows": int(data.data.shape[0]),
        "features": [str(x) for x in data.feature_names],
        "classes": [str(x) for x in data.target_names],
        "missing_values": int(np.isnan(data.data).sum()),
        "class_counts": {
            str(name): int((data.target == index).sum())
            for index, name in enumerate(data.target_names)
        },
    }


def prepare_data(data):
    return train_test_split(
        data.data, data.target, test_size=0.2, random_state=RANDOM_STATE, stratify=data.target
    )


def build_model() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=500, random_state=RANDOM_STATE)),
    ])


def evaluate(model, x_test, y_test, target_names) -> dict[str, Any]:
    predictions = model.predict(x_test)
    return {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
        "classification_report": classification_report(
            y_test, predictions, target_names=target_names, output_dict=True
        ),
    }


def write_csv(path: Path, data) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([*data.feature_names, "target", "target_name"])
        for row, target in zip(data.data, data.target):
            writer.writerow([*map(float, row), int(target), data.target_names[target]])


def run(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = load_iris()
    x_train, x_test, y_train, y_test = prepare_data(data)
    model = build_model()
    model.fit(x_train, y_train)
    evaluation = evaluate(model, x_test, y_test, data.target_names)
    report = {
        "business_understanding": business_understanding(),
        "data_understanding": data_understanding(data),
        "data_preparation": {
            "train_rows": int(len(x_train)),
            "test_rows": int(len(x_test)),
            "split": "80/20 stratified holdout",
            "preprocessing": "StandardScaler fit inside a pipeline on training data only",
        },
        "modeling": {"algorithm": "StandardScaler + multinomial LogisticRegression"},
        "evaluation": evaluation,
        "deployment": {
            "next_step": "Package the fitted pipeline behind a prediction API after external validation.",
            "monitoring": ["input ranges", "class distribution", "accuracy on reviewed labels"],
        },
    }
    (output_dir / "crispdm_report.json").write_text(
        json.dumps(report, indent=2, default=_json_default) + "\n", encoding="utf-8"
    )
    write_csv(output_dir / "iris_snapshot.csv", data)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    report = run(args.output_dir)
    print(f"Iris CRISP-DM run complete: accuracy={report['evaluation']['accuracy']:.3f}")
    print(f"Artifacts written to {args.output_dir}")


if __name__ == "__main__":
    main()
