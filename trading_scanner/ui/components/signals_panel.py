"""Signals panel — patterns, indicators, trend display with context."""

import pandas as pd
import streamlit as st

from analysis.models import IndicatorValues, ScanResult, TrendResult
from ui.theme import BG_CARD, BORDER, GREEN, RED, TEXT_MUTED, TEXT_SECONDARY, YELLOW

# ── Pattern descriptions ─────────────────────────────────────────────────────

PATTERN_DESC = {
    "Bullish Engulfing": "Onceki kirmizi mumu tamamen yutuyor. Guclu alis sinyali — dususten yukselise donus.",
    "Bearish Engulfing": "Onceki yesil mumu tamamen yutuyor. Guclu satis sinyali — yukselisten dususe donus.",
    "Hammer": "Uzun alt fitil, kucuk govde. Saticilar baskiydi ama alicilar geri aldi. Dipta donus sinyali.",
    "Shooting Star": "Uzun ust fitil, kucuk govde. Alicilar yukseltti ama saticilar geri aldi. Tepede donus sinyali.",
    "Doji": "Acilis ve kapanis neredeyse esit. Kararsizlik — trend degisimi olabilir.",
    "Long-Legged Doji": "Cok uzun fitiller. Sert kararsizlik — buyuk hareket oncesi sinyal.",
    "Gravestone Doji": "Uzun ust fitil, sifir alt fitil. Tepede olusursa guclu satis sinyali.",
    "Dragonfly Doji": "Uzun alt fitil, sifir ust fitil. Dipte olusursa guclu alis sinyali.",
    "Bullish Pin Bar": "Cok uzun alt fitil (%70+). Sert red — fiyat asagi gitmek istemedi.",
    "Bearish Pin Bar": "Cok uzun ust fitil (%70+). Sert red — fiyat yukari gitmek istemedi.",
    "Inside Bar": "Onceki mumun icinde kaldi. Sikisma — kirilim yonunde islem ac.",
    "Morning Star": "3 mumlu donus: kirmizi + kucuk govde + yesil. Guclu yukselis sinyali.",
    "Evening Star": "3 mumlu donus: yesil + kucuk govde + kirmizi. Guclu dusus sinyali.",
    "Tweezer Top": "Iki ardisik mum ayni tepede. Direnc testi basarisiz — satis sinyali.",
    "Tweezer Bottom": "Iki ardisik mum ayni dipte. Destek testi basarili — alis sinyali.",
    "Double Top": "Iki kez ayni tepeye temas. Guclu direnc — dusus beklenir.",
    "Double Bottom": "Iki kez ayni dibe temas. Guclu destek — yukselis beklenir.",
    "Head & Shoulders": "Omuz-Bas-Omuz. Klasik donus formasyonu — dusus beklenir.",
    "Inv Head & Shoulders": "Ters OBO. Klasik donus formasyonu — yukselis beklenir.",
    "Ascending Triangle": "Duz ust, yukselen alt. Alis baskisi artiyor — yukari kirilim beklenir.",
    "Descending Triangle": "Duz alt, dusen ust. Satis baskisi artiyor — asagi kirilim beklenir.",
    "Symmetrical Triangle": "Daralan ucgen. Kirilim yonu belirsiz — bekle ve kirilimi takip et.",
    "Rising Channel": "Paralel yukselis kanali. Trend devam ediyor.",
    "Falling Channel": "Paralel dusus kanali. Trend devam ediyor.",
    "Horizontal Channel": "Yatay kanal. Bant ticareti — destek al, direnc sat.",
    "Bull Flag": "Yukselis sonrasi kucuk geri cekilme. Devam formasyonu — yukselis devam edecek.",
    "Bear Flag": "Dusus sonrasi kucuk toparlanma. Devam formasyonu — dusus devam edecek.",
}

# ── Indicator signal interpretation ──────────────────────────────────────────

