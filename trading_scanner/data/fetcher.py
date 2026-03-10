"""OHLCV data fetcher using TradingView via tvDatafeed."""

import logging

import pandas as pd
from tvDatafeed import Interval as TvInterval, TvDatafeed

from config import (
    CACHE_TTL_HOURS,
    H4_TARGET_BARS,
    H1_TARGET_BARS,
    INSTRUMENTS,
    InstrumentConfig,
)
from data.cache import CacheStore

logger = logging.getLogger(__name__)

_TV_INTERVALS = {
    "H4": TvInterval.in_4_hour,
    "H1": TvInterval.in_1_hour,
}

_cache = CacheStore()
_tv: TvDatafeed | None = None


def _get_tv() -> TvDatafeed:
    global _tv
    if _tv is None:
        _tv = TvDatafeed()
    return _tv


def _standardize(df: pd.DataFrame) -> pd.DataFrame:
    """Rename tvDatafeed columns to standard OHLCV."""
    col_map = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }
    renamed = df.rename(columns=col_map)
    keep = [c for c in ("Open", "High", "Low", "Close", "Volume") if c in renamed.columns]
    return renamed[keep]


def _fetch_tv(
    instrument: InstrumentConfig,
    interval_key: str,
    n_bars: int,
) -> pd.DataFrame | None:
    """Fetch data from TradingView."""
    try:
        tv = _get_tv()
        df = tv.get_hist(
            symbol=instrument.tv_symbol,
            exchange=instrument.exchange,
            interval=_TV_INTERVALS[interval_key],
            n_bars=n_bars,
        )
        if df is None or df.empty:
            logger.warning("No data for %s@%s", instrument.tv_symbol, instrument.exchange)
            return None
        return _standardize(df)
    except Exception:
        logger.exception("Fetch failed for %s@%s", instrument.tv_symbol, instrument.exchange)
        return None


def fetch_ohlcv(symbol: str, interval: str = "H4") -> pd.DataFrame | None:
    """Fetch OHLCV data with cache. Returns DataFrame with OHLCV columns."""
    instrument = INSTRUMENTS.get(symbol)
    if instrument is None:
        logger.error("Unknown instrument: %s", symbol)
        return None

    cache_key = f"{interval}_{symbol}"
    cached = _cache.get(cache_key, CACHE_TTL_HOURS)
    if cached is not None:
        return cached

    n_bars = H4_TARGET_BARS if interval == "H4" else H1_TARGET_BARS
    df = _fetch_tv(instrument, interval, n_bars)
    if df is not None:
        _cache.set(cache_key, df)
    return df


def fetch_all(interval: str = "H4") -> dict[str, pd.DataFrame | None]:
    """Fetch data for all configured instruments."""
    results = {}
    for symbol in INSTRUMENTS:
        try:
            results[symbol] = fetch_ohlcv(symbol, interval)
        except Exception:
            logger.exception("Error fetching %s", symbol)
            results[symbol] = None
    return results


def invalidate_cache(symbol: str | None = None) -> None:
    """Clear cache for a symbol or all."""
    if symbol:
        _cache.invalidate(f"H4_{symbol}")
        _cache.invalidate(f"H1_{symbol}")
    else:
        _cache.clear()
