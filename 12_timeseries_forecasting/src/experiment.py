"""Small, CPU-safe time-series forecasting experiment.

The forecast for time t only uses observations strictly before t.  This is
deliberately explicit so that the example is safe to adapt for coursework.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
from datetime import datetime, timezone

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


SEASONAL_PERIOD = 12
LAGS = (1, 2, 3, 6, 12)
DATA_SEED = 7
HORIZONS = (6, 12, 24, 36)
MODEL_CONFIG = {
    "max_iter": 180,
    "learning_rate": 0.05,
    "max_leaf_nodes": 8,
    "l2_regularization": 0.5,
    "random_state": 7,
}


def make_dataset(n: int = 240, seed: int = DATA_SEED) -> pd.DataFrame:
    """Return a deterministic monthly signal; no external download is needed."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2000-01-01", periods=n, freq="MS")
    t = np.arange(n)
    y = (
        20
        + 0.045 * t
        + 2.8 * np.sin(2 * np.pi * t / 12)
        + 0.9 * np.sin(2 * np.pi * t / 6)
        + rng.normal(0, 0.65, n)
    )
    return pd.DataFrame({"date": dates, "value": y})


def make_features(values: np.ndarray, t: int) -> list[float]:
    """Features for y[t], using values[0:t] only."""
    if t < max(LAGS):
        raise ValueError("not enough history for lag features")
    history = values[:t]
    return [*(history[t - lag] for lag in LAGS), float(history[t - 1] - history[t - 2]), float(np.mean(history[t - 3:t])), float(np.mean(history[t - 12:t]))]


def feature_matrix(values: np.ndarray, start: int, stop: int) -> tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for t in range(start, stop):
        X.append(make_features(values, t))
        y.append(values[t])
    return np.asarray(X), np.asarray(y)


def recursive_forecast(model, observed: np.ndarray, horizon: int) -> np.ndarray:
    """Forecast recursively, feeding each prediction back as history."""
    if horizon < 0:
        raise ValueError("horizon must be non-negative")
    history = list(map(float, observed))
    predictions = []
    for _ in range(horizon):
        t = len(history)
        pred = float(model.predict(np.asarray([make_features(np.asarray(history), t)]))[0])
        predictions.append(pred)
        history.append(pred)
    return np.asarray(predictions)


def seasonal_naive_forecast(
    observed: np.ndarray,
    horizon: int,
    seasonal_period: int = SEASONAL_PERIOD,
) -> np.ndarray:
    """Closed-loop seasonal-naive forecast from one shared forecast origin.

    After the first seasonal cycle, predictions—not actual future targets—are
    appended to history. This makes the baseline comparable with the model's
    recursive multi-step path.
    """
    if horizon < 0:
        raise ValueError("horizon must be non-negative")
    if seasonal_period <= 0:
        raise ValueError("seasonal_period must be positive")
    if len(observed) < seasonal_period:
        raise ValueError("not enough history for seasonal-naive forecast")

    history = list(map(float, observed))
    predictions = []
    for _ in range(horizon):
        prediction = history[-seasonal_period]
        predictions.append(prediction)
        history.append(prediction)
    return np.asarray(predictions)


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    actual = np.asarray(actual)
    predicted = np.asarray(predicted)
    if actual.size == 0 or predicted.size == 0:
        raise ValueError("metrics require non-empty arrays")
    if actual.shape != predicted.shape:
        raise ValueError("actual and predicted arrays must have the same shape")
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("metrics require finite arrays")
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
    }


def _package_version(package: str) -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "unavailable"


def _source_revision() -> str:
    project_dir = Path(__file__).resolve().parents[1]
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    except OSError:
        revision = ""
    return revision or "unknown"


def _repository_dirty() -> bool:
    project_dir = Path(__file__).resolve().parents[1]
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            check=False,
        ).stdout
    except OSError:
        return False
    return bool(status.strip())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _block_metrics(actual: np.ndarray, baseline: np.ndarray, model: np.ndarray) -> dict:
    return {
        "baseline_seasonal_naive": metrics(actual, baseline),
        "model_hist_gradient_boosting": metrics(actual, model),
    }


