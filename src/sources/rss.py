"""
RSS парсер для сбора новостей из фидов.
"""

import feedparser
from datetime import datetime
from time import mktime
from dataclasses import dataclass


@dataclass
class RSSItem:
    title: str
    summary: str
    link: str
    published_at: datetime
    source: str
    author: str = None


class RSSParser:
    """Парсер RSS фидов."""

    def __init__(self, feeds: dict[str, str] = None):
        """
        Args:
            feeds: Словарь {название: url} RSS фидов
        """
        self.feeds = feeds or {}

    def add_feed(self, name: str, url: str):
        """Добавить RSS фид."""
        self.feeds[name] = url

    def parse_feed(self, url: str, source_name: str = "RSS") -> list[RSSItem]:
        """Парсить один RSS фид."""
        feed = feedparser.parse(url)
        items = []

        for entry in feed.entries:
            # Парсинг даты публикации
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime.fromtimestamp(mktime(entry.published_parsed))
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_at = datetime.fromtimestamp(mktime(entry.updated_parsed))
            else:
                published_at = datetime.now()

            # Получение summary
            summary = ""
            if hasattr(entry, 'summary'):
                summary = entry.summary
            elif hasattr(entry, 'description'):
                summary = entry.description

            items.append(RSSItem(
                title=entry.get('title', ''),
                summary=summary,
                link=entry.get('link', ''),
                published_at=published_at,
                source=source_name,
                author=entry.get('author'),
            ))

        return items

    def fetch_all(self) -> list[RSSItem]:
        """Получить новости из всех фидов."""
        all_items = []

        for name, url in self.feeds.items():
            try:
                items = self.parse_feed(url, source_name=name)
                all_items.extend(items)
            except Exception as e:
                print(f"Error fetching {name}: {e}")

        return all_items


# Примеры RSS фидов для технических новостей
DEFAULT_TECH_FEEDS = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "Hacker News": "https://hnrss.org/frontpage",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
}

# Примеры для велосипедной тематики
CYCLING_FEEDS = {
    "BikeRadar": "https://www.bikeradar.com/feed/",
    "CyclingTips": "https://cyclingtips.com/feed/",
    "Road.cc": "https://road.cc/feed",
}
