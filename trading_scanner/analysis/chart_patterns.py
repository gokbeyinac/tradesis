"""Chart pattern detection — multi-bar patterns on OHLCV data."""

import logging

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

from analysis.models import ChartPattern
from config import (
    CHANNEL_LOOKBACK,
    CHART_PATTERN_LOOKBACK,
    DOUBLE_TOP_MIN_CORRECTION,
    DOUBLE_TOP_TOLERANCE,
    FLAG_POLE_MIN_MOVE,
    SWING_WINDOW,
    TRIANGLE_LOOKBACK,
    WEDGE_LOOKBACK,
)

logger = logging.getLogger(__name__)


def _get_swings(df: pd.DataFrame, window: int = SWING_WINDOW):
    """Return swing high/low indices and prices."""
    highs_idx = argrelextrema(df["High"].values, np.greater_equal, order=window)[0]
    lows_idx = argrelextrema(df["Low"].values, np.less_equal, order=window)[0]
    highs = [(int(i), float(df["High"].iloc[i])) for i in highs_idx]
    lows = [(int(i), float(df["Low"].iloc[i])) for i in lows_idx]
    return highs, lows


def _detect_double_top(
    highs: list[tuple[int, float]],
    lows: list[tuple[int, float]],
    df: pd.DataFrame,
) -> ChartPattern | None:
    """Double top: two peaks at similar level with correction between."""
    if len(highs) < 2:
        return None
    for i in range(len(highs) - 1):
        idx1, p1 = highs[i]
        idx2, p2 = highs[i + 1]
        if abs(p1 - p2) / p1 > DOUBLE_TOP_TOLERANCE:
            continue
        between_lows = [p for j, p in lows if idx1 < j < idx2]
        if not between_lows:
            continue
        correction = (max(p1, p2) - min(between_lows)) / max(p1, p2)
        if correction >= DOUBLE_TOP_MIN_CORRECTION:
            neckline = min(between_lows)
            target = neckline - (max(p1, p2) - neckline)
            return ChartPattern(
                "Double Top", "bearish", 0.8, idx1, idx2,
                target_price=round(target, 5),
            )
    return None


def _detect_double_bottom(
    highs: list[tuple[int, float]],
    lows: list[tuple[int, float]],
    df: pd.DataFrame,
) -> ChartPattern | None:
    """Double bottom: two troughs at similar level."""
    if len(lows) < 2:
        return None
    for i in range(len(lows) - 1):
        idx1, p1 = lows[i]
        idx2, p2 = lows[i + 1]
        if abs(p1 - p2) / max(p1, 0.0001) > DOUBLE_TOP_TOLERANCE:
            continue
        between_highs = [p for j, p in highs if idx1 < j < idx2]
        if not between_highs:
            continue
        correction = (max(between_highs) - min(p1, p2)) / max(max(between_highs), 0.0001)
        if correction >= DOUBLE_TOP_MIN_CORRECTION:
            neckline = max(between_highs)
            target = neckline + (neckline - min(p1, p2))
            return ChartPattern(
                "Double Bottom", "bullish", 0.8, idx1, idx2,
                target_price=round(target, 5),
            )
    return None


def _detect_head_shoulders(
    highs: list[tuple[int, float]],
    lows: list[tuple[int, float]],
    df: pd.DataFrame,
) -> ChartPattern | None:
    """Head and Shoulders pattern."""
    if len(highs) < 3:
        return None
    for i in range(len(highs) - 2):
        idx_l, p_l = highs[i]
        idx_h, p_h = highs[i + 1]
        idx_r, p_r = highs[i + 2]
        if p_h <= p_l or p_h <= p_r:
            continue
        if abs(p_l - p_r) / p_l > 0.03:
            continue
        shoulder_avg = (p_l + p_r) / 2
        if (p_h - shoulder_avg) / shoulder_avg < 0.02:
            continue
        return ChartPattern(
            "Head & Shoulders", "bearish", 0.85, idx_l, idx_r,
            target_price=round(shoulder_avg - (p_h - shoulder_avg), 5),
        )
    return None


def _detect_inv_head_shoulders(
    highs: list[tuple[int, float]],
    lows: list[tuple[int, float]],
    df: pd.DataFrame,
) -> ChartPattern | None:
    """Inverse Head and Shoulders."""
    if len(lows) < 3:
        return None
    for i in range(len(lows) - 2):
        idx_l, p_l = lows[i]
        idx_h, p_h = lows[i + 1]
        idx_r, p_r = lows[i + 2]
        if p_h >= p_l or p_h >= p_r:
            continue
        if abs(p_l - p_r) / max(p_l, 0.0001) > 0.03:
            continue
        shoulder_avg = (p_l + p_r) / 2
        if (shoulder_avg - p_h) / max(shoulder_avg, 0.0001) < 0.02:
            continue
        return ChartPattern(
            "Inv Head & Shoulders", "bullish", 0.85, idx_l, idx_r,
            target_price=round(shoulder_avg + (shoulder_avg - p_h), 5),
        )
    return None


