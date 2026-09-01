import math


def number(value: object, default: float = 0.0) -> float:
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else default
    except (TypeError, ValueError):
        return default


def finite(value: object, field: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"invalid_artifact_value:{field}") from error
    if not math.isfinite(parsed):
        raise ValueError(f"invalid_artifact_value:{field}")
    return parsed
