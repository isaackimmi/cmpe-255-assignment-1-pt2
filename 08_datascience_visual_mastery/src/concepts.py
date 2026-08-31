"""Small, auditable calculations behind the visual lessons."""
from __future__ import annotations

import math
from dataclasses import dataclass


def naive_bayes_posterior(prior: float, likelihood_positive: float,
                          likelihood_negative: float) -> float:
    """P(class | positive evidence), using Bayes' rule."""
    if not 0 < prior < 1:
        raise ValueError("prior must be between 0 and 1")
    if not 0 <= likelihood_positive <= 1 or not 0 <= likelihood_negative <= 1:
        raise ValueError("likelihoods must be probabilities")
    numerator = likelihood_positive * prior
    denominator = numerator + likelihood_negative * (1 - prior)
    return numerator / denominator if denominator else 0.0


@dataclass(frozen=True)
class ConfusionMetrics:
    threshold: float
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float
    recall: float
    fpr: float
    cost: float


def threshold_metrics(y_true: list[int], scores: list[float], threshold: float,
                      false_positive_cost: float = 1.0,
                      false_negative_cost: float = 4.0) -> ConfusionMetrics:
    """Compute threshold metrics; score >= threshold is a positive prediction."""
    if len(y_true) != len(scores) or not y_true:
        raise ValueError("labels and scores must be non-empty and aligned")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    pred = [int(score >= threshold) for score in scores]
    tp = sum(a == 1 and b == 1 for a, b in zip(y_true, pred))
    fp = sum(a == 0 and b == 1 for a, b in zip(y_true, pred))
    tn = sum(a == 0 and b == 0 for a, b in zip(y_true, pred))
    fn = sum(a == 1 and b == 0 for a, b in zip(y_true, pred))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    return ConfusionMetrics(threshold, tp, fp, tn, fn, precision, recall, fpr,
                            false_positive_cost * fp + false_negative_cost * fn)


def quadratic(x: float) -> float:
    return (x - 3.0) ** 2 + 1.0


def quadratic_derivative(x: float) -> float:
    return 2.0 * (x - 3.0)


def gradient_descent(start: float = -2.0, learning_rate: float = 0.18,
                     steps: int = 12) -> list[float]:
    if steps < 0 or learning_rate <= 0:
        raise ValueError("steps must be non-negative and learning rate positive")
    values = [float(start)]
    for _ in range(steps):
        values.append(values[-1] - learning_rate * quadratic_derivative(values[-1]))
    return values


def backprop_demo(x: float = 2.0, w: float = 3.0, b: float = 1.0,
                  target: float = 10.0) -> dict[str, float]:
    """For y_hat = w*x+b, loss = 0.5*(y_hat-target)^2."""
    y_hat = w * x + b
    error = y_hat - target
    return {"y_hat": y_hat, "loss": 0.5 * error ** 2,
            "dL_dy": error, "dy_dw": x, "dy_db": 1.0,
            "dL_dw": error * x, "dL_db": error}


def sigmoid(value: float) -> float:
    return 1 / (1 + math.exp(-value))
