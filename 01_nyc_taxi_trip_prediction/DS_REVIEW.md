# Data-science review status

This file is retained as a short pointer so an older audit does not contradict the executable pipeline. The authoritative review is [`FINAL_POLISH_REVIEW.md`](FINAL_POLISH_REVIEW.md); the implementation now addresses its highest-priority findings:

- the primary holdout scores every structurally eligible future row, while training-derived target trimming is a separately labeled inlier sensitivity;
- naive timestamps have an explicit `America/New_York` policy, aware timestamps normalize to UTC, mixed/ambiguous inputs are rejected, and timestamp groups cannot straddle a split boundary;
- the real-CSV contract audits unique IDs, vendor/passenger semantics, timestamp coverage, NYC-like service-area bounds, and structural drop reasons;
- `outputs/metrics.json` records fold boundaries, fold mean/dispersion, source metadata, and scoring denominators;
- the UI explorer recomputes metric/baseline/slice results from `outputs/predictions.csv` and surfaces fold, coefficient, and cleaning artifacts.

The checked-in data remains deterministic synthetic NYC-like fallback data. Its metrics are a reproducibility demonstration, not evidence of real taxi performance.
