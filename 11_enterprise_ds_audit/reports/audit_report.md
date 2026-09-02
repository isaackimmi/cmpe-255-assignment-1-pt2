# Enterprise Data-Science Quality and Governance Audit

**Recommendation:** `CONDITIONAL`
**Summary:** 3 fail(s), 2 inconclusive, 1 advisory finding(s); release recommendation: CONDITIONAL
**Policy:** `2026.08.2`

## Findings

| Check | Category | Status | Severity | Detail |
|---|---|---|---|---|
| schema | schema | FAIL | high | 41 rows; missing=[]; extra=[]; row_errors=1 |
| missingness | completeness | FAIL | medium | null_rates={'customer_id': 0.0, 'snapshot_date': 0.0, 'tenure_months': 0.0, 'monthly_spend': 0.0244, 'support_tickets_90d': 0.0, 'plan': 0.0, 'churned': 0.0, 'churn_confirmed_at': 0.7561, 'internal_note': 0.9756}; violations=['monthly_spend'] |
| duplicate_identifiers | data_integrity | FAIL | high | duplicate_key_values=[['C0001', '2025-01-02']]; exact_duplicate_rows=1; conflicting_keys=0; excluded=1 |
| domain_validity | domain | INCONCLUSIVE | high | 0 domain violation(s) across 41 raw rows; as_of_date=2025-12-31 |
| leakage_risk | governance | PASS | low | features=['tenure_months', 'monthly_spend', 'support_tickets_90d', 'plan']; offending=0; excluded_suspicious=['customer_id', 'churned', 'churn_confirmed_at'] |
| model_quality | model_quality | INCONCLUSIVE | high | status=INCONCLUSIVE; reason=model evaluation blocked until schema and domain validation pass; test_rows=0 |
| reproducibility | governance | PASS | low | canonical_hash=723c75df5915fabd92d0de1fdd7257a5fb91f449ea1071dff4f95bf57ffda4af; rerun_match=True; source_hash=a2cf5ace8a8b… |

## Structured evidence

### `schema`

**Rule:** 41 rows; missing=[]; extra=[]; row_errors=1

```json
{
  "control": "schema",
  "duplicate_headers": [],
  "extra_columns": [],
  "header": [
    "customer_id",
    "snapshot_date",
    "tenure_months",
    "monthly_spend",
    "support_tickets_90d",
    "plan",
    "churned",
    "churn_confirmed_at",
    "internal_note"
  ],
  "missing_columns": [],
  "required_columns": [
    "churn_confirmed_at",
    "churned",
    "customer_id",
    "internal_note",
    "monthly_spend",
    "plan",
    "snapshot_date",
    "support_tickets_90d",
    "tenure_months"
  ],
  "row_error_count": 1,
  "row_errors": [
    {
      "fields": [
        "monthly_spend: missing value"
      ],
      "reason": "parse",
      "row": 8
    }
  ],
  "rows_inspected": 41,
  "rule": "41 rows; missing=[]; extra=[]; row_errors=1",
  "severity": "high",
  "status": "FAIL"
}
```

### `missingness`

**Rule:** null_rates={'customer_id': 0.0, 'snapshot_date': 0.0, 'tenure_months': 0.0, 'monthly_spend': 0.0244, 'support_tickets_90d': 0.0, 'plan': 0.0, 'churned': 0.0, 'churn_confirmed_at': 0.7561, 'internal_note': 0.9756}; violations=['monthly_spend']

