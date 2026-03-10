"""Scanner engine — orchestrates all analysis layers."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from analysis.candle_patterns import detect_candle_patterns
from analysis.chart_patterns import detect_chart_patterns
from analysis.indicators import compute_all, get_current_values
from analysis.models import IndicatorValues, ScanResult, TrendResult
from analysis.support_resistance import find_sr_levels
from analysis.trend import analyze_trend
from config import INSTRUMENTS
from data.fetcher import fetch_ohlcv
from forecast.models import ForecastResult
from sentiment.models import SentimentScore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FullScanResult:
    """Complete scan including sentiment and forecast."""
    scan: ScanResult
    sentiment: SentimentScore | None
    forecast_prophet: ForecastResult | None
    forecast_timesfm: ForecastResult | None


class ScannerEngine:
    """Runs all analysis layers for instruments."""

    def scan_technical(self, symbol: str, interval: str = "H4") -> ScanResult | None:
        """Run technical analysis only (fast)."""
        df = fetch_ohlcv(symbol, interval)
        if df is None or df.empty:
            logger.warning("No data for %s", symbol)
            return None

        df_ind = compute_all(df)
        indicators = get_current_values(df_ind)
        sr_levels = find_sr_levels(df)
        candle_pats = detect_candle_patterns(df)
        chart_pats = detect_chart_patterns(df)
        trend = analyze_trend(df)

        return ScanResult(
            symbol=symbol,
            price=round(float(df["Close"].iloc[-1]), 5),
            sr_levels=tuple(sr_levels),
            candle_patterns=tuple(candle_pats),
            chart_patterns=tuple(chart_pats),
            trend=trend,
            indicators=indicators,
            scanned_at=datetime.now(timezone.utc).isoformat(),
        )

    def scan_sentiment(self, symbol: str) -> SentimentScore | None:
        """Run sentiment analysis."""
        try:
            from sentiment.analyzer import analyze_sentiment
            return analyze_sentiment(symbol)
        except Exception:
            logger.exception("Sentiment scan failed for %s", symbol)
            return None

    def scan_forecast(self, symbol: str) -> tuple[ForecastResult | None, ForecastResult | None]:
        """Run forecast models. Returns (prophet, timesfm)."""
        df = fetch_ohlcv(symbol)
        if df is None or df.empty:
            return None, None

        prophet_result = None
        timesfm_result = None

        try:
            from forecast.prophet_forecast import predict_prophet
            prophet_result = predict_prophet(df)
        except Exception:
            logger.exception("Prophet forecast failed for %s", symbol)

        try:
            from forecast.timesfm_forecast import predict_timesfm
            timesfm_result = predict_timesfm(df)
        except Exception:
            logger.exception("TimesFM forecast failed for %s", symbol)

        return prophet_result, timesfm_result

    def scan_full(self, symbol: str) -> FullScanResult | None:
        """Run all layers for a single instrument."""
        scan = self.scan_technical(symbol)
        if scan is None:
            return None

        sentiment = self.scan_sentiment(symbol)
        prophet, timesfm = self.scan_forecast(symbol)

        return FullScanResult(
            scan=scan,
            sentiment=sentiment,
            forecast_prophet=prophet,
            forecast_timesfm=timesfm,
        )

    def scan_all_technical(self) -> dict[str, ScanResult | None]:
        """Fast scan: technical only for all instruments."""
        results = {}
        for symbol in INSTRUMENTS:
            try:
                results[symbol] = self.scan_technical(symbol)
            except Exception:
                logger.exception("Scan failed for %s", symbol)
                results[symbol] = None
        return results
