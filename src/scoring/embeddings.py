"""
Embeddings и cosine similarity для скоринга релевантности.
"""

import os
import math
from openai import OpenAI


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Вычислить cosine similarity между двумя векторами."""
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have the same length")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


class EmbeddingService:
    """Сервис для получения embeddings через OpenAI API."""

    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = "text-embedding-3-small"  # Дешёвая модель

    def get_embedding(self, text: str) -> list[float]:
        """Получить embedding для текста."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def get_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Получить embeddings для списка текстов (batch)."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Вычислить similarity между двумя текстами."""
        embeddings = self.get_embeddings_batch([text1, text2])
        return cosine_similarity(embeddings[0], embeddings[1])
