# Enterprise Data-Science Quality and Governance Audit

**Recommendation:** `CONDITIONAL`  
**Summary:** 4 fail(s), 0 warning(s); release recommendation: CONDITIONAL

## Findings

| Check | Status | Severity | Detail |
|---|---|---|---|
| schema | FAIL | high | 41 rows; missing=[]; extra=[]; parse_errors=['row 8 monthly_spend'] |
| missingness | FAIL | medium | null_rates={'customer_id': 0.0, 'snapshot_date': 0.0, 'tenure_months': 0.0, 'monthly_spend': 0.0244, 'support_tickets_90d': 0.0, 'plan': 0.0, 'churned': 0.0, 'churn_confirmed_at': 0.7561, 'internal_note': 0.9756}; threshold=0.05 |
| duplicate_identifiers | FAIL | high | duplicate_customer_ids=['C0001'] |
| leakage_risk | FAIL | high | churn_confirmed_at is populated from the outcome window and must not be available at prediction time; internal_note may contain outcome/cancellation language and requires review |
| reproducibility | PASS | low | {"input_sha256": "7372a7fd43364c9e5d2b6120b3cf2d42da5de65918e2128ad18e226dbd951a04", "python": "3.14.7", "seed": 255, "split": "first 70% train / final 30% holdout by snapshot_date"} |
| model_quality | PASS | medium | {"majority_baseline": {"accuracy": 0.6667, "balanced_accuracy": 0.5, "f1": 0, "precision": 0, "recall": 0.0}, "model": {"accuracy": 0.6667, "balanced_accuracy": 0.75, "f1": 0.6667, "precision": 0.5, "recall": 1.0}, "test_rows": 12, "ticket_threshold": 2, "train_rows": 26} |

## Decision

Do not approve for production scoring until the high-severity schema/identifier and leakage findings are remediated. The model-quality result is only a baseline on synthetic data and does not establish business readiness.

## Limitations

This audit does not assess fairness, privacy, access controls, lineage, drift, calibration, label validity, or operational monitoring. Human data-owner sign-off is required.
