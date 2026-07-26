import logging
from datetime import datetime, timezone
from typing import List, Optional
import feedparser
import httpx

logger = logging.getLogger(__name__)


class RSSNewsItem:
    """DTO for parsed RSS item data."""
    def __init__(self, title: str, url: str, summary: str, published_at: Optional[datetime] = None) -> None:
        self.title = title
        self.url = url
        self.summary = summary
        self.published_at = published_at or datetime.now(timezone.utc)


class RSSParser:
    """Parser for fetching and parsing RSS feeds from active sources."""

    async def fetch_feed(self, feed_url: str, limit: int = 20) -> List[RSSNewsItem]:
        """
        Asynchronously fetches an RSS feed and parses entries.
        """
        logger.info(f"Парсинг RSS потока: {feed_url}")
        items: List[RSSNewsItem] = []
        
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(feed_url)
                response.raise_for_status()
                content = response.text

            # feedparser синхронный, парсим полученный текст
            feed = feedparser.parse(content)
            
            for entry in feed.entries[:limit]:
                title = getattr(entry, "title", "Без названия")
                url = getattr(entry, "link", feed_url)
                summary = getattr(entry, "summary", getattr(entry, "description", title))
                
                # Парсинг даты публикации
                published_at = datetime.now(timezone.utc)
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    from time import mktime
                    published_at = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)

                items.append(RSSNewsItem(title=title, url=url, summary=summary, published_at=published_at))
                
        except Exception as exc:
            logger.error(f"Ошибка при парсинге RSS источника {feed_url}: {exc}")
            
        return items