"""Technical indicators — pure functions operating on DataFrames."""

import numpy as np
import pandas as pd

from analysis.models import IndicatorValues
from config import (
    BB_PERIOD, BB_STD,
    CCI_PERIOD, CMF_PERIOD,
    MACD_FAST, MACD_SIGNAL, MACD_SLOW,
    RSI_PERIOD,
    STOCH_D, STOCH_K,
)


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(
    series: pd.Series,
    fast: int = MACD_FAST,
    slow: int = MACD_SLOW,
    signal: int = MACD_SIGNAL,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD line, signal line, histogram."""
    macd_line = ema(series, fast) - ema(series, slow)
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(
    series: pd.Series,
    period: int = BB_PERIOD,
    std_dev: float = BB_STD,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Upper, middle, lower Bollinger Bands."""
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return upper, middle, lower


def stochastic(
    df: pd.DataFrame,
    k_period: int = STOCH_K,
    d_period: int = STOCH_D,
) -> tuple[pd.Series, pd.Series]:
    """%K and %D Stochastic Oscillator."""
    low_min = df["Low"].rolling(window=k_period).min()
    high_max = df["High"].rolling(window=k_period).max()
    k = 100 * (df["Close"] - low_min) / (high_max - low_min).replace(0, np.nan)
    d = sma(k, d_period)
    return k, d


def cci(df: pd.DataFrame, period: int = CCI_PERIOD) -> pd.Series:
    """Commodity Channel Index."""
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    tp_sma = sma(tp, period)
    mean_dev = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - tp_sma) / (0.015 * mean_dev).replace(0, np.nan)


def cmf(df: pd.DataFrame, period: int = CMF_PERIOD) -> pd.Series:
    """Chaikin Money Flow."""
    high_low = (df["High"] - df["Low"]).replace(0, np.nan)
    mfm = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / high_low
    mfv = mfm * df["Volume"]
    return mfv.rolling(window=period).sum() / df["Volume"].rolling(window=period).sum().replace(0, np.nan)


def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    """Add all indicator columns to DataFrame. Returns new DataFrame."""
    result = df.copy()

    result["EMA_20"] = ema(df["Close"], 20)
    result["EMA_50"] = ema(df["Close"], 50)
    result["EMA_200"] = ema(df["Close"], 200)

    result["RSI"] = rsi(df["Close"])

    macd_line, signal_line, histogram = macd(df["Close"])
    result["MACD"] = macd_line
    result["MACD_Signal"] = signal_line
    result["MACD_Hist"] = histogram

    bb_upper, bb_middle, bb_lower = bollinger_bands(df["Close"])
    result["BB_Upper"] = bb_upper
    result["BB_Middle"] = bb_middle
    result["BB_Lower"] = bb_lower

    k, d = stochastic(df)
    result["Stoch_K"] = k
    result["Stoch_D"] = d

    result["CCI"] = cci(df)
    result["CMF"] = cmf(df)

    return result


def get_current_values(df_with_indicators: pd.DataFrame) -> IndicatorValues:
    """Extract latest indicator readings."""
    last = df_with_indicators.iloc[-1]
    return IndicatorValues(
        rsi=round(float(last.get("RSI", 50)), 2),
        macd=round(float(last.get("MACD", 0)), 6),
        macd_signal=round(float(last.get("MACD_Signal", 0)), 6),
        macd_histogram=round(float(last.get("MACD_Hist", 0)), 6),
        bb_upper=round(float(last.get("BB_Upper", 0)), 5),
        bb_middle=round(float(last.get("BB_Middle", 0)), 5),
        bb_lower=round(float(last.get("BB_Lower", 0)), 5),
        stoch_k=round(float(last.get("Stoch_K", 50)), 2),
        stoch_d=round(float(last.get("Stoch_D", 50)), 2),
        cci=round(float(last.get("CCI", 0)), 2),
        cmf=round(float(last.get("CMF", 0)), 4),
    )
