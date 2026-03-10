"""Trading Scanner configuration — all parameters managed here."""

from dataclasses import dataclass


# ── Instruments ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class InstrumentConfig:
    name: str
    tv_symbol: str
    exchange: str
    tolerance: float = 0.003  # S/R tolerance band


INSTRUMENTS: dict[str, InstrumentConfig] = {
    "US30": InstrumentConfig("US30", "US30", "TRADENATION"),
    "US500": InstrumentConfig("US500", "US500", "TRADENATION"),
    "DE40": InstrumentConfig("DE40", "DE40", "TRADENATION"),
    "EURUSD": InstrumentConfig("EURUSD", "EURUSD", "TRADENATION"),
    "GBPUSD": InstrumentConfig("GBPUSD", "GBPUSD", "TRADENATION"),
}

# News search queries per instrument
NEWS_QUERIES: dict[str, str] = {
    "US30": "Dow Jones US30 stock market",
    "US500": "S&P 500 stock market",
    "DE40": "DAX 40 German stock market",
    "EURUSD": "EUR USD forex",
    "GBPUSD": "GBP USD forex pound dollar",
}

# ── Data ─────────────────────────────────────────────────────────────────────

CACHE_TTL_HOURS = 4
H4_TARGET_BARS = 500
H1_TARGET_BARS = 800

# ── Support / Resistance ────────────────────────────────────────────────────

SR_TOLERANCE = 0.003        # ±0.3%
SR_MIN_TESTS = 2
SR_STRONG_TESTS = 3
PROXIMITY_ALERT = 0.01      # 1%
SWING_WINDOW = 5

# ── Indicators ──────────────────────────────────────────────────────────────

RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2.5
STOCH_K = 14
STOCH_D = 3
CCI_PERIOD = 20
CMF_PERIOD = 20

# ── EMA ─────────────────────────────────────────────────────────────────────

EMA_FAST = 20
EMA_MID = 50
EMA_SLOW = 200
TREND_SLOPE_LOOKBACK = 20

# ── Candle Patterns ─────────────────────────────────────────────────────────

PIN_BAR_RATIO = 0.70
STRONG_CANDLE_BODY_RATIO = 0.60
DOJI_MAX_BODY_RATIO = 0.10
TWEEZER_TOLERANCE = 0.001   # 0.1%

# ── Chart Patterns ──────────────────────────────────────────────────────────

CHART_PATTERN_LOOKBACK = 100
DOUBLE_TOP_TOLERANCE = 0.005
DOUBLE_TOP_MIN_CORRECTION = 0.03
CUP_DEPTH_MIN = 0.10
CUP_DEPTH_MAX = 0.30
FLAG_POLE_MIN_MOVE = 0.03
WEDGE_LOOKBACK = 25
TRIANGLE_LOOKBACK = 25
CHANNEL_LOOKBACK = 30

# ── Sentiment ───────────────────────────────────────────────────────────────

SENTIMENT_MODEL = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
SENTIMENT_MAX_NEWS = 10
SENTIMENT_CACHE_TTL_HOURS = 4

# ── Forecast ────────────────────────────────────────────────────────────────

FORECAST_HORIZON = 30
TIMESFM_MODEL = "google/timesfm-2.0-500m-pytorch"
