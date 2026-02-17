"""Тесты для hot score калькулятора."""

import pytest
from datetime import datetime, timezone, timedelta

from src.scoring.hot_score import HotScoreCalculator, NewsItem


class TestHotScoreCalculator:
    """Тесты для HotScoreCalculator."""

    def setup_method(self):
        self.calculator = HotScoreCalculator()

    def test_freshness_new_article(self):
        """Свежая статья должна иметь высокий freshness score."""
        now = datetime.now(timezone.utc)
        score = self.calculator.calculate_freshness(now)
        assert score > 0.9

    def test_freshness_old_article(self):
        """Старая статья (24ч) должна иметь низкий freshness score."""
        old = datetime.now(timezone.utc) - timedelta(hours=24)
        score = self.calculator.calculate_freshness(old)
        assert score < 0.2

    def test_freshness_decay(self):
        """Score должен уменьшаться со временем."""
        now = datetime.now(timezone.utc)
        score_now = self.calculator.calculate_freshness(now)
        score_6h = self.calculator.calculate_freshness(now - timedelta(hours=6))
        score_12h = self.calculator.calculate_freshness(now - timedelta(hours=12))

        assert score_now > score_6h > score_12h

    def test_virality_normalization(self):
        """Виральность нормализуется по источнику."""
        item_twitter = NewsItem(
            title="Test",
            summary="Test",
            url="http://test.com",
            published_at=datetime.now(timezone.utc),
            source="twitter",
            retweets=500,
        )
        item_rss = NewsItem(
            title="Test",
            summary="Test",
            url="http://test.com",
            published_at=datetime.now(timezone.utc),
            source="rss",
            shares=25,
        )

        score_twitter = self.calculator.calculate_virality(item_twitter)
        score_rss = self.calculator.calculate_virality(item_rss)

        assert score_twitter == 0.5  # 500/1000
        assert score_rss == 0.5  # 25/50

    def test_calculate_returns_score(self):
        """calculate() должен возвращать score между 0 и 1."""
        item = NewsItem(
            title="Test News",
            summary="Test summary",
            url="http://test.com",
            published_at=datetime.now(timezone.utc),
            source="newsapi",
            shares=50,
            sentiment=0.5,
            controversy=0.3,
        )

        score = self.calculator.calculate(item)
        assert 0 <= score <= 1

    def test_rank_news_returns_top_n(self):
        """rank_news() должен возвращать top N новостей."""
        items = [
            NewsItem(
                title=f"News {i}",
                summary="Summary",
                url=f"http://test.com/{i}",
                published_at=datetime.now(timezone.utc) - timedelta(hours=i),
                source="newsapi",
            )
            for i in range(10)
        ]

        top_3 = self.calculator.rank_news(items, top_n=3)
        assert len(top_3) == 3


class TestCosinesimilarity:
    """Тесты для cosine similarity."""

    def test_identical_vectors(self):
        from src.scoring.embeddings import cosine_similarity

        vec = [1.0, 2.0, 3.0]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        from src.scoring.embeddings import cosine_similarity

        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        assert cosine_similarity(vec1, vec2) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        from src.scoring.embeddings import cosine_similarity

        vec1 = [1.0, 2.0]
        vec2 = [-1.0, -2.0]
        assert cosine_similarity(vec1, vec2) == pytest.approx(-1.0)
