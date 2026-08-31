# Project 11 — Enterprise Data-Science Quality and Governance Audit

This project is a small, runnable audit of a customer-churn modeling dataset. It intentionally includes realistic governance defects (missing values, a duplicate customer, an out-of-scope identifier, and a post-outcome field) so the audit produces actionable findings rather than a perfect score.

## Run

The implementation uses only the Python standard library.

```bash
python3 run_audit.py
python3 -m unittest discover -s tests -v
```

`run_audit.py` creates `artifacts/sample_customers.csv` deterministically, audits it, and writes:

- `reports/audit_report.md` — human-readable findings and release recommendation
- `reports/audit_results.json` — machine-readable check results

The sample is synthetic; no production records are used. The model-quality section is a deliberately small deterministic decision-stump baseline, not a production training pipeline.

## Audit coverage

- Schema: required columns, type/parseability, allowed categorical values, duplicate IDs, and row count.
- Missingness: per-column null rates and a configurable threshold.
- Leakage risks: target-like fields, post-outcome timestamps, and identifier-like columns.
- Reproducibility: seed/configuration, stable input SHA-256, deterministic split, and runtime metadata.
- Model quality: time-ordered holdout, majority baseline, accuracy, precision, recall, F1, and balanced accuracy.

## Limitations

This is a teaching artifact, not a certification framework. It does not prove fairness, privacy compliance, access control, lineage, drift, label correctness, calibration, robustness, or production monitoring. A real release would need an approved data dictionary, ownership and retention policies, protected-attribute impact analysis, a temporal validation design agreed with stakeholders, and independent review.
## Integration verification

- **Prompt alignment:** Public Project 11 asks for an advanced audit of all projects and a detailed report; this provides schema, missingness, duplicate, leakage, reproducibility, and model-quality checks.
- **Results/artifacts:** Four failures and `CONDITIONAL` release recommendation; unittest passed 3/3; reports and sample CSV are present.
- **Issue/resolution:** Findings are intentional fixtures demonstrating detection, not defects to suppress.
