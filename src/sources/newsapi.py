"""
NewsAPI.org клиент для сбора новостей.
Бесплатный tier: 100 запросов/день.
"""

import os
from datetime import datetime, timedelta
import requests
from dataclasses import dataclass


@dataclass
class NewsArticle:
    title: str
    description: str
    url: str
    published_at: datetime
    source_name: str
    author: str = None
    content: str = None


class NewsAPIClient:
    """Клиент для NewsAPI.org."""

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('NEWSAPI_KEY')
        if not self.api_key:
            raise ValueError("NEWSAPI_KEY is required")

    def _request(self, endpoint: str, params: dict) -> dict:
        """Выполнить запрос к API."""
        params['apiKey'] = self.api_key
        response = requests.get(f"{self.BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()

    def search_news(
        self,
        query: str,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20,
        from_date: datetime = None,
    ) -> list[NewsArticle]:
        """
        Поиск новостей по ключевым словам.

        Args:
            query: Поисковый запрос
            language: Язык (en, ru, etc)
            sort_by: Сортировка (publishedAt, relevancy, popularity)
            page_size: Количество результатов (макс 100)
            from_date: Новости не старше этой даты
        """
        if from_date is None:
            from_date = datetime.now() - timedelta(days=1)

        params = {
            'q': query,
            'language': language,
            'sortBy': sort_by,
            'pageSize': page_size,
            'from': from_date.isoformat(),
        }

        data = self._request('everything', params)

        articles = []
        for item in data.get('articles', []):
            try:
                published_at = datetime.fromisoformat(
                    item['publishedAt'].replace('Z', '+00:00')
                )
            except (ValueError, TypeError):
                continue

            articles.append(NewsArticle(
                title=item.get('title', ''),
                description=item.get('description', ''),
                url=item.get('url', ''),
                published_at=published_at,
                source_name=item.get('source', {}).get('name', 'Unknown'),
                author=item.get('author'),
                content=item.get('content'),
            ))

        return articles

    def get_top_headlines(
        self,
        category: str = None,
        country: str = "us",
        query: str = None,
        page_size: int = 20,
    ) -> list[NewsArticle]:
        """
        Получить топ заголовки.

        Args:
            category: business, entertainment, health, science, sports, technology
            country: Код страны (us, gb, ru, etc)
            query: Фильтр по ключевым словам
            page_size: Количество результатов
        """
        params = {
            'country': country,
            'pageSize': page_size,
        }

        if category:
            params['category'] = category
        if query:
            params['q'] = query

        data = self._request('top-headlines', params)

        articles = []
        for item in data.get('articles', []):
            try:
                published_at = datetime.fromisoformat(
                    item['publishedAt'].replace('Z', '+00:00')
                )
            except (ValueError, TypeError):
                continue

            articles.append(NewsArticle(
                title=item.get('title', ''),
                description=item.get('description', ''),
                url=item.get('url', ''),
                published_at=published_at,
                source_name=item.get('source', {}).get('name', 'Unknown'),
                author=item.get('author'),
                content=item.get('content'),
            ))

        return articles
