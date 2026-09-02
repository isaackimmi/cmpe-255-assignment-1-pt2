"""Dependency-free, validation-first data-science skills for Project 05."""

import csv
import html
import math
import random


NUMERIC = ("tenure_months", "monthly_usage", "support_tickets")
REQUIRED_COLUMNS = ("customer_id", *NUMERIC, "plan", "renewed")
VALID_PLANS = {"basic", "pro", "enterprise"}


def _finite(value, field, row_number):
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"row {row_number}: {field} must be numeric, got {value!r}") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"row {row_number}: {field} must be finite, got {value!r}")
    return parsed


def _parse_row(raw, row_number):
    customer_id = (raw.get("customer_id") or "").strip()
    if not customer_id:
        raise ValueError(f"row {row_number}: customer_id is required")
    plan = (raw.get("plan") or "").strip().lower()
    if plan not in VALID_PLANS:
        raise ValueError(f"row {row_number}: plan must be one of {sorted(VALID_PLANS)}, got {plan!r}")
    parsed = {"customer_id": customer_id, "plan": plan}
    for col in NUMERIC:
        raw_value = (raw.get(col) or "").strip()
        parsed[col] = None if raw_value == "" else _finite(raw_value, col, row_number)
        if parsed[col] is not None and parsed[col] < 0:
            raise ValueError(f"row {row_number}: {col} must be nonnegative, got {parsed[col]}")
    if parsed["support_tickets"] is not None and not parsed["support_tickets"].is_integer():
        raise ValueError(f"row {row_number}: support_tickets must be a whole number")
    raw_renewed = (raw.get("renewed") or "").strip()
    if raw_renewed not in {"0", "1"}:
        raise ValueError(f"row {row_number}: renewed must be 0 or 1, got {raw_renewed!r}")
    parsed["renewed"] = int(raw_renewed)
    return parsed


def load_clean(path, impute=True):
    """Load and validate the fixture, optionally applying global median imputation.

    Validation happens before any deduplication or imputation. Duplicate IDs are
    allowed only when their parsed records are identical; conflicting duplicates
    raise a row-specific error. ``impute=False`` is the pipeline-safe mode for
    splitting before fitting preprocessing.
    """
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
        if missing:
            raise ValueError(f"missing required columns: {missing}")
        rows, by_id, duplicate_count = [], {}, 0
        for row_number, raw in enumerate(reader, start=2):
            parsed = _parse_row(raw, row_number)
            previous = by_id.get(parsed["customer_id"])
            if previous is not None:
                if parsed != previous:
                    raise ValueError(f"row {row_number}: conflicting duplicate customer_id {parsed['customer_id']!r}")
                duplicate_count += 1
                continue
            by_id[parsed["customer_id"]] = parsed
            rows.append(parsed)
    if not rows:
        raise ValueError("input contains no data rows")
    return (impute_numeric(rows)[0], duplicate_count) if impute else (rows, duplicate_count)


