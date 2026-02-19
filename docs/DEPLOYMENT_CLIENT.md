# Развертывание у заказчика

## 🎯 Что развертываем

У заказчика разворачиваются **2 Docker контейнера**:

1. **Python API** (FastAPI) - порт 8000
2. **n8n workflow** - порт 5678

Они работают вместе и обмениваются данными через внутреннюю Docker сеть.

---

## 🐳 Архитектура развертывания

```
ЗАКАЗЧИК (VPS или локальный сервер)
│
├── Docker Network: news-curator
│   │
│   ├── Container 1: news-curator-api (Python)
│   │   ├── Порт: 8000
│   │   ├── Код: /app/src/
│   │   ├── Env: OPENAI_API_KEY, SLACK_WEBHOOK_URL
│   │   └── Задача: Скоринг + Рерайт + Slack
│   │
│   └── Container 2: news-curator-n8n
│       ├── Порт: 5678 (UI)
│       ├── Workflow: news-curator-slack-mvp.json
│       ├── Env: переменные для n8n
│       └── Задача: Оркестрация + RSS + Логи
│
├── Volumes:
│   └── n8n_data (персистентные данные n8n)
│
└── Файлы на хосте:
    ├── docker-compose.yml
    ├── .env (секреты)
    ├── src/ (Python код)
    ├── n8n/workflows/ (JSON workflow)
    └── config/

Внешние сервисы (не на сервере заказчика):
- OpenAI API (cloud)
- Slack (cloud)
- Google Sheets (cloud)
- RSS источники (cloud)
```

---

## 📦 Python модули и зависимости

### 1. Core API Framework

```python
# requirements.txt

# FastAPI - веб-фреймворк для API
fastapi>=0.109.0

# Uvicorn - ASGI сервер для запуска FastAPI
uvicorn[standard]>=0.27.0

# Pydantic - валидация данных
pydantic>=2.0.0
```

**Зачем:** Python API работает как REST сервис, который принимает запросы от n8n.

---

### 2. OpenAI Integration

```python
# OpenAI SDK - для embeddings и GPT
openai>=1.0.0
```

**Использование:**
- `get_embedding()` - получение векторов для новостей (cosine similarity)
- `LLMRewriter.rewrite_to_tweet()` - рерайт через GPT-4o-mini
- `sentiment_analysis()` - анализ тональности

**API calls:**
- `POST https://api.openai.com/v1/embeddings` - text-embedding-3-small
- `POST https://api.openai.com/v1/chat/completions` - gpt-4o-mini

---

### 3. HTTP Requests

```python
# Requests - для Slack webhook и внешних API
requests>=2.31.0
```

**Использование:**
- `SlackModerator.send_for_moderation()` - отправка в Slack webhook
- Будущие интеграции с другими сервисами

---

### 4. RSS Parsing (опционально для Python)

```python
# Feedparser - парсинг RSS фидов
feedparser>=6.0.0
```

**Примечание:** RSS парсинг делает **n8n нода**, но библиотека нужна если захотим парсить RSS напрямую в Python (для тестов или прямого вызова).

---

### 5. Configuration

```python
# PyYAML - чтение topics.yaml
pyyaml>=6.0

# Python-dotenv - чтение .env файла
python-dotenv>=1.0.0
```

**Использование:**
- Загрузка тем из `config/topics.yaml`
- Загрузка секретов из `.env`

---

### 6. Development & Testing

```python
# Pytest - unit тесты
pytest>=7.0.0
```

**Опционально:**
```python
# Pandas - для анализа логов (если нужно)
# pandas>=2.0.0

# Numpy - для математики (если нужно)
# numpy>=1.24.0
```

---

## 🔧 Полный список Python пакетов

### Основные (обязательные):

| Пакет | Версия | Зачем |
|-------|--------|-------|
| `fastapi` | >=0.109.0 | API фреймворк |
| `uvicorn` | >=0.27.0 | ASGI сервер |
| `pydantic` | >=2.0.0 | Валидация данных |
| `openai` | >=1.0.0 | OpenAI API (embeddings + GPT) |
| `requests` | >=2.31.0 | HTTP клиент (Slack) |
| `pyyaml` | >=6.0 | Конфиги YAML |
| `python-dotenv` | >=1.0.0 | .env файлы |

### Опциональные:

| Пакет | Версия | Зачем |
|-------|--------|-------|
| `feedparser` | >=6.0.0 | RSS парсинг (если нужно в Python) |
| `pytest` | >=7.0.0 | Тестирование |
| `tweepy` | >=4.14.0 | Twitter API (не используется в MVP) |

### Размер образа:

```bash
# Python 3.11-slim base: ~150 MB
# + dependencies: ~200 MB
# = Итого Docker image: ~350 MB
```

---

## 🚀 Процесс развертывания

### Шаг 1: Подготовка сервера заказчика

