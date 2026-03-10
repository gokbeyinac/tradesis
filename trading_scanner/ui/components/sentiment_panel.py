"""Sentiment panel — news headlines and sentiment gauge."""

import streamlit as st

from sentiment.models import SentimentScore
from ui.theme import BG_CARD, BORDER, GREEN, RED, TEXT_MUTED, YELLOW


def render_sentiment(sentiment: SentimentScore | None) -> None:
    """Render sentiment analysis results."""
    if sentiment is None:
        st.info("Sentiment verisi yok")
        return

    # Overall gauge
    overall_color = GREEN if sentiment.overall == "bullish" else RED if sentiment.overall == "bearish" else YELLOW
    st.markdown(f"""
    <div style="background:{BG_CARD};border:1px solid {BORDER};border-radius:8px;padding:16px;margin-bottom:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="color:{overall_color};font-size:1.3em;font-weight:bold;">
                {sentiment.overall.upper()}
            </span>
            <span style="color:{TEXT_MUTED};">
                +{sentiment.positive:.0%} / -{sentiment.negative:.0%} / ~{sentiment.neutral:.0%}
            </span>
        </div>
        <div style="margin-top:8px;height:6px;border-radius:3px;background:#2d3139;overflow:hidden;display:flex;">
            <div style="width:{sentiment.positive*100}%;background:{GREEN};"></div>
            <div style="width:{sentiment.neutral*100}%;background:{YELLOW};"></div>
            <div style="width:{sentiment.negative*100}%;background:{RED};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Headlines
    for title, sent in sentiment.headlines:
        color = GREEN if sent == "positive" else RED if sent == "negative" else YELLOW
        icon = "+" if sent == "positive" else "-" if sent == "negative" else "~"
        st.markdown(f"""
        <div style="background:{BG_CARD};border-left:3px solid {color};padding:8px 12px;margin-bottom:4px;border-radius:0 4px 4px 0;">
            <span style="color:{color};font-weight:bold;">[{icon}]</span>
            <span style="color:#e0e0e0;font-size:0.9em;"> {title}</span>
        </div>
        """, unsafe_allow_html=True)
