"""Small, CPU-safe time-series forecasting experiment.

The forecast for time t only uses observations strictly before t.  This is
deliberately explicit so that the example is safe to adapt for coursework.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


SEASONAL_PERIOD = 12
LAGS = (1, 2, 3, 6, 12)


def make_dataset(n: int = 240, seed: int = 7) -> pd.DataFrame:
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
    history = list(map(float, observed))
    predictions = []
    for _ in range(horizon):
        t = len(history)
        pred = float(model.predict(np.asarray([make_features(np.asarray(history), t)]))[0])
        predictions.append(pred)
        history.append(pred)
    return np.asarray(predictions)


def seasonal_naive(values: np.ndarray, start: int, stop: int) -> np.ndarray:
    """One-step seasonal baseline, allowed to use observations already known."""
    return np.asarray([values[t - SEASONAL_PERIOD] for t in range(start, stop)])


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(np.sqrt(mean_squared_error(actual, predicted))),
    }


def run(output_dir: str | Path = "outputs") -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data = make_dataset()
    values = data["value"].to_numpy()
    n = len(values)
    train_end, validation_end = int(n * 0.70), int(n * 0.85)
    minimum = max(LAGS)

    X_train, y_train = feature_matrix(values, minimum, train_end)
    model = HistGradientBoostingRegressor(
        max_iter=180, learning_rate=0.05, max_leaf_nodes=8,
        l2_regularization=0.5, random_state=7,
    )
    model.fit(X_train, y_train)

    # Validation and test are forecast recursively: predictions, never future
    # targets, become history after the forecast origin.
    validation_pred = recursive_forecast(model, values[:train_end], validation_end - train_end)
    test_pred = recursive_forecast(model, np.r_[values[:train_end], validation_pred], n - validation_end)
    baseline_pred = seasonal_naive(values, validation_end, n)
    actual = values[validation_end:]
    results = {
        "dataset_rows": n,
        "split": {"train_end": train_end, "validation_end": validation_end, "test_start": validation_end},
        "baseline_seasonal_naive": metrics(actual, baseline_pred),
        "model_hist_gradient_boosting": metrics(actual, test_pred),
        "leakage_control": "Chronological split; lag/rolling features use values before t; model test forecast is recursive.",
    }
    (output_dir / "metrics.json").write_text(json.dumps(results, indent=2) + "\n")
    data.to_csv(output_dir / "synthetic_monthly_series.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(data.date, values, label="observed", color="#3949ab", linewidth=1.4)
    test_dates = data.date.iloc[validation_end:]
    ax.plot(test_dates, baseline_pred, label="seasonal naive", linestyle="--", color="#ef6c00")
    ax.plot(test_dates, test_pred, label="gradient boosting", color="#00897b")
    ax.axvline(data.date.iloc[validation_end], color="black", alpha=0.35, linestyle=":", label="test start")
    ax.set(title="CPU-safe monthly time-series forecast", xlabel="month", ylabel="value")
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_dir / "forecast.png", dpi=140)
    plt.close(fig)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="outputs")
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir), indent=2))
