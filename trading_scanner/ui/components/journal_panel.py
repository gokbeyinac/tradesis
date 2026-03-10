"""Journal panel — trade log and statistics."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import INSTRUMENTS
from journal.db import JournalDB
from ui.theme import BG_PRIMARY, BLUE, GREEN, RED, YELLOW

_journal = JournalDB()


def render_journal() -> None:
    """Render trade journal tab."""
    with st.expander("Yeni Trade Ekle", expanded=False):
        with st.form("new_trade"):
            c1, c2, c3 = st.columns(3)
            with c1:
                j_date = st.date_input("Tarih")
                j_instrument = st.selectbox("Enstruman", list(INSTRUMENTS.keys()))
                j_direction = st.selectbox("Yon", ["long", "short"])
            with c2:
                j_entry = st.number_input("Entry Price", format="%.5f")
                j_sl = st.number_input("Stop Loss", format="%.5f")
                j_tp = st.number_input("Take Profit", format="%.5f")
            with c3:
                j_candle = st.text_input("Mum Formasyonu")
                j_chart = st.text_input("Grafik Formasyonu")
                j_trend = st.text_input("Trend")
                j_notes = st.text_area("Notlar")

            if st.form_submit_button("Kaydet"):
                rr = 0.0
                if j_sl and j_entry and j_tp and j_sl != j_entry:
                    rr = abs(j_tp - j_entry) / abs(j_entry - j_sl)

                _journal.add_trade({
                    "date": str(j_date),
                    "instrument": j_instrument,
                    "direction": j_direction,
                    "entry_price": j_entry or None,
                    "stop_loss": j_sl or None,
                    "take_profit": j_tp or None,
                    "risk_reward": round(rr, 2),
                    "candle_pattern": j_candle or None,
                    "chart_pattern": j_chart or None,
                    "trend": j_trend or None,
                    "result": "open",
                    "notes": j_notes or None,
                })
                st.success("Trade kaydedildi")

    trades_df = _journal.get_all()
    if trades_df.empty:
        st.info("Henuz trade kaydedilmedi")
        return

    # Open trades
    open_trades = trades_df[trades_df["result"] == "open"]
    if not open_trades.empty:
        st.subheader("Acik Pozisyonlar")
        st.dataframe(open_trades, use_container_width=True, hide_index=True)

        with st.form("update_trade"):
            uc1, uc2, uc3 = st.columns(3)
            with uc1:
                u_id = st.number_input("Trade ID", min_value=1, step=1)
            with uc2:
                u_result = st.selectbox("Sonuc", ["win", "loss", "breakeven"])
            with uc3:
                u_pnl = st.number_input("PnL (pips)", format="%.1f")

            if st.form_submit_button("Guncelle"):
                _journal.update_result(int(u_id), u_result, u_pnl)
                st.success("Trade guncellendi")
                st.rerun()

    st.subheader("Tum Trade'ler")
    st.dataframe(trades_df, use_container_width=True, hide_index=True)


def render_statistics() -> None:
    """Render trade statistics."""
    stats = _journal.get_statistics()

    if stats["total_trades"] == 0:
        st.info("Yeterli veri yok. Trade kaydetmeye baslayin.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Trade", stats["total_trades"])
    c2.metric("Win Rate", f"{stats['win_rate']}%")
    c3.metric("Win / Loss", f"{stats['wins']} / {stats['losses']}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Enstruman Performansi")
        if stats["by_instrument"]:
            inst_df = pd.DataFrame(list(stats["by_instrument"].items()), columns=["Instrument", "Win Rate %"])
            fig = go.Figure(go.Bar(x=inst_df["Instrument"], y=inst_df["Win Rate %"], marker_color=BLUE))
            fig.update_layout(template="plotly_dark", paper_bgcolor=BG_PRIMARY, plot_bgcolor=BG_PRIMARY, height=300)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Formasyon Win Rate")
        if stats["by_candle_pattern"]:
            cp_df = pd.DataFrame(list(stats["by_candle_pattern"].items()), columns=["Pattern", "Win Rate %"])
            fig = go.Figure(go.Bar(x=cp_df["Pattern"], y=cp_df["Win Rate %"], marker_color=YELLOW))
            fig.update_layout(template="plotly_dark", paper_bgcolor=BG_PRIMARY, plot_bgcolor=BG_PRIMARY, height=300)
            st.plotly_chart(fig, use_container_width=True)
