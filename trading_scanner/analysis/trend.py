"""Trend analysis using EMA alignment and trendline slope."""

import numpy as np
import pandas as pd

from analysis.indicators import ema
from analysis.models import TrendResult
from config import EMA_FAST, EMA_MID, EMA_SLOW, TREND_SLOPE_LOOKBACK


def _classify_slope(slope: float, price: float) -> str:
    """Classify slope relative to price magnitude."""
    normalized = slope / price if price > 0 else 0
    if normalized > 0.001:
        return "up"
    if normalized < -0.001:
        return "down"
    return "flat"


def analyze_trend(df: pd.DataFrame) -> TrendResult:
    """Determine trend from EMA alignment and slope."""
    close = df["Close"]

    ema_fast = float(ema(close, EMA_FAST).iloc[-1])
    ema_mid = float(ema(close, EMA_MID).iloc[-1])
    ema_slow = float(ema(close, EMA_SLOW).iloc[-1])

    # Trendline slope via linear regression on recent closes
    recent = close.tail(TREND_SLOPE_LOOKBACK).values
    x = np.arange(len(recent))
    slope = float(np.polyfit(x, recent, 1)[0])

    price = float(close.iloc[-1])
    slope_dir = _classify_slope(slope, price)

    # EMA alignment
    if ema_fast > ema_mid > ema_slow:
        trend = "strong_bullish" if slope_dir == "up" else "weak_bullish"
    elif ema_fast < ema_mid < ema_slow:
        trend = "strong_bearish" if slope_dir == "down" else "weak_bearish"
    else:
        if slope_dir == "up":
            trend = "weak_bullish"
        elif slope_dir == "down":
            trend = "weak_bearish"
        else:
            trend = "sideways"

    return TrendResult(
        trend=trend,
        ema_fast=round(ema_fast, 5),
        ema_mid=round(ema_mid, 5),
        ema_slow=round(ema_slow, 5),
        slope=round(slope, 6),
        slope_direction=slope_dir,
    )