def _interpret_indicators(ind: IndicatorValues, trend: TrendResult, price: float) -> dict:
    """Interpret indicators and produce a summary signal."""
    signals = []  # (name, direction, explanation)

    # RSI
    if ind.rsi > 70:
        signals.append(("RSI", "bearish", f"Asiri alim ({ind.rsi:.0f}) — geri cekilme riski"))
    elif ind.rsi < 30:
        signals.append(("RSI", "bullish", f"Asiri satim ({ind.rsi:.0f}) — toparlanma beklenir"))
    else:
        zone = "notral bolge" if 40 <= ind.rsi <= 60 else ("alis yonlu" if ind.rsi > 50 else "satis yonlu")
        signals.append(("RSI", "neutral", f"{ind.rsi:.0f} — {zone}"))

    # Stochastic
    if ind.stoch_k > 80:
        signals.append(("Stoch", "bearish", f"Asiri alim (%K={ind.stoch_k:.0f}) — tepe riski"))
    elif ind.stoch_k < 20:
        signals.append(("Stoch", "bullish", f"Asiri satim (%K={ind.stoch_k:.0f}) — dip firsati"))
    else:
        signals.append(("Stoch", "neutral", f"%K={ind.stoch_k:.0f} — notral"))

    # MACD
    if ind.macd_histogram > 0:
        signals.append(("MACD", "bullish", f"Pozitif histogram ({ind.macd_histogram:.4f}) — yukselis momenti"))
    else:
        signals.append(("MACD", "bearish", f"Negatif histogram ({ind.macd_histogram:.4f}) — dusus momenti"))

    # CCI
    if ind.cci > 100:
        signals.append(("CCI", "bearish", f"Asiri alim ({ind.cci:.0f}) — geri cekilme riski"))
    elif ind.cci < -100:
        signals.append(("CCI", "bullish", f"Asiri satim ({ind.cci:.0f}) — toparlanma beklenir"))
    else:
        signals.append(("CCI", "neutral", f"{ind.cci:.0f} — notral"))

    # CMF
    if ind.cmf > 0.05:
        signals.append(("CMF", "bullish", f"Guclu alis baskisi ({ind.cmf:.4f})"))
    elif ind.cmf < -0.05:
        signals.append(("CMF", "bearish", f"Guclu satis baskisi ({ind.cmf:.4f})"))
    else:
        signals.append(("CMF", "neutral", f"Zayif akis ({ind.cmf:.4f})"))

    # Bollinger Bands
    if price >= ind.bb_upper:
        signals.append(("BB", "bearish", f"Fiyat ust bandin ustunde — asiri genisleme"))
    elif price <= ind.bb_lower:
        signals.append(("BB", "bullish", f"Fiyat alt bandin altinda — toparlanma beklenir"))
    else:
        bb_pos = (price - ind.bb_lower) / (ind.bb_upper - ind.bb_lower) * 100 if ind.bb_upper != ind.bb_lower else 50
        signals.append(("BB", "neutral", f"Bant icinde (%{bb_pos:.0f} seviye)"))

    # Overall score
    bullish = sum(1 for _, d, _ in signals if d == "bullish")
    bearish = sum(1 for _, d, _ in signals if d == "bearish")

    if bullish >= 4:
        overall = ("GUCLU ALIS", "bullish")
    elif bullish >= 3 and bearish <= 1:
        overall = ("ALIS", "bullish")
    elif bearish >= 4:
        overall = ("GUCLU SATIS", "bearish")
    elif bearish >= 3 and bullish <= 1:
        overall = ("SATIS", "bearish")
    else:
        # Check for divergence
        if bullish >= 2 and bearish >= 2:
            overall = ("KARISIK SINYAL", "neutral")
        else:
            overall = ("BEKLE", "neutral")

    # Divergence detection
    divergences = []
    rsi_dir = next((d for n, d, _ in signals if n == "RSI"), "neutral")
    macd_dir = next((d for n, d, _ in signals if n == "MACD"), "neutral")
    stoch_dir = next((d for n, d, _ in signals if n == "Stoch"), "neutral")

    if rsi_dir != macd_dir and rsi_dir != "neutral" and macd_dir != "neutral":
        divergences.append(f"RSI ({rsi_dir}) vs MACD ({macd_dir}) uyumsuzluk — dikkat!")
    if stoch_dir == "bearish" and macd_dir == "bullish":
        divergences.append("Stoch asiri alimda ama MACD yukselis diyor — kisa vadede geri cekilme, orta vadede yukselis")
    if stoch_dir == "bullish" and macd_dir == "bearish":
        divergences.append("Stoch asiri satimda ama MACD dusus diyor — kisa vadede sekme, orta vadede dusus")

    return {
        "signals": signals,
        "overall": overall,
        "divergences": divergences,
        "bullish_count": bullish,
        "bearish_count": bearish,
    }


# ── Tooltip CSS ──────────────────────────────────────────────────────────────

TOOLTIP_CSS = """
<style>
.info-tooltip-wrap:hover .info-tooltip-text {
    visibility: visible !important;
    opacity: 1 !important;
}
</style>
"""


# ── Render functions ─────────────────────────────────────────────────────────

