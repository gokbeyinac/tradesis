"""News scraping via GoogleNews."""

import logging

from sentiment.models import NewsItem

logger = logging.getLogger(__name__)


def scrape_news(query: str, max_results: int = 10) -> list[NewsItem]:
    """Fetch recent news for a search query."""
    try:
        from GoogleNews import GoogleNews

        gn = GoogleNews(lang="en", period="7d")
        gn.clear()
        gn.search(query)
        results = gn.results()

        items = []
        for r in results[:max_results]:
            items.append(NewsItem(
                title=r.get("title", ""),
                date=r.get("date", ""),
                source=r.get("media", ""),
                url=r.get("link", ""),
            ))
        return items
    except Exception:
        logger.exception("News scraping failed for query: %s", query)
        return []
