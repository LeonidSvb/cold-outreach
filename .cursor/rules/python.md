# Python Rules - Cold Outreach Automation Platform

**Описание:** Правила для Python разработки в проекте автоматизации холодных рассылок.

---

## Основные принципы

- Пишите чёткий, технический код с точными примерами на Python
- Используйте функциональное программирование; избегайте классов где возможно
- Приоритет читаемости и модульности над дублированием кода
- Используйте описательные имена переменных (например, `is_active`, `has_permission`)
- Используйте `snake_case` для директорий и файлов (например, `modules/apollo/lead_collector.py`)
- **КРИТИЧНО: НИКОГДА не используйте эмодзи в Python скриптах** (проблемы с кодировкой Windows)
- **Все комментарии только на английском языке**

---

## Python/FastAPI Backend

### Структура функций
- Используйте `def` для чистых функций и `async def` для асинхронных операций
- Используйте type hints для всех сигнатур функций
- Предпочитайте Pydantic модели вместо словарей для валидации входных данных
- Структура файла: экспортируемый router, sub-routes, utilities, типы (models, schemas)

### Обработка ошибок
- Обрабатывайте ошибки и edge cases в начале функций
- Используйте early returns для ошибок, избегайте глубокой вложенности if
- Помещайте "happy path" последним в функции для читаемости
- Используйте guard clauses для проверки предусловий
- Логируйте ошибки с понятными сообщениями
- Используйте HTTPException для ожидаемых ошибок

### Зависимости
- FastAPI
- Pydantic v2
- httpx (для HTTP запросов)
- pandas (для CSV обработки)
- python-dotenv (для .env файлов)

---

## FastAPI Специфика

### Роуты и эндпоинты
- Используйте функциональные компоненты (обычные функции) и Pydantic модели
- Используйте декларативные определения роутов с чёткими type annotations
- Минимизируйте использование `@app.on_event("startup")`, предпочитайте lifespan context managers
- Используйте middleware для логирования, мониторинга ошибок и оптимизации

### Валидация
- Используйте Pydantic `BaseModel` для валидации input/output
- Создавайте schema классы для каждой модели данных
- Валидируйте данные на уровне роутов, бизнес-логика в отдельных функциях

### Производительность
- Минимизируйте блокирующие I/O операции
- Используйте async функции для всех database и external API запросов
- Реализуйте кэширование для часто используемых данных (Redis/in-memory)
- Используйте lazy loading для больших датасетов

---

## Web Scraping (HTTP-Only)

### Основные принципы
- **Используйте ТОЛЬКО встроенные Python библиотеки** (urllib, requests)
- **НИКОГДА не используйте внешние сервисы** типа Firecrawl, Selenium
- Используйте requests для простых HTTP GET/POST запросов
- Парсите HTML с BeautifulSoup для эффективной экстракции данных
- Уважайте terms of service сайтов и используйте правильные headers (User-Agent)

### Обработка данных
- Реализуйте rate limiting и случайные задержки между запросами
- Обрабатывайте timeouts и connection errors gracefully
- Валидируйте форматы scraped данных перед обработкой
- Логируйте все ошибки с детальным контекстом

### Retry логика
- Реализуйте robust error handling для:
  - Connection timeouts (`requests.Timeout`)
  - Parsing errors (`BeautifulSoup` exceptions)
- Retry failed requests с exponential backoff
- Логируйте детальные сообщения об ошибках для отладки

---

## Data Processing (CSV/Pandas)

### Работа с CSV
- Используйте pandas для манипуляции и анализа данных
- Предпочитайте method chaining для трансформаций данных
- Используйте `loc` и `iloc` для явного выбора данных
- Используйте `groupby` для эффективной агрегации

### Валидация данных
- Проверяйте качество данных в начале анализа
- Обрабатывайте missing data корректно (imputation, removal, flagging)
- Валидируйте типы данных и диапазоны значений
- Сохраняйте данные в подходящих форматах (CSV, JSON)

---

## Модульная структура проекта

### Организация модулей
```
modules/
├── shared/              # Общие утилиты
│   ├── logger.py       # Система логирования
│   └── google_sheets.py
├── apollo/             # Apollo API интеграция
│   ├── apollo_lead_collector.py
│   └── results/        # JSON результаты с timestamp
├── openai/             # OpenAI обработка
│   ├── openai_mass_processor.py
│   └── results/
├── scraping/           # Web scraping (HTTP-only)
│   ├── domain_analyzer.py
│   ├── content_extractor.py
│   └── results/
└── instantly/          # Instantly API
    ├── instantly_campaign_optimizer.py
    └── results/
```

