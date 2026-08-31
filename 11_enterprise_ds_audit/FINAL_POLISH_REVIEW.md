# Project 11 final polish review

## Recommendation

**Do not approve this as a production release-control audit yet.** The project is a strong, dependency-free teaching demonstration and the seeded fixture is correctly kept out of approval, but the current implementation still has correctness and explainability gaps that matter for a governance decision. Keep the project at **CONDITIONAL / blocked** until the P0 items below are resolved, then regenerate and re-review the JSON, Markdown report, and UI screenshot together.

The current checked-in result is directionally sound: `reports/audit_results.json` reports 3 failures, 2 inconclusive controls, and a `CONDITIONAL` recommendation. The implementation also has meaningful safeguards: typed row parsing and shape errors (`src/enterprise_audit.py:96-116`, `219-237`), model blocking when schema/domain validation is not clean (`src/enterprise_audit.py:509-521`), manifest-based leakage checks (`src/enterprise_audit.py:327-370`), structured JSON evidence, and reproducibility metadata (`src/enterprise_audit.py:525-567`). Validation in this checkout passed: 11/11 unit tests, Python compilation, and `node --check app.js`.

## Prioritized actions

### P0 — Bind model evaluation to the declared feature contract

**Evidence:** Leakage evaluation accepts `feature_manifest` and validates it (`src/enterprise_audit.py:327-370`), but `_evaluate_model` ignores that manifest and always learns/predicts from `support_tickets_90d` (`src/enterprise_audit.py:386-459`). The core runner passes only typed rows into model evaluation (`src/enterprise_audit.py:516-519`).

**Risk:** A caller can declare a different production feature set, receive `leakage_risk=PASS`, and still get model-quality evidence from a feature that is not in that set. This breaks the central audit claim that the evaluated model is the audited model contract.

**Action:** Pass the validated manifest into model evaluation and construct the baseline from those features (or explicitly make the baseline’s feature manifest immutable and include it in the result). Add a test proving that changing/removing `support_tickets_90d` changes or blocks model evaluation. Hash the actual model/feature configuration used for evaluation.

### P0 — Correct duplicate evidence and define the duplicate gate

**Evidence:** `_duplicate_evidence` compares `[customer_id, None]` with `duplicate_keys`, whose values are `[customer_id, snapshot_date]` (`src/enterprise_audit.py:252-269`, especially line 260). The checked-in result simultaneously reports `C0001@2025-01-02` as a duplicate key (`reports/audit_results.json:140-146`) and `C0001` as a “valid multi-snapshot” ID (`reports/audit_results.json:160-163`). Model eligibility removes only exact duplicate rows, not all repeated `(customer_id, snapshot_date)` keys (`src/enterprise_audit.py:386-395`).

**Risk:** Reviewers can be given contradictory evidence about the dataset grain, and conflicting records at the declared duplicate key can enter model evaluation even though the duplicate control fails.

**Action:** Derive multi-snapshot IDs from the set of customer IDs whose repeated rows have distinct snapshot dates; separately report exact duplicates and conflicting duplicate keys. State whether duplicate-key conflicts are fatal, and either block model evaluation or apply a documented deterministic retention rule. Add tests for exact duplicates, same customer/different dates, and same customer/same date/different payload.

### P0 — Make the release decision and its prose use one policy

**Evidence:** Blocking findings are high-severity failures or any `INCONCLUSIVE`, while `APPROVE` additionally requires zero failures of any severity and zero warnings (`src/enterprise_audit.py:569-574`). If a medium/low failure exists without a blocking finding or warning, the decision text still says “All mandatory controls and model-quality gates passed” (`src/enterprise_audit.py:575-581`).

**Risk:** The status, decision state, and human-readable explanation can disagree. A release reviewer should not have to infer why a recommendation is `CONDITIONAL` from the summary counters.

**Action:** Define and test a complete decision matrix for high/medium/low `FAIL`, `WARN`, and `INCONCLUSIVE`. Generate prose from the same blocking and warning collections used for the decision, including non-blocking failures. Prefer explicit `BLOCKED`, `CONDITIONAL`, and `APPROVED` semantics over deriving them indirectly from counters.

### P0 — Turn findings into an actual interactive evidence workflow

**Evidence:** The findings table renders plain rows with a decorative arrow and no row click, keyboard action, or detail target (`app.js:85-93`; `index.html:95-103`). The dashboard only renders compact evidence panels for schema, leakage, missingness, and reproducibility (`app.js:95-106`; `index.html:106-110`); duplicate identifiers, domain validity, model-quality windows, decision blockers, and warning findings have no drill-down view. The model panel shows only a few summary metrics and hides confusion matrices, class support, confidence intervals, split IDs, thresholds, and exclusions (`app.js:67-83`).

**Risk:** The page is an attractive report summary with search/filter controls, but it does not let a reviewer interactively explore the findings that drive release. The most important evidence remains trapped in JSON or truncated detail strings.

**Action:** Make each finding row a real button/link (with keyboard support) that opens an accessible detail drawer or panel keyed by check name. Render structured evidence: offending rows/columns and counts, duplicate samples, domain violations, temporal split bounds and IDs, model confusion matrices/CIs/thresholds, and the exact decision blockers. Keep the Markdown report as a linked export, but do not require a reviewer to leave the dashboard to inspect the gate.

## P1 improvements