def _validate_rows(rows):
    rows = [dict(row) for row in rows]
    if not rows:
        raise ValueError("rows must be non-empty")
    for index, row in enumerate(rows, start=1):
        for col in NUMERIC:
            value = row.get(col)
            if value is not None and (not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
                raise ValueError(f"row {index}: {col} must be finite and nonnegative")
        if row.get("renewed") not in (0, 1):
            raise ValueError(f"row {index}: renewed must be 0 or 1")
    return rows


def median(values):
    values = sorted(values)
    if not values:
        raise ValueError("cannot compute a median from no observed values")
    middle = len(values) // 2
    return values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2


def fit_imputers(rows, columns=NUMERIC):
    rows = _validate_rows(rows)
    imputers = {}
    for col in columns:
        observed = [row[col] for row in rows if row.get(col) is not None]
        if not observed:
            raise ValueError(f"cannot impute {col}: all values are missing")
        imputers[col] = median(observed)
    return imputers


def apply_imputers(rows, imputers):
    rows = _validate_rows(rows)
    filled, counts = [], {col: 0 for col in imputers}
    for row in rows:
        copy = dict(row)
        for col, value in imputers.items():
            if copy.get(col) is None:
                copy[col] = value
                counts[col] += 1
        filled.append(copy)
    return filled, counts


def impute_numeric(rows, fit_rows=None, columns=NUMERIC):
    """Median-impute selected numeric columns and return rows plus fit metadata."""
    fit_rows = rows if fit_rows is None else fit_rows
    imputers = fit_imputers(fit_rows, columns)
    filled, counts = apply_imputers(rows, imputers)
    return filled, {"counts": counts, "medians": imputers}


def train_test_split(rows, test_fraction=0.30, seed=255, stratify=None):
    rows = _validate_rows(rows)
    if len(rows) < 2:
        raise ValueError("at least two rows are required for a train/test split")
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between 0 and 1")
    if stratify is not None and any(row.get(stratify) not in (0, 1) for row in rows):
        raise ValueError(f"stratify column {stratify!r} must contain binary labels")
    test_size = max(1, min(len(rows) - 1, round(len(rows) * test_fraction)))
    rng = random.Random(seed)
    indices = list(range(len(rows)))
    if stratify is None:
        rng.shuffle(indices)
        test_indices = set(indices[:test_size])
    else:
        groups = {label: [i for i, row in enumerate(rows) if row[stratify] == label] for label in (0, 1)}
        selected = []
        for group in groups.values():
            rng.shuffle(group)
            if group:
                selected.extend(group[:max(1, round(len(group) * test_fraction))])
        while len(selected) > test_size:
            removable = next((i for i, index in enumerate(selected) if sum(rows[j][stratify] == rows[index][stratify] for j in selected) > 1), 0)
            selected.pop(removable)
        while len(selected) < test_size:
            selected.append(next(i for i in indices if i not in selected))
        test_indices = set(selected)
    return ([row for i, row in enumerate(rows) if i not in test_indices], [row for i, row in enumerate(rows) if i in test_indices])


def _validate_vector(values, name):
    values = list(values)
    if not values:
        raise ValueError(f"{name} must be non-empty")
    if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in values):
        raise ValueError(f"{name} must contain only finite numeric values")
    return values


def _validate_pair(xs, ys):
    xs, ys = _validate_vector(xs, "xs"), _validate_vector(ys, "ys")
    if len(xs) != len(ys):
        raise ValueError(f"xs and ys must have equal lengths, got {len(xs)} and {len(ys)}")
    return xs, ys


def mean(xs):
    xs = _validate_vector(xs, "values")
    return sum(xs) / len(xs)


def correlation(xs, ys):
    xs, ys = _validate_pair(xs, ys)
    mx, my = mean(xs), mean(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denominator = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
    return numerator / denominator if denominator else 0.0


def linear_regression(xs, ys):
    xs, ys = _validate_pair(xs, ys)
    mx, my = mean(xs), mean(ys)
    denominator = sum((x - mx) ** 2 for x in xs)
    if denominator == 0:
        raise ValueError("linear_regression requires at least two distinct x values")
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / denominator
    return my - slope * mx, slope


def regression_metrics(actual, predicted):
    actual, predicted = _validate_pair(actual, predicted)
    errors = [a - p for a, p in zip(actual, predicted)]
    return {"mae": mean(abs(error) for error in errors), "rmse": math.sqrt(mean(error**2 for error in errors))}


def _validate_labels(values, name):
    values = list(values)
    if not values:
        raise ValueError(f"{name} must be non-empty")
    if any(value not in (0, 1) for value in values):
        raise ValueError(f"{name} must contain only 0/1 labels")
    return values


def classification_metrics(actual, predicted):
    actual, predicted = _validate_labels(actual, "actual"), _validate_labels(predicted, "predicted")
    if len(actual) != len(predicted):
        raise ValueError(f"actual and predicted must have equal lengths, got {len(actual)} and {len(predicted)}")
    tp = sum(a == p == 1 for a, p in zip(actual, predicted))
    tn = sum(a == p == 0 for a, p in zip(actual, predicted))
    fp = sum(a == 0 and p == 1 for a, p in zip(actual, predicted))
    fn = sum(a == 1 and p == 0 for a, p in zip(actual, predicted))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    specificity = tn / (tn + fp) if tn + fp else 0.0
    return {
        "accuracy": (tp + tn) / len(actual), "precision": precision, "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "specificity": specificity, "balanced_accuracy": (recall + specificity) / 2,
        "confusion_matrix": [[tn, fp], [fn, tp]], "n": len(actual),
    }


def _validate_points(points):
    points = [list(point) for point in points]
    if not points:
        raise ValueError("points must be non-empty")
    dimensions = len(points[0])
    if dimensions == 0:
        raise ValueError("points must have at least one dimension")
    for index, point in enumerate(points, start=1):
        if len(point) != dimensions:
            raise ValueError(f"point {index} has dimension {len(point)}, expected {dimensions}")
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in point):
            raise ValueError(f"point {index} must contain only finite numeric values")
    return points


