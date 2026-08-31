# Project 11 — Enterprise Data-Science Quality and Governance Audit

This project is a small, runnable audit of a customer-churn modeling dataset. The fixture intentionally includes realistic data defects (a missing required value and an exact duplicate row). Post-outcome and identifier-like fields remain in the raw file, but the explicit production feature manifest excludes them; leakage is therefore reported from the manifest rather than asserted unconditionally.

## Run

The implementation uses only the Python standard library.

```bash
python3 run_audit.py
python3 -m unittest discover -s tests -v
```

`run_audit.py` creates `artifacts/sample_customers.csv` deterministically, audits it with the `SAFE_FEATURES` manifest, and writes:

- `reports/audit_report.md` — human-readable findings and release recommendation
- `reports/audit_results.json` — machine-readable check results

## Governance dashboard

`index.html` is a dependency-free responsive dashboard for the generated reports. It presents the release recommendation, quality-dimension health, severity mix, model-quality baseline, schema/leakage/missingness/reproducibility evidence, and a filterable findings table. The page fetches both `reports/audit_results.json` and `reports/audit_report.md` at load time.

Because browsers restrict `fetch()` for local `file://` pages, serve the project directory locally:

```bash
cd HW/cmpe-255-assignment-1-pt2/11_enterprise_ds_audit
python3 -m http.server 8000
```

Then open <http://localhost:8000> and use the status/severity filters or search box to inspect findings. Re-run `python3 run_audit.py` before refreshing if the fixture or reports need to be regenerated.

The sample is synthetic; no production records are used. The dashboard labels this explicitly as a synthetic fixture. The model-quality section is a deliberately small deterministic decision-stump baseline, not a production training pipeline.

## Audit coverage

- Schema: required columns, type/parseability, allowed categorical values, duplicate IDs, and row count.
- Missingness: per-column null rates and a configurable threshold.
- Leakage risks: target-like fields, post-outcome timestamps, and identifier-like columns detected from the configured feature manifest, including row-level temporal evidence.
- Reproducibility: policy/configuration/source/dependency hashes, repository revision, stable input and canonical result SHA-256 values, rerun comparison, and exact split row/date manifests.
- Model quality: two temporal holdouts, minimum row/class-support gates, majority baseline, confusion matrices, confidence intervals, calibration diagnostics, and an explicit operating threshold. Invalid input produces `INCONCLUSIVE` and never reaches model code.

## Limitations

This is a teaching artifact, not a certification framework. It does not prove fairness, privacy compliance, access control, lineage, drift, label correctness, calibration, robustness, or production monitoring. A real release would need an approved data dictionary, ownership and retention policies, protected-attribute impact analysis, a temporal validation design agreed with stakeholders, and independent review.
## Integration verification

- **Prompt alignment:** Public Project 11 asks for an advanced audit of all projects and a detailed report; this provides schema, missingness, duplicate, leakage, reproducibility, and model-quality checks.
- **Results/artifacts:** The fixture remains `CONDITIONAL` because required-field missingness and exact duplication block release; model evaluation is explicitly `INCONCLUSIVE` until those issues are corrected. Reports and sample CSV are present.
- **Issue/resolution:** Findings are intentional fixtures demonstrating detection, not defects to suppress. A clean fixture is covered by tests to verify that safe leakage can pass.
