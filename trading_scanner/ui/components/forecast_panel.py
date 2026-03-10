"""Forecast panel — price prediction charts."""

import plotly.graph_objects as go
import streamlit as st

from forecast.models import ForecastResult
from ui.theme import BG_PRIMARY, BLUE, GREEN, TEXT_MUTED, YELLOW


def render_forecast(
    prophet: ForecastResult | None,
    timesfm: ForecastResult | None,
) -> None:
    """Render forecast chart with confidence intervals."""
    if prophet is None and timesfm is None:
        st.info("Tahmin verisi yok")
        return

    fig = go.Figure()

    for result, color, dash in [
        (prophet, BLUE, None),
        (timesfm, GREEN, "dash"),
    ]:
        if result is None:
            continue

        fig.add_trace(go.Scatter(
            x=list(result.dates),
            y=list(result.values),
            mode="lines+markers",
            name=result.model_name,
            line={"color": color, "dash": dash, "width": 1},
            marker={"size": 6, "color": color},
            hovertemplate="%{x}<br>Tahmin: %{y:.5f}<extra>" + result.model_name + "</extra>",
        ))

        fig.add_trace(go.Scatter(
            x=list(result.dates) + list(reversed(result.dates)),
            y=list(result.upper) + list(reversed(result.lower)),
            fill="toself",
            fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
            line={"width": 0},
            name=f"{result.model_name} CI",
            showlegend=False,
            hoverinfo="skip",
        ))

    # Compute y-axis range with fine tick steps
    all_vals = []
    for result in (prophet, timesfm):
        if result is not None:
            all_vals.extend(result.values)
            all_vals.extend(result.upper)
            all_vals.extend(result.lower)

    y_min = min(all_vals)
    y_max = max(all_vals)
    y_range_size = y_max - y_min
    # ~15-20 ticks for detailed price levels
    dtick = y_range_size / 20
    # Round dtick to a clean number
    import math
    magnitude = 10 ** math.floor(math.log10(max(dtick, 1e-10)))
    dtick = round(dtick / magnitude) * magnitude
    if dtick == 0:
        dtick = magnitude

    fig.update_layout(
        template="plotly_dark",
        height=500,
        paper_bgcolor=BG_PRIMARY,
        plot_bgcolor=BG_PRIMARY,
        margin={"l": 70, "r": 20, "t": 30, "b": 30},
        xaxis={"type": "category", "tickangle": -45, "nticks": 15},
        yaxis={
            "dtick": dtick,
            "tickformat": ".2f",
            "gridcolor": "#2d3139",
            "gridwidth": 1,
            "range": [y_min - dtick, y_max + dtick],
        },
        legend={"yanchor": "top", "y": 0.99, "xanchor": "left", "x": 0.01},
    )

    st.plotly_chart(fig, use_container_width=True)