def render_indicators(indicators: IndicatorValues, trend: TrendResult, price: float) -> None:
    """Render indicator summary with signal interpretation."""
    st.markdown(TOOLTIP_CSS, unsafe_allow_html=True)

    interp = _interpret_indicators(indicators, trend, price)
    overall_label, overall_dir = interp["overall"]
    overall_color = GREEN if overall_dir == "bullish" else RED if overall_dir == "bearish" else YELLOW

    # Overall signal badge
    st.markdown(f"""
    <div style="background:{BG_CARD};border:2px solid {overall_color};border-radius:10px;padding:14px;margin-bottom:12px;text-align:center;">
        <div style="color:{TEXT_MUTED};font-size:0.8em;">Genel Sinyal</div>
        <div style="color:{overall_color};font-size:1.6em;font-weight:bold;">{overall_label}</div>
        <div style="color:{TEXT_MUTED};font-size:0.8em;margin-top:4px;">
            {interp["bullish_count"]} alis / {interp["bearish_count"]} satis sinyali
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Divergence warnings
    for div in interp["divergences"]:
        st.markdown(f"""
        <div style="background:#ff17441a;border:1px solid {YELLOW};border-radius:6px;padding:8px 12px;margin-bottom:8px;">
            <span style="color:{YELLOW};font-weight:bold;">⚠️ Uyumsuzluk:</span>
            <span style="color:#e0e0e0;font-size:0.9em;"> {div}</span>
        </div>
        """, unsafe_allow_html=True)

    # Individual signals
    for name, direction, explanation in interp["signals"]:
        color = GREEN if direction == "bullish" else RED if direction == "bearish" else TEXT_SECONDARY
        icon = "▲" if direction == "bullish" else "▼" if direction == "bearish" else "●"
        st.markdown(f"""
        <div style="background:{BG_CARD};border-left:3px solid {color};padding:6px 12px;margin-bottom:4px;border-radius:0 6px 6px 0;display:flex;justify-content:space-between;align-items:center;">
            <span style="color:{color};font-weight:bold;font-size:0.9em;">{icon} {name}</span>
            <span style="color:#e0e0e0;font-size:0.85em;">{explanation}</span>
        </div>
        """, unsafe_allow_html=True)


def render_patterns(scan: ScanResult, df: pd.DataFrame) -> None:
    """Render detected patterns with context."""
    all_pats = list(scan.candle_patterns) + list(scan.chart_patterns)
    if not all_pats:
        st.info("Formasyon tespit edilmedi")
        return

    # Sort by bar index descending (newest first = right to left on chart)
    all_pats.sort(key=lambda p: getattr(p, "bar_index", getattr(p, "end_index", 0)), reverse=True)

    for pat in all_pats:
        name = pat.pattern
        direction = pat.direction
        conf = pat.confidence
        color = GREEN if direction == "bullish" else RED if direction == "bearish" else YELLOW
        desc = PATTERN_DESC.get(name, "")

        # Get time and price context from DataFrame
        bar_idx = getattr(pat, "bar_index", None) or getattr(pat, "end_index", None)
        time_str = ""
        price_str = ""
        if bar_idx is not None and 0 <= bar_idx < len(df):
            row = df.iloc[bar_idx]
            time_str = str(df.index[bar_idx].strftime("%m/%d %H:%M"))
            price_str = f"O:{row['Open']:.2f} H:{row['High']:.2f} L:{row['Low']:.2f} C:{row['Close']:.2f}"

        # Offset label
        offset = getattr(pat, "bar_offset", None)
        if offset is not None:
            if offset == 0:
                when = "Son mum"
            elif offset == -1:
                when = "1 mum once"
            else:
                when = f"{abs(offset)} mum once"
        else:
            when = ""

        action = "ALIS yonu" if direction == "bullish" else "SATIS yonu" if direction == "bearish" else "BEKLE"

        st.markdown(f"""
        <div style="background:{BG_CARD};border-left:4px solid {color};border-radius:0 8px 8px 0;padding:12px;margin-bottom:8px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                <span style="color:{color};font-weight:bold;font-size:1.05em;">{name}</span>
                <span style="background:{color}22;color:{color};padding:2px 8px;border-radius:4px;font-size:0.8em;font-weight:bold;">{action}</span>
            </div>
            <div style="color:#e0e0e0;font-size:0.85em;margin-bottom:6px;">{desc}</div>
            <div style="display:flex;gap:16px;color:{TEXT_MUTED};font-size:0.78em;">
                <span>📍 {when} ({time_str})</span>
                <span>💰 {price_str}</span>
                <span>🎯 Guven: {conf:.0%}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