def standardize_points(points, means=None, scales=None):
    points = _validate_points(points)
    dimensions = len(points[0])
    means = list(means) if means is not None else [mean([point[d] for point in points]) for d in range(dimensions)]
    scales = list(scales) if scales is not None else [math.sqrt(mean([(point[d] - means[d]) ** 2 for point in points])) for d in range(dimensions)]
    if len(means) != dimensions or len(scales) != dimensions or any(scale < 0 or not math.isfinite(scale) for scale in scales):
        raise ValueError("standardization parameters do not match point dimensions")
    safe_scales = [scale if scale else 1.0 for scale in scales]
    return [[(point[d] - means[d]) / safe_scales[d] for d in range(dimensions)] for point in points], {"means": means, "scales": safe_scales}


def unstandardize_points(points, params):
    points = _validate_points(points)
    means, scales = params["means"], params["scales"]
    return [[point[d] * scales[d] + means[d] for d in range(len(point))] for point in points]


def _nearest_labels(points, centers):
    return [min(range(len(centers)), key=lambda j: sum((point[d] - centers[j][d]) ** 2 for d in range(len(point)))) for point in points]


def _inertia(points, labels, centers):
    return sum(sum((point[d] - centers[label][d]) ** 2 for d in range(len(point))) for point, label in zip(points, labels))


def kmeans(points, k=2, seed=255, iterations=30, n_init=1, return_metadata=False):
    points = _validate_points(points)
    if not isinstance(k, int) or not 1 <= k <= len(points):
        raise ValueError(f"k must be an integer between 1 and {len(points)}")
    if not isinstance(iterations, int) or iterations <= 0:
        raise ValueError("iterations must be a positive integer")
    if not isinstance(n_init, int) or n_init <= 0:
        raise ValueError("n_init must be a positive integer")
    rng, best, init_inertias = random.Random(seed), None, []
    for _ in range(n_init):
        centers, converged = [list(point) for point in rng.sample(points, k)], False
        for iteration in range(1, iterations + 1):
            labels = _nearest_labels(points, centers)
            new_centers = []
            for cluster in range(k):
                group = [point for point, label in zip(points, labels) if label == cluster]
                new_centers.append([mean([point[d] for point in group]) for d in range(len(points[0]))] if group else centers[cluster])
            if new_centers == centers:
                converged, centers = True, new_centers
                break
            centers = new_centers
        labels = _nearest_labels(points, centers)
        inertia = _inertia(points, labels, centers)
        init_inertias.append(inertia)
        candidate = (inertia, labels, centers, converged, iteration)
        if best is None or inertia < best[0]:
            best = candidate
    _, labels, centers, converged, used_iterations = best
    metadata = {"inertia": _inertia(points, labels, centers), "converged": converged, "iterations": used_iterations, "n_init": n_init, "initialization_inertias": init_inertias}
    return (labels, centers, metadata) if return_metadata else (labels, centers)


def silhouette_score(points, labels):
    points, labels = _validate_points(points), list(labels)
    if len(labels) != len(points):
        raise ValueError("labels must have the same length as points")
    clusters = sorted(set(labels))
    if len(clusters) < 2:
        return 0.0
    scores = []
    for index, point in enumerate(points):
        same = [j for j, label in enumerate(labels) if label == labels[index] and j != index]
        within = mean([math.dist(point, points[j]) for j in same]) if same else 0.0
        between = min(mean([math.dist(point, points[j]) for j, label in enumerate(labels) if label == other]) for other in clusters if other != labels[index])
        scores.append((between - within) / max(within, between) if max(within, between) else 0.0)
    return mean(scores)


def _axis_domain(values):
    values = list(values)
    if not values:
        return 0.0, 1.0
    low, high = min(values), max(values)
    if low == high:
        padding = max(abs(low) * 0.05, 1.0)
        return low - padding, high + padding
    padding = (high - low) * 0.05
    return low - padding, high + padding


