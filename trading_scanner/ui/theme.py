"""Dark theme constants and CSS."""

BG_PRIMARY = "#0e1117"
BG_CARD = "#1a1d23"
BORDER = "#2d3139"
TEXT_MUTED = "#8b8d93"
TEXT_SECONDARY = "#b0b3b8"

GREEN = "#00c853"
RED = "#ff1744"
YELLOW = "#ffd740"
BLUE = "#42a5f5"

THEME_CSS = f"""
<style>
    .stApp {{ background-color: {BG_PRIMARY}; }}
    .metric-card {{
        background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 8px;
        padding: 16px; text-align: center;
    }}
    .price-text {{ font-family: 'Courier New', monospace; font-size: 1.4em; font-weight: bold; }}
    .bullish {{ color: {GREEN}; }}
    .bearish {{ color: {RED}; }}
    .neutral {{ color: {YELLOW}; }}
    .alert-badge {{
        background: {RED}1a; border: 1px solid {RED}; border-radius: 4px;
        padding: 2px 8px; font-size: 0.8em; color: {RED};
    }}
    .sentiment-pos {{ color: {GREEN}; font-weight: bold; }}
    .sentiment-neg {{ color: {RED}; font-weight: bold; }}
    .sentiment-neu {{ color: {YELLOW}; }}
    .indicator-card {{
        background: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 6px;
        padding: 10px; text-align: center; margin-bottom: 4px;
    }}
</style>
"""

TREND_LABELS = {
    "strong_bullish": ("STRONG BULL", "bullish"),
    "weak_bullish": ("WEAK BULL", "bullish"),
    "strong_bearish": ("STRONG BEAR", "bearish"),
    "weak_bearish": ("WEAK BEAR", "bearish"),
    "sideways": ("SIDEWAYS", "neutral"),
}

TREND_EMOJIS = {
    "strong_bullish": "📈",
    "weak_bullish": "↗️",
    "strong_bearish": "📉",
    "weak_bearish": "↘️",
    "sideways": "➡️",
}
