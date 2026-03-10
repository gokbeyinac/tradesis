"""Candlestick chart using TradingView lightweight-charts."""

import pandas as pd
import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts

from ui.theme import BG_PRIMARY


COLOR_GREEN = "rgba(0, 200, 83, 1)"
COLOR_RED = "rgba(255, 23, 68, 1)"
COLOR_YELLOW = "rgba(255, 215, 64, 1)"
COLOR_GREEN_T = "rgba(0, 200, 83, 0.4)"
COLOR_RED_T = "rgba(255, 23, 68, 0.4)"


def _to_unix(dt) -> int:
    return int(dt.timestamp())


def render_candlestick(
    df: pd.DataFrame,
    sr_levels: list,
    candle_patterns: list,
    chart_patterns: list,
    n_bars: int = 100,
) -> None:
    """Render TradingView-style candlestick chart."""
    display_df = df.tail(n_bars)
    display_start = len(df) - len(display_df)

    # Candle data with unix timestamps
    candle_data = []
    for idx, row in display_df.iterrows():
        candle_data.append({
            "time": _to_unix(idx),
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
        })

    # One marker per bar — keep highest confidence pattern only
    bar_best: dict[int, object] = {}
    for pat in candle_patterns:
        disp_idx = pat.bar_index - display_start
        if 0 <= disp_idx < len(display_df):
            existing = bar_best.get(disp_idx)
            if existing is None or pat.confidence > existing.confidence:
                bar_best[disp_idx] = pat

    markers = []
    for disp_idx, pat in bar_best.items():
        dt = display_df.index[disp_idx]

        if pat.direction == "bearish":
            markers.append({
                "time": _to_unix(dt),
                "position": "aboveBar",
                "color": COLOR_RED,
                "shape": "arrowDown",
                "text": pat.pattern,
            })
        elif pat.direction == "bullish":
            markers.append({
                "time": _to_unix(dt),
                "position": "belowBar",
                "color": COLOR_GREEN,
                "shape": "arrowUp",
                "text": pat.pattern,
            })
        else:
            markers.append({
                "time": _to_unix(dt),
                "position": "aboveBar",
                "color": COLOR_YELLOW,
                "shape": "circle",
                "text": pat.pattern,
            })

    # Sort markers by time (required by lightweight-charts)
    markers.sort(key=lambda m: m["time"])

    # S/R price lines
    price_lines = []
    for level in sr_levels:
        if level.strength == "medium":
            color = COLOR_YELLOW
        elif level.type == "resistance":
            color = COLOR_RED
        else:
            color = COLOR_GREEN

        price_lines.append({
            "price": level.price,
            "color": color,
            "lineWidth": 1,
            "lineStyle": 2,
            "axisLabelVisible": True,
            "title": f"{level.type[0].upper()} ({level.test_count}x)",
        })

    # Chart config
    chart_options = {
        "height": 550,
        "layout": {
            "background": {"color": BG_PRIMARY},
            "textColor": "#8b8d93",
        },
        "grid": {
            "vertLines": {"color": "#1e222d"},
            "horzLines": {"color": "#1e222d"},
        },
        "crosshair": {
            "mode": 0,
        },
        "timeScale": {
            "timeVisible": True,
            "secondsVisible": False,
        },
    }

    series = [{
        "type": "Candlestick",
        "data": candle_data,
        "options": {
            "upColor": COLOR_GREEN,
            "downColor": COLOR_RED,
            "borderUpColor": COLOR_GREEN,
            "borderDownColor": COLOR_RED,
            "wickUpColor": COLOR_GREEN_T,
            "wickDownColor": COLOR_RED_T,
        },
        "markers": markers,
        "priceLines": price_lines,
    }]

    renderLightweightCharts([{
        "chart": chart_options,
        "series": series,
    }], key=f"chart_{n_bars}")
