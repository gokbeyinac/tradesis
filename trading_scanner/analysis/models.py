"""Analysis result models — all frozen dataclasses."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class SRLevel:
    """Support or resistance level."""
    price: float
    type: str               # "support" | "resistance"
    test_count: int
    strength: str            # "medium" | "strong"
    last_test: str
    proximity_alert: bool


@dataclass(frozen=True)
class CandlePattern:
    """Detected candlestick pattern."""
    pattern: str
    direction: str           # "bullish" | "bearish" | "neutral"
    confidence: float        # 0.0 - 1.0
    bar_index: int           # index in DataFrame
    bar_offset: int          # offset from last bar (0 = last, -1 = second last)


@dataclass(frozen=True)
class ChartPattern:
    """Detected chart pattern."""
    pattern: str
    direction: str           # "bullish" | "bearish"
    confidence: float
    start_index: int
    end_index: int
    target_price: float | None = None
    annotations: tuple = ()


@dataclass(frozen=True)
class TrendResult:
    """Trend analysis result."""
    trend: str               # "strong_bullish" | "weak_bullish" | "sideways" | "weak_bearish" | "strong_bearish"
    ema_fast: float
    ema_mid: float
    ema_slow: float
    slope: float
    slope_direction: str     # "up" | "flat" | "down"


@dataclass(frozen=True)
class IndicatorValues:
    """Current indicator readings."""
    rsi: float
    macd: float
    macd_signal: float
    macd_histogram: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    stoch_k: float
    stoch_d: float
    cci: float
    cmf: float


@dataclass(frozen=True)
class ScanResult:
    """Complete scan result for one instrument."""
    symbol: str
    price: float
    sr_levels: tuple[SRLevel, ...]
    candle_patterns: tuple[CandlePattern, ...]
    chart_patterns: tuple[ChartPattern, ...]
    trend: TrendResult
    indicators: IndicatorValues
    scanned_at: str
