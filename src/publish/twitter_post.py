"""
Twitter Publisher - публикация постов в Twitter/X.
Basic tier: 1500 твитов/мес.
"""

import os
from dataclasses import dataclass
from datetime import datetime
import tweepy


@dataclass
class PublishResult:
    success: bool
    tweet_id: str = None
    tweet_url: str = None
    error: str = None
    published_at: datetime = None


class TwitterPublisher:
    """Публикатор постов в Twitter."""

    def __init__(
        self,
        consumer_key: str = None,
        consumer_secret: str = None,
        access_token: str = None,
        access_token_secret: str = None,
    ):
        self.consumer_key = consumer_key or os.getenv('TWITTER_CONSUMER_KEY')
        self.consumer_secret = consumer_secret or os.getenv('TWITTER_CONSUMER_SECRET')
        self.access_token = access_token or os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = access_token_secret or os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

        self.client = tweepy.Client(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
        )

        self._username = None

    @property
    def username(self) -> str:
        """Получить username текущего аккаунта."""
        if self._username is None:
            me = self.client.get_me()
            self._username = me.data.username if me.data else None
        return self._username

    def post(self, text: str, reply_to: str = None) -> PublishResult:
        """
        Опубликовать твит.

        Args:
            text: Текст твита (макс 280 символов)
            reply_to: ID твита для ответа (опционально)
        """
        if len(text) > 280:
            return PublishResult(
                success=False,
                error=f"Tweet too long: {len(text)} chars (max 280)"
            )

        try:
            params = {"text": text}
            if reply_to:
                params["in_reply_to_tweet_id"] = reply_to

            response = self.client.create_tweet(**params)

            tweet_id = response.data['id']
            tweet_url = f"https://twitter.com/{self.username}/status/{tweet_id}"

            return PublishResult(
                success=True,
                tweet_id=tweet_id,
                tweet_url=tweet_url,
                published_at=datetime.now(),
            )

        except tweepy.TweepyException as e:
            return PublishResult(
                success=False,
                error=str(e),
            )

    def post_with_link(self, text: str, url: str) -> PublishResult:
        """Опубликовать твит со ссылкой."""
        # Twitter считает ссылки как 23 символа
        max_text_length = 280 - 24  # 23 для ссылки + 1 пробел

        if len(text) > max_text_length:
            text = text[:max_text_length - 3] + "..."

        full_text = f"{text} {url}"
        return self.post(full_text)

    def get_tweet_metrics(self, tweet_id: str) -> dict:
        """Получить метрики твита для обратной связи."""
        response = self.client.get_tweet(
            tweet_id,
            tweet_fields=['public_metrics', 'created_at'],
        )

        if not response.data:
            return {}

        metrics = response.data.public_metrics or {}
        return {
            'likes': metrics.get('like_count', 0),
            'retweets': metrics.get('retweet_count', 0),
            'replies': metrics.get('reply_count', 0),
            'quotes': metrics.get('quote_count', 0),
            'impressions': metrics.get('impression_count', 0),
        }


class DryRunPublisher:
    """Тестовый публикатор для проверки без реальной отправки."""

    def __init__(self):
        self.published = []

    def post(self, text: str, reply_to: str = None) -> PublishResult:
        """Симуляция публикации."""
        fake_id = f"dry_run_{len(self.published)}"

        result = PublishResult(
            success=True,
            tweet_id=fake_id,
            tweet_url=f"https://twitter.com/test/status/{fake_id}",
            published_at=datetime.now(),
        )

        self.published.append({
            'text': text,
            'reply_to': reply_to,
            'result': result,
        })

        print(f"[DRY RUN] Would post: {text[:50]}...")
        return result
