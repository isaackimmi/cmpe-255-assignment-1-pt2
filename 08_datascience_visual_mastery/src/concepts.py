"""Small, auditable calculations behind the visual lessons."""
from __future__ import annotations

import math
from dataclasses import dataclass
from collections.abc import Sequence


NumberOrNumbers = float | Sequence[float]


def _probability_values(value: NumberOrNumbers, name: str) -> list[float]:
    values = [float(value)] if isinstance(value, (int, float)) else [float(item) for item in value]
    if not values or any(not math.isfinite(item) or not 0 <= item <= 1 for item in values):
        raise ValueError(f"{name} must contain finite probabilities between 0 and 1")
    return values


def naive_bayes_posterior(prior: float, likelihood_positive: NumberOrNumbers,
                          likelihood_negative: NumberOrNumbers) -> float:
    """Return ``P(class | evidence)`` for one or more independent features.

    Scalar likelihoods preserve the original one-feature example.  Sequences
    demonstrate the Naive Bayes product ``∏ P(feature | class)``.  If the
    evidence has zero probability under both classes, the posterior is
    undefined and a ``ValueError`` is raised rather than silently returning 0.
    """
    if not math.isfinite(prior) or not 0 <= prior <= 1:
        raise ValueError("prior must be between 0 and 1")
    positive = _probability_values(likelihood_positive, "likelihood_positive")
    negative = _probability_values(likelihood_negative, "likelihood_negative")
    if len(positive) != len(negative):
        raise ValueError("likelihood feature lists must be aligned")
    positive_product = math.prod(positive)
    negative_product = math.prod(negative)
    numerator = positive_product * prior
    denominator = numerator + negative_product * (1 - prior)
    if denominator == 0:
        raise ValueError("evidence has zero probability under both classes")
    return numerator / denominator


@dataclass(frozen=True)
class CostMatrix:
    """Costs indexed by outcome cells in an actual-by-predicted matrix."""

    true_positive: float = 0.0
    false_positive: float = 1.0
    true_negative: float = 0.0
    false_negative: float = 4.0

    def __post_init__(self) -> None:
        values = (self.true_positive, self.false_positive,
                  self.true_negative, self.false_negative)
        if any(not math.isfinite(value) or value < 0 for value in values):
            raise ValueError("costs must be finite and non-negative")


@dataclass(frozen=True)
class ConfusionMetrics:
    threshold: float
    tp: int
    fp: int
    tn: int
    fn: int
    precision: float | None
    recall: float | None
    fpr: float | None
    cost: float
    cost_matrix: CostMatrix


def threshold_metrics(y_true: list[int], scores: list[float], threshold: float,
                      false_positive_cost: float = 1.0,
                      false_negative_cost: float = 4.0,
                      true_positive_cost: float = 0.0,
                      true_negative_cost: float = 0.0,
                      zero_division: str = "undefined") -> ConfusionMetrics:
    """Compute threshold metrics; undefined ratios are returned as ``None``.

    Scores are probabilities, so both scores and the threshold must be in
    ``[0, 1]``.  The default ``zero_division='undefined'`` teaching policy is
    represented by ``None`` when a metric's denominator is zero.  Pass
    ``zero_division='zero'`` to use the common zero-filled reporting policy.
    """
    if len(y_true) != len(scores) or not y_true:
        raise ValueError("labels and scores must be non-empty and aligned")
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1")
    if zero_division not in ("undefined", "zero"):
        raise ValueError("zero_division must be 'undefined' or 'zero'")
    if any(label not in (0, 1) for label in y_true):
        raise ValueError("labels must be binary 0/1 values")
    if any(not math.isfinite(score) or not 0 <= score <= 1 for score in scores):
        raise ValueError("scores must be finite probabilities between 0 and 1")
    costs = CostMatrix(true_positive_cost, false_positive_cost,
                       true_negative_cost, false_negative_cost)
    pred = [int(score >= threshold) for score in scores]
    tp = sum(a == 1 and b == 1 for a, b in zip(y_true, pred))
    fp = sum(a == 0 and b == 1 for a, b in zip(y_true, pred))
    tn = sum(a == 0 and b == 0 for a, b in zip(y_true, pred))
    fn = sum(a == 1 and b == 0 for a, b in zip(y_true, pred))
    undefined = None if zero_division == "undefined" else 0.0
    precision = tp / (tp + fp) if tp + fp else undefined
    recall = tp / (tp + fn) if tp + fn else undefined
    fpr = fp / (fp + tn) if fp + tn else undefined
    cost = (costs.true_positive * tp + costs.false_positive * fp
            + costs.true_negative * tn + costs.false_negative * fn)
    return ConfusionMetrics(threshold, tp, fp, tn, fn, precision, recall, fpr,
                            cost, costs)