def _svg_axes(w, h, pad, x_domain, y_domain, x_label, y_label):
    x0, x1, y0, y1 = *x_domain, *y_domain
    x_ticks = "".join(f'<text x="{pad + fraction * (w - 2 * pad):.1f}" y="{h - pad + 18}" text-anchor="middle" font-family="sans-serif" font-size="11">{x0 + fraction * (x1 - x0):.1f}</text>' for fraction in (0, 0.5, 1))
    y_ticks = "".join(f'<text x="{pad - 8}" y="{h - pad - fraction * (h - 2 * pad) + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="11">{y0 + fraction * (y1 - y0):.1f}</text>' for fraction in (0, 0.5, 1))
    return f'<line x1="{pad}" y1="{h - pad}" x2="{w - pad}" y2="{h - pad}" stroke="black"/><line x1="{pad}" y1="{pad}" x2="{pad}" y2="{h - pad}" stroke="black"/>{x_ticks}{y_ticks}<text x="{w / 2}" y="{h - 7}" text-anchor="middle" font-family="sans-serif">{html.escape(x_label)}</text><text transform="translate(15 {h / 2}) rotate(-90)" text-anchor="middle" font-family="sans-serif">{html.escape(y_label)}</text>'


def svg_scatter(rows, path):
    rows = [row for row in rows if row.get("tenure_months") is not None and row.get("monthly_usage") is not None]
    w, h, pad = 640, 400, 55
    x_domain, y_domain = _axis_domain([row["tenure_months"] for row in rows]), _axis_domain([row["monthly_usage"] for row in rows])
    sx, sy = lambda value: pad + (value - x_domain[0]) / (x_domain[1] - x_domain[0]) * (w - 2 * pad), lambda value: h - pad - (value - y_domain[0]) / (y_domain[1] - y_domain[0]) * (h - 2 * pad)
    circles = "".join(f'<circle cx="{sx(row["tenure_months"]):.1f}" cy="{sy(row["monthly_usage"]):.1f}" r="5" fill="{("#2563eb" if row["renewed"] else "#dc2626")}"/>' for row in rows)
    legend = '<circle cx="470" cy="48" r="5" fill="#2563eb"/><text x="480" y="52" font-family="sans-serif" font-size="11">renewed</text><circle cx="535" cy="48" r="5" fill="#dc2626"/><text x="545" y="52" font-family="sans-serif" font-size="11">not renewed</text>'
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="100%" height="100%" fill="white"/><text x="{w / 2}" y="25" text-anchor="middle" font-family="sans-serif" font-size="18">Tenure vs monthly usage</text>{legend}{_svg_axes(w, h, pad, x_domain, y_domain, "tenure (months)", "monthly usage")}{circles}</svg>'
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(svg)


def svg_clusters(points, labels, centers, path):
    points, labels = ([list(point) for point in points], list(labels))
    if not points:
        if labels or centers:
            raise ValueError("empty points require empty labels and centers")
        centers = []
    else:
        points, centers = _validate_points(points), _validate_points(centers)
    if len(labels) != len(points) or any(label not in range(len(centers)) for label in labels):
        raise ValueError("labels must match points and reference a supplied center")
    w, h, pad = 640, 400, 55
    x_domain, y_domain = _axis_domain([point[0] for point in points]), _axis_domain([point[1] for point in points])
    sx, sy = lambda value: pad + (value - x_domain[0]) / (x_domain[1] - x_domain[0]) * (w - 2 * pad), lambda value: h - pad - (value - y_domain[0]) / (y_domain[1] - y_domain[0]) * (h - 2 * pad)
    palette = ("#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2")
    if len(centers) > len(palette):
        raise ValueError("plot supports at most six clusters")
    circles = "".join(f'<circle cx="{sx(point[0]):.1f}" cy="{sy(point[1]):.1f}" r="5" fill="{palette[label]}"/>' for point, label in zip(points, labels))
    marks = "".join(f'<path d="M {sx(center[0]) - 7:.1f} {sy(center[1]) - 7:.1f} L {sx(center[0]) + 7:.1f} {sy(center[1]) + 7:.1f} M {sx(center[0]) + 7:.1f} {sy(center[1]) - 7:.1f} L {sx(center[0]) - 7:.1f} {sy(center[1]) + 7:.1f}" stroke="black" stroke-width="2"/>' for center in centers)
    legend = "".join(f'<circle cx="{440 + index * 55}" cy="48" r="5" fill="{palette[index]}"/><text x="{450 + index * 55}" y="52" font-family="sans-serif" font-size="11">cluster {index}</text>' for index in range(len(centers)))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="100%" height="100%" fill="white"/><text x="{w / 2}" y="25" text-anchor="middle" font-family="sans-serif" font-size="18">Customer health clusters</text>{legend}{_svg_axes(w, h, pad, x_domain, y_domain, "monthly usage", "support tickets")}{circles}{marks}</svg>'
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(svg)
