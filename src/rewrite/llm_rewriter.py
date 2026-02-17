"""
LLM Rewriter - рерайт новостей в Twitter посты через OpenAI.
"""

import os
import json
from dataclasses import dataclass
from openai import OpenAI


@dataclass
class RewriteResult:
    text: str
    length: int
    has_hook: bool
    hashtags: list[str]


class LLMRewriter:
    """Рерайтер новостей в Twitter посты."""

    SYSTEM_PROMPT = """You are a social media manager.
Your task is to rewrite news into engaging Twitter posts.

Rules:
- Max 260 characters (leave room for links)
- Professional but engaging tone, like an industry insider
- Add 1-2 relevant hashtags at the end
- Do NOT copy original text — rephrase completely
- Do NOT use emoji excessively — max 1
- Include a hook in the first line to grab attention
- Write in English

Return JSON only:
{
  "text": "your tweet text here",
  "hashtags": ["hashtag1", "hashtag2"]
}"""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = model

    def rewrite(
        self,
        title: str,
        summary: str,
        topic_context: str = "",
        num_variants: int = 2,
    ) -> list[RewriteResult]:
        """
        Переписать новость в Twitter пост.

        Args:
            title: Заголовок новости
            summary: Краткое содержание
            topic_context: Контекст темы для тональности
            num_variants: Количество вариантов для генерации
        """
        user_prompt = f"""Rewrite this news as a Twitter post.
Generate {num_variants} different variants.

Original title: {title}
Original summary: {summary}
Topic context: {topic_context or 'general news'}

Return JSON array:
[{{"text": "variant 1", "hashtags": [...]}}, {{"text": "variant 2", "hashtags": [...]}}]"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
        )

        content = response.choices[0].message.content
        data = json.loads(content)

        # Нормализация ответа (может быть array или object с array)
        if isinstance(data, dict):
            variants = data.get('variants', data.get('tweets', [data]))
        else:
            variants = data

        results = []
        for variant in variants:
            text = variant.get('text', '')
            hashtags = variant.get('hashtags', [])

            # Проверка наличия hook (первое предложение должно быть < 50 символов и цепляющим)
            first_line = text.split('\n')[0].split('.')[0]
            has_hook = len(first_line) < 60 and any(
                word in first_line.lower()
                for word in ['breaking', 'just', 'new', 'why', 'how', 'what', '!', '?']
            )

            results.append(RewriteResult(
                text=text,
                length=len(text),
                has_hook=has_hook,
                hashtags=hashtags,
            ))

        return results

    def select_best(self, variants: list[RewriteResult]) -> RewriteResult:
        """Выбрать лучший вариант поста."""
        # Фильтруем по длине (≤ 280)
        valid = [v for v in variants if v.length <= 280]

        if not valid:
            # Если все слишком длинные, берём самый короткий
            return min(variants, key=lambda v: v.length)

        # Предпочитаем варианты с hook
        with_hook = [v for v in valid if v.has_hook]
        if with_hook:
            return with_hook[0]

        return valid[0]

    def analyze_sentiment(self, text: str) -> dict:
        """Анализ sentiment и controversy для скоринга."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Rate the sentiment and controversy of the text. Return JSON only."
                },
                {
                    "role": "user",
                    "content": f"""Rate this text:
"{text}"

Return JSON:
{{"sentiment": <float -1 to 1>, "controversy": <float 0 to 1>}}

sentiment: -1 = very negative, 0 = neutral, 1 = very positive
controversy: 0 = boring/neutral, 1 = highly controversial/provocative"""
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )

        return json.loads(response.choices[0].message.content)
