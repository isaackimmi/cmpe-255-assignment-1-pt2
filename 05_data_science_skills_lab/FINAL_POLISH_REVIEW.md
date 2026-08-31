# Project 05 Final Polish Review

## Recommendation

**Conditional go for an offline teaching artifact; no-go for a final “interactive analytics” demo until the P0/P1 items below are addressed.**

The current pipeline is materially stronger than the older `DS_REVIEW.md` suggests: validation is explicit, preprocessing boundaries are mostly correct, classification is held out, clustering is scaled and diagnosed, and the test suite passes. The dashboard also works as a polished artifact viewer. The remaining gap is that the UI makes a few small-sample results look like headline analytics while exposing very little of the evidence behind them. Its controls switch modules and pre-rendered SVGs, but do not yet let a user interrogate the data or model outputs.

## What is already sound

- Input validation covers required columns, finite/nonnegative numeric values, known plans, binary labels, missing rows, and conflicting duplicate IDs (`src/skills_lab.py:14-73`).
- Regression splits before fitting feature imputation and excludes missing regression targets from scoring (`run_lab.py:53-88`, `run_lab.py:157-162`).
- Classification uses a seeded stratified holdout, a fixed predeclared rule, imbalance-aware metrics, and a majority baseline (`run_lab.py:90-109`).
- Clustering standardizes features, evaluates candidate `k`, uses repeated initializations, and reports silhouette/inertia/convergence metadata (`run_lab.py:117-153`).
- Plotting now handles empty and constant ranges and includes axes, ticks, and legends (`src/skills_lab.py:321-371`).
- Verification performed for this review from static project inspection: `python3 -m unittest discover -s tests -v` passed 8/8 and `python3 -m compileall -q src run_lab.py` passed. Source inspection confirms module buttons and chart-tab handlers are wired, but no browser automation or local server was used for this final audit.

## Prioritized improvements

### P0 — Put evaluation uncertainty and baselines beside the headline numbers

**Evidence.** The regression result is based on one seeded shuffled split with only seven scored rows (`run_lab.py:60-88`; `artifacts/metrics.json:24-43`). It reports an apparently excellent `R²` of about 0.985 and MAE of about 2.06, but the dashboard exposes only the MAE (`index.html:63-67`, `app.js:22-24`). Classification also has only seven test rows (`run_lab.py:92-109`; `artifacts/metrics.json:45-80`), and its 71% accuracy exactly equals the majority-class baseline (`artifacts/metrics.json:62-80`), a fact the UI does not show (`index.html:57-61`).

**Why it matters.** A learner or reviewer can reasonably read the large regression R² or the “held-out rule” accuracy as evidence of a useful model, even though both estimates are high-variance and the classification rule does not beat the displayed baseline at all.

**Action.** Add `n`/scored-row counts, the baseline, and a plain-language comparison to each model card. For example: “MAE 2.06 on 7 observed test targets; mean baseline MAE 15.57” and “71% on 7 cases; same as majority baseline.” For a stronger skills demonstration, add repeated stratified/seeded holdouts or cross-validation with fold variability; keep the single split as a reproducibility example rather than the sole performance claim.

### P1 — Expose the actual analytics behind each module, not only templated takeaways

**Evidence.** `renderMetrics()` renders four headline values plus data-quality counts (`app.js:16-34`). `selectModule()` changes a title, paragraph, one result string, and one “why” label (`app.js:37-50`); the module descriptions are static strings (`app.js:1-7`). The loaded `summary` artifact is stored but never rendered (`app.js:9`, `app.js:69-75`). Consequently, the UI does not expose the regression predictions/excluded-target list, classification confusion matrix/F1/specificity, EDA sample size or ticket correlation, or clustering candidate-k table/inertia/silhouette values that are present in the artifacts (`artifacts/metrics.json:14-19`, `artifacts/metrics.json:45-168`, `artifacts/summary.json:387-432`).

**Action.** Give each selected module a small evidence block driven from `state.metrics`/`state.summary`: show observed `n` and missingness for EDA; MAE/RMSE/R², baseline, and prediction rows for regression; the confusion matrix, F1, specificity, baseline delta, and imputed-feature count for classification; and a candidate-k table plus cluster sizes/centers for clustering. Keep explanatory prose, but make the numeric evidence the primary content.

### P1 — Either make charts genuinely exploratory or label them as artifact previews

**Evidence.** The chart UI has only two tabs (`index.html:96-106`). `selectChart()` swaps the `src` of an `<img>` between two pre-rendered SVG files and changes the caption (`app.js:52-65`); the Python generator emits fixed circles/paths and no point identifiers or hover content (`src/skills_lab.py:340-371`). There are no filters, tooltips, point selection, zoom, or linked chart/table behavior.

