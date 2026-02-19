# n8n Workflows

## Активный Workflow

### news-curator-slack-mvp.json
**Статус:** Активный (MVP с Slack модерацией)

**Описание:** Полный цикл обработки новостей с модерацией через Slack

**Архитектура:**
```
RSS Feed (Google News)
  → Python API: Hot Score (тренд-анализ)
  → Filter (score >= 0.4)
  → Select Top 3-4
  → Python API: Rewrite
  → Slack Moderation
  → Google Sheets Log
```

**Ключевые фичи:**
- RSS как основной источник (Google News: ebike)
- ML-скоринг с тренд-анализом (частота упоминаний за 6ч)
- Автоматический рерайт через LLM
- Slack модерация с кнопками "Одобрить/Отклонить"
- Логирование в Google Sheets

**Требования:**
- `SLACK_WEBHOOK_URL` - обязательно
- `OPENAI_API_KEY` - обязательно
- `GOOGLE_SHEETS_SPREADSHEET_ID` - опционально

**Использование:**
1. Импортировать workflow в n8n
2. Настроить переменные окружения
3. Запустить вручную или настроить cron (2-3 раза в день)

---

## Архив

### archive/
Старые workflow перенесены в папку archive:
- `news-curator-mvp.json` - первая версия MVP
- `news-curator-mvp-mock.json` - мок-версия для тестирования
- `news-curator-email.json` - версия с email уведомлениями
- `news-curator-production.json` - production версия без Slack

---

## Настройка Slack Webhook

1. Перейти на https://api.slack.com/messaging/webhooks
2. Создать новое приложение Slack
3. Активировать Incoming Webhooks
4. Создать webhook для канала (например, #news-moderation)
5. Скопировать Webhook URL
6. Добавить в `.env`:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

---

## Настройка Google Sheets

1. Создать новую Google Таблицу
2. Создать лист с названием `news_log`
3. Добавить заголовки: `timestamp`, `title`, `url`, `hot_score`, `rewritten_text`, `status`
4. Скопировать ID таблицы из URL
5. Добавить в `.env`:
   ```
   GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
   ```
6. Настроить Google Sheets credentials для n8n

---

## Расписание (cron)

Рекомендуемое расписание для США (EST):
- **09:00 EST** - утренний сбор новостей
- **13:00 EST** - дневной сбор
- **18:00 EST** - вечерний сбор

Настройка в n8n:
1. Заменить "Manual Trigger" на "Cron" node
2. Expression: `0 9,13,18 * * *` (09:00, 13:00, 18:00 каждый день)
3. Timezone: `America/New_York`
