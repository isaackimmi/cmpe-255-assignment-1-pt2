# Project 11 data-science robustness review

## Verdict

The fixture run is useful as a teaching demonstration: it detects the seeded missing value, duplicate identifier, and intended governance flags, and produces a `CONDITIONAL` recommendation. It is not yet a reliable release-control audit. The largest risks are that leakage status is hard-coded rather than detected, malformed input can crash the audit after a schema failure, and the release gate does not enforce severity or warning policy.

Line references below refer to the files as reviewed in this checkout.

## Validation performed

- `python3 -m unittest discover -s tests -v` — passed 3/3.
- `python3 -m py_compile src/enterprise_audit.py run_audit.py tests/test_audit.py` — passed.
- `node --check app.js` — passed.
- The checked-in fixture hash (`7372a7fd43364c9e5d2b6120b3cf2d42da5de65918e2128ad18e226dbd951a04`) matches the hash in `reports/audit_results.json`; the report shows 4 failures and `CONDITIONAL`.
- Temporary adversarial CSVs (not committed) produced the following results: a fully populated syntactically valid fixture still received `leakage_risk=FAIL`; an extra value on a later row received `schema=PASS`; and malformed `support_tickets_90d` or `churned` in the holdout raised `ValueError` from the model-quality phase.

## Findings

### [HIGH] Input validation is incomplete and the audit does not fail closed

Evidence: `src/enterprise_audit.py:77-87` derives the schema from `rows[0]` and the header only. `csv.DictReader` stores extra values on later rows under a `None` key, which is never inspected, so a later-row undeclared column was accepted as `schema=PASS` in testing. The parse loop records errors but does not stop downstream processing; `src/enterprise_audit.py:98-104` reuses the original strings and calls `int()` while building the model, so a malformed holdout value crashes with `ValueError` after the schema check has already identified the bad value.

Fix: validate header uniqueness and every row’s exact field count/keys, including `None` keys from `DictReader`. Parse once into typed records and retain row-level errors. If the input contract is invalid, return an explicit `INCONCLUSIVE`/blocked model result and skip evaluation; never proceed to model code with invalid rows or raise an uncaught exception.

### [HIGH] Leakage control is a hard-coded assertion, not a detector

Evidence: `src/enterprise_audit.py:93-94` always emits the same `FAIL`, regardless of the input contents or feature set. A fully populated, otherwise-valid temporary fixture still failed this check. The declared `SAFE_FEATURES` allowlist at `src/enterprise_audit.py:14` is never consumed. This conflicts with the README’s stated coverage of target-like, post-outcome, and identifier-like detection (`README.md:36-40`). There is no check that `churn_confirmed_at` occurs after the prediction timestamp, and no check that the actual model feature manifest excludes unsafe columns.

Fix: require an explicit prediction-time column, label column, and feature manifest. Detect target/identifier/post-outcome columns from that manifest and validate temporal ordering and availability. Report the exact offending column, affected row count, and representative evidence; allow `PASS` when the configured feature set is demonstrably safe.

### [HIGH] Release recommendation is not severity- or warning-aware

Evidence: `src/enterprise_audit.py:110-112` sets `CONDITIONAL` only when any check has status `FAIL`; every warning-only result would become `APPROVE`, regardless of its `severity`. Conversely, the unconditional leakage failure makes `APPROVE` unreachable for normal calls. The generated decision prose is also static (`src/enterprise_audit.py:121`) rather than derived from the current blocking findings.

Fix: define a decision matrix: high-severity failures and any `INCONCLUSIVE` control block approval; warnings produce `CONDITIONAL`; `APPROVE` requires all mandatory controls to pass plus minimum data/model gates. Generate the decision text from the actual blocking check names and include the policy version in the result.

### [HIGH] Reproducibility is reported without proving reproducibility

Evidence: `src/enterprise_audit.py:95-97` records only the input hash, Python version, passed seed, and a prose split description. The audit’s model path is deterministic and does not use `seed` (`src/enterprise_audit.py:100-107`), so the seed is metadata rather than an effective control. `generated_at_utc` is intentionally variable (`src/enterprise_audit.py:113`), and there is no source/configuration hash, dependency/environment lock, code revision, output hash, exact cutoff, or train/test row manifest. The existing reproducibility test checks only that sample generation repeats (`tests/test_audit.py:25-28`), not that audit outputs repeat.

Fix: version and hash the audit code/configuration, capture the runtime/dependency lock and repository revision, record exact train/test date bounds and row IDs, and rerun the audit to compare canonical result hashes. Separate volatile run metadata from the canonical reproducibility artifact.

### [HIGH] Model-quality `PASS` is too weak and can be invalid or misleading

Evidence: `src/enterprise_audit.py:98-109` evaluates one small 70/30 holdout after dropping only blank `monthly_spend` rows and duplicate IDs. Other schema-invalid rows remain eligible for model code. The only acceptance rule is balanced accuracy at least 0.05 above a majority baseline; it has no minimum train/test size, class-support requirement, uncertainty interval, repeated temporal backtests, calibration check, or business threshold. The checked-in “PASS” is based on just 12 test rows (`reports/audit_report.md:15`). `threshold=99` is a silent fallback when no positive training labels exist.