**Action.** Preferred: render the point data as inline SVG/DOM and add accessible hover/focus tooltips, customer/cluster labels, a renewal and plan filter, and a visible `n`/missingness note. For clustering, add a control or table for candidate `k` and its silhouette/inertia. If this scope is intentionally static, rename the section to “Generated artifact previews” and avoid implying that the chart itself is interactive analytics.

### P1 — Correct the stale review/documentation story

**Evidence.** `DS_REVIEW.md` says the current results still score an imputed target, use in-sample classification, raw unscaled clustering, and weak validation (`DS_REVIEW.md:5-7`, `DS_REVIEW.md:11-22`, `DS_REVIEW.md:24-34`, `DS_REVIEW.md:61-71`). Those claims conflict with the current implementation and artifacts cited above. It also records a four-test check while the current suite has eight tests (`DS_REVIEW.md:122-129`; `tests/test_skills_lab.py:17-135`).

**Action.** Mark `DS_REVIEW.md` explicitly as historical or update/remove superseded findings. Keep one current source of truth for the evaluation design, artifact schema, and test count; otherwise a reviewer receives contradictory signals about whether the lab is trustworthy.

### P2 — Make the synthetic fixture’s limits visible at the point of use

**Evidence.** The fixture has 23 clean rows and only 22 observed usage values (`artifacts/metrics.json:2-19`). The dashboard calls the classification result “held-out rule” and the correlation card only “correlation coefficient” (`index.html:51-67`) without showing those sample sizes or the one test usage feature imputed for classification (`artifacts/metrics.json:54-60`). The regression module is a one-feature baseline using tenure (`run_lab.py:63-67`; `app.js:4`).

**Action.** Add compact qualifiers such as “descriptive r, n=22,” “classification n=7; 1 usage feature imputed,” and “one-feature regression baseline.” Preserve the existing synthetic/offline disclaimers (`README.md:27-29`, `index.html:31-35`) but repeat the most relevant limitation next to each claim.

### P2 — Give clusters interpretable names and show their evidence

**Evidence.** The selected clusters have centers around `(35.1 usage, 3.4 tickets)` and `(64.6 usage, 0.36 tickets)` with sizes 9 and 14 (`artifacts/metrics.json:82-122`), but the dashboard only says “2 customer groups” (`app.js:6`) and the SVG legend calls them `cluster 0`/`cluster 1` (`src/skills_lab.py:365-371`).

**Action.** Present descriptive names such as “lower-use / higher-support” and “higher-use / lower-support,” retaining the numeric centers and an explicit “descriptive, not causal” label. Avoid implying that cluster IDs have intrinsic meaning.

### P3 — Small accessibility and interaction polish

**Evidence.** The tab controls have `role="tab"` and selection state but no `aria-controls`/tabpanel relationship (`index.html:100-106`), and the chart image has no point-level accessible representation (`index.html:105`, `src/skills_lab.py:345-370`). The module controls are usable buttons and correctly expose pressed state through `app.js:37-43`.

**Action.** Add a labeled tabpanel relationship, a keyboard-visible focus treatment, and an accessible data table or summary for the chart so the visual is not the only way to inspect the analytics.

## Final assessment by dimension

| Dimension | Status | Rationale |
| --- | --- | --- |
| Data validation and preprocessing | Good | Explicit validation and train-local feature imputation are implemented and tested. |
| DS methodology disclosure | Needs polish | Small single holdouts and baseline parity are not surfaced in the UI. |
| Reproducibility | Good | Seed, split fraction, cluster settings, and input hash are recorded. |
| Charts | Good as generated artifacts | Axes and legends are present, but charts are not exploratory. |
| UI interactivity | Partial | Module and chart-tab state changes work; analytics remain mostly static copy and images. |
| Documentation consistency | Needs correction | `DS_REVIEW.md` describes superseded defects and outdated test counts. |

## Suggested release sequence

1. Surface sample sizes, baselines, imputation notes, and model diagnostics in the module detail area (P0/P1).
2. Update or label `DS_REVIEW.md` so the project has a consistent current narrative.
3. Add at least one real chart interaction (filters plus tooltips/table) or relabel the chart section as static artifact previews.
4. Add cluster names and the candidate-k evidence table, then finish the accessibility relationship polish.

After steps 1–3, the project should be suitable for a final classroom/demo review as a carefully caveated offline skills lab. Without them, it is visually polished and technically improved, but the UI over-indexes on presentation relative to inspectable analytics.
