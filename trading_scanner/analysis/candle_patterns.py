"""Candlestick pattern detection — pure functions."""

import pandas as pd

from analysis.models import CandlePattern
from config import DOJI_MAX_BODY_RATIO, PIN_BAR_RATIO, STRONG_CANDLE_BODY_RATIO, TWEEZER_TOLERANCE


def _body(row: pd.Series) -> float:
    return abs(row["Close"] - row["Open"])


def _range(row: pd.Series) -> float:
    return row["High"] - row["Low"]


def _body_ratio(row: pd.Series) -> float:
    r = _range(row)
    return _body(row) / r if r > 0 else 0


def _is_bullish(row: pd.Series) -> bool:
    return row["Close"] > row["Open"]


def _upper_wick(row: pd.Series) -> float:
    return row["High"] - max(row["Close"], row["Open"])


def _lower_wick(row: pd.Series) -> float:
    return min(row["Close"], row["Open"]) - row["Low"]


def _detect_doji(row: pd.Series, idx: int, offset: int) -> CandlePattern | None:
    if _body_ratio(row) <= DOJI_MAX_BODY_RATIO and _range(row) > 0:
        uw = _upper_wick(row)
        lw = _lower_wick(row)
        r = _range(row)
        if uw / r > 0.4 and lw < r * 0.1:
            name = "Gravestone Doji"
        elif lw / r > 0.4 and uw < r * 0.1:
            name = "Dragonfly Doji"
        elif uw / r > 0.3 and lw / r > 0.3:
            name = "Long-Legged Doji"
        else:
            name = "Doji"
        return CandlePattern(name, "neutral", 0.7, idx, offset)
    return None


def _detect_pin_bar(row: pd.Series, idx: int, offset: int) -> CandlePattern | None:
    r = _range(row)
    if r == 0:
        return None
    lw = _lower_wick(row)
    uw = _upper_wick(row)
    body = _body(row)

    if lw / r >= PIN_BAR_RATIO and body / r < 0.2:
        return CandlePattern("Bullish Pin Bar", "bullish", 0.8, idx, offset)
    if uw / r >= PIN_BAR_RATIO and body / r < 0.2:
        return CandlePattern("Bearish Pin Bar", "bearish", 0.8, idx, offset)
    return None


def _detect_hammer(row: pd.Series, idx: int, offset: int) -> CandlePattern | None:
    r = _range(row)
    if r == 0:
        return None
    lw = _lower_wick(row)
    uw = _upper_wick(row)
    body = _body(row)

    if lw >= body * 2 and uw < body * 0.5 and body / r > 0.15:
        return CandlePattern("Hammer", "bullish", 0.75, idx, offset)
    if uw >= body * 2 and lw < body * 0.5 and body / r > 0.15:
        return CandlePattern("Shooting Star", "bearish", 0.75, idx, offset)
    return None


def _detect_engulfing(prev: pd.Series, curr: pd.Series, idx: int, offset: int) -> CandlePattern | None:
    prev_body = _body(prev)
    curr_body = _body(curr)
    if curr_body <= prev_body:
        return None

    if not _is_bullish(prev) and _is_bullish(curr):
        if curr["Open"] <= prev["Close"] and curr["Close"] >= prev["Open"]:
            return CandlePattern("Bullish Engulfing", "bullish", 0.85, idx, offset)

    if _is_bullish(prev) and not _is_bullish(curr):
        if curr["Open"] >= prev["Close"] and curr["Close"] <= prev["Open"]:
            return CandlePattern("Bearish Engulfing", "bearish", 0.85, idx, offset)
    return None


def _detect_inside_bar(prev: pd.Series, curr: pd.Series, idx: int, offset: int) -> CandlePattern | None:
    if curr["High"] <= prev["High"] and curr["Low"] >= prev["Low"]:
        return CandlePattern("Inside Bar", "neutral", 0.6, idx, offset)
    return None


def _detect_morning_evening_star(
    bar1: pd.Series, bar2: pd.Series, bar3: pd.Series, idx: int, offset: int,
) -> CandlePattern | None:
    b1_body = _body(bar1)
    b2_body = _body(bar2)
    b3_body = _body(bar3)

    if b1_body == 0 or b3_body == 0:
        return None

    small_body = b2_body < b1_body * 0.3

    if not _is_bullish(bar1) and small_body and _is_bullish(bar3) and b3_body > b1_body * 0.5:
        return CandlePattern("Morning Star", "bullish", 0.85, idx, offset)

    if _is_bullish(bar1) and small_body and not _is_bullish(bar3) and b3_body > b1_body * 0.5:
        return CandlePattern("Evening Star", "bearish", 0.85, idx, offset)
    return None


def _detect_tweezer(prev: pd.Series, curr: pd.Series, idx: int, offset: int) -> CandlePattern | None:
    high_match = abs(prev["High"] - curr["High"]) / prev["High"] <= TWEEZER_TOLERANCE
    low_match = abs(prev["Low"] - curr["Low"]) / max(prev["Low"], 0.0001) <= TWEEZER_TOLERANCE

    if high_match and _is_bullish(prev) and not _is_bullish(curr):
        return CandlePattern("Tweezer Top", "bearish", 0.7, idx, offset)
    if low_match and not _is_bullish(prev) and _is_bullish(curr):
        return CandlePattern("Tweezer Bottom", "bullish", 0.7, idx, offset)
    return None


def detect_candle_patterns(df: pd.DataFrame, lookback: int = 10) -> list[CandlePattern]:
    """Scan last N bars for candlestick patterns."""
    patterns = []
    n = len(df)
    start = max(0, n - lookback)

    for i in range(start, n):
        offset = i - (n - 1)
        row = df.iloc[i]

        for detector in (_detect_doji, _detect_pin_bar, _detect_hammer):
            result = detector(row, i, offset)
            if result:
                patterns.append(result)

        if i >= 1:
            prev = df.iloc[i - 1]
            for detector in (_detect_engulfing, _detect_inside_bar, _detect_tweezer):
                result = detector(prev, row, i, offset)
                if result:
                    patterns.append(result)

        if i >= 2:
            result = _detect_morning_evening_star(
                df.iloc[i - 2], df.iloc[i - 1], row, i, offset,
            )
            if result:
                patterns.append(result)

    return patterns
