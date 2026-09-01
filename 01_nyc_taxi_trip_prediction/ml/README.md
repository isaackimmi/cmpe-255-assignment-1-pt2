# Project 01 ML layer

`run_experiment.py` is the reproducible training/evaluation entry point. The
`ml/model.py` module is the lightweight inference adapter used by FastAPI: it
loads the checked-in metrics and prediction artifacts, recomputes selected
holdout slices, and exposes the deterministic synthetic estimator. No test
target is used to create a primary prediction; the robust-inlier population is
explicitly a sensitivity view.
