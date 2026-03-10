"""Sentiment analysis models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NewsItem:
    """Single news article."""
    title: str
    date: str
    source: str
    url: str


@dataclass(frozen=True)
class SentimentScore:
    """Aggregated sentiment for an instrument."""
    positive: float      # 0.0 - 1.0
    negative: float
    neutral: float
    overall: str         # "bullish" | "bearish" | "neutral"
    headlines: tuple[tuple[str, str], ...]  # (title, sentiment)