**Минимальные требования:**
- OS: Linux (Ubuntu 22.04 / Debian 11+) или macOS
- RAM: 2 GB минимум, 4 GB рекомендуется
- Диск: 10 GB свободного места
- Docker: >=20.10
- Docker Compose: >=2.0

**Установка Docker (если нет):**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Проверка
docker --version
docker-compose --version
```

---

### Шаг 2: Клонирование репозитория

```bash
cd /opt  # или любая другая директория
git clone https://github.com/baton2809/hot-news-agent.git
cd hot-news-agent
```

---

### Шаг 3: Настройка переменных окружения

```bash
cp config/.env.example .env
nano .env
```

**Обязательные переменные:**

```bash
# OpenAI API (обязательно)
OPENAI_API_KEY=sk-proj-...

# Slack Webhook (обязательно для модерации)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# n8n UI доступ (обязательно)
N8N_USER=admin
N8N_PASSWORD=<сложный_пароль>

# Google Sheets (опционально, для логирования)
GOOGLE_SHEETS_SPREADSHEET_ID=<your_sheet_id>

# NewsAPI (опционально, не используется в MVP)
# NEWSAPI_KEY=<your_key>
```

---

### Шаг 4: Запуск контейнеров

```bash
# Сборка и запуск
docker-compose up -d --build

# Проверка статуса
docker-compose ps

# Должны быть запущены:
# news-curator-api    Up      0.0.0.0:8000->8000/tcp
# news-curator-n8n    Up      0.0.0.0:5678->5678/tcp
```

---

### Шаг 5: Проверка работоспособности

**Проверка Python API:**
```bash
curl http://localhost:8000/health

# Ожидаемый ответ:
{
  "status": "healthy",
  "openai_key": "set",
  "slack_webhook": "set",
  "scorer": "ready",
  "rewriter": "ready",
  "slack_moderator": "ready"
}
```

**Проверка n8n:**
```bash
# Открыть в браузере
http://<server_ip>:5678

# Логин: admin (из .env N8N_USER)
# Пароль: из N8N_PASSWORD
```

---

### Шаг 6: Импорт workflow в n8n

1. Открыть n8n UI: `http://localhost:5678`
2. Логин с credentials из `.env`
3. Workflow должен загрузиться автоматически из `n8n/workflows/news-curator-slack-mvp.json`
4. Если нет - импортировать вручную:
   - Workflows → Import from File
   - Выбрать `n8n/workflows/news-curator-slack-mvp.json`
   - Import

---

### Шаг 7: Тестовый запуск

1. В n8n UI открыть workflow "News Curator - Slack Moderation MVP"
2. Нажать "Execute Workflow" (правый верх)
3. Подождать 30-60 секунд
4. Проверить:
   - n8n показывает зеленые галочки на нодах
   - Slack канал получил сообщение с новостями
   - Google Sheets лог обновился (если настроен)

---

### Шаг 8: Настройка расписания

1. В workflow заменить "Manual Trigger" на "Cron" node:
   - Delete "When clicking 'Test workflow'" node
   - Add "Schedule Trigger" node
   - Cron expression: `0 9,13,18 * * *` (09:00, 13:00, 18:00 EST)
   - Timezone: `America/New_York`

2. Активировать workflow (toggle в правом верхнем углу)

3. Workflow будет запускаться автоматически 3 раза в день

---

## 📂 Структура файлов на сервере

```
/opt/hot-news-agent/  (или другая директория)
│
├── docker-compose.yml          # Оркестрация контейнеров
├── Dockerfile                  # Сборка Python API
├── requirements.txt            # Python зависимости
├── .env                        # Секреты (НЕ в Git!)
├── .gitignore
├── README.md
├── ROADMAP.md
│
├── src/                        # Python код API
│   ├── api/
│   │   └── main.py            # FastAPI app
│   ├── scoring/
│   │   ├── hot_score.py       # Скоринг алгоритм
│   │   └── embeddings.py      # OpenAI embeddings
│   ├── rewrite/
│   │   └── llm_rewriter.py    # GPT рерайт
│   ├── integrations/
│   │   └── slack.py           # Slack модерация
│   └── sources/
│       ├── rss.py             # RSS парсер
│       └── newsapi.py         # NewsAPI клиент
│
├── n8n/workflows/
│   ├── news-curator-slack-mvp.json  # Активный workflow
│   ├── README.md
│   └── archive/               # Старые версии
│
├── config/
│   ├── topics.yaml            # Темы для скоринга
│   └── .env.example           # Шаблон .env
│
├── data/                      # Логи (опционально)
│   └── news_log.csv
│
└── docs/                      # Документация
    ├── USE_CASES.md
    ├── DEPLOYMENT_CLIENT.md
    └── ML_STRATEGY.md
```

---

## 🔐 Секреты и безопасность

### Что НЕ попадает в Git:

- `.env` - все секреты
- `config/.env` - дубликат
- `data/*.csv` - логи с данными
- Credentials - любые файлы с ключами