def roc_points(y_true: list[int], scores: list[float]) -> list[tuple[float, float, float | None]]:
    """Return ROC points as ``(fpr, tpr, threshold)`` including both endpoints."""
    if len(y_true) != len(scores) or not y_true:
        raise ValueError("labels and scores must be non-empty and aligned")
    if any(label not in (0, 1) for label in y_true):
        raise ValueError("labels must be binary 0/1 values")
    if any(not math.isfinite(score) or not 0 <= score <= 1 for score in scores):
        raise ValueError("scores must be finite probabilities between 0 and 1")
    positives = sum(y_true)
    negatives = len(y_true) - positives
    if not positives or not negatives:
        raise ValueError("ROC requires both positive and negative labels")

    points = [(0.0, 0.0, None)]
    for threshold in sorted(set(scores), reverse=True):
        metrics = threshold_metrics(y_true, scores, threshold)
        points.append((metrics.fpr or 0.0, metrics.recall or 0.0, threshold))
    points.append((1.0, 1.0, None))
    # Equal scores can create vertical jumps; sorting makes the integration
    # contract explicit and preserves all threshold points for visualization.
    return sorted(points, key=lambda point: (point[0], point[1]))


def roc_auc(y_true: list[int], scores: list[float]) -> float:
    """Integrate the ROC curve with the trapezoidal rule."""
    points = roc_points(y_true, scores)
    return sum((x2 - x1) * (y1 + y2) / 2
               for (x1, y1, _), (x2, y2, _) in zip(points, points[1:]))


def quadratic(x: float) -> float:
    return (x - 3.0) ** 2 + 1.0


def quadratic_derivative(x: float) -> float:
    return 2.0 * (x - 3.0)


def gradient_descent(start: float = -2.0, learning_rate: float = 0.18,
                     steps: int = 12) -> list[float]:
    if (not math.isfinite(start) or not math.isfinite(learning_rate)
            or steps < 0 or learning_rate <= 0):
        raise ValueError("start must be finite, steps non-negative, and learning rate positive")
    values = [float(start)]
    for _ in range(steps):
        values.append(values[-1] - learning_rate * quadratic_derivative(values[-1]))
    return values


def backprop_demo(x: float = 2.0, w: float = 3.0, b: float = 1.0,
                  target: float = 10.0) -> dict[str, float]:
    """Backpropagate through one affine neuron and a squared-error loss."""
    if any(not math.isfinite(value) for value in (x, w, b, target)):
        raise ValueError("backprop inputs must be finite")
    y_hat = w * x + b
    error = y_hat - target
    return {"y_hat": y_hat, "loss": 0.5 * error ** 2,
            "dL_dy": error, "dy_dwx": 1.0, "dwx_dw": x, "dy_dw": x,
            "dy_db": 1.0,
            "dL_dw": error * x, "dL_db": error}


def sigmoid(value: float) -> float:
    """Numerically stable sigmoid for every finite real input."""
    if not math.isfinite(value):
        raise ValueError("sigmoid input must be finite")
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1 + exp_value)