Fix: make model evaluation `INCONCLUSIVE` when data validation fails, the holdout is empty/small, or either class lacks support. Use the production feature pipeline, explicit label/time eligibility, multiple temporal evaluation windows, confidence intervals, confusion matrices, and business-relevant operating thresholds. Treat a small synthetic baseline as diagnostic evidence, not a release-quality pass.

### [MEDIUM] Missingness detection recognizes only the empty string and uses one global policy

Evidence: `_parse` and the rate calculation (`src/enterprise_audit.py:47-57,89-91`) do not normalize whitespace, `NA`/`N/A`/`null`, `None`, or numeric `NaN`/infinity. The same `>0.05` threshold is applied to every column, including fields declared nullable in `REQUIRED` (`src/enterprise_audit.py:8-12`), with no required-vs-optional policy or subgroup/time-slice analysis.

Fix: define canonical missing tokens by type, normalize before validation, reject non-finite numeric values, and configure per-column thresholds and allowed-null semantics. Report counts/denominators and missingness by relevant time or population slices.

### [MEDIUM] Domain and temporal semantics are under-validated

Evidence: `src/enterprise_audit.py:47-58,86-87` checks parseability and allowed plan values but not ranges or relationships. Negative tenure/spend/ticket counts, an empty `customer_id`, a future `snapshot_date`, or a `churn_confirmed_at` before `snapshot_date` can pass the schema control. A single blank ID is also not treated as a duplicate (`src/enterprise_audit.py:88-92`); the adversarial probe returned `duplicate_customer_ids=[]`.

Fix: enforce non-empty ID format and uniqueness policy, non-negative numeric ranges, valid date bounds, and label/timestamp consistency. Include invalid values and counts in structured evidence rather than only a truncated parse-error list.

### [MEDIUM] Duplicate handling assumes the wrong data grain and silently removes records

Evidence: `src/enterprise_audit.py:88-100` treats any repeated `customer_id` as a duplicate, without defining whether the grain is customer or customer-snapshot. It then removes every row for each duplicated ID from model evaluation and does not report the number or identity of excluded rows. The seeded duplicate is an exact repeated row, so the current fixture finding is reasonable, but the same logic would reject valid longitudinal snapshots.

Fix: declare the dataset grain and duplicate key (for example, exact row or `(customer_id, snapshot_date)`). Distinguish exact duplicates from multiple valid snapshots, apply a documented retention/aggregation rule, and report affected rows and label impact.

### [MEDIUM] Evidence is difficult to audit or act on

Evidence: check details are opaque interpolated strings (`src/enterprise_audit.py:87-109`) rather than structured evidence objects. The report contains a few IDs and rates but no complete row/column references, exclusion counts, temporal bounds, feature manifest, or observed values for the leakage claim (`reports/audit_report.md:8-15`). `audit_dataset` also emits an environment-specific absolute dataset path (`src/enterprise_audit.py:113`), which reduces portability.

Fix: emit structured findings with `control`, `status`, `severity`, `evidence` (file, row, column, count, and safe/redacted sample), rule/config version, and remediation owner. Include exact split boundaries and exclusions. Store a portable relative path or dataset URI while retaining the input hash.

### [MEDIUM] Tests cover only the intended happy path and seeded defects

Evidence: `tests/test_audit.py:16-35` contains three tests: detection of the generated defects, deterministic fixture generation, and presence of metric keys. There are no tests for safe leakage `PASS`, later-row shape errors, malformed holdout values, missing sentinels, blank IDs, duplicate headers, empty/single-row data, invalid ranges, timestamp ordering, warning-only recommendations, or reproducibility of the full audit result.

Fix: add table-driven unit tests for each contract boundary and integration tests asserting controlled `INCONCLUSIVE` behavior, decision-matrix outcomes, and stable canonical evidence. Keep at least one clean fixture so hard-coded failures cannot pass unnoticed.

### [LOW] Metric helper silently accepts mismatched arrays

Evidence: `_metric` uses `zip(y, pred)` without a length assertion (`src/enterprise_audit.py:61-69`). The current caller supplies equal lengths, but direct or future callers can receive an apparently valid metric computed on truncated pairs.

Fix: assert equal lengths and either return an explicit undefined metric state or include denominators/class support when a metric has no positive or negative examples.

## Recommended remediation order

1. Make row/schema parsing typed, complete, and fail-closed; add adversarial tests.
2. Replace the unconditional leakage assertion with prediction-time/feature-manifest validation.
3. Implement the severity-aware decision matrix and structured evidence schema.
4. Strengthen reproducibility artifacts and model-quality eligibility/statistical gates.
5. Define data grain, missingness/domain policies, and expand the test suite.