def _detect_triangle(
    highs: list[tuple[int, float]],
    lows: list[tuple[int, float]],
    n: int,
) -> ChartPattern | None:
    """Ascending, descending, or symmetrical triangle."""
    lookback_start = n - TRIANGLE_LOOKBACK
    recent_highs = [(i, p) for i, p in highs if i >= lookback_start]
    recent_lows = [(i, p) for i, p in lows if i >= lookback_start]

    if len(recent_highs) < 2 or len(recent_lows) < 2:
        return None

    high_slope = (recent_highs[-1][1] - recent_highs[0][1]) / max(recent_highs[-1][0] - recent_highs[0][0], 1)
    low_slope = (recent_lows[-1][1] - recent_lows[0][1]) / max(recent_lows[-1][0] - recent_lows[0][0], 1)

    avg_price = (recent_highs[-1][1] + recent_lows[-1][1]) / 2
    h_norm = high_slope / avg_price if avg_price > 0 else 0
    l_norm = low_slope / avg_price if avg_price > 0 else 0

    start_idx = min(recent_highs[0][0], recent_lows[0][0])
    end_idx = max(recent_highs[-1][0], recent_lows[-1][0])

    if abs(h_norm) < 0.0002 and l_norm > 0.0002:
        return ChartPattern("Ascending Triangle", "bullish", 0.75, start_idx, end_idx)
    if h_norm < -0.0002 and abs(l_norm) < 0.0002:
        return ChartPattern("Descending Triangle", "bearish", 0.75, start_idx, end_idx)
    if h_norm < -0.0001 and l_norm > 0.0001:
        return ChartPattern("Symmetrical Triangle", "neutral", 0.65, start_idx, end_idx)

    return None


def _detect_channel(
    highs: list[tuple[int, float]],
    lows: list[tuple[int, float]],
    n: int,
) -> ChartPattern | None:
    """Rising, falling, or horizontal channel."""
    lookback_start = n - CHANNEL_LOOKBACK
    recent_highs = [(i, p) for i, p in highs if i >= lookback_start]
    recent_lows = [(i, p) for i, p in lows if i >= lookback_start]

    if len(recent_highs) < 2 or len(recent_lows) < 2:
        return None

    high_slope = (recent_highs[-1][1] - recent_highs[0][1]) / max(recent_highs[-1][0] - recent_highs[0][0], 1)
    low_slope = (recent_lows[-1][1] - recent_lows[0][1]) / max(recent_lows[-1][0] - recent_lows[0][0], 1)

    avg_price = (recent_highs[-1][1] + recent_lows[-1][1]) / 2
    h_norm = high_slope / avg_price if avg_price > 0 else 0
    l_norm = low_slope / avg_price if avg_price > 0 else 0

    if abs(h_norm - l_norm) > 0.0005:
        return None

    start_idx = min(recent_highs[0][0], recent_lows[0][0])
    end_idx = max(recent_highs[-1][0], recent_lows[-1][0])

    avg_slope = (h_norm + l_norm) / 2
    if avg_slope > 0.0002:
        return ChartPattern("Rising Channel", "bullish", 0.7, start_idx, end_idx)
    if avg_slope < -0.0002:
        return ChartPattern("Falling Channel", "bearish", 0.7, start_idx, end_idx)
    return ChartPattern("Horizontal Channel", "neutral", 0.65, start_idx, end_idx)


def _detect_flag(
    highs: list[tuple[int, float]],
    lows: list[tuple[int, float]],
    df: pd.DataFrame,
) -> ChartPattern | None:
    """Bull or bear flag."""
    n = len(df)
    if n < 20:
        return None

    pole_end = n - 10
    pole_start = max(0, pole_end - 15)

    pole_move = (float(df["Close"].iloc[pole_end]) - float(df["Close"].iloc[pole_start])) / float(df["Close"].iloc[pole_start])

    if abs(pole_move) < FLAG_POLE_MIN_MOVE:
        return None

    flag_data = df.iloc[pole_end:]
    if len(flag_data) < 5:
        return None

    flag_range = (flag_data["High"].max() - flag_data["Low"].min()) / flag_data["Close"].mean()
    if flag_range > abs(pole_move) * 0.5:
        return None

    if pole_move > 0:
        return ChartPattern("Bull Flag", "bullish", 0.7, pole_start, n - 1)
    return ChartPattern("Bear Flag", "bearish", 0.7, pole_start, n - 1)


def detect_chart_patterns(
    df: pd.DataFrame,
    lookback: int = CHART_PATTERN_LOOKBACK,
) -> list[ChartPattern]:
    """Scan for chart patterns in the data."""
    if df is None or len(df) < 20:
        return []

    window = df.tail(lookback)
    highs, lows = _get_swings(window)
    patterns = []

    detectors = [
        lambda: _detect_double_top(highs, lows, window),
        lambda: _detect_double_bottom(highs, lows, window),
        lambda: _detect_head_shoulders(highs, lows, window),
        lambda: _detect_inv_head_shoulders(highs, lows, window),
        lambda: _detect_triangle(highs, lows, len(window)),
        lambda: _detect_channel(highs, lows, len(window)),
        lambda: _detect_flag(highs, lows, window),
    ]

    for detect in detectors:
        try:
            result = detect()
            if result:
                patterns.append(result)
        except Exception:
            logger.exception("Chart pattern detection error")

    return patterns
