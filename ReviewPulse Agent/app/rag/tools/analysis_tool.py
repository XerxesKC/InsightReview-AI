from __future__ import annotations

from collections.abc import Sequence
from statistics import mean
from typing import Any


def summarize_numeric_series(values: Sequence[float | int]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": mean(values),
        "min": min(values),
        "max": max(values),
    }

