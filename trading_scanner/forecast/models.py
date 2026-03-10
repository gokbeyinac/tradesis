"""Forecast result models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ForecastResult:
    """Price forecast output."""
    dates: tuple[str, ...]
    values: tuple[float, ...]
    lower: tuple[float, ...]
    upper: tuple[float, ...]
    model_name: str
