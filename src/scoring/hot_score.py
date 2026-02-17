"""
Hot Score Calculator - гибридный скоринг "горячести" новостей.

Веса сигналов:
- Свежесть: 0.25
- Виральность: 0.25
- Релевантность теме: 0.30
- Сентимент/провокативность: 0.10
- Уникальность: 0.10
"""

import math
from datetime import datetime, timezone
from dataclasses import dataclass


@dataclass
class NewsItem:
    title: str
    summary: str
    url: str
    published_at: datetime
    source: str
    shares: int = 0
    retweets: int = 0
    upvotes: int = 0
    sentiment: float = 0.0  # -1 to 1
    controversy: float = 0.0  # 0 to 1
    embedding: list = None


class HotScoreCalculator:
    """Калькулятор hot score для новостей."""

    WEIGHTS = {
        'freshness': 0.25,
        'virality': 0.25,
        'relevance': 0.30,
        'sentiment': 0.10,
        'uniqueness': 0.10,
    }

    # Нормализация виральности по источникам
    VIRALITY_NORMS = {
        'twitter': 1000,
        'reddit': 500,
        'newsapi': 100,
        'rss': 50,
    }

    def __init__(self, topic_embeddings: list = None):
        self.topic_embeddings = topic_embeddings or []
        self.published_embeddings = []

    def calculate_freshness(self, published_at: datetime) -> float:
        """Экспоненциальный decay: score = e^(-hours/12)."""
        now = datetime.now(timezone.utc)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        hours = (now - published_at).total_seconds() / 3600
        return math.exp(-hours / 12)

    def calculate_virality(self, item: NewsItem) -> float:
        """Нормализованная виральность по источнику."""
        norm = self.VIRALITY_NORMS.get(item.source, 100)
        total_engagement = item.shares + item.retweets + item.upvotes
        return min(1.0, total_engagement / norm)

    def calculate_relevance(self, item: NewsItem) -> float:
        """Cosine similarity к целевым темам."""
        if not item.embedding or not self.topic_embeddings:
            return 0.5  # Дефолт без embeddings

        from .embeddings import cosine_similarity

        max_sim = 0.0
        for topic_emb in self.topic_embeddings:
            sim = cosine_similarity(item.embedding, topic_emb)
            max_sim = max(max_sim, sim)

        return max_sim

    def calculate_sentiment_score(self, item: NewsItem) -> float:
        """Абсолютный sentiment + controversy."""
        # Нейтральные новости скучные, берём абсолютное значение
        return (abs(item.sentiment) + item.controversy) / 2

    def calculate_uniqueness(self, item: NewsItem) -> float:
        """1 - max similarity к уже опубликованным."""
        if not item.embedding or not self.published_embeddings:
            return 1.0

        from .embeddings import cosine_similarity

        max_sim = 0.0
        for pub_emb in self.published_embeddings:
            sim = cosine_similarity(item.embedding, pub_emb)
            max_sim = max(max_sim, sim)

        return 1.0 - max_sim

    def calculate(self, item: NewsItem) -> float:
        """Рассчитать итоговый hot score."""
        scores = {
            'freshness': self.calculate_freshness(item.published_at),
            'virality': self.calculate_virality(item),
            'relevance': self.calculate_relevance(item),
            'sentiment': self.calculate_sentiment_score(item),
            'uniqueness': self.calculate_uniqueness(item),
        }

        total = sum(scores[k] * self.WEIGHTS[k] for k in scores)
        return total

    def rank_news(self, items: list[NewsItem], top_n: int = 4) -> list[NewsItem]:
        """Отсортировать новости по hot score и вернуть топ-N."""
        scored = [(item, self.calculate(item)) for item in items]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored[:top_n]]

    def add_published(self, embedding: list):
        """Добавить embedding опубликованной новости."""
        self.published_embeddings.append(embedding)
