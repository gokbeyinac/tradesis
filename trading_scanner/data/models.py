"""Data layer models."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OHLCVBar:
    """Single OHLCV bar."""
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Interval:
    """Timeframe interval."""
    name: str
    minutes: int


H4 = Interval("H4", 240)
H1 = Interval("H1", 60)
