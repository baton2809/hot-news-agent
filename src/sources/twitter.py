"""
Twitter/X API клиент для сбора trending и новостей.
Basic tier: читать можно, постить 1500 твитов/мес.
"""

import os
from datetime import datetime
from dataclasses import dataclass
import tweepy


@dataclass
class Tweet:
    id: str
    text: str
    created_at: datetime
    author_id: str
    author_username: str
    retweet_count: int = 0
    like_count: int = 0
    reply_count: int = 0
    quote_count: int = 0


class TwitterClient:
    """Клиент для Twitter/X API v2."""

    def __init__(
        self,
        bearer_token: str = None,
        consumer_key: str = None,
        consumer_secret: str = None,
        access_token: str = None,
        access_token_secret: str = None,
    ):
        self.bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
        self.consumer_key = consumer_key or os.getenv('TWITTER_CONSUMER_KEY')
        self.consumer_secret = consumer_secret or os.getenv('TWITTER_CONSUMER_SECRET')
        self.access_token = access_token or os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = access_token_secret or os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

        # Client для чтения (bearer token)
        self.client = tweepy.Client(
            bearer_token=self.bearer_token,
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token=self.access_token,
            access_token_secret=self.access_token_secret,
        )

    def search_recent(
        self,
        query: str,
        max_results: int = 20,
    ) -> list[Tweet]:
        """
        Поиск недавних твитов (последние 7 дней).

        Args:
            query: Поисковый запрос (поддерживает операторы Twitter)
            max_results: Количество результатов (10-100)
        """
        response = self.client.search_recent_tweets(
            query=query,
            max_results=max_results,
            tweet_fields=['created_at', 'public_metrics', 'author_id'],
            expansions=['author_id'],
            user_fields=['username'],
        )

        if not response.data:
            return []

        # Маппинг author_id -> username
        users = {u.id: u.username for u in (response.includes.get('users') or [])}

        tweets = []
        for tweet in response.data:
            metrics = tweet.public_metrics or {}
            tweets.append(Tweet(
                id=tweet.id,
                text=tweet.text,
                created_at=tweet.created_at,
                author_id=tweet.author_id,
                author_username=users.get(tweet.author_id, ''),
                retweet_count=metrics.get('retweet_count', 0),
                like_count=metrics.get('like_count', 0),
                reply_count=metrics.get('reply_count', 0),
                quote_count=metrics.get('quote_count', 0),
            ))

        return tweets

    def get_user_tweets(
        self,
        username: str,
        max_results: int = 10,
    ) -> list[Tweet]:
        """Получить твиты пользователя."""
        # Сначала получаем user_id
        user = self.client.get_user(username=username)
        if not user.data:
            return []

        response = self.client.get_users_tweets(
            id=user.data.id,
            max_results=max_results,
            tweet_fields=['created_at', 'public_metrics'],
        )

        if not response.data:
            return []

        tweets = []
        for tweet in response.data:
            metrics = tweet.public_metrics or {}
            tweets.append(Tweet(
                id=tweet.id,
                text=tweet.text,
                created_at=tweet.created_at,
                author_id=user.data.id,
                author_username=username,
                retweet_count=metrics.get('retweet_count', 0),
                like_count=metrics.get('like_count', 0),
                reply_count=metrics.get('reply_count', 0),
                quote_count=metrics.get('quote_count', 0),
            ))

        return tweets
