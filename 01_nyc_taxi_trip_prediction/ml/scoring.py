import math

from .numeric import number


def score(rows: list[dict], actual_key: str = "actual", prediction_key: str = "prediction") -> dict:
    actual = [number(row.get(actual_key)) for row in rows]
    predicted = [number(row.get(prediction_key)) for row in rows]
    if not rows:
        return {"rows": 0, "mae_seconds": None, "rmse_seconds": None, "r2": None}
    errors = [predicted_value - actual_value for actual_value, predicted_value in zip(actual, predicted)]
    mean_actual = sum(actual) / len(actual)
    ss_total = sum((value - mean_actual) ** 2 for value in actual)
    ss_residual = sum(error ** 2 for error in errors)
    return {
        "rows": len(rows),
        "mae_seconds": round(sum(abs(error) for error in errors) / len(errors), 3),
        "rmse_seconds": round(math.sqrt(ss_residual / len(errors)), 3),
        "r2": round(1 - ss_residual / ss_total, 4) if ss_total else None,
    }
