# Synthetic CRISP-DM report

## Business understanding
Estimate taxi trip duration for an educational planning and audit demonstration. This project does not make dispatch, pricing, safety, or NYC traffic-performance claims.

## Data understanding and audit
Generated 1,200 deterministic NYC-like trips in memory. This is a synthetic fixture, not a download of the NYC TLC corpus. The complete audit is saved in `audit_report.json` with row-level findings, severity, action, and status. It recorded 187 findings across all audit categories.

## Target-quality policy
`trip_duration_minutes` must be numeric, finite, greater than 0, and at most 180 minutes. Rows failing any rule are excluded before the chronological split. Raw, retained, and excluded populations plus excluded IDs are recorded in the audit and `run_manifest.json`.

## Data preparation
Pickup hour, weekday, and rush-hour indicators are derived before splitting. Invalid feature values are coerced to missing. Numeric medians and missingness indicators are fitted inside the model pipeline on training rows only, then applied unchanged to the holdout and inference rows.

## Modeling and evaluation
A CPU-safe histogram gradient-boosting regressor was trained on the first 80% chronologically; the final 20% was held out. These are synthetic smoke-test metrics, not evidence of generalization to real taxi trips. The holdout spans 2024-02-18T18:28:00 through 2024-02-29T23:50:00.

- Retained rows: **1,194** (955 train / 239 holdout)
- MAE: **2.790 minutes**
- RMSE: **3.624 minutes**
- R²: **0.892** (coefficient of determination, not accuracy)
- Within 5 minutes: **84.1%** (application threshold, not generic accuracy)

The global-mean baseline scores MAE **8.658** minutes and the distance-only linear baseline scores **3.486** minutes on the same holdout. These single-window baselines are calibration references, not proof of temporal generalization. Row-level model errors and slice metrics are saved in `prediction_errors.json`.

## Deployment and monitoring
`run_platform.py --infer` loads the saved model and uses the same serialized preprocessing pipeline. In production, validate licensed real TLC data, monitor missingness, drift, error slices, and prediction latency before considering operational use.

## Reproducibility
`run_manifest.json` records the run identity, command, seed, row argument, source/data hashes, git revision, Python and package versions, feature contract, model parameters, split rule, target policy, artifact hashes, and population/time-range counts.

## Limitations and deviations
The original prompt and licensed TLC data were unavailable. The generated data uses a deliberately simple mechanism, so the reported score measures recovery of this toy mechanism. The browser inference lab is a separate hand-written directional calculator; it is not the evaluated saved-model inference. Real-data ingestion, rolling-origin validation, uncertainty intervals, route geometry, weather, traffic feeds, privacy controls, and a hosted API remain future work.
