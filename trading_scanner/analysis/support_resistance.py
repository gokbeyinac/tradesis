"""Support/Resistance level detection using pivot clustering."""

import logging

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

from analysis.models import SRLevel
from config import (
    PROXIMITY_ALERT,
    SR_MIN_TESTS,
    SR_STRONG_TESTS,
    SR_TOLERANCE,
    SWING_WINDOW,
)

logger = logging.getLogger(__name__)


def _find_pivots(df: pd.DataFrame, window: int = SWING_WINDOW) -> tuple[np.ndarray, np.ndarray]:
    """Find swing highs and swing lows."""
    highs_idx = argrelextrema(df["High"].values, np.greater_equal, order=window)[0]
    lows_idx = argrelextrema(df["Low"].values, np.less_equal, order=window)[0]
    return highs_idx, lows_idx


def _cluster_levels(
    prices: list[tuple[float, int]],
    tolerance: float,
) -> list[dict]:
    """Cluster nearby prices into S/R levels."""
    if not prices:
        return []

    sorted_prices = sorted(prices, key=lambda x: x[0])
    clusters: list[list[tuple[float, int]]] = []
    current_cluster: list[tuple[float, int]] = [sorted_prices[0]]

    for price, idx in sorted_prices[1:]:
        cluster_avg = np.mean([p for p, _ in current_cluster])
        if abs(price - cluster_avg) / cluster_avg <= tolerance:
            current_cluster.append((price, idx))
        else:
            clusters.append(current_cluster)
            current_cluster = [(price, idx)]
    clusters.append(current_cluster)

    return [
        {
            "price": float(np.mean([p for p, _ in c])),
            "test_count": len(c),
            "last_test_idx": max(i for _, i in c),
        }
        for c in clusters
        if len(c) >= SR_MIN_TESTS
    ]


def find_sr_levels(
    df: pd.DataFrame,
    tolerance: float = SR_TOLERANCE,
) -> list[SRLevel]:
    """Detect support and resistance levels from OHLCV data."""
    if df is None or len(df) < SWING_WINDOW * 2:
        return []

    highs_idx, lows_idx = _find_pivots(df)
    current_price = float(df["Close"].iloc[-1])

    resistance_prices = [(float(df["High"].iloc[i]), i) for i in highs_idx]
    support_prices = [(float(df["Low"].iloc[i]), i) for i in lows_idx]

    resistance_clusters = _cluster_levels(resistance_prices, tolerance)
    support_clusters = _cluster_levels(support_prices, tolerance)

    levels = []

    for cluster in resistance_clusters:
        price = cluster["price"]
        if price <= current_price:
            continue
        proximity = abs(price - current_price) / current_price
        levels.append(SRLevel(
            price=round(price, 5),
            type="resistance",
            test_count=cluster["test_count"],
            strength="strong" if cluster["test_count"] >= SR_STRONG_TESTS else "medium",
            last_test=str(df.index[cluster["last_test_idx"]]),
            proximity_alert=proximity <= PROXIMITY_ALERT,
        ))

    for cluster in support_clusters:
        price = cluster["price"]
        if price >= current_price:
            continue
        proximity = abs(price - current_price) / current_price
        levels.append(SRLevel(
            price=round(price, 5),
            type="support",
            test_count=cluster["test_count"],
            strength="strong" if cluster["test_count"] >= SR_STRONG_TESTS else "medium",
            last_test=str(df.index[cluster["last_test_idx"]]),
            proximity_alert=proximity <= PROXIMITY_ALERT,
        ))

    return sorted(levels, key=lambda x: x.price, reverse=True)
