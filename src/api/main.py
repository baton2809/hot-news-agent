"""
FastAPI сервер для скоринга и рерайта новостей.
Используется n8n workflow через HTTP Request ноды.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os

# Импорты из нашего кода
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scoring.hot_score import HotScoreCalculator, NewsItem
from scoring.embeddings import get_embedding
from rewrite.llm_rewriter import LLMRewriter

app = FastAPI(title="News Curator API", version="1.0.0")

# CORS для n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные объекты
scorer = HotScoreCalculator()
rewriter = LLMRewriter()


class NewsItemRequest(BaseModel):
    """Модель для входящей новости."""
    title: str
    summary: str
    url: str
    published_at: str  # ISO format
    source: str
    shares: int = 0
    retweets: int = 0
    upvotes: int = 0


class ScoredNewsItem(BaseModel):
    """Модель для новости с hot score."""
    title: str
    summary: str
    url: str
    published_at: str
    source: str
    hot_score: float
    freshness: float
    virality: float
    relevance: float
    sentiment: float
    uniqueness: float


class ScoreRequest(BaseModel):
    """Запрос на скоринг."""
    news: List[NewsItemRequest]
    topic_keywords: List[str] = []
    top_n: int = 3


class RewriteRequest(BaseModel):
    """Запрос на рерайт."""
    title: str
    summary: str
    url: str
    topic: str = "bicycle insurance"


class RewriteResponse(BaseModel):
    """Ответ рерайта."""
    tweet: str
    sentiment: float
    controversy: float
    length: int


@app.get("/")
def root():
    """Health check."""
    return {
        "status": "ok",
        "service": "News Curator API",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "openai_key": "set" if os.getenv("OPENAI_API_KEY") else "missing",
        "scorer": "ready",
        "rewriter": "ready"
    }


@app.post("/score", response_model=List[ScoredNewsItem])
async def score_news(request: ScoreRequest):
    """
    Скоринг новостей с полными 5 сигналами.

    Возвращает топ-N новостей по hot_score.
    """
    try:
        # Получить embeddings для темы (если указаны keywords)
        if request.topic_keywords:
            topic_text = " ".join(request.topic_keywords)
            topic_embedding = get_embedding(topic_text)
            scorer.topic_embeddings = [topic_embedding]

        # Конвертировать входные данные в NewsItem
        news_items = []
        for item in request.news:
            # Парсинг даты
            try:
                published_at = datetime.fromisoformat(item.published_at.replace('Z', '+00:00'))
            except:
                published_at = datetime.now()

            # Получить embedding для новости
            text = f"{item.title} {item.summary}"
            embedding = get_embedding(text)

            news_item = NewsItem(
                title=item.title,
                summary=item.summary,
                url=item.url,
                published_at=published_at,
                source=item.source.lower(),
                shares=item.shares,
                retweets=item.retweets,
                upvotes=item.upvotes,
                embedding=embedding
            )
            news_items.append(news_item)

        # Скоринг
        scored = []
        for item in news_items:
            hot_score = scorer.calculate(item)

            scored.append(ScoredNewsItem(
                title=item.title,
                summary=item.summary,
                url=item.url,
                published_at=item.published_at.isoformat(),
                source=item.source,
                hot_score=round(hot_score, 3),
                freshness=round(scorer.calculate_freshness(item.published_at), 3),
                virality=round(scorer.calculate_virality(item), 3),
                relevance=round(scorer.calculate_relevance(item), 3),
                sentiment=round(scorer.calculate_sentiment_score(item), 3),
                uniqueness=round(scorer.calculate_uniqueness(item), 3)
            ))

        # Сортировка и топ-N
        scored.sort(key=lambda x: x.hot_score, reverse=True)
        return scored[:request.top_n]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring error: {str(e)}")


@app.post("/rewrite", response_model=RewriteResponse)
async def rewrite_news(request: RewriteRequest):
    """
    Генерация твита через LLM.

    Возвращает лучший вариант из 2 генераций.
    """
    try:
        result = rewriter.rewrite_to_tweet(
            title=request.title,
            summary=request.summary,
            url=request.url,
            topic_context=request.topic
        )

        return RewriteResponse(
            tweet=result['best_tweet'],
            sentiment=result.get('sentiment', 0.0),
            controversy=result.get('controversy', 0.0),
            length=len(result['best_tweet'])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rewrite error: {str(e)}")


@app.post("/score-and-rewrite")
async def score_and_rewrite(request: ScoreRequest):
    """
    Комбо: скоринг + рерайт топ-N новостей.

    Удобно для n8n - один вызов вместо двух.
    """
    try:
        # Скоринг
        scored = await score_news(request)

        # Рерайт каждой
        results = []
        for item in scored:
            rewrite = await rewrite_news(RewriteRequest(
                title=item.title,
                summary=item.summary,
                url=item.url,
                topic=" ".join(request.topic_keywords) if request.topic_keywords else "news"
            ))

            results.append({
                "title": item.title,
                "url": item.url,
                "hot_score": item.hot_score,
                "tweet": rewrite.tweet,
                "tweet_length": rewrite.length
            })

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Combined error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