### Что нужно настроить у заказчика:

1. **OpenAI API Key**
   - Получить на https://platform.openai.com/api-keys
   - Добавить минимум $5 на баланс
   - Скопировать в `.env`

2. **Slack Webhook**
   - Создать Slack App на https://api.slack.com/apps
   - Включить Incoming Webhooks
   - Создать webhook для канала (например #news-moderation)
   - Скопировать URL в `.env`

3. **n8n пароль**
   - Сгенерировать сложный пароль (32+ символов)
   - Записать в `.env` как `N8N_PASSWORD`

4. **Google Sheets ID** (опционально)
   - Создать Google Sheet
   - Настроить доступ для n8n через OAuth
   - Скопировать ID из URL в `.env`

---

## 🧪 Проверка работы модулей

### Тест 1: Python API загружается

```bash
docker logs news-curator-api

# Должно быть:
# INFO:     Started server process [1]
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Тест 2: OpenAI работает

```bash
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{
    "news": [{"title":"Test","summary":"Test","url":"https://test.com","published_at":"2026-02-19T10:00:00Z","source":"rss"}],
    "topic_keywords": ["test"],
    "top_n": 1
  }'

# Должен вернуть JSON с hot_score
```

### Тест 3: Slack работает

```bash
curl -X POST http://localhost:8000/slack/moderation \
  -H "Content-Type: application/json" \
  -d '{
    "news_items": [{
      "id": 1,
      "title": "Test",
      "summary": "Test",
      "url": "https://test.com",
      "published": "2026-02-19",
      "hot_score": 0.5,
      "rewritten_text": "Test tweet"
    }]
  }'

# Сообщение должно появиться в Slack
```

---

## 📊 Мониторинг

### Логи контейнеров:

```bash
# Все логи
docker-compose logs -f

# Только Python API
docker-compose logs -f scoring-api

# Только n8n
docker-compose logs -f n8n

# Последние 100 строк
docker-compose logs --tail=100 scoring-api
```

### Рестарт при проблемах:

```bash
# Рестарт всех сервисов
docker-compose restart

# Только API
docker-compose restart scoring-api

# Полная перезагрузка с пересборкой
docker-compose down
docker-compose up -d --build
```

### Health checks:

```bash
# Python API
curl http://localhost:8000/health

# n8n (проверка доступности UI)
curl http://localhost:5678
```

---

## 💰 Стоимость для заказчика

| Компонент | Стоимость |
|-----------|-----------|
| **VPS сервер** | $5-10/мес (2GB RAM, DigitalOcean/Hetzner) |
| **OpenAI API** | ~$5-15/мес (embeddings + GPT) |
| **Slack** | $0 (бесплатный план) |
| **Google Sheets** | $0 (бесплатно) |
| **RSS источники** | $0 (бесплатно) |
| **n8n** | $0 (self-hosted) |
| **Python + Docker** | $0 (open source) |
| **Итого** | **$10-25/мес** |

### Детализация OpenAI API:

- **Embeddings** (text-embedding-3-small):
  - 100 новостей/день × 3 раза = 300 embeddings/день
  - 9000 embeddings/месяц × $0.00002 = **$0.18/мес**

- **GPT-4o-mini** (рерайт):
  - 12 новостей/день (4 × 3 раза)
  - 360 новостей/месяц × ~500 tokens × $0.000150/1K = **$27/мес**
  - Можно снизить до $5-10 если использовать кеширование

**Оптимизация:** Кешировать рерайты для похожих новостей.

---

## 🚀 Обновление кода

```bash
# На сервере заказчика
cd /opt/hot-news-agent
git pull origin main
docker-compose up -d --build

# Проверить статус
docker-compose ps
docker-compose logs -f
```

---

## 📞 Поддержка для заказчика

### Частые проблемы:

**1. Python API не стартует**
```bash
# Проверить логи
docker logs news-curator-api

# Проверить .env
cat .env | grep OPENAI_API_KEY

# Пересобрать
docker-compose up -d --build scoring-api
```

**2. n8n не видит Python API**
```bash
# Проверить сеть
docker network ls
docker network inspect hot-news-agent_news-curator

# В n8n использовать: http://scoring-api:8000 (НЕ localhost)
```

**3. Slack не получает сообщения**
```bash
# Проверить webhook URL
curl -X POST $SLACK_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"text":"Test"}'
```

---

## ✅ Checklist развертывания

- [ ] Docker установлен на сервере
- [ ] Репозиторий склонирован
- [ ] `.env` создан и заполнен
- [ ] OpenAI API key получен
- [ ] Slack webhook создан
- [ ] `docker-compose up -d` выполнен
- [ ] Python API health check OK
- [ ] n8n UI открывается
- [ ] Workflow импортирован
- [ ] Тестовый запуск успешен
- [ ] Slack получил тестовое сообщение
- [ ] Расписание настроено
- [ ] Workflow активирован

**Готово! Система работает у заказчика.**