### Стандарт структуры скрипта
```python
#!/usr/bin/env python3
"""
=== SCRIPT NAME ===
Version: 1.0.0 | Created: YYYY-MM-DD

PURPOSE:
Brief description

FEATURES:
- Key capabilities
- Main features

USAGE:
1. Configure CONFIG section below
2. Run: python script_name.py
3. Results saved to results/

IMPROVEMENTS:
v1.0.0 - Initial version
"""

# CONFIG SECTION - All settings here
CONFIG = {
    "API_SETTINGS": {...},
    "PROCESSING": {...},
    "OUTPUT": {...}
}

# SCRIPT STATISTICS - Auto-updated
SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "last_run": None,
    "success_rate": 0.0
}

# MAIN LOGIC
def main():
    pass

if __name__ == "__main__":
    main()
```

---

## Конфигурация и окружение

### Environment Variables
- **НИКОГДА не перезаписывайте .env файлы** без явного разрешения
- Используйте централизованный `.env` для всех API ключей
- Загружайте переменные через `python-dotenv`
- Используйте type hints при доступе к env переменным

### API Keys Management
- Храните все API ключи в `.env` файле
- Используйте `os.getenv()` с default значениями
- Логируйте ошибки при отсутствии критичных ключей
- Никогда не коммитьте `.env` в git

---

## Оптимизация производительности

### Асинхронность
- Используйте `async def` для I/O-bound задач
- Используйте `httpx` для асинхронных HTTP запросов
- Реализуйте connection pooling для database connections
- Используйте background tasks для длительных операций

### Batch Processing
- Планируйте изменения заранее - что нужно изменить во всех файлах
- Делайте массовые изменения одним батчем, а не файл за файлом
- Используйте find/replace, regex для массовых правок
- Коммитьте батчи изменений, не каждый файл отдельно

---

## Тестирование

### Testing Framework
- Используйте pytest для unit тестов
- **ИСПОЛЬЗУЙТЕ ТОЛЬКО реальные данные** (no mocks в production)
- Тестируйте edge cases и error handling
- Пишите integration тесты для API endpoints

### Логирование
- Используйте structured logging (JSON) для easy parsing
- Логируйте performance metrics (время выполнения, API costs)
- Сохраняйте session history для аналитики
- Интегрируйте с dashboard для визуализации

---

## Git и Version Control

### Commit Standards
- Пишите чёткие, описательные commit messages
- Делайте atomic commits - один commit = одна feature/fix
- Проверяйте изменения через git diff перед коммитом
- **Никогда не коммитьте** secrets, .env файлы, временные файлы

### Именование файлов
**Scripts:** `{purpose}.py` (без дат)
- Примеры: `apollo_lead_collector.py`, `openai_mass_processor.py`

**Results:** `{script_name}_{YYYYMMDD_HHMMSS}.json` (с timestamp)
- Примеры: `apollo_leads_20250119_143022.json`

---

## Ключевые конвенции

1. **Простота превыше всего** - предпочитайте простые решения сложным
2. **DRY принцип** - избегайте дублирования кода
3. **Real data only** - никогда не используйте fake/test данные в production
4. **HTTP-only scraping** - только встроенные библиотеки Python
5. **Embedded configs** - все настройки внутри скриптов (no external configs)
6. **No emojis** - никогда не используйте эмодзи в коде (Windows encoding issues)
7. **English comments** - все комментарии только на английском

---

## Специфичные для проекта правила

### FastAPI Backend Structure
```
backend/
├── main.py              # FastAPI app initialization
├── routers/             # API routes
│   ├── upload.py
│   ├── files.py
│   └── preview.py
├── models/              # Pydantic models
├── utils/               # Helper functions
└── config.py            # Configuration
```

### API Response Format
```python
# Success response
{
    "success": true,
    "data": {...},
    "message": "Success message"
}

# Error response
{
    "success": false,
    "error": "Error message",
    "details": {...}
}
```

### CSV Processing Standards
- Автоматическое определение delimiter
- Валидация column types
- Обработка encoding issues (UTF-8, latin1)
- Сохранение metadata (row counts, column info)

---

Refer to FastAPI, pandas, and requests documentation for best practices.