```json
{
  "control": "missingness",
  "denominator": 41,
  "null_counts": {
    "churn_confirmed_at": 31,
    "churned": 0,
    "customer_id": 0,
    "internal_note": 40,
    "monthly_spend": 1,
    "plan": 0,
    "snapshot_date": 0,
    "support_tickets_90d": 0,
    "tenure_months": 0
  },
  "null_rates": {
    "churn_confirmed_at": 0.7561,
    "churned": 0.0,
    "customer_id": 0.0,
    "internal_note": 0.9756,
    "monthly_spend": 0.0244,
    "plan": 0.0,
    "snapshot_date": 0.0,
    "support_tickets_90d": 0.0,
    "tenure_months": 0.0
  },
  "policy": {
    "churn_confirmed_at": {
      "allow_null": true,
      "max_rate": 1.0
    },
    "churned": {
      "allow_null": false,
      "max_rate": 0.0
    },
    "customer_id": {
      "allow_null": false,
      "max_rate": 0.0
    },
    "internal_note": {
      "allow_null": true,
      "max_rate": 1.0
    },
    "monthly_spend": {
      "allow_null": false,
      "max_rate": 0.0
    },
    "plan": {
      "allow_null": false,
      "max_rate": 0.0
    },
    "snapshot_date": {
      "allow_null": false,
      "max_rate": 0.0
    },
    "support_tickets_90d": {
      "allow_null": false,
      "max_rate": 0.0
    },
    "tenure_months": {
      "allow_null": false,
      "max_rate": 0.0
    }
  },
  "rule": "null_rates={'customer_id': 0.0, 'snapshot_date': 0.0, 'tenure_months': 0.0, 'monthly_spend': 0.0244, 'support_tickets_90d': 0.0, 'plan': 0.0, 'churned': 0.0, 'churn_confirmed_at': 0.7561, 'internal_note': 0.9756}; violations=['monthly_spend']",
  "severity": "medium",
  "status": "FAIL",
  "violations": {
    "monthly_spend": {
      "allow_null": false,
      "count": 1,
      "max_rate": 0.0,
      "rate": 0.0244
    }
  }
}
```

### `duplicate_identifiers`

**Rule:** duplicate_key_values=[['C0001', '2025-01-02']]; exact_duplicate_rows=1; conflicting_keys=0; excluded=1

```json
{
  "conflicting_duplicate_key_count": 0,
  "conflicting_duplicate_keys": [],
  "conflicting_duplicate_rows": 0,
  "control": "duplicate_identifiers",
  "duplicate_gate": "FAIL and block model evaluation when a customer_id/snapshot_date key has conflicting payloads; exact duplicates are deterministically excluded",
  "duplicate_key": [
    "customer_id",
    "snapshot_date"
  ],
  "duplicate_key_values": [
    [
      "C0001",
      "2025-01-02"
    ]
  ],
  "exact_duplicate_key_values": [
    [
      "C0001",
      "2025-01-02"
    ]
  ],
  "exact_duplicate_rows": 1,
  "exact_duplicate_samples": [
    {
      "churn_confirmed_at": "2025-01-07",
      "churned": "1",
      "customer_id": "C0001",
      "internal_note": null,
      "monthly_spend": "62.06",
      "plan": "pro",
      "snapshot_date": "2025-01-02",
      "support_tickets_90d": "5",
      "tenure_months": "10"
    }
  ],
  "excluded_row_count": 1,
  "grain": "customer_snapshot",
  "rule": "duplicate_key_values=[['C0001', '2025-01-02']]; exact_duplicate_rows=1; conflicting_keys=0; excluded=1",
  "severity": "high",
  "status": "FAIL",
  "valid_multi_snapshot_customer_ids": []
}
```

### `domain_validity`

**Rule:** 0 domain violation(s) across 41 raw rows; as_of_date=2025-12-31

```json
{
  "as_of_date": "2025-12-31",
  "control": "domain_validity",
  "rows_checked": 41,
  "rule": "0 domain violation(s) across 41 raw rows; as_of_date=2025-12-31",
  "severity": "high",
  "status": "INCONCLUSIVE",
  "violation_count": 0,
  "violations": []
}
```

### `leakage_risk`

**Rule:** features=['tenure_months', 'monthly_spend', 'support_tickets_90d', 'plan']; offending=0; excluded_suspicious=['customer_id', 'churned', 'churn_confirmed_at']

```json
{
  "control": "leakage_risk",
  "excluded_suspicious_columns": [
    "customer_id",
    "churned",
    "churn_confirmed_at"
  ],
  "feature_manifest": [
    "tenure_months",
    "monthly_spend",
    "support_tickets_90d",
    "plan"
  ],
  "invalid_contract": [],
  "label_column": "churned",
  "offending_features": [],
  "prediction_time_column": "snapshot_date",
  "rule": "features=['tenure_months', 'monthly_spend', 'support_tickets_90d', 'plan']; offending=0; excluded_suspicious=['customer_id', 'churned', 'churn_confirmed_at']",
  "safe_feature_allowlist": [
    "tenure_months",
    "monthly_spend",
    "support_tickets_90d",
    "plan"
  ],
  "severity": "low",
  "status": "PASS"
}
```

