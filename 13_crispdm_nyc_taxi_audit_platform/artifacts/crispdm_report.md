# CRISP-DM report

## Business understanding
Estimate taxi trip duration to support planning and dispatch analysis.

## Data understanding and audit
Generated 1,200 deterministic NYC-like trips. The audit found 7 missing distances and 6 non-positive durations; invalid target rows were excluded and numeric feature gaps were median-imputed.

## Data preparation
Derived pickup hour, weekday, and rush-hour indicator. Used distance, passenger count, pickup/dropoff zones, and temporal features.

## Modeling
A CPU-safe histogram gradient-boosting regressor was trained on the first 80% chronologically; the final 20% was held out.

## Evaluation
- MAE: **2.794 minutes**
- RMSE: **3.622 minutes**
- R²: **0.892**
- Within 5 minutes: **84.5%**

## Deployment and monitoring
`run_platform.py --infer` loads the saved model. In production, monitor missingness, duration drift, error by zone/time, and prediction latency.

## Limitations and deviations
This is a sample-data reproduction because the original prompt file and TLC data were unavailable. It omits coordinates, weather, fares, traffic feeds, privacy controls, model comparison, and a hosted API. Metrics are illustrative only.