### Strengthen model-quality claims before allowing `PASS`

**Evidence:** The model uses two temporal windows and minimum row/class-support gates (`src/enterprise_audit.py:397-412`), but acceptance is only `balanced_accuracy_delta >= 0.05` in every window (`src/enterprise_audit.py:443-459`). The bootstrap interval is reported but not used as a gate (`src/enterprise_audit.py:438`), and the Brier score is computed from hard 0/1 decisions while calibration is labeled diagnostic (`src/enterprise_audit.py:439`, `459`).

**Action:** Keep this explicitly diagnostic, or add decision criteria for uncertainty, business operating thresholds, minimum effective sample size, and an agreed number of temporal backtests. Do not present a tiny synthetic baseline as evidence of business readiness; the README’s limitation is correct and should also be prominent in the model panel.

### Make reproducibility an independent rerun and include all material inputs

**Evidence:** “Rerun” is two calls to `_run_core` in the same process over the same in-memory inputs (`src/enterprise_audit.py:528-537`). The canonical payload includes checks, model output, input hash, and config, but not the source/runtime/dependency/repository metadata later recorded in `reproducibility` (`src/enterprise_audit.py:535-564`). The checked-in result has `dependency_lock_sha256: "none"` (`reports/audit_results.json:229-249`).

**Action:** Run a clean second process or provide a separately persisted canonical artifact; include policy, source/configuration, runtime, dependency, repository, and model-pipeline hashes in the canonical comparison. Hash `run_audit.py` and any configuration that changes generated outputs. Keep volatile timestamps outside the canonical payload, as the current report correctly does.

### Remove date-dependent audit behavior

**Evidence:** Domain validity compares dates with the machine’s current `date.today()` (`src/enterprise_audit.py:272-314`). The result can therefore change over time without any input or code change.

**Action:** Require an explicit `as_of_date`/audit timestamp in the policy configuration, record it in evidence, and test future-date behavior against that fixed value. Also fix the wording in the domain detail: line 511 says “typed rows,” while `rows_checked` is the raw-row count returned by `_domain_evidence` (`src/enterprise_audit.py:314`, `509-511`).

### Improve evidence portability and structured reporting

**Evidence:** The JSON has useful evidence objects, but the Markdown writer reduces each check to an interpolated detail string (`src/enterprise_audit.py:596-623`). Evidence is capped in places (`src/enterprise_audit.py:314`, `496`), and the report does not surface complete row/column references, exclusion policy, or model split evidence. The dashboard mostly reads these compact summaries rather than structured evidence (`app.js:95-106`).

**Action:** Standardize evidence fields such as `control`, `rule`, `status`, `severity`, `count`, `denominator`, `rows`, `columns`, `samples`, `config_version`, and `remediation`. Make truncation explicit and provide a machine-readable full artifact or export path. Redact or classify customer identifiers before displaying them in a governance UI.

### Expand contract tests and add UI behavior tests

**Evidence:** The backend suite now covers 11 useful cases (`tests/test_audit.py:11-157`), including clean leakage, malformed rows, missing sentinels, duplicate headers, model blocking, reproducibility, and metric length checks. It does not cover the duplicate-evidence contradiction, feature-manifest/model mismatch, fixed audit date, complete decision matrix, or canonical provenance changes. There are no tests for the dashboard’s rendering, filters, empty state, or evidence drill-down.

**Action:** Add table-driven backend tests for each policy boundary and a small DOM-level UI test suite for load, status/severity/search filters, keyboard-accessible finding details, malformed/missing report data, and `INCONCLUSIVE` model display.

## UI polish and artifact consistency

- The statistic labeled “Blocking failures” is computed as every `FAIL` plus every `INCONCLUSIVE` (`app.js:22-32`), although the backend’s blocking policy is severity-aware. Rename it to “Failures / inconclusive” or compute the actual blocking collection from `result.decision.blocking_findings`.
- High-severity count is based on severity alone, so a future high-severity `PASS` would still be described as needing attention (`app.js:26-31`, `53-64`). Count high-severity non-passing controls for risk callouts.
- “Leakage & privacy flags” overstates the implementation (`index.html:108`): the code checks feature leakage and identifier-like columns, while the README explicitly says privacy compliance is out of scope (`README.md:42-44`). Rename the panel or implement a real privacy control.
- The Markdown report is fetched but not rendered or otherwise used after load (`app.js:2`, `116-121`). Either remove the unnecessary fetch or expose report metadata/sections in the UI.
- The checked-in screenshot `ui_screenshots/project-11.png` is stale relative to the current artifacts: it shows 6 checks, 4 failures, and older release-gate copy, while the current JSON contains 7 checks, 3 failures, 2 inconclusive results, and current gate text. Regenerate the screenshot after the implementation and reports are finalized; treat screenshot parity as a release check.

## Final assessment

This is ready to present as a thoughtful **synthetic governance-audit teaching artifact**, not as a defensible production release gate. The backend has moved beyond the earlier hard-coded-leakage design and now demonstrates several good controls, but the model contract/evaluation disconnect and contradictory duplicate evidence are correctness blockers. The UI also needs a finding-level evidence interaction model, not just filters over a static table. After the P0 fixes, rerun the clean and seeded fixtures, verify that `APPROVE` is reachable only under the documented policy, regenerate both reports and the screenshot, and perform a fresh review.