def _plot_forecast(
    data: pd.DataFrame,
    values: np.ndarray,
    baseline: np.ndarray,
    model: np.ndarray,
    forecast_start: int,
    forecast_end: int,
    output_path: Path,
    title_suffix: str = "",
) -> None:
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(data.date, values, label="observed", color="#3949ab", linewidth=1.4)
    forecast_dates = data.date.iloc[forecast_start:forecast_end]
    forecast_length = len(forecast_dates)
    ax.plot(forecast_dates, baseline[:forecast_length], label="seasonal naive", linestyle="--", color="#ef6c00")
    ax.plot(forecast_dates, model[:forecast_length], label="gradient boosting", color="#00897b")
    ax.axvline(data.date.iloc[forecast_start], color="black", alpha=0.35, linestyle=":", label="forecast origin")
    test_start = int(len(values) * 0.85)
    if forecast_start < test_start < forecast_end:
        ax.axvline(data.date.iloc[test_start], color="#8d99ae", alpha=0.7, linestyle="--", label="test start")
    ax.set(title=f"CPU-safe monthly time-series forecast{title_suffix}", xlabel="month", ylabel="value")
    ax.legend(ncol=4, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def run(output_dir: str | Path = "outputs") -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data = make_dataset()
    values = data["value"].to_numpy()
    n = len(values)
    train_end, validation_end = int(n * 0.70), int(n * 0.85)
    test_start = validation_end
    validation_horizon = validation_end - train_end
    test_horizon = n - test_start
    minimum = max(LAGS)

    X_train, y_train = feature_matrix(values, minimum, train_end)
    model = HistGradientBoostingRegressor(**MODEL_CONFIG)
    model.fit(X_train, y_train)

    # Both forecasters start at the same training boundary and run closed-loop
    # through validation and test. Actual validation/test targets are retained
    # only for scoring after forecasts are complete.
    total_horizon = n - train_end
    model_forecast = recursive_forecast(model, values[:train_end], total_horizon)
    baseline_forecast = seasonal_naive_forecast(values[:train_end], total_horizon)
    validation_actual = values[train_end:validation_end]
    test_actual = values[test_start:]
    validation_model = model_forecast[:validation_horizon]
    validation_baseline = baseline_forecast[:validation_horizon]
    test_model = model_forecast[validation_horizon:]
    test_baseline = baseline_forecast[validation_horizon:]

    horizon_metrics = {
        str(horizon): _block_metrics(
            test_actual[:horizon], test_baseline[:horizon], test_model[:horizon]
        )
        for horizon in HORIZONS
        if horizon <= test_horizon
    }
    forecast_rows = pd.DataFrame(
        {
            "date": data.date.iloc[train_end:].dt.strftime("%Y-%m-%d").to_numpy(),
            "split": ["validation"] * validation_horizon + ["test"] * test_horizon,
            "forecast_lead": np.arange(1, total_horizon + 1),
            "test_prefix_month": [None] * validation_horizon + list(range(1, test_horizon + 1)),
            "actual": values[train_end:],
            "baseline_seasonal_naive": baseline_forecast,
            "model_hist_gradient_boosting": model_forecast,
        }
    )
    forecast_rows["baseline_residual"] = forecast_rows["actual"] - forecast_rows["baseline_seasonal_naive"]
    forecast_rows["model_residual"] = forecast_rows["actual"] - forecast_rows["model_hist_gradient_boosting"]
    forecast_rows["baseline_absolute_error"] = forecast_rows["baseline_residual"].abs()
    forecast_rows["model_absolute_error"] = forecast_rows["model_residual"].abs()
    forecast_rows.to_csv(output_dir / "forecast_predictions.csv", index=False)

    forecast_artifacts = {}
    full_forecast_end = n
    _plot_forecast(
        data, values, baseline_forecast, model_forecast, train_end,
        full_forecast_end, output_dir / "forecast.png",
        title_suffix=" · validation + test",
    )
    for horizon in horizon_metrics:
        horizon_end = validation_end + int(horizon)
        filename = f"forecast_horizon_{horizon}.png"
        _plot_forecast(
            data, values, baseline_forecast, model_forecast, train_end,
            horizon_end, output_dir / filename,
            title_suffix=f" · first {horizon} test months",
        )
        forecast_artifacts[horizon] = filename

    results = {
        "dataset_rows": n,
        "split": {
            "train_end": train_end,
            "validation_end": validation_end,
            "test_start": test_start,
            "train_rows": train_end,
            "validation_rows": validation_horizon,
            "test_rows": test_horizon,
        },
        "forecast_protocol": {
            "name": "single_origin_closed_loop_with_reporting_slices",
            "interpretation": "One 72-step forecast from the training origin; nominal validation and test blocks are reporting slices, not tuning or refit stages.",
            "forecast_origin_index": train_end,
            "forecast_origin": data.date.iloc[train_end].strftime("%Y-%m-%d"),
            "history_through_index": train_end - 1,
            "history_through": data.date.iloc[train_end - 1].strftime("%Y-%m-%d"),
            "forecast_lead_start": 1,
            "forecast_lead_end": total_horizon,
            "test_lead_start": validation_horizon + 1,
            "test_lead_end": total_horizon,
            "validation_role": "reporting_slice_only",
            "test_role": "late_lead_reporting_slice",
            "refit_after_validation": False,
            "validation_horizon": validation_horizon,
            "test_horizon": test_horizon,
            "actual_intermediate_observations_used": False,
            "predictions_feed_back_into_history": True,
            "test_targets_used_as_inputs": False,
        },
        "validation": _block_metrics(validation_actual, validation_baseline, validation_model),
        "test": _block_metrics(test_actual, test_baseline, test_model),
        # Keep the original top-level metric keys as the full-test result for
        # simple consumers, while providing explicit block/horizon semantics.
        "baseline_seasonal_naive": metrics(test_actual, test_baseline),
        "model_hist_gradient_boosting": metrics(test_actual, test_model),
        "horizon_metrics": horizon_metrics,
        "horizon_metric_semantics": "cumulative_test_prefix_months_1_through_horizon_from_the_single_forecast_origin",
        "lead_metrics": {
            str(lead): _block_metrics(
                test_actual[lead - 1:lead],
                test_baseline[lead - 1:lead],
                test_model[lead - 1:lead],
            )
            for lead in range(1, test_horizon + 1)
        },
        "available_horizons": [int(horizon) for horizon in horizon_metrics],
        "forecast_artifacts": forecast_artifacts,
        "forecast_predictions_artifact": "forecast_predictions.csv",
        "provenance": {
            "data": {
                "generator": "make_dataset",
                "seed": DATA_SEED,
                "rows": n,
                "start": data.date.iloc[0].strftime("%Y-%m-%d"),
                "frequency": "MS",
            },
            "features": {"lags": list(LAGS), "seasonal_period": SEASONAL_PERIOD, "feature_count": len(LAGS) + 3},
            "split_fractions": {"train": 0.70, "validation": 0.15, "test": 0.15},
            "model": {"estimator": "HistGradientBoostingRegressor", **MODEL_CONFIG},
            "software": {
                "python": platform.python_version(),
                "numpy": _package_version("numpy"),
                "pandas": _package_version("pandas"),
                "scikit_learn": _package_version("scikit-learn"),
                "matplotlib": _package_version("matplotlib"),
            },
            "source_revision": _source_revision(),
            "repository_dirty": _repository_dirty(),
        },
        "artifact_manifest": "artifact_manifest.json",
        "leakage_control": "Chronological split; lag/rolling features use values before t; both forecasts share one closed-loop origin and never use actual validation/test targets as inputs.",
    }
    (output_dir / "metrics.json").write_text(json.dumps(results, indent=2) + "\n")
    data.to_csv(output_dir / "synthetic_monthly_series.csv", index=False)
    artifact_names = [
        "metrics.json",
        "synthetic_monthly_series.csv",
        "forecast_predictions.csv",
        "forecast.png",
        *forecast_artifacts.values(),
    ]
    manifest = {
        "manifest_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_revision": results["provenance"]["source_revision"],
        "repository_dirty": results["provenance"]["repository_dirty"],
        "reproduction": {
            "command": "python -m src.experiment --output-dir outputs",
            "environment": "requirements-lock.txt",
            "test_command": "pytest -q",
            "status": "artifacts_generated; tests_run_separately",
        },
        "artifacts": {
            name: {"sha256": _sha256(output_dir / name), "bytes": (output_dir / name).stat().st_size}
            for name in artifact_names
        },
    }
    (output_dir / "artifact_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir), indent=2))
