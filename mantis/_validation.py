import math


def finite_float(value, name: str) -> float:
    """Convert a numeric input to float and reject NaN/Inf."""
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须是有限数值") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} 必须是有限数值")
    return result


def positive_float(value, name: str) -> float:
    """Convert a numeric input to a finite, positive float."""
    result = finite_float(value, name)
    if result <= 0:
        raise ValueError(f"{name} 必须大于 0")
    return result
