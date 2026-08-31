# Data-science robustness note — Project 03

## Current assessment

This project is a reproducible synthetic teaching lab, not validated customer intelligence. The generated data contains three intentionally separated Gaussian prototype chunks with equal counts, so the strong silhouette and perfect low-k ARI primarily demonstrate recovery of an authored toy structure. They do not establish that real customers form these groups, that a campaign will lift outcomes, or that assignments will remain stable over time.

## Validation protocol

The run predeclares `k=2…7` and compares `standard` with a `log1p` monetary-feature variant. For each candidate, preprocessing and K-Means are fit on 12 repeated 80/20 training splits; held-out rows are assigned with `predict()`. Mean held-out silhouette is the selection criterion, with ARI stability and lower `k` as tie-breakers. Full-sample silhouette, Calinski–Harabasz, Davies–Bouldin, and PCA are descriptive diagnostics only. ARI measures agreement between repeated fitted partitions; it is not a per-customer probability.

The selected run is `standard`, `k=3`: held-out silhouette `0.69097 ± 0.02897`, stability ARI mean/min `1.0 / 1.0`, and full-sample silhouette `0.69305`. The log1p table is a measured preprocessing variant, not an “improvement”; the selected standard run has the higher `k=3` held-out and full-sample silhouette in this toy sample.

## Artifact and explorer checks

Python `validate_artifacts()` checks exact assignment and explorer schemas, finite values, row counts, contiguous cluster labels, selected metric agreement, manifest metadata, and the complete SHA-256 hash set. The browser repeats the contract before rendering. The summary also records range-violation counts, duplicate/missing counts, per-feature scale/skew/IQR-outlier diagnostics, and the feature correlation matrix for this generated input. `artifacts/explorer_points.csv` adds deterministic customer IDs, raw features, PCA coordinates, nearest-centroid distance, runner-up margin, and a confidence/uncertainty label. Distance, margin, and confidence are geometry proxies in fitted scaled space—not calibrated probabilities.

The browser explorer supports raw feature-pair selection, a PCA projection-only view, segment filtering, keyboard/click point inspection, and point-level feature/diagnostic details. Heuristic profile names and campaign guidance remain explicitly hypothesis-only.

## Remaining limitations and observed-data path

- The generator does not test imbalance, overlap, non-spherical structure, contamination, missingness, duplicates, temporal drift, or aggregation-window changes.
- Repeated random splits overlap and come from one synthetic population; an observed-data workflow should predeclare a temporal or independent holdout.
- A real input path needs a documented customer grain/window, domain-range and duplicate policy, skew/outlier/correlation audit, feature-weight sensitivity, and a business outcome acceptance rule.
- K-Means should be compared with robust or non-spherical alternatives when the observed geometry warrants it.
- Before use with real customers, refit and serialize the complete preprocessing/model path, evaluate segment stability over time, test outcome value and fairness, and monitor drift. Never use these teaching segments to deny service or infer sensitive traits.

## Verification

- `./.venv/bin/python -m pytest -q`
- `./.venv/bin/python -m py_compile src/experiment.py tests/test_experiment.py`
- `node --check app.js`

This note supersedes the earlier review text that described in-sample `k` selection, an `improved_scores.csv` artifact, or an absent scoring path.
