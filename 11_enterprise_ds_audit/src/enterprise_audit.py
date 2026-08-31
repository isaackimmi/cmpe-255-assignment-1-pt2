"""Dependency-free data-science quality and governance audit.

The audit deliberately keeps the model baseline small and transparent. The
quality controls around it are stricter: CSV shape, typing, domain rules,
feature availability, and reproducibility evidence are evaluated before
model code is allowed to run.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import random
import re
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


POLICY_VERSION = "2026.08.2"
DEFAULT_AS_OF_DATE = "2025-12-31"
REQUIRED = {
    "customer_id": "str",
    "snapshot_date": "date",
    "tenure_months": "int",
    "monthly_spend": "float",
    "support_tickets_90d": "int",
    "plan": "category",
    "churned": "bool",
    "churn_confirmed_at": "date_or_null",
    "internal_note": "str_or_null",
}
ALLOWED_PLANS = {"basic", "pro", "enterprise"}
SAFE_FEATURES = ["tenure_months", "monthly_spend", "support_tickets_90d", "plan"]
MODEL_FEATURE_MANIFEST = ["support_tickets_90d"]
MODEL_PIPELINE_CONFIG = {
    "name": "ticket_threshold_decision_stump",
    "feature_manifest": MODEL_FEATURE_MANIFEST,
    "threshold_rule": "minimum positive training ticket count",
    "baseline": "majority_class",
}
PREDICTION_TIME_COLUMN = "snapshot_date"
LABEL_COLUMN = "churned"
MISSING_TOKENS = {"", "na", "n/a", "nan", "nat", "null", "none"}
NULLABLE_COLUMNS = {column for column, typ in REQUIRED.items() if typ.endswith("_or_null")}
MISSINGNESS_POLICY = {
    column: {"allow_null": column in NULLABLE_COLUMNS, "max_rate": 1.0 if column in NULLABLE_COLUMNS else 0.0}
    for column in REQUIRED
}
MIN_TRAIN_ROWS = 12
MIN_TEST_ROWS = 10
MIN_CLASS_SUPPORT = 2
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
OUTCOME_WORDS = ("outcome", "target", "label", "churn", "cancel", "confirmed", "resolved", "post")


def generate_sample(path: Path, seed: int = 255) -> None:
    rng = random.Random(seed)
    fields = list(REQUIRED)
    start = datetime(2025, 1, 1)
    rows = []
    for i in range(1, 41):
        tenure = 3 + (i * 7) % 45
        spend = round(45 + ((i * 17) % 160) + rng.random(), 2)
        tickets = (i * 3 + rng.randrange(3)) % 8
        plan = ["basic", "pro", "enterprise"][i % 3]
        churn = int(tenure < 14 and tickets >= 4 or tickets >= 7 or (i % 19 == 0))
        snap = (start + timedelta(days=i)).date().isoformat()
        rows.append(
            {
                "customer_id": f"C{i:04d}",
                "snapshot_date": snap,
                "tenure_months": tenure,
                "monthly_spend": spend,
                "support_tickets_90d": tickets,
                "plan": plan,
                "churned": churn,
                "churn_confirmed_at": (start + timedelta(days=i + 5)).date().isoformat() if churn else "",
                "internal_note": "priority account" if i == 11 else "",
            }
        )
    rows[6]["monthly_spend"] = ""  # missingness finding
    rows[10]["internal_note"] = "manual cancellation approved"  # governance-sensitive free text
    rows.append(dict(rows[0]))  # exact duplicate row finding
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _normalise_missing(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in MISSING_TOKENS:
        return None
    return value.strip() if isinstance(value, str) else value


def _read(path: Path) -> tuple[list[str], list[dict[str, str]], list[dict[str, Any]]]:
    """Read raw rows while retaining shape and parser errors for fail-closed use."""
    errors: list[dict[str, Any]] = []
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle, strict=True)
            try:
                header = next(reader)
            except StopIteration:
                return [], [], [{"row": 1, "reason": "empty_csv"}]
            if not header:
                return [], [], [{"row": 1, "reason": "empty_header"}]
            raw_rows: list[dict[str, str]] = []
            for row_number, values in enumerate(reader, 2):
                if len(values) != len(header):
                    errors.append({"row": row_number, "reason": "field_count", "expected": len(header), "observed": len(values)})
                padded = values[: len(header)] + [""] * max(0, len(header) - len(values))
                raw_rows.append(dict(zip(header, padded)))
            return header, raw_rows, errors
    except (OSError, UnicodeError, csv.Error) as exc:
        return [], [], [{"row": 1, "reason": type(exc).__name__, "message": str(exc)}]


def _parse(row: dict[str, Any], col: str, typ: str) -> Any:
    value = _normalise_missing(row.get(col))
    if value is None:
        if typ.endswith("_or_null"):
            return None
        raise ValueError("missing value")
    if typ in {"str", "str_or_null"}:
        return str(value)
    if typ in {"date", "date_or_null"}:
        datetime.strptime(str(value), "%Y-%m-%d")
        return str(value)
    if typ == "int":
        return int(str(value))
    if typ == "float":
        parsed = float(str(value))
        if not math.isfinite(parsed):
            raise ValueError("non-finite value")
        return parsed
    if typ == "bool":
        if str(value).lower() not in {"0", "1"}:
            raise ValueError("expected 0 or 1")
        return int(str(value))
    if typ == "category":
        return str(value)
    raise ValueError(f"unknown type {typ}")


def _metric(y: Iterable[int], pred: Iterable[int]) -> dict[str, Any]:
    actual = list(y)
    predicted = list(pred)
    if len(actual) != len(predicted):
        raise ValueError("metric inputs must have equal lengths")
    tp = sum(a == b == 1 for a, b in zip(actual, predicted))
    tn = sum(a == b == 0 for a, b in zip(actual, predicted))
    fp = sum(a == 0 and b == 1 for a, b in zip(actual, predicted))
    fn = sum(a == 1 and b == 0 for a, b in zip(actual, predicted))
    accuracy = (tp + tn) / len(actual) if actual else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    tpr = recall
    tnr = tn / (tn + fp) if tn + fp else 0.0
    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "balanced_accuracy": round((tpr + tnr) / 2, 4),
        "confusion_matrix": {"true_positive": tp, "true_negative": tn, "false_positive": fp, "false_negative": fn},
        "class_support": {"negative": tn + fp, "positive": tp + fn},
    }


def _check(name: str, status: str, detail: str, severity: str = "medium", evidence: dict[str, Any] | None = None, category: str = "governance") -> dict[str, Any]:
    structured = dict(evidence or {})
    structured.setdefault("control", name)
    structured.setdefault("rule", detail)
    structured.setdefault("status", status)
    structured.setdefault("severity", severity)
    return {"name": name, "category": category, "status": status, "severity": severity, "detail": detail, "evidence": structured, "rule_version": POLICY_VERSION}


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_revision(start: Path) -> str:
    try:
        completed = subprocess.run(["git", "-C", str(start.parent), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
        return completed.stdout.strip() or "unavailable"
    except OSError:
        return "unavailable"


def _repo_relative(path: Path) -> tuple[str, str]:
    try:
        completed = subprocess.run(["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=False)
        root = Path(completed.stdout.strip()) if completed.returncode == 0 else None
        if root:
            return str(path.relative_to(root)), str(root)
    except (OSError, ValueError):
        pass
    return path.name, ""


def _source_metadata(path: Path) -> dict[str, Any]:
    source_path = Path(__file__).resolve()
    runner_path = source_path.parents[1] / "run_audit.py"
    requirements = source_path.parents[1] / "requirements.txt"
    lock_hash = _sha256_bytes(requirements.read_bytes()) if requirements.exists() else "none"
    relative_path, repo_root = _repo_relative(path.resolve())
    return {
        "dataset_uri": relative_path,
        "source_sha256": _sha256_bytes(source_path.read_bytes()),
        "runner_sha256": _sha256_bytes(runner_path.read_bytes()) if runner_path.exists() else "none",
        "dependency_lock_sha256": lock_hash,
        "repository_revision": _git_revision(source_path),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repo_root": repo_root,
    }


def _parse_typed_rows(header: list[str], rows: list[dict[str, str]], shape_errors: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors = list(shape_errors)
    typed: list[dict[str, Any]] = []
    expected = set(REQUIRED)
    for row_number, raw in enumerate(rows, 2):
        if set(raw) != expected:
            errors.append({"row": row_number, "reason": "row_keys", "unexpected": sorted(set(raw) - expected), "missing": sorted(expected - set(raw))})
        parsed: dict[str, Any] = {"_row_number": row_number}
        row_errors: list[str] = []
        for column, typ in REQUIRED.items():
            try:
                parsed[column] = _parse(raw, column, typ)
            except (ValueError, TypeError, OverflowError) as exc:
                row_errors.append(f"{column}: {str(exc)}")
        if row_errors:
            errors.append({"row": row_number, "reason": "parse", "fields": row_errors})
        else:
            typed.append(parsed)
    return typed, errors


def _missingness(rows: list[dict[str, str]], header: list[str]) -> tuple[dict[str, float], dict[str, int], dict[str, Any]]:
    denominator = len(rows)
    counts = {column: sum(_normalise_missing(row.get(column)) is None for row in rows) for column in header}
    rates = {column: round(count / denominator, 4) if denominator else 0.0 for column, count in counts.items()}
    violations = {
        column: {"count": counts[column], "rate": rates[column], **MISSINGNESS_POLICY.get(column, {"allow_null": False, "max_rate": 0.0})}
        for column in header
        if column in MISSINGNESS_POLICY and rates[column] > MISSINGNESS_POLICY[column]["max_rate"]
    }
    return rates, counts, violations


def _duplicate_evidence(rows: list[dict[str, str]]) -> dict[str, Any]:
    key_columns = ("customer_id", "snapshot_date")
    key_groups: dict[tuple[Any, ...], list[tuple[int, dict[str, str]]]] = {}
    for row_number, row in enumerate(rows, 2):
        key = tuple(_normalise_missing(row.get(column)) for column in key_columns)
        key_groups.setdefault(key, []).append((row_number, row))
    exact_counts = Counter(_json({column: _normalise_missing(row.get(column)) for column in REQUIRED}) for row in rows)
    duplicate_keys = [list(key) for key, group in key_groups.items() if None not in key and len(group) > 1]
    exact_values = [json.loads(value) for value, count in exact_counts.items() if count > 1]
    exact_rows = sum(count - 1 for count in exact_counts.values() if count > 1)
    exact_key_values = []
    conflicting_duplicate_keys = []
    for key, group in key_groups.items():
        if None in key or len(group) < 2:
            continue
        payloads = {_json({column: _normalise_missing(row.get(column)) for column in REQUIRED}) for _, row in group}
        sample = [{"row": row_number, "values": {column: _normalise_missing(row.get(column)) for column in REQUIRED}} for row_number, row in group[:5]]
        if len(payloads) == 1:
            exact_key_values.append(list(key))
        else:
            conflicting_duplicate_keys.append({"key": list(key), "rows": [row_number for row_number, _ in group], "samples": sample})
    customer_dates: dict[Any, set[Any]] = {}
    for row in rows:
        customer_id = _normalise_missing(row.get("customer_id"))
        if customer_id is not None:
            customer_dates.setdefault(customer_id, set()).add(_normalise_missing(row.get("snapshot_date")))
    multi_snapshot_ids = [customer_id for customer_id, dates in customer_dates.items() if len(dates) > 1]
    conflicting_rows = sum(len(item["rows"]) for item in conflicting_duplicate_keys)
    return {
        "grain": "customer_snapshot",
        "duplicate_key": list(key_columns),
        "duplicate_key_values": duplicate_keys,
        "exact_duplicate_key_values": exact_key_values,
        "conflicting_duplicate_keys": conflicting_duplicate_keys,
        "conflicting_duplicate_key_count": len(conflicting_duplicate_keys),
        "conflicting_duplicate_rows": conflicting_rows,
        "exact_duplicate_rows": exact_rows,
        "exact_duplicate_samples": exact_values[:5],
        "valid_multi_snapshot_customer_ids": multi_snapshot_ids[:20],
        "excluded_row_count": exact_rows + conflicting_rows,
        "duplicate_gate": "FAIL and block model evaluation when a customer_id/snapshot_date key has conflicting payloads; exact duplicates are deterministically excluded",
    }


def _domain_evidence(rows: list[dict[str, str]], as_of_date: str = DEFAULT_AS_OF_DATE) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    audit_date = date.fromisoformat(as_of_date)
    for row_number, raw in enumerate(rows, 2):
        customer_id = _normalise_missing(raw.get("customer_id"))
        if customer_id is None or not ID_PATTERN.fullmatch(str(customer_id)):
            violations.append({"row": row_number, "column": "customer_id", "value": customer_id, "rule": "non-empty safe identifier format"})

        parsed_values: dict[str, Any] = {}
        for column in ("tenure_months", "monthly_spend", "support_tickets_90d"):
            try:
                parsed_values[column] = _parse(raw, column, REQUIRED[column])
                if parsed_values[column] < 0:
                    violations.append({"row": row_number, "column": column, "value": parsed_values[column], "rule": "non-negative"})
            except (ValueError, TypeError, OverflowError):
                pass
        plan = _normalise_missing(raw.get("plan"))
        if plan is not None and plan not in ALLOWED_PLANS:
            violations.append({"row": row_number, "column": "plan", "value": plan, "rule": "allowed plan"})

        snapshot_value = _normalise_missing(raw.get("snapshot_date"))
        confirmation_value = _normalise_missing(raw.get("churn_confirmed_at"))
        label_value = _normalise_missing(raw.get("churned"))
        try:
            snapshot = date.fromisoformat(str(snapshot_value))
        except (TypeError, ValueError):
            snapshot = None
        if snapshot and snapshot > audit_date:
            violations.append({"row": row_number, "column": "snapshot_date", "value": snapshot_value, "rule": "not in the future"})
        try:
            confirmed = date.fromisoformat(str(confirmation_value)) if confirmation_value is not None else None
        except (TypeError, ValueError):
            confirmed = None
        if confirmed:
            if snapshot and confirmed < snapshot:
                violations.append({"row": row_number, "column": "churn_confirmed_at", "value": confirmation_value, "rule": "on or after snapshot_date"})
            if confirmed > audit_date:
                violations.append({"row": row_number, "column": "churn_confirmed_at", "value": confirmation_value, "rule": "not in the future"})
            if str(label_value) == "0":
                violations.append({"row": row_number, "column": "churn_confirmed_at", "value": confirmation_value, "rule": "null when churned is false"})
        elif str(label_value) == "1" and confirmation_value is None:
            violations.append({"row": row_number, "column": "churn_confirmed_at", "value": None, "rule": "present when churned is true"})
    return {"violation_count": len(violations), "violations": violations[:20], "rows_checked": len(rows), "as_of_date": as_of_date}


def _is_identifier_like(column: str) -> bool:
    lowered = column.lower()
    return lowered == "customer_id" or lowered.endswith("_id") or lowered in {"id", "uuid", "identifier"}


def _is_outcome_like(column: str) -> bool:
    lowered = column.lower()
    return any(word in lowered for word in OUTCOME_WORDS)


def _leakage_check(header: list[str], typed: list[dict[str, Any]], prediction_time_column: str | None, label_column: str | None, feature_manifest: list[str]) -> tuple[str, dict[str, Any]]:
    invalid_contract: list[dict[str, Any]] = []
    if not prediction_time_column or prediction_time_column not in header:
        invalid_contract.append({"field": prediction_time_column, "reason": "prediction time column missing"})
    if not label_column or label_column not in header:
        invalid_contract.append({"field": label_column, "reason": "label column missing"})
    if not feature_manifest:
        invalid_contract.append({"field": "feature_manifest", "reason": "must not be empty"})
    if len(set(feature_manifest)) != len(feature_manifest):
        invalid_contract.append({"field": "feature_manifest", "reason": "duplicate feature names"})
    for feature in feature_manifest:
        if feature not in header:
            invalid_contract.append({"field": feature, "reason": "feature missing from input"})
    offending: list[dict[str, Any]] = []
    for feature in feature_manifest:
        if feature in header and feature not in SAFE_FEATURES:
            offending.append({"column": feature, "reason": "not in SAFE_FEATURES allowlist", "affected_row_count": len(typed)})
    if label_column in feature_manifest:
        offending.append({"column": label_column, "reason": "label included as feature", "affected_row_count": len(typed)})
    if prediction_time_column in feature_manifest:
        offending.append({"column": prediction_time_column, "reason": "prediction timestamp included as feature", "affected_row_count": len(typed)})
    for feature in feature_manifest:
        if _is_identifier_like(feature):
            offending.append({"column": feature, "reason": "identifier-like feature", "affected_row_count": len(typed)})
        elif _is_outcome_like(feature):
            offending.append({"column": feature, "reason": "target-like or post-outcome feature", "affected_row_count": len(typed)})
    if "churn_confirmed_at" in feature_manifest and prediction_time_column == "snapshot_date":
        post_time_rows = [{"row": row["_row_number"], "value": row["churn_confirmed_at"], "prediction_time": row["snapshot_date"]} for row in typed if row.get("churn_confirmed_at") and row["churn_confirmed_at"] > row["snapshot_date"]]
        if post_time_rows:
            offending.append({"column": "churn_confirmed_at", "reason": "populated after prediction timestamp", "affected_row_count": len(post_time_rows), "samples": post_time_rows[:5]})
    evidence = {
        "prediction_time_column": prediction_time_column,
        "label_column": label_column,
        "feature_manifest": feature_manifest,
        "safe_feature_allowlist": SAFE_FEATURES,
        "invalid_contract": invalid_contract,
        "offending_features": offending,
        "excluded_suspicious_columns": [column for column in header if column not in feature_manifest and (_is_identifier_like(column) or _is_outcome_like(column))],
    }
    if invalid_contract:
        return "INCONCLUSIVE", evidence
    if offending:
        return "FAIL", evidence
    return "PASS", evidence


def _bootstrap_interval(y: list[int], pred: list[int], seed: int, samples: int = 200) -> list[float]:
    if not y:
        return [0.0, 0.0]
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(samples):
        indices = [rng.randrange(len(y)) for _ in y]
        metric = _metric([y[index] for index in indices], [pred[index] for index in indices])
        values.append(metric["balanced_accuracy"])
    values.sort()
    return [round(values[int(samples * 0.025)], 4), round(values[int(samples * 0.975) - 1], 4)]


def _evaluate_model(typed: list[dict[str, Any]], duplicate_evidence: dict[str, Any], feature_manifest: list[str], seed: int) -> dict[str, Any]:
    model_config = {**MODEL_PIPELINE_CONFIG, "declared_feature_manifest": list(feature_manifest)}
    model_config_hash = _canonical_hash(model_config)
    if not set(MODEL_FEATURE_MANIFEST).issubset(feature_manifest):
        return {
            "status": "INCONCLUSIVE",
            "reason": "declared feature manifest does not contain the immutable baseline feature set",
            "feature_manifest": list(feature_manifest),
            "model_feature_manifest": MODEL_FEATURE_MANIFEST,
            "model_configuration": model_config,
            "model_configuration_sha256": model_config_hash,
            "excluded_rows": {"feature_contract": len(typed)},
        }
    if duplicate_evidence.get("conflicting_duplicate_keys"):
        return {
            "status": "INCONCLUSIVE",
            "reason": "conflicting duplicate keys are excluded from model evaluation",
            "feature_manifest": list(feature_manifest),
            "model_feature_manifest": MODEL_FEATURE_MANIFEST,
            "model_configuration": model_config,
            "model_configuration_sha256": model_config_hash,
            "excluded_rows": {"conflicting_duplicate_key": duplicate_evidence.get("conflicting_duplicate_rows", 0)},
            "duplicate_key_conflicts": duplicate_evidence["conflicting_duplicate_keys"],
        }
    eligible: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    excluded = {"exact_duplicate": 0}
    for row in sorted(typed, key=lambda item: (item["snapshot_date"], item["_row_number"])):
        key = tuple(row[column] for column in REQUIRED)
        if key in seen:
            excluded["exact_duplicate"] += 1
            continue
        seen.add(key)
        eligible.append(row)
    if len(eligible) < MIN_TRAIN_ROWS + MIN_TEST_ROWS:
        return {"status": "INCONCLUSIVE", "reason": "fewer than minimum eligible rows", "minimum_train_rows": MIN_TRAIN_ROWS, "minimum_test_rows": MIN_TEST_ROWS, "eligible_rows": len(eligible), "excluded_rows": excluded, "feature_manifest": list(feature_manifest), "model_feature_manifest": MODEL_FEATURE_MANIFEST, "model_configuration": model_config, "model_configuration_sha256": model_config_hash}

    windows = [("early_holdout", 0.60, 0.20), ("final_holdout", 0.70, 0.30)]
    evaluations: list[dict[str, Any]] = []
    all_row_ids: set[str] = set()
    for name, train_fraction, test_fraction in windows:
        train_end = int(len(eligible) * train_fraction)
        test_end = min(len(eligible), train_end + max(MIN_TEST_ROWS, int(len(eligible) * test_fraction)))
        train = eligible[:train_end]
        test = eligible[train_end:test_end]
        train_labels = [row["churned"] for row in train]
        test_labels = [row["churned"] for row in test]
        support = {"train": dict(Counter(str(label) for label in train_labels)), "test": dict(Counter(str(label) for label in test_labels))}
        if len(train) < MIN_TRAIN_ROWS or len(test) < MIN_TEST_ROWS or any(support[split].get(str(label), 0) < MIN_CLASS_SUPPORT for split in ("train", "test") for label in (0, 1)):
            return {"status": "INCONCLUSIVE", "reason": "minimum rows or class support not met", "minimum_train_rows": MIN_TRAIN_ROWS, "minimum_test_rows": MIN_TEST_ROWS, "minimum_class_support": MIN_CLASS_SUPPORT, "window": name, "train_rows": len(train), "test_rows": len(test), "class_support": support, "excluded_rows": excluded, "feature_manifest": list(feature_manifest), "model_feature_manifest": MODEL_FEATURE_MANIFEST, "model_configuration": model_config, "model_configuration_sha256": model_config_hash}
        positive_thresholds = [row["support_tickets_90d"] for row in train if row["churned"] == 1]
        if not positive_thresholds:
            return {"status": "INCONCLUSIVE", "reason": "training data has no positive labels", "window": name, "excluded_rows": excluded, "feature_manifest": list(feature_manifest), "model_feature_manifest": MODEL_FEATURE_MANIFEST, "model_configuration": model_config, "model_configuration_sha256": model_config_hash}
        threshold = min(positive_thresholds)
        predictions = [int(row["support_tickets_90d"] >= threshold) for row in test]
        majority_label = int(sum(train_labels) >= len(train_labels) / 2)
        baseline_predictions = [majority_label] * len(test)
        model_metric = _metric(test_labels, predictions)
        baseline_metric = _metric(test_labels, baseline_predictions)
        delta = round(model_metric["balanced_accuracy"] - baseline_metric["balanced_accuracy"], 4)
        row_ids = [f"{row['customer_id']}@{row['snapshot_date']}" for row in test]
        all_row_ids.update(row_ids)
        evaluations.append(
            {
                "name": name,
                "train_rows": len(train),
                "test_rows": len(test),
                "train_date_bounds": [train[0]["snapshot_date"], train[-1]["snapshot_date"]],
                "test_date_bounds": [test[0]["snapshot_date"], test[-1]["snapshot_date"]],
                "train_row_ids": [f"{row['customer_id']}@{row['snapshot_date']}" for row in train],
                "test_row_ids": row_ids,
                "ticket_threshold": threshold,
                "model": model_metric,
                "majority_baseline": baseline_metric,
                "balanced_accuracy_delta": delta,
                "balanced_accuracy_ci95": _bootstrap_interval(test_labels, predictions, seed + len(evaluations)),
                "brier_score": round(sum((actual - predicted) ** 2 for actual, predicted in zip(test_labels, predictions)) / len(test_labels), 4),
                "operating_threshold": {"feature": "support_tickets_90d", "value": threshold, "minimum_delta": 0.05},
            }
        )
    passes = all(evaluation["balanced_accuracy_delta"] >= 0.05 for evaluation in evaluations)
    primary = evaluations[-1]
    return {
        "status": "PASS" if passes else "WARN",
        "reason": "all temporal windows clear the minimum baseline lift" if passes else "one or more temporal windows do not clear the minimum baseline lift",
        "train_rows": primary["train_rows"],
        "test_rows": primary["test_rows"],
        "ticket_threshold": primary["ticket_threshold"],
        "model": primary["model"],
        "majority_baseline": primary["majority_baseline"],
        "balanced_accuracy_delta": primary["balanced_accuracy_delta"],
        "balanced_accuracy_ci95": primary["balanced_accuracy_ci95"],
        "temporal_windows": evaluations,
        "operating_threshold": primary["operating_threshold"],
        "excluded_rows": excluded,
        "evaluated_test_row_ids": sorted(all_row_ids),
        "calibration": {"status": "DIAGNOSTIC", "brier_score": primary["brier_score"], "note": "binary decision-stump probabilities; production calibration is still required"},
        "feature_manifest": list(feature_manifest),
        "model_feature_manifest": MODEL_FEATURE_MANIFEST,
        "model_configuration": model_config,
        "model_configuration_sha256": model_config_hash,
    }


def _config(prediction_time_column: str | None, label_column: str | None, feature_manifest: list[str], as_of_date: str) -> dict[str, Any]:
    return {
        "policy_version": POLICY_VERSION,
        "required": REQUIRED,
        "safe_features": SAFE_FEATURES,
        "prediction_time_column": prediction_time_column,
        "label_column": label_column,
        "feature_manifest": feature_manifest,
        "as_of_date": as_of_date,
        "missingness_policy": MISSINGNESS_POLICY,
        "grain": "customer_snapshot",
        "duplicate_key": ["customer_id", "snapshot_date"],
        "minimum_train_rows": MIN_TRAIN_ROWS,
        "minimum_test_rows": MIN_TEST_ROWS,
        "minimum_class_support": MIN_CLASS_SUPPORT,
    }


def _canonical_hash(payload: dict[str, Any]) -> str:
    return _sha256_bytes(_json(payload).encode("utf-8"))


def _canonical_payload(core: dict[str, Any], metadata: dict[str, Any], config: dict[str, Any], raw_digest: str) -> dict[str, Any]:
    return {
        "dataset_uri": metadata["dataset_uri"],
        "input_sha256": raw_digest,
        "checks": core["checks"],
        "model_quality": core["model_quality"],
        "config": config,
        "provenance": {
            "policy_version": POLICY_VERSION,
            "source_sha256": metadata["source_sha256"],
            "runner_sha256": metadata["runner_sha256"],
            "dependency_lock_sha256": metadata["dependency_lock_sha256"],
            "repository_revision": metadata["repository_revision"],
            "python": metadata["python"],
            "platform": metadata["platform"],
            "model_configuration_sha256": core["model_quality"].get("model_configuration_sha256", "unavailable"),
        },
    }


def _independent_canonical_hash(path: Path, prediction_time_column: str | None, label_column: str | None, feature_manifest: list[str], as_of_date: str, seed: int) -> str:
    """Recompute the canonical artifact in a clean Python process."""
    source_path = Path(__file__).resolve()
    script = """
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from enterprise_audit import _canonical_hash, _canonical_payload, _config, _read, _run_core, _source_metadata
path = Path(sys.argv[2])
prediction_time_column, label_column, feature_manifest, as_of_date, seed = json.loads(sys.argv[3])
header, rows, read_errors = _read(path)
core = _run_core(header, rows, read_errors, prediction_time_column, label_column, feature_manifest, as_of_date, seed)
metadata = _source_metadata(path)
config = _config(prediction_time_column, label_column, feature_manifest, as_of_date)
raw_digest = __import__('hashlib').sha256(path.read_bytes()).hexdigest() if path.exists() else 'unavailable'
print(_canonical_hash(_canonical_payload(core, metadata, config, raw_digest)))
"""
    args = [str(source_path.parent), str(path), json.dumps([prediction_time_column, label_column, feature_manifest, as_of_date, seed])]
    try:
        completed = subprocess.run([sys.executable, "-c", script, *args], capture_output=True, text=True, check=False, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    value = completed.stdout.strip().splitlines()
    return value[-1] if completed.returncode == 0 and value and re.fullmatch(r"[0-9a-f]{64}", value[-1]) else "unavailable"


def _release_decision(checks: list[dict[str, Any]], quality: dict[str, Any]) -> dict[str, Any]:
    blocking = [{"name": check["name"], "severity": check["severity"], "status": check["status"], "detail": check["detail"]} for check in checks if check["status"] == "INCONCLUSIVE" or (check["status"] == "FAIL" and check["severity"] == "high")]
    blocking_names = {item["name"] for item in blocking}
    advisory = [{"name": check["name"], "severity": check["severity"], "status": check["status"], "detail": check["detail"]} for check in checks if check["name"] not in blocking_names and check["status"] in {"FAIL", "WARN"}]
    fails = sum(check["status"] == "FAIL" for check in checks)
    inconclusive = sum(check["status"] == "INCONCLUSIVE" for check in checks)
    recommendation = "APPROVE" if not blocking and not advisory and quality.get("status") == "PASS" else "CONDITIONAL"
    decision_state = "APPROVED" if recommendation == "APPROVE" else ("BLOCKED" if blocking else "CONDITIONAL")
    if blocking:
        decision_text = "Release is blocked by: " + ", ".join(item["name"] for item in blocking) + "."
    elif advisory:
        decision_text = "Release is conditional pending review of: " + ", ".join(item["name"] for item in advisory) + "."
    else:
        decision_text = "All mandatory controls and model-quality gates passed."
    return {"blocking": blocking, "advisory": advisory, "fails": fails, "inconclusive": inconclusive, "recommendation": recommendation, "decision_state": decision_state, "text": decision_text}


def _run_core(header: list[str], rows: list[dict[str, str]], shape_errors: list[dict[str, Any]], prediction_time_column: str | None, label_column: str | None, feature_manifest: list[str], as_of_date: str, seed: int) -> dict[str, Any]:
    typed, parse_errors = _parse_typed_rows(header, rows, shape_errors)
    missing_cols = sorted(set(REQUIRED) - set(header))
    extra_cols = sorted(set(header) - set(REQUIRED))
    duplicate_headers = sorted(column for column, count in Counter(header).items() if count > 1)
    schema_evidence = {
        "rows_inspected": len(rows),
        "header": header,
        "required_columns": sorted(REQUIRED),
        "missing_columns": missing_cols,
        "extra_columns": extra_cols,
        "duplicate_headers": duplicate_headers,
        "row_errors": parse_errors[:20],
        "row_error_count": len(parse_errors),
    }
    schema_invalid = bool(missing_cols or extra_cols or duplicate_headers or parse_errors or len(set(header)) != len(header))
    checks = [_check("schema", "FAIL" if schema_invalid else "PASS", f"{len(rows)} rows; missing={missing_cols}; extra={extra_cols}; row_errors={len(parse_errors)}", "high", schema_evidence, "schema")]

    rates, counts, missing_violations = _missingness(rows, header)
    checks.append(_check("missingness", "FAIL" if missing_violations else "PASS", f"null_rates={rates}; violations={sorted(missing_violations)}", "medium" if missing_violations else "low", {"null_rates": rates, "null_counts": counts, "denominator": len(rows), "policy": MISSINGNESS_POLICY, "violations": missing_violations}, "completeness"))

    duplicate_evidence = _duplicate_evidence(rows)
    has_duplicates = bool(duplicate_evidence["duplicate_key_values"] or duplicate_evidence["exact_duplicate_rows"])
    checks.append(_check("duplicate_identifiers", "FAIL" if has_duplicates else "PASS", f"duplicate_key_values={duplicate_evidence['duplicate_key_values']}; exact_duplicate_rows={duplicate_evidence['exact_duplicate_rows']}; conflicting_keys={duplicate_evidence['conflicting_duplicate_key_count']}; excluded={duplicate_evidence['excluded_row_count']}", "high" if has_duplicates else "low", duplicate_evidence, "data_integrity"))

    domain_evidence = _domain_evidence(rows, as_of_date)
    domain_status = "INCONCLUSIVE" if schema_invalid else ("FAIL" if domain_evidence["violation_count"] else "PASS")
    checks.append(_check("domain_validity", domain_status, f"{domain_evidence['violation_count']} domain violation(s) across {domain_evidence['rows_checked']} raw rows; as_of_date={as_of_date}", "high" if domain_status != "PASS" else "low", domain_evidence, "domain") )

    leakage_status, leakage_evidence = _leakage_check(header, typed, prediction_time_column, label_column, feature_manifest)
    checks.append(_check("leakage_risk", leakage_status, f"features={feature_manifest}; offending={len(leakage_evidence['offending_features'])}; excluded_suspicious={leakage_evidence['excluded_suspicious_columns']}", "high" if leakage_status != "PASS" else "low", leakage_evidence, "governance"))

    if schema_invalid or domain_status != "PASS":
        quality = {"status": "INCONCLUSIVE", "reason": "model evaluation blocked until schema and domain validation pass", "excluded_rows": {"invalid_input": len(rows) - len(typed)}, "feature_manifest": list(feature_manifest), "model_feature_manifest": MODEL_FEATURE_MANIFEST, "model_configuration": {**MODEL_PIPELINE_CONFIG, "declared_feature_manifest": list(feature_manifest)}, "model_configuration_sha256": _canonical_hash({**MODEL_PIPELINE_CONFIG, "declared_feature_manifest": list(feature_manifest)})}
    else:
        quality = _evaluate_model(typed, duplicate_evidence, feature_manifest, seed)
    quality_status = quality.get("status", "INCONCLUSIVE")
    checks.append(_check("model_quality", quality_status, f"status={quality_status}; reason={quality.get('reason', 'evaluated')}; test_rows={quality.get('test_rows', 0)}", "high" if quality_status == "INCONCLUSIVE" else "medium", quality, "model_quality"))
    return {"checks": checks, "model_quality": quality}


def audit_dataset(path: Path, seed: int = 255, prediction_time_column: str | None = None, label_column: str | None = None, feature_manifest: list[str] | None = None, as_of_date: str = DEFAULT_AS_OF_DATE):
    """Audit a CSV using an explicit prediction-time contract and feature manifest."""
    path = Path(path)
    try:
        date.fromisoformat(as_of_date)
    except (TypeError, ValueError) as exc:
        raise ValueError("as_of_date must be an ISO date (YYYY-MM-DD)") from exc
    header, rows, read_errors = _read(path)
    manifest = list(feature_manifest or [])
    metadata = _source_metadata(path)
    config = _config(prediction_time_column, label_column, manifest, as_of_date)
    raw_digest = _sha256_bytes(path.read_bytes()) if path.exists() else "unavailable"
    first = _run_core(header, rows, read_errors, prediction_time_column, label_column, manifest, as_of_date, seed)
    canonical_hash = _canonical_hash(_canonical_payload(first, metadata, config, raw_digest))
    rerun_hash = _independent_canonical_hash(path, prediction_time_column, label_column, manifest, as_of_date, seed)
    quality = first["model_quality"]
    windows = quality.get("temporal_windows") or [{}]
    primary = windows[-1]
    split = {
        "grain": "customer_snapshot",
        "primary_window": "final_holdout",
        "train_date_bounds": primary.get("train_date_bounds", []),
        "test_date_bounds": primary.get("test_date_bounds", []),
        "train_row_ids": primary.get("train_row_ids", []),
        "test_row_ids": primary.get("test_row_ids", []),
    }
    repro = {
        "policy_version": POLICY_VERSION,
        "seed": seed,
        "input_sha256": raw_digest,
        "source_sha256": metadata["source_sha256"],
        "runner_sha256": metadata["runner_sha256"],
        "configuration_sha256": _canonical_hash(config),
        "model_configuration_sha256": quality.get("model_configuration_sha256", "unavailable"),
        "dependency_lock_sha256": metadata["dependency_lock_sha256"],
        "repository_revision": metadata["repository_revision"],
        "python": metadata["python"],
        "platform": metadata["platform"],
        "split": "time-ordered temporal holdouts",
        "split_manifest": split,
        "canonical_result_sha256": canonical_hash,
        "rerun_canonical_result_sha256": rerun_hash,
        "rerun_match": canonical_hash == rerun_hash,
    }
    repro_status = "PASS" if repro["rerun_match"] else "FAIL"
    first["checks"].append(_check("reproducibility", repro_status, f"canonical_hash={canonical_hash}; rerun_match={repro['rerun_match']}; source_hash={metadata['source_sha256'][:12]}…", "high" if repro_status == "FAIL" else "low", repro))
    checks = first["checks"]
    decision = _release_decision(checks, quality)
    summary = f"{decision['fails']} fail(s), {decision['inconclusive']} inconclusive, {len(decision['advisory'])} advisory finding(s); release recommendation: {decision['recommendation']}"
    return {
        "dataset": metadata["dataset_uri"],
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "policy_version": POLICY_VERSION,
        "config": config,
        "checks": checks,
        "reproducibility": repro,
        "model_quality": quality,
        "release_recommendation": decision["recommendation"],
        "decision_state": decision["decision_state"],
        "decision": {
            "policy_version": POLICY_VERSION,
            "blocking_findings": decision["blocking"],
            "advisory_findings": decision["advisory"],
            "warning_findings": decision["advisory"],
            "policy": {
                "blocking": ["INCONCLUSIVE", "high FAIL"],
                "conditional": ["WARN", "medium FAIL", "low FAIL", "high WARN"],
                "approved": ["all controls PASS", "model_quality PASS", "no blocking or advisory findings"],
            },
            "text": decision["text"],
        },
        "summary": summary,
    }


def write_report(result: dict[str, Any], markdown_path: Path, json_path: Path) -> None:
    json_path.write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# Enterprise Data-Science Quality and Governance Audit",
        "",
        f"**Recommendation:** `{result['release_recommendation']}`",
        f"**Summary:** {result['summary']}",
        f"**Policy:** `{result.get('policy_version', 'unknown')}`",
        "",
        "## Findings",
        "",
        "| Check | Category | Status | Severity | Detail |",
        "|---|---|---|---|---|",
    ]
    for check in result["checks"]:
        detail = str(check["detail"]).replace("|", "\\|")
        lines.append(f"| {check['name']} | {check.get('category', 'governance')} | {check['status']} | {check['severity']} | {detail} |")
    lines += ["", "## Structured evidence", ""]
    for check in result["checks"]:
        lines += [f"### `{check['name']}`", "", f"**Rule:** {check['detail']}", "", "```json", json.dumps(check.get("evidence", {}), indent=2, sort_keys=True, default=str), "```", ""]
    lines += [
        "",
        "## Decision",
        "",
        result.get("decision", {}).get("text", "No decision evidence available."),
        "",
        "The canonical reproducibility hash and independent-process rerun comparison are stored in `reports/audit_results.json`; the volatile audit timestamp is excluded from that canonical artifact.",
        "",
        "## Limitations",
        "",
        "This audit does not assess fairness, privacy, access controls, lineage, drift, label validity, or operational monitoring. The model result is a deterministic diagnostic baseline, not evidence of business readiness. Human data-owner sign-off is required.",
        "",
    ]
    markdown_path.write_text("\n".join(lines))
