"""Streamlit Trading Scanner Dashboard."""

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import INSTRUMENTS
from data.fetcher import fetch_ohlcv, invalidate_cache
from scanner.engine import ScannerEngine
from ui.components.chart import render_candlestick
from ui.components.forecast_panel import render_forecast
from ui.components.journal_panel import render_journal, render_statistics
from ui.components.sentiment_panel import render_sentiment
from ui.components.signals_panel import render_indicators, render_patterns
from ui.theme import THEME_CSS, TREND_EMOJIS, TREND_LABELS

# Forex pairs need 5 decimal places, indices need 2
FOREX_PAIRS = {"EURUSD", "GBPUSD"}


def _format_price(symbol: str, price: float) -> str:
    if symbol in FOREX_PAIRS:
        return f"{price:.5f}"
    return f"{price:,.2f}"


# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Trading Scanner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(THEME_CSS, unsafe_allow_html=True)

engine = ScannerEngine()

# ── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Trading Scanner")
    st.caption(f"Son guncelleme: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if st.button("Yenile", use_container_width=True):
        invalidate_cache()
        st.cache_data.clear()
        st.rerun()

    page = st.radio("Navigasyon", ["Scanner", "Journal", "Statistics"], label_visibility="collapsed")

    n_bars = st.slider("Gosterilecek mum sayisi", 30, 200, 100)

# ── Scanner page ─────────────────────────────────────────────────────────────

if page == "Scanner":

    @st.cache_data(ttl=900)
    def _scan_all():
        return engine.scan_all_technical()

    scans = _scan_all()

    # Summary cards
    cols = st.columns(len(INSTRUMENTS))
    for idx, symbol in enumerate(INSTRUMENTS):
        scan = scans.get(symbol)
        with cols[idx]:
            if scan is None:
                st.error(f"{symbol}: veri yok")
                continue

            label, css_class = TREND_LABELS.get(scan.trend.trend, ("?", "neutral"))
            emoji = TREND_EMOJIS.get(scan.trend.trend, "")
            alerts = [l for l in scan.sr_levels if l.proximity_alert]

            # Most recent pattern (highest bar_index)
            latest_pat = ""
            latest_pat_color = "#ffd740"
            if scan.candle_patterns:
                newest = max(scan.candle_patterns, key=lambda p: p.bar_index)
                latest_pat = newest.pattern
                latest_pat_color = "#00c853" if newest.direction == "bullish" else "#ff1744" if newest.direction == "bearish" else "#ffd740"

            # Short-term momentum
            short_label = label
            if scan.indicators.rsi > 50 and scan.indicators.macd_histogram > 0:
                if scan.trend.trend in ("weak_bearish", "strong_bearish"):
                    short_label = f"{label} (toparlanma)"
            elif scan.indicators.rsi < 50 and scan.indicators.macd_histogram < 0:
                if scan.trend.trend in ("weak_bullish", "strong_bullish"):
                    short_label = f"{label} (zayiflama)"

            price_str = _format_price(symbol, scan.price)

            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size:0.9em;color:#8b8d93;">{symbol}</div>
                <div class="price-text">{price_str}</div>
                <div class="{css_class}">{emoji} {short_label}</div>
                {"<div class='alert-badge'>⚠️ S/R yakin</div>" if alerts else ""}
                {"<div style='color:" + latest_pat_color + ";font-size:0.85em;'>🕯️ " + latest_pat + "</div>" if latest_pat else ""}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Detail panel
    available = [s for s in INSTRUMENTS if scans.get(s) is not None]
    selected = st.selectbox("Detay", available)

    if selected:
        scan = scans[selected]

        # Timeframe selector
        tf = st.radio("Timeframe", ["H4", "H1"], horizontal=True, key="tf_select")

        df = fetch_ohlcv(selected, interval=tf)

        if df is not None:
            # Re-analyze if H1
            if tf == "H1":
                scan_tf = engine.scan_technical(selected, interval="H1")
                if scan_tf is not None:
                    scan = scan_tf

            # Chart
            render_candlestick(
                df,
                list(scan.sr_levels),
                list(scan.candle_patterns),
                list(scan.chart_patterns),
                n_bars=n_bars,
            )

            # Indicators + Patterns
            col1, col2 = st.columns([3, 2])
            with col1:
                st.subheader("Sinyal Analizi")
                render_indicators(scan.indicators, scan.trend, scan.price)

                st.subheader("S/R Seviyeleri")
                if scan.sr_levels:
                    import pandas as pd
                    fmt = ".5f" if selected in FOREX_PAIRS else ".2f"
                    sr_data = [
                        {"Tip": l.type, "Fiyat": format(l.price, fmt), "Test": l.test_count,
                         "Guc": l.strength, "Alert": "⚠️" if l.proximity_alert else ""}
                        for l in scan.sr_levels
                    ]
                    st.dataframe(pd.DataFrame(sr_data), use_container_width=True, hide_index=True)

            with col2:
                st.subheader("Formasyonlar")
                render_patterns(scan, df)

            # Sentiment & Forecast
            st.markdown("---")
            sent_col, fore_col = st.columns(2)

            with sent_col:
                st.subheader("Haber Sentimenti")
                if st.button("Sentiment Analizi Calistir", key="sent_btn"):
                    with st.spinner("Haberler analiz ediliyor..."):
                        sentiment = engine.scan_sentiment(selected)
                        st.session_state["sentiment_result"] = sentiment

                if "sentiment_result" in st.session_state:
                    render_sentiment(st.session_state["sentiment_result"])

            with fore_col:
                st.subheader("Fiyat Tahmini (Prophet)")
                if st.button("Tahmin Calistir", key="fore_btn"):
                    with st.spinner("Tahmin hesaplaniyor..."):
                        from forecast.prophet_forecast import predict_prophet
                        fresh_df = fetch_ohlcv(selected)
                        prophet = predict_prophet(fresh_df) if fresh_df is not None else None
                        st.session_state["forecast_result"] = (prophet, None)

                if "forecast_result" in st.session_state:
                    prophet, timesfm = st.session_state["forecast_result"]
                    render_forecast(prophet, timesfm)


# ── Journal page ─────────────────────────────────────────────────────────────

elif page == "Journal":
    st.header("Trade Journal")
    render_journal()

# ── Statistics page ──────────────────────────────────────────────────────────

elif page == "Statistics":
    st.header("Istatistikler")
    render_statistics()
