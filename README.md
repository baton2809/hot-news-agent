# AI News Curator Agent

Автоматический агент, который ежедневно публикует 3-4 релевантных "горячих" новостных поста в Twitter по заданным темам.

## Архитектура

```
[Источники] → [Сбор] → [Скоринг "горячести"] → [Фильтр топ-3-4] → [Рерайт через LLM] → [Публикация в Twitter]
```

## Структура проекта

```
hot-news-agent/
├── n8n/workflows/       # JSON workflow из n8n
├── src/
│   ├── scoring/         # логика скоринга и embeddings
│   ├── sources/         # сбор новостей (NewsAPI, RSS, Twitter)
│   ├── rewrite/         # рерайт через LLM
│   └── publish/         # публикация в Twitter
├── config/              # конфигурация и темы
├── data/                # логи новостей
└── tests/
```

## Скоринг "горячести"

| Сигнал | Вес | Логика |
|--------|-----|--------|
| Свежесть | 0.25 | `score = e^(-hours/12)` |
| Виральность | 0.25 | shares/retweets нормализованные |
| Релевантность | 0.30 | Cosine similarity embeddings |
| Сентимент | 0.10 | Абсолютный sentiment score |
| Уникальность | 0.10 | 1 - max similarity к уже опубликованным |

## Установка

```bash
pip install -r requirements.txt
cp config/.env.example config/.env
# Заполнить API ключи в .env
```

## API

- NewsAPI.org — 100 запросов/день бесплатно
- Twitter/X Developer — Basic tier, 1500 твитов/мес
- OpenAI API — для рерайта и embeddings

## Roadmap

См. [ROADMAP.md](ROADMAP.md) — детальный план с блоками, статусами и следующими шагами.
