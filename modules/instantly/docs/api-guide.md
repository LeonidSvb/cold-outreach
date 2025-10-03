# INSTANTLY API - ПОЛНЫЙ ГАЙД
*Документация по работе с Instantly API v2*

## ✅ ЧТО РАБОТАЕТ

### Аутентификация:
- **РАБОТАЕТ:** Raw base64 ключ через curl
- **НЕ РАБОТАЕТ:** Python urllib/requests (блокируется Cloudflare)
- **Формат:** `Authorization: Bearer YzZlYTFiZmQtNmZhYy00ZTQxLTkyNWMtNDYyODQ3N2UyOTU0Om94cnhsVkhYQ3p3Rg==`

### Рабочие эндпоинты:
```bash
# ✅ Общая аналитика кампаний
curl -H "Authorization: Bearer {KEY}" https://api.instantly.ai/api/v2/campaigns/analytics

# ✅ Детальная аналитика конкретной кампании
curl -H "Authorization: Bearer {KEY}" https://api.instantly.ai/api/v2/campaigns/analytics?id={campaign_id}

# ✅ Обзор аналитики
curl -H "Authorization: Bearer {KEY}" https://api.instantly.ai/api/v2/campaigns/analytics/overview

# ✅ Ежедневная аналитика
curl -H "Authorization: Bearer {KEY}" "https://api.instantly.ai/api/v2/campaigns/analytics/daily?start_date=2024-01-01&end_date=2025-09-21"

# ✅ Аналитика по этапам
curl -H "Authorization: Bearer {KEY}" https://api.instantly.ai/api/v2/campaigns/analytics/steps?campaign_id={campaign_id}

# ✅ Email аккаунты
curl -H "Authorization: Bearer {KEY}" https://api.instantly.ai/api/v2/accounts

# ✅ Детальные письма
curl -H "Authorization: Bearer {KEY}" https://api.instantly.ai/api/v2/emails?limit=100
```

### Получение лидов:
```bash
# ✅ Лиды через POST
curl -X POST -H "Authorization: Bearer {KEY}" -H "Content-Type: application/json" -d '{"campaign_id":"{campaign_id}","limit":20}' https://api.instantly.ai/api/v2/leads/list
```

## ❌ ЧТО НЕ РАБОТАЕТ

### Проблемные методы:
- **Python urllib/requests** - блокировка Cloudflare 403
- **GET /api/v2/leads** - 404 Not Found
- **Декодирование base64 ключа** - ключ нужен в сыром виде
- **Фильтр по типу писем** `?ue_type=2` - не работает для получения только ответов

### Несуществующие эндпоинты:
```
❌ GET /api/v2/leads?campaign_id={id}
❌ POST /api/v2/accounts/warmup-analytics (требует специальные права)
❌ GET /api/v1/* (старая версия API)
```

## 📊 СТРУКТУРА ДАННЫХ

### Campaign Analytics Response:
```json
{
  "campaign_name": "string",
  "campaign_id": "uuid",
  "campaign_status": number, // 1=Active, 2=Paused, 3=Completed, -1=Unhealthy, -2=Bounce
  "leads_count": number,
  "contacted_count": number,
  "open_count": number,
  "reply_count": number,
  "bounced_count": number,
  "emails_sent_count": number,
  "total_opportunities": number,
  "total_opportunity_value": number
}
```

### Accounts Response:
```json
{
  "items": [
    {
      "email": "string",
      "status": number, // 1=Active, -1=Inactive
      "warmup_status": number,
      "stat_warmup_score": number,
      "organization": "uuid"
    }
  ]
}
```

### Daily Analytics:
```json
[
  {
    "date": "YYYY-MM-DD",
    "sent": number,
    "opened": number,
    "unique_opened": number,
    "replies": number,
    "unique_replies": number,
    "clicks": number,
    "unique_clicks": number
  }
]
```

## 🔧 ЛУЧШИЕ ПРАКТИКИ

### 1. Аутентификация:
- Используйте raw base64 ключ БЕЗ декодирования
- Добавляйте User-Agent для обхода некоторых фильтров
- Используйте curl или аналогичные инструменты вместо Python requests

### 2. Сбор данных:
- Начинайте с общей аналитики кампаний
- Затем детализируйте каждую кампанию отдельно
- Собирайте данные по аккаунтам параллельно
- Используйте date range фильтры для больших объемов

### 3. Обработка ошибок:
- 403 ошибки обычно = Cloudflare блокировка
- 401 ошибки = проблемы с API ключом
- 404 ошибки = неправильный endpoint
- Добавляйте retry logic с задержками

## 📈 МЕТРИКИ ДЛЯ АНАЛИЗА

### Ключевые показатели кампаний:
- `emails_sent_count` - общие отправки
- `reply_count` - формальные ответы
- `open_count` - открытия (часто 0)
- `bounced_count` - bounces
- `total_opportunities` - конверсии
- `total_opportunity_value` - стоимость

### Расчетные метрики:
- Reply Rate = reply_count / emails_sent_count * 100
- Bounce Rate = bounced_count / emails_sent_count * 100
- Opportunity Rate = total_opportunities / emails_sent_count * 100
- Avg Opportunity Value = total_opportunity_value / total_opportunities

### Качественные фильтры:
- Реальный Reply Rate ≈ Формальный * 0.3-0.5 (учет OOO)
- Позитивный Reply Rate ≈ Формальный * 0.1-0.2

## 🛠️ КОМАНДЫ ДЛЯ БЫСТРОГО СБОРА

### Полный сбор данных одной командой:
```bash
#!/bin/bash
KEY="YzZlYTFiZmQtNmZhYy00ZTQxLTkyNWMtNDYyODQ3N2UyOTU0Om94cnhsVkhYQ3p3Rg=="

# Общие данные
curl -H "Authorization: Bearer $KEY" https://api.instantly.ai/api/v2/campaigns/analytics > campaigns.json
curl -H "Authorization: Bearer $KEY" https://api.instantly.ai/api/v2/accounts > accounts.json
curl -H "Authorization: Bearer $KEY" https://api.instantly.ai/api/v2/campaigns/analytics/overview > overview.json

# Ежедневная аналитика за последние 30 дней
curl -H "Authorization: Bearer $KEY" "https://api.instantly.ai/api/v2/campaigns/analytics/daily?start_date=$(date -d '30 days ago' +%Y-%m-%d)&end_date=$(date +%Y-%m-%d)" > daily.json
```

## 🚨 ИЗВЕСТНЫЕ ОГРАНИЧЕНИЯ

1. **Rate Limits:** Неизвестны, но рекомендуется 1-2 запроса в секунду
2. **Cloudflare Protection:** Блокирует стандартные HTTP библиотеки
3. **Date Ranges:** Большие диапазоны могут вызывать таймауты
4. **Pagination:** Некоторые эндпоинты используют `next_starting_after`
5. **Real-time Data:** Данные могут обновляться с задержкой 15-30 минут

## 🎯 РЕКОМЕНДУЕМЫЙ WORKFLOW

1. **Тест подключения** → `campaigns/analytics`
2. **Сбор кампаний** → детализация каждой
3. **Сбор аккаунтов** → проверка статусов
4. **Временные данные** → daily/steps analytics
5. **Обработка и анализ** → расчет реальных метрик
6. **Сохранение** → структурированные JSON файлы

---
*Обновлено: 21 сентября 2025*
*Протестировано на Instantly API v2*