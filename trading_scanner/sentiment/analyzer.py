"""Sentiment analysis using HuggingFace FinBERT model."""

import logging

from config import NEWS_QUERIES, SENTIMENT_MAX_NEWS, SENTIMENT_MODEL
from sentiment.models import SentimentScore
from sentiment.news_scraper import scrape_news

logger = logging.getLogger(__name__)

_pipeline = None


def _get_pipeline():
    """Lazy-load the sentiment pipeline."""
    global _pipeline
    if _pipeline is None:
        from transformers import pipeline
        _pipeline = pipeline(
            "text-classification",
            model=SENTIMENT_MODEL,
            top_k=None,
            device=-1,  # CPU
        )
    return _pipeline


def analyze_sentiment(symbol: str) -> SentimentScore | None:
    """Analyze news sentiment for an instrument."""
    query = NEWS_QUERIES.get(symbol)
    if not query:
        return None

    news = scrape_news(query, SENTIMENT_MAX_NEWS)
    if not news:
        return None

    try:
        pipe = _get_pipeline()
        titles = [n.title for n in news if n.title.strip()]
        if not titles:
            return None

        results = pipe(titles)

        positive_count = 0
        negative_count = 0
        neutral_count = 0
        headlines = []

        for title, result in zip(titles, results):
            scores = {r["label"]: r["score"] for r in result}
            top_label = max(scores, key=scores.get)

            if top_label == "positive":
                positive_count += 1
                headlines.append((title, "positive"))
            elif top_label == "negative":
                negative_count += 1
                headlines.append((title, "negative"))
            else:
                neutral_count += 1
                headlines.append((title, "neutral"))

        total = len(titles)
        pos_ratio = positive_count / total
        neg_ratio = negative_count / total
        neu_ratio = neutral_count / total

        if pos_ratio > neg_ratio and pos_ratio > 0.4:
            overall = "bullish"
        elif neg_ratio > pos_ratio and neg_ratio > 0.4:
            overall = "bearish"
        else:
            overall = "neutral"

        return SentimentScore(
            positive=round(pos_ratio, 2),
            negative=round(neg_ratio, 2),
            neutral=round(neu_ratio, 2),
            overall=overall,
            headlines=tuple(headlines),
        )
    except Exception:
        logger.exception("Sentiment analysis failed for %s", symbol)
        return None
