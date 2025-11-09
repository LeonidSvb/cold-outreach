# Website Scraping Module

Универсальная система для scraping сайтов с гибкой конфигурацией.

---

## 📁 Структура

```
modules/scraping/
├── lib/                      # Переиспользуемые компоненты
│   ├── http_utils.py        # HTTP client с retry
│   ├── text_utils.py        # HTML → текст, email extraction
│   └── stats_tracker.py     # Статистика и бенчмарки
│
├── scripts/
│   └── website_scraper.py   # Универсальный scraper
│
├── docs/
│   └── BENCHMARKS.md        # Бенчмарки и time estimates
│
└── results/                  # Output файлы
```

---

## 🚀 Quick Start

### Установка зависимостей

```bash
pip install requests beautifulsoup4 pandas
```

### Базовое использование

```bash
# Standard scraping (с emails)
python modules/scraping/scripts/website_scraper.py \
    --input leads.csv \
    --output results.csv \
    --mode standard

# Результат: CSV с колонками [url, status, emails, phones, content]
```

---

## 🎯 Режимы работы

| Режим | Скорость | Что делает | Использование |
|-------|----------|-----------|---------------|
| **quick** | ⚡⚡⚡ Очень быстро | Только detection static/dynamic | Фильтрация сайтов |
| **standard** | ⚡⚡ Быстро | Scraping + emails/phones | Контакты для outreach |
| **full** | ⚡ Медленно | Scraping + AI analysis | Персонализация |

---

## 📖 Примеры

### Пример 1: Быстрая проверка сайтов

```bash
python modules/scraping/scripts/website_scraper.py \
    --input 10000_urls.csv \
    --output checked.csv \
    --mode quick \
    --workers 100

# Время: ~8 минут для 10,000 сайтов
```

### Пример 2: Извлечение контактов

```bash
python modules/scraping/scripts/website_scraper.py \
    --input hvac_companies.csv \
    --output hvac_with_contacts.csv \
    --mode standard \
    --workers 25

# Время: ~8 минут для 1,000 сайтов
```

### Пример 3: Кастомная конфигурация

```bash
python modules/scraping/scripts/website_scraper.py \
    --input leads.csv \
    --output results.csv \
    --check-static \
    --extract-emails \
    --scrape-mode smart \
    --workers 50 \
    --timeout 20
```

---

## 📊 Output формат

Один CSV файл со всеми результатами:

```csv
url,status,site_type,emails,phones,content,processing_time
https://example.com,success,static,contact@example.com,123-456-7890,"Company info...",0.523
https://example2.com,dynamic,dynamic,,,Low content detected,0.102
https://example3.com,timeout,,,,,15.001
```

**Колонки:**
- `url` - исходный URL
- `status` - результат обработки (success/timeout/dynamic/error)
- `site_type` - тип сайта (static/dynamic)
- `emails` - найденные email адреса (через запятую)
- `phones` - найденные телефоны
- `content` - очищенный текст сайта
- `processing_time` - время обработки (секунды)

**Фильтрация результатов:**

```python
import pandas as pd

df = pd.read_csv('results.csv')

# Только успешные
success = df[df['status'] == 'success']

# Только с emails
with_emails = df[df['emails'].notna() & (df['emails'] != '')]

# Динамические сайты (для Firecrawl)
dynamic = df[df['status'] == 'dynamic']
```

---

## ⚙️ Параметры

### Основные

- `--input FILE` - входной CSV с URL'ами (**обязательно**)
- `--output FILE` - выходной CSV (**обязательно**)
- `--mode {quick|standard|full}` - режим работы

### Флаги (для кастомной конфигурации)

- `--check-static` - проверять static/dynamic
- `--extract-emails` - извлекать emails
- `--extract-phones` - извлекать телефоны
- `--scrape-mode {single|smart|all}` - режим scraping страниц
- `--ai-analysis` - запустить AI анализ

### Производительность

- `--workers N` - количество параллельных потоков (default: 25)
- `--timeout N` - HTTP timeout в секундах (default: 15)
- `--max-text-length N` - максимальная длина текста (default: 15000)

### Утилиты

- `--estimate-only` - показать только оценку времени (не запускать scraping)

---

## 📈 Статистика

После выполнения показывается детальная статистика:

```
================================================================================
EXECUTION SUMMARY
================================================================================
Total items:           1000
Completed:             1000
Success:               720 (72.0%)
Failed:                280 (28.0%)

Duration:              8.2 min (492 sec)
Speed:                 2.03 items/sec
Parallel workers:      25

Processing times:
  Average:             0.485 sec
  Min:                 0.102 sec
  Max:                 15.001 sec

Results by status:
  success                 720 ( 72.0%)
  dynamic                 180 ( 18.0%)
  timeout                  70 (  7.0%)
  connection_error         30 (  3.0%)
================================================================================

OPTIMIZATION RECOMMENDATIONS:
  1. HIGH TIMEOUTS (70): Consider increasing --timeout parameter
  2. MANY DYNAMIC SITES (180): Consider using --use-firecrawl for better coverage
```

---

## 🔍 Фильтрация по status

После scraping можно легко фильтровать результаты:

```python
import pandas as pd

df = pd.read_csv('results.csv')

# Успешные → готово к использованию
success = df[df['status'] == 'success']
success.to_csv('ready_to_use.csv', index=False)

# Динамические → обработать через Firecrawl
dynamic = df[df['status'] == 'dynamic']
dynamic.to_csv('process_with_firecrawl.csv', index=False)

# Таймауты → retry с увеличенным timeout
timeouts = df[df['status'] == 'timeout']
timeouts.to_csv('retry_with_higher_timeout.csv', index=False)
```

---

## 📚 Документация

- **[BENCHMARKS.md](docs/BENCHMARKS.md)** - детальные бенчмарки и time estimates
- **[API Documentation](lib/)** - документация библиотек

---

## 💡 Best Practices

1. **Начинайте с quick mode** для проверки качества данных
2. **Используйте --estimate-only** для планирования времени
3. **Разбивайте большие задачи на батчи** (<2000 сайтов за раз)
4. **Сохраняйте результаты** для повторного использования
5. **Фильтруйте по status** для обработки проблемных случаев

---

## 🐛 Troubleshooting

### Проблема: Много timeout'ов (>10%)
**Решение:** Увеличьте `--timeout 30` или уменьшите `--workers 15`

### Проблема: Много dynamic sites (>20%)
**Решение:** Используйте Firecrawl для fallback обработки

### Проблема: Низкая скорость (<5 items/sec)
**Решение:** Увеличьте `--workers 50` (если нет rate limiting)

### Проблема: HTTP 429 errors (rate limiting)
**Решение:** Уменьшите `--workers 10` и добавьте delay

---

## 📞 Support

Если есть вопросы - смотрите документацию в `docs/BENCHMARKS.md` или обратитесь к автору.
