# Enterprise Data-Science Quality and Governance Audit

**Recommendation:** `CONDITIONAL`
**Summary:** 3 fail(s), 2 inconclusive, 0 warning(s); release recommendation: CONDITIONAL
**Policy:** `2026.08.1`

## Findings

| Check | Status | Severity | Detail |
|---|---|---|---|
| schema | FAIL | high | 41 rows; missing=[]; extra=[]; row_errors=1 |
| missingness | FAIL | medium | null_rates={'customer_id': 0.0, 'snapshot_date': 0.0, 'tenure_months': 0.0, 'monthly_spend': 0.0244, 'support_tickets_90d': 0.0, 'plan': 0.0, 'churned': 0.0, 'churn_confirmed_at': 0.7561, 'internal_note': 0.9756}; violations=['monthly_spend'] |
| duplicate_identifiers | FAIL | high | duplicate_key_values=[['C0001', '2025-01-02']]; exact_duplicate_rows=1; excluded=1 |
| domain_validity | INCONCLUSIVE | high | 0 domain violation(s) across 41 typed rows |
| leakage_risk | PASS | low | features=['tenure_months', 'monthly_spend', 'support_tickets_90d', 'plan']; offending=0; excluded_suspicious=['customer_id', 'churned', 'churn_confirmed_at'] |
| model_quality | INCONCLUSIVE | high | status=INCONCLUSIVE; reason=model evaluation blocked until schema and domain validation pass; test_rows=0 |
| reproducibility | PASS | low | canonical_hash=46a6cc1a7db2d5a568a9df12faf1913f8101f1d61106b0a613b0258d67a52d53; rerun_match=True; source_hash=c1157cd99846… |

## Decision

Release is blocked by: schema, duplicate_identifiers, domain_validity, model_quality.

The canonical reproducibility hash and rerun comparison are stored in `reports/audit_results.json`; the volatile audit timestamp is excluded from that canonical artifact.

## Limitations

This audit does not assess fairness, privacy, access controls, lineage, drift, label validity, or operational monitoring. The model result is a deterministic diagnostic baseline, not evidence of business readiness. Human data-owner sign-off is required.
