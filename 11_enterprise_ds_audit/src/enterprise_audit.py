"""Dependency-free data-science quality and governance audit."""
from __future__ import annotations
import csv, hashlib, json, platform, random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

REQUIRED = {
    "customer_id": "str", "snapshot_date": "date", "tenure_months": "int",
    "monthly_spend": "float", "support_tickets_90d": "int", "plan": "category",
    "churned": "bool", "churn_confirmed_at": "date_or_null", "internal_note": "str_or_null",
}
ALLOWED_PLANS = {"basic", "pro", "enterprise"}
SAFE_FEATURES = ["tenure_months", "monthly_spend", "support_tickets_90d", "plan"]


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
        rows.append({"customer_id": f"C{i:04d}", "snapshot_date": snap,
                     "tenure_months": tenure, "monthly_spend": spend,
                     "support_tickets_90d": tickets, "plan": plan, "churned": churn,
                     "churn_confirmed_at": (start + timedelta(days=i + 5)).date().isoformat() if churn else "",
                     "internal_note": "priority account" if i == 11 else ""})
    rows[6]["monthly_spend"] = ""  # missingness finding
    rows[10]["internal_note"] = "manual cancellation approved"  # governance-sensitive free text
    rows.append(dict(rows[0]))  # duplicate identifier finding
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)


def _read(path: Path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _parse(row, col, typ):
    value = row.get(col, "")
    if typ.endswith("_or_null") and value == "": return None
    if typ == "str" or typ == "str_or_null": return value
    if typ == "date" or typ == "date_or_null": datetime.strptime(value, "%Y-%m-%d"); return value
    if typ == "int": return int(value)
    if typ == "float": return float(value)
    if typ == "bool":
        if str(value) not in {"0", "1"}: raise ValueError(value)
        return int(value)
    if typ == "category": return value
    raise ValueError(typ)


def _metric(y, pred):
    tp = sum(a == b == 1 for a, b in zip(y, pred)); tn = sum(a == b == 0 for a, b in zip(y, pred))
    fp = sum(a == 0 and b == 1 for a, b in zip(y, pred)); fn = sum(a == 1 and b == 0 for a, b in zip(y, pred))
    accuracy = (tp + tn) / len(y) if y else 0
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    tpr = recall; tnr = tn / (tn + fp) if tn + fp else 0
    return {"accuracy": round(accuracy, 4), "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4), "balanced_accuracy": round((tpr + tnr) / 2, 4)}


def _check(name, status, detail, severity="medium"):
    return {"name": name, "status": status, "severity": severity, "detail": detail}


def audit_dataset(path: Path, seed: int = 255):
    rows = _read(path); actual_fields = list(rows[0]) if rows else []
    checks = []
    missing_cols = sorted(set(REQUIRED) - set(actual_fields)); extra_cols = sorted(set(actual_fields) - set(REQUIRED))
    parse_errors = []
    for n, row in enumerate(rows, 2):
        for col, typ in REQUIRED.items():
            if col not in row: continue
            try: _parse(row, col, typ)
            except (ValueError, TypeError): parse_errors.append(f"row {n} {col}")
    schema_ok = not missing_cols and not parse_errors and not extra_cols and all(r.get("plan") in ALLOWED_PLANS for r in rows)
    checks.append(_check("schema", "PASS" if schema_ok else "FAIL", f"{len(rows)} rows; missing={missing_cols}; extra={extra_cols}; parse_errors={parse_errors[:5]}", "high"))
    dupes = [k for k, v in Counter(r.get("customer_id") for r in rows).items() if v > 1]
    rates = {c: round(sum(r.get(c, "") == "" for r in rows) / len(rows), 4) for c in actual_fields} if rows else {}
    bad_missing = {c: v for c, v in rates.items() if v > 0.05}
    checks.append(_check("missingness", "FAIL" if bad_missing else "PASS", f"null_rates={rates}; threshold=0.05", "medium" if bad_missing else "low"))
    checks.append(_check("duplicate_identifiers", "FAIL" if dupes else "PASS", f"duplicate_customer_ids={dupes}", "high" if dupes else "low"))
    leakage = ["churn_confirmed_at is populated from the outcome window and must not be available at prediction time", "internal_note may contain outcome/cancellation language and requires review"]
    checks.append(_check("leakage_risk", "FAIL", "; ".join(leakage), "high"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    repro = {"seed": seed, "input_sha256": digest, "python": platform.python_version(), "split": "first 70% train / final 30% holdout by snapshot_date"}
    checks.append(_check("reproducibility", "PASS", json.dumps(repro, sort_keys=True), "low"))
    clean = [r for r in rows if r.get("monthly_spend") != "" and r.get("customer_id") not in dupes]
    clean.sort(key=lambda r: r["snapshot_date"])
    cut = max(1, int(len(clean) * 0.7)); train, test = clean[:cut], clean[cut:]
    y_train = [int(r["churned"]) for r in train]; y_test = [int(r["churned"]) for r in test]
    # Deterministic, transparent baseline: learn a single ticket threshold on train.
    threshold = min((int(r["support_tickets_90d"]) for r in train if int(r["churned"])), default=99)
    pred = [int(int(r["support_tickets_90d"]) >= threshold) for r in test]
    majority = [1 if sum(y_train) >= len(y_train) / 2 else 0] * len(y_test)
    model = _metric(y_test, pred); base = _metric(y_test, majority)
    quality_ok = model["balanced_accuracy"] >= base["balanced_accuracy"] + 0.05
    quality = {"train_rows": len(train), "test_rows": len(test), "ticket_threshold": threshold, "model": model, "majority_baseline": base}
    checks.append(_check("model_quality", "PASS" if quality_ok else "WARN", json.dumps(quality, sort_keys=True), "medium"))
    fails = sum(c["status"] == "FAIL" for c in checks); warns = sum(c["status"] == "WARN" for c in checks)
    recommendation = "CONDITIONAL" if fails else "APPROVE"
    summary = f"{fails} fail(s), {warns} warning(s); release recommendation: {recommendation}"
    return {"dataset": str(path), "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "checks": checks, "reproducibility": repro, "model_quality": quality, "release_recommendation": recommendation, "summary": summary}


def write_report(result, markdown_path: Path, json_path: Path):
    json_path.write_text(json.dumps(result, indent=2) + "\n")
    lines = ["# Enterprise Data-Science Quality and Governance Audit", "", f"**Recommendation:** `{result['release_recommendation']}`  ", f"**Summary:** {result['summary']}", "", "## Findings", "", "| Check | Status | Severity | Detail |", "|---|---|---|---|"]
    for c in result["checks"]:
        lines.append(f"| {c['name']} | {c['status']} | {c['severity']} | {c['detail'].replace('|', '\\|')} |")
    lines += ["", "## Decision", "", "Do not approve for production scoring until the high-severity schema/identifier and leakage findings are remediated. The model-quality result is only a baseline on synthetic data and does not establish business readiness.", "", "## Limitations", "", "This audit does not assess fairness, privacy, access controls, lineage, drift, calibration, label validity, or operational monitoring. Human data-owner sign-off is required.", ""]
    markdown_path.write_text("\n".join(lines))