### `model_quality`

**Rule:** status=INCONCLUSIVE; reason=model evaluation blocked until schema and domain validation pass; test_rows=0

```json
{
  "control": "model_quality",
  "excluded_rows": {
    "invalid_input": 1
  },
  "feature_manifest": [
    "tenure_months",
    "monthly_spend",
    "support_tickets_90d",
    "plan"
  ],
  "model_configuration": {
    "baseline": "majority_class",
    "declared_feature_manifest": [
      "tenure_months",
      "monthly_spend",
      "support_tickets_90d",
      "plan"
    ],
    "feature_manifest": [
      "support_tickets_90d"
    ],
    "name": "ticket_threshold_decision_stump",
    "threshold_rule": "minimum positive training ticket count"
  },
  "model_configuration_sha256": "b667d1dbce555892e572af564f07c6d0d1e669b988fcdb75247d50ff2e8cc961",
  "model_feature_manifest": [
    "support_tickets_90d"
  ],
  "reason": "model evaluation blocked until schema and domain validation pass",
  "rule": "status=INCONCLUSIVE; reason=model evaluation blocked until schema and domain validation pass; test_rows=0",
  "severity": "high",
  "status": "INCONCLUSIVE"
}
```

### `reproducibility`

**Rule:** canonical_hash=723c75df5915fabd92d0de1fdd7257a5fb91f449ea1071dff4f95bf57ffda4af; rerun_match=True; source_hash=a2cf5ace8a8b…

```json
{
  "canonical_result_sha256": "723c75df5915fabd92d0de1fdd7257a5fb91f449ea1071dff4f95bf57ffda4af",
  "configuration_sha256": "63c7476a32edf913a95c34fd0eed0e8fbf9bda7c0b4b5086e849c27f4a8b419b",
  "control": "reproducibility",
  "dependency_lock_sha256": "none",
  "input_sha256": "7372a7fd43364c9e5d2b6120b3cf2d42da5de65918e2128ad18e226dbd951a04",
  "model_configuration_sha256": "b667d1dbce555892e572af564f07c6d0d1e669b988fcdb75247d50ff2e8cc961",
  "platform": "macOS-26.6.2-arm64-arm-64bit-Mach-O",
  "policy_version": "2026.08.2",
  "python": "3.14.7",
  "repository_revision": "08697d2ff0b5757e60f2682deba38c2001e8beec",
  "rerun_canonical_result_sha256": "723c75df5915fabd92d0de1fdd7257a5fb91f449ea1071dff4f95bf57ffda4af",
  "rerun_match": true,
  "rule": "canonical_hash=723c75df5915fabd92d0de1fdd7257a5fb91f449ea1071dff4f95bf57ffda4af; rerun_match=True; source_hash=a2cf5ace8a8b\u2026",
  "runner_sha256": "f290200a5e5e3a6f9d6185b2cd769a3a8cfe472a1edb411d99185a333bec43d5",
  "seed": 255,
  "severity": "low",
  "source_sha256": "a2cf5ace8a8bf0196b4ed481a4970dee9499f9b48e03450114d6db4425ad85eb",
  "split": "time-ordered temporal holdouts",
  "split_manifest": {
    "grain": "customer_snapshot",
    "primary_window": "final_holdout",
    "test_date_bounds": [],
    "test_row_ids": [],
    "train_date_bounds": [],
    "train_row_ids": []
  },
  "status": "PASS"
}
```


## Decision

Release is blocked by: schema, duplicate_identifiers, domain_validity, model_quality.

The canonical reproducibility hash and independent-process rerun comparison are stored in `reports/audit_results.json`; the volatile audit timestamp is excluded from that canonical artifact.

## Limitations

This audit does not assess fairness, privacy, access controls, lineage, drift, label validity, or operational monitoring. The model result is a deterministic diagnostic baseline, not evidence of business readiness. Human data-owner sign-off is required.
