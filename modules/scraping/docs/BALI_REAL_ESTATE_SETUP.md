# Сбор Агентств Недвижимости Бали - Инструкция

## Что Создано

Скрипт `bali_real_estate_collector.py` использует Google Places API для поиска крупных агентств недвижимости на Бали.

**Возможности:**
- Поиск через Google Maps по 12 разным запросам
- Фильтрация только крупных агентств (рейтинг >= 4.0, отзывов >= 10)
- Автоматический сбор: название, адрес, телефон, сайт, рейтинг
- Извлечение email адресов с сайтов агентств
- Дедупликация и сортировка по рейтингу
- Сохранение в JSON со статистикой

---

## Быстрый Старт (5 минут)

### Шаг 1: Получить Google Places API Ключ

1. **Перейти:** https://console.cloud.google.com/
2. **Создать проект** (или выбрать существующий)
3. **Включить API:**
   - Найти "Places API (New)"
   - Нажать "Enable"
4. **Создать ключ:**
   - Credentials → Create Credentials → API Key
   - Скопировать ключ

**Важно:** Google даёт $200 бесплатных кредитов в месяц. Для 300 агентств потребуется примерно $5-10.

---

### Шаг 2: Настроить API Ключ

Добавить в `.env` файл в корне проекта:

```bash
GOOGLE_PLACES_API_KEY=ваш_ключ_сюда
```

**Или** открыть скрипт и вставить ключ напрямую:

```python
CONFIG = {
    "API_KEY": "ваш_ключ_сюда",  # Замените на ваш ключ
    ...
}
```

---

### Шаг 3: Запустить Скрипт

```bash
cd "C:\Users\79818\Desktop\Outreach - new\modules\scraping\scripts"
python bali_real_estate_collector.py
```

**Что происходит:**
1. Поиск по 12 запросам в Google Maps
2. Фильтрация крупных агентств (рейтинг >= 4.0, >= 10 отзывов)
3. Сбор контактов с каждого сайта
4. Сохранение в `../results/bali_real_estate_agencies_YYYYMMDD_HHMMSS.json`

**Время выполнения:** 10-15 минут (в зависимости от количества агентств)

---

## Результаты

### Формат JSON

```json
{
  "metadata": {
    "generated_at": "2025-11-02T10:30:00",
    "location": "Bali, Indonesia",
    "total_agencies": 150,
    "target_count": 300,
    "progress_percent": 50.0
  },
  "companies": [
    {
      "name": "Bali Villa Experts",
      "address": "Jl. Sunset Road No. 123, Seminyak, Bali",
      "phone": "+62 361 123456",
      "website": "https://balivillaexperts.com",
      "emails": ["info@balivillaexperts.com", "sales@balivillaexperts.com"],
      "rating": 4.8,
      "reviews_count": 156,
      "place_id": "ChIJ...",
      "source": "Google Places API"
    }
  ],
  "statistics": {
    "with_emails": 120,
    "with_website": 145,
    "average_rating": 4.5,
    "average_reviews": 45.3
  }
}
```

---

## Настройка Параметров

### Если Нужно Больше Агентств (300+)

Открыть `bali_real_estate_collector.py` и изменить фильтры:

```python
CONFIG = {
    # Снизить требования для получения большего количества
    "MIN_RATING": 3.5,      # Было: 4.0
    "MIN_REVIEWS": 5,       # Было: 10
    "TARGET_COUNT": 500,    # Было: 300
}
```

### Добавить Свои Запросы

```python
CONFIG = {
    "SEARCH_QUERIES": [
        "real estate agency Bali",
        "property agency Bali",
        # Добавьте свои:
        "villa rental Ubud Bali",
        "Canggu real estate office",
        "Seminyak property consultant",
    ]
}
```

### Изменить Область Поиска

```python
CONFIG = {
    "LOCATION": {
        "lat": -8.6500,    # Координаты Денпасара
        "lng": 115.2167,
        "radius": 30000,   # 30км вместо 50км
    }
}
```

---

## Частые Вопросы

### Q: Сколько стоит Google Places API?

**A:** $200 бесплатных кредитов каждый месяц. Для 300 агентств потребуется:
- Text Search: ~150 запросов × $0.032 = ~$5
- Place Details: ~300 запросов × $0.017 = ~$5
- **Итого:** ~$10 (в пределах бесплатного лимита)

### Q: Что если скрипт нашел меньше 300 агентств?

**A:** Попробуйте:
1. Снизить `MIN_RATING` до 3.5
2. Снизить `MIN_REVIEWS` до 5
3. Добавить больше search queries
4. Увеличить radius до 100000 (100км)

### Q: Как получить больше emails?

**A:** Скрипт автоматически проверяет:
- Главную страницу
- /contact
- /contact-us
- /about

Если нужно больше, можно использовать:
- Hunter.io API (отдельный сервис)
- Apollo.io (платформа для B2B контактов)

### Q: Можно ли искать в других городах?

**A:** Да! Измените:

```python
CONFIG = {
    "LOCATION": {
        "lat": <широта>,
        "lng": <долгота>,
        "radius": 50000,
    },
    "SEARCH_QUERIES": [
        "real estate agency <город>",
        ...
    ]
}
```

---

## Следующие Шаги

### После Сбора Данных

1. **Проверить результаты:**
   ```bash
   # Открыть JSON файл и посмотреть статистику
   ```

2. **Экспортировать в CSV** (если нужно):
   ```python
   import json
   import pandas as pd

   with open('results/bali_real_estate_agencies_YYYYMMDD_HHMMSS.json') as f:
       data = json.load(f)

   df = pd.DataFrame(data['companies'])
   df.to_csv('bali_agencies.csv', index=False)
   ```

3. **Загрузить в CRM** или использовать для email кампаний

---

## Структура Файлов

```
modules/scraping/
├── scripts/
│   └── bali_real_estate_collector.py    # Основной скрипт
├── results/
│   └── bali_real_estate_agencies_*.json # Результаты
└── docs/
    └── BALI_REAL_ESTATE_SETUP.md        # Эта инструкция
```

---

## Поддержка

**Если возникли проблемы:**

1. Проверить API ключ в `.env`
2. Проверить баланс Google Cloud Console
3. Проверить логи в `data/logs/`

**Логи:**
- Все действия записываются через Universal Logger
- Файлы логов: `data/logs/<дата>.log`

---

## Дополнительные Возможности

### Интеграция с Apollo.io

Если нужно быстрее получить 300+ лидов с email:

```bash
# Использовать Apollo API вместо Google Places
python modules/apollo/scripts/apollo_lead_collector.py
```

Apollo даёт:
- Готовые email адреса
- LinkedIn профили
- Размер компании
- Технологии которые используют

Но требует Apollo API key (платная подписка).

---

**Создано:** 2025-11-02
**Версия:** 1.0.0
**Статус:** ✅ Готово к использованию
