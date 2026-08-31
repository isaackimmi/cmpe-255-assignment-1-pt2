# Project 06 — Anomaly Detection

This project reproduces a small, controlled anomaly-detection study using a deterministic synthetic data set. The data are two correlated normal clusters plus three anomaly mechanisms: globally distant points, a dense local fringe, and a compact shifted cluster. Labels are used only for evaluation; all detectors fit the unlabeled feature matrix.

## Methods and improvement

- Isolation Forest: isolates unusual observations using random partitions.
- Local Outlier Factor (LOF): compares local density to neighboring density.
- Elliptic Envelope: robust covariance / Mahalanobis-style detector; useful as a simple global elliptical baseline.
- Rank ensemble (meaningful improvement): averages each detector's percentile rank. This avoids treating incompatible raw score scales as directly comparable and combines global, local, and robust views.

The contamination rate is the known synthetic anomaly prevalence (100 / 900), so each method flags exactly 100 points. In a real unsupervised deployment this rate would need to be estimated or selected through an operating-cost policy.

## Run

From this directory:

```bash
python -m pip install -r requirements.txt
python src/anomaly_experiment.py --output-dir artifacts
python -m pytest -q
```

The run writes `artifacts/metrics.json` and `artifacts/anomaly_scores.png`. The experiment is deterministic with seed 42 and accepts `--seed` for sensitivity checks.

## Evaluation

Because anomaly prevalence is low, accuracy is intentionally omitted. The report includes ROC-AUC (ranking quality), average precision (precision-recall quality under class imbalance), and fixed-budget precision, recall, and F1. It also reports recall for each anomaly category so an apparently strong aggregate score cannot hide a method's failure on local or clustered anomalies.

## Limitations and interpretation

This is a teaching reproduction, not a claim of production performance. The data are two-dimensional, synthetic, and generated from distributions that favor these algorithms. Labels and the true contamination rate are unavailable in a genuinely unsupervised setting. Elliptic Envelope's unimodal elliptical assumption is mismatched to the two-cluster population; LOF is sensitive to `n_neighbors`; Isolation Forest and all thresholds can vary with random seed and drift. Feature scaling is fit on all observations here for a compact demonstration; a production pipeline should fit preprocessing on a clean training set and monitor leakage. Results should be treated as a method comparison and failure-mode illustration, not a universal ranking.
## Integration verification

- **Prompt alignment:** Public Project 06 asks for anomaly detection with CRISP-DM, popular methods, evaluation, and dashboard details; detectors, ensemble, category recall, metrics, and plot are present.
- **Results/artifacts:** Elliptic Envelope led this synthetic run (ROC-AUC 0.8808, AP 0.6883, F1 0.64); JSON/PNG regenerated; pytest passed 3/3.
- **Issue/resolution:** System Python lacked packages and Python 3.14 Matplotlib aborted during cache setup; compatible existing environment completed the run.
