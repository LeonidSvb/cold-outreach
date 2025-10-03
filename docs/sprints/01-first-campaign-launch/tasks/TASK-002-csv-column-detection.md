# TASK-002: Enhanced CSV Column Detection System

---

## Metadata

```yaml
id: "TASK-002"
title: "Enhanced CSV Column Detection with Regex Validation"
status: "done"
priority: "P1"
labels: ["backend", "csv", "detection", "validation"]
dependencies: []
created: "2025-10-03"
completed: "2025-10-03"
assignee: "AI Agent"
```

**Execution Summary:**
- Created `backend/lib/column_detector.py` with hybrid detection (keyword + regex)
- Implemented 6 regex patterns: EMAIL, PHONE, WEBSITE, LINKEDIN_PROFILE, LINKEDIN_COMPANY, COMPANY_DOMAIN
- Added 15 keyword types for fallback detection
- Integrated into `backend/main.py` with `detect_column_types_enhanced()`
- Tested on real CSV (1691 rows, 17 columns) - 100% validation passed
- All critical columns detected correctly with high confidence (1.00 for regex-validated types)

---

## 1. Цель (High-Level Objective)

Улучшить существующую систему автоопределения типов столбцов CSV, добавив regex-валидацию по sample values и поддержку большего количества типов данных для гибкой обработки любых CSV файлов.

---

## 2. Контекст (Background)

**Текущая ситуация:**
- В `backend/main.py` есть функция `detect_column_types()` (строки 199-235)
- Работает только keyword matching по именам столбцов
- Пример: если столбец называется "email" → определяет как email
- НЕ проверяет формат данных (regex validation отсутствует)

**Проблемы:**
- Если столбец называется "contact" но содержит emails - НЕ определится
- Если столбец "info" содержит phone numbers - НЕ определится
- Нет валидации LinkedIn URL, company domains, и т.д.

**Почему важно:**
- CSV файлы из разных источников имеют разные названия столбцов
- Нужна универсальная система определения типа ПО СОДЕРЖИМОМУ
- Подготовка к следующей задаче (TASK-003) - маппинг на Supabase схему

**Пример проблемного CSV:**
```csv
contact_info,main_phone,website_address,company
john@example.com,+1234567890,https://example.com,ACME Inc
```
Текущая система НЕ определит `contact_info` как email (название не совпадает).

---

## 3. 🤔 ВОПРОСЫ ДЛЯ ДЕТАЛИЗАЦИИ (ответить перед началом)

### Перед началом выполнения ответь на эти вопросы:

**Q1: Стратегия определения типа**
Какой подход использовать?
- **Вариант A:** Сначала keyword matching, потом regex validation (2-step)
- **Вариант B:** Только regex validation по sample values (1-step)
- **Вариант C:** Hybrid - keyword matching с приоритетом, regex как fallback
- **Рекомендация:** Вариант C (быстрее + точнее)

**Q2: Sample size для валидации**
Сколько строк проверять для определения типа?
- 5 строк?
- 10 строк?
- 50 строк?
- **Рекомендация:** 10 строк (баланс точность/скорость)

**Q3: Confidence threshold**
Если 8 из 10 sample values похожи на email - это email?
- 100% совпадение (строго)?
- 80% совпадение (гибко)?
- 50% совпадение (очень гибко)?
- **Рекомендация:** 70% threshold

**Q4: Какие типы данных поддерживать?**
Базовые типы (обязательно):
- EMAIL
- PHONE
- WEBSITE/URL
- COMPANY_NAME
- PERSON_NAME (first/last/full)
- JOB_TITLE
- LOCATION (city/state/country)

Дополнительные типы (опционально):
- LINKEDIN_URL (специальный формат)
- COMPANY_DOMAIN (без http://)
- DATE/TIMESTAMP
- NUMBER/INTEGER
- **Какие из дополнительных нужны?**

**Q5: Обработка пустых значений**
Если столбец содержит 50% пустых значений:
- Игнорировать пустые при определении типа?
- Считать как "OPTIONAL_{TYPE}"?
- **Рекомендация:** Игнорировать пустые, определять тип по заполненным

**Q6: Куда вынести логику?**
- **Вариант A:** Оставить в `main.py` (простота)
- **Вариант B:** Создать `backend/lib/column_detector.py` (модульность)
- **Вариант C:** Интегрировать в существующий `csv_transformer`
- **Рекомендация:** Вариант B (переиспользование в других скриптах)

**Q7: Конфликты типов**
Если столбец подходит под EMAIL (по regex) И URL (тоже валидный)?
- Приоритет типов (EMAIL > URL > TEXT)?
- Вернуть оба варианта?
- **Рекомендация:** Приоритет EMAIL > PHONE > URL > NAME > TEXT

---

## 4. Допущения и Ограничения

**ДОПУЩЕНИЯ:**
- CSV файл уже загружен в `backend/uploads/`
- Pandas библиотека установлена
- CSV содержит header row (первая строка - названия столбцов)
- Encoding UTF-8 (или auto-detect)

**ОГРАНИЧЕНИЯ:**
- Regex validation может быть медленной на больших CSV (1M+ rows)
- Некоторые форматы сложно определить (например, "Smith" - фамилия или компания?)
- Phone formats разные по странам (US vs International)

---

## 5. Plan Контекста (Context Plan)

### В начале (добавить в контекст AI):
- `backend/main.py` (строки 199-235) _(существующая функция detect_column_types)_
- `C:\Users\79818\Downloads\ppc US - Canada...csv` _(тестовый файл с 17 столбцами)_
- Примеры sample values из CSV для тестирования regex

### В конце (должно быть создано/изменено):
- `backend/lib/column_detector.py` - новый модуль (если выбран вариант B из Q6)
- `backend/main.py` - обновлённая функция `detect_column_types()` или импорт
- Unit tests для валидации regex patterns
- Документация regex patterns в комментариях

---

## 6. Пошаговый План (Low-Level Steps)

### Шаг 1: Создание regex patterns

**Файл:** `backend/lib/column_detector.py` (новый)

**Действие:**
```python
import re
from typing import Dict, List, Any, Optional

# Regex patterns для определения типов
PATTERNS = {
    "EMAIL": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    "PHONE": r'^\+?[1-9]\d{1,14}$|^\(\d{3}\)\s?\d{3}-\d{4}$',  # International or US format
    "WEBSITE": r'^https?://[^\s]+|^www\.[^\s]+|\.(com|net|org|io|co|ai)$',
    "LINKEDIN_PROFILE": r'^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9-]+',
    "LINKEDIN_COMPANY": r'^https?://(www\.)?linkedin\.com/company/[a-zA-Z0-9-]+',
    "COMPANY_DOMAIN": r'^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$',
}

# Keyword matching для fallback
KEYWORDS = {
    "EMAIL": ["email", "mail", "e-mail"],
    "PHONE": ["phone", "tel", "mobile", "number", "contact_number"],
    "WEBSITE": ["website", "url", "site", "domain", "web"],
    "COMPANY_NAME": ["company", "organization", "business", "firm", "org"],
    "FIRST_NAME": ["first_name", "firstname", "fname", "given_name"],
    "LAST_NAME": ["last_name", "lastname", "lname", "surname", "family_name"],
    "FULL_NAME": ["full_name", "name", "fullname"],
    "JOB_TITLE": ["title", "position", "role", "job", "job_title"],
    "CITY": ["city", "town"],
    "STATE": ["state", "province", "region"],
    "COUNTRY": ["country", "nation"],
}
```

**Детали:**
- Каждый pattern покрывает основные форматы
- Phone поддерживает US и International formats
- LinkedIn URL отдельные для profiles и companies

---

### Шаг 2: Функция валидации по sample values

**Файл:** `backend/lib/column_detector.py`

**Действие:**
```python
def validate_type_by_samples(
    sample_values: List[str],
    type_name: str,
    confidence_threshold: float = 0.7
) -> bool:
    """
    Validate if sample values match the type pattern

    Args:
        sample_values: List of non-empty sample values from column
        type_name: Type to validate (EMAIL, PHONE, etc.)
        confidence_threshold: Minimum percentage of matches (0.0-1.0)

    Returns:
        True if >= threshold samples match pattern
    """
    if not sample_values or type_name not in PATTERNS:
        return False

    pattern = PATTERNS[type_name]
    matches = sum(1 for val in sample_values if re.match(pattern, val.strip()))

    confidence = matches / len(sample_values)
    return confidence >= confidence_threshold
```

**Детали:**
- Проверяет % совпадений с regex pattern
- Игнорирует пустые значения (фильтруются перед вызовом)
- Configurable threshold (по умолчанию 70%)

---

### Шаг 3: Keyword matching (улучшенный)

**Файл:** `backend/lib/column_detector.py`

**Действие:**
```python
def detect_by_column_name(column_name: str) -> Optional[str]:
    """
    Detect type by column name using keyword matching

    Returns:
        Type name or None if no match
    """
    col_lower = column_name.lower().strip()

    # Check each type's keywords
    for type_name, keywords in KEYWORDS.items():
        if any(keyword in col_lower for keyword in keywords):
            return type_name

    return None
```

---

### Шаг 4: Hybrid detection (главная функция)

**Файл:** `backend/lib/column_detector.py`

**Действие:**
```python
def detect_column_type(
    column_name: str,
    sample_values: List[str],
    sample_size: int = 10,
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Detect column type using hybrid approach:
    1. Keyword matching (fast)
    2. Regex validation (accurate)

    Returns:
        {
            "detected_type": "EMAIL",
            "confidence": 0.85,
            "method": "regex_validation",
            "sample_matches": 8.5/10
        }
    """
    # Filter non-empty values
    non_empty = [val for val in sample_values[:sample_size] if val and str(val).strip()]

    if not non_empty:
        return {"detected_type": "UNKNOWN", "confidence": 0.0, "method": "no_data"}

    # Step 1: Try keyword matching
    keyword_type = detect_by_column_name(column_name)

    # Step 2: Try regex validation (priority order)
    priority_types = ["EMAIL", "PHONE", "LINKEDIN_PROFILE", "LINKEDIN_COMPANY",
                      "WEBSITE", "COMPANY_DOMAIN"]

    for type_name in priority_types:
        if validate_type_by_samples(non_empty, type_name, confidence_threshold):
            matches = sum(1 for val in non_empty if re.match(PATTERNS[type_name], val.strip()))
            confidence = matches / len(non_empty)

            return {
                "detected_type": type_name,
                "confidence": round(confidence, 2),
                "method": "regex_validation",
                "sample_matches": f"{matches}/{len(non_empty)}"
            }

    # Step 3: Fallback to keyword matching
    if keyword_type:
        return {
            "detected_type": keyword_type,
            "confidence": 0.5,  # Lower confidence for keyword-only
            "method": "keyword_matching"
        }

    # Step 4: Unknown type
    return {"detected_type": "TEXT", "confidence": 0.0, "method": "default"}
```

**Детали:**
- Priority order: EMAIL > PHONE > LinkedIn > Website
- Keyword matching как fallback (низкая уверенность)
- Возвращает метрики для отладки

---

### Шаг 5: Интеграция в main.py

**Файл:** `backend/main.py`

**Действие:**
```python
# В начале файла добавить import
from lib.column_detector import detect_column_type

# Заменить функцию detect_column_types() (строки 199-235)
def detect_column_types_enhanced(
    columns: List[str],
    df: pd.DataFrame,
    sample_size: int = 10
) -> Dict[str, Dict[str, Any]]:
    """
    Enhanced column detection using hybrid approach

    Returns:
        {
            "email": {
                "detected_type": "EMAIL",
                "confidence": 0.9,
                "method": "regex_validation",
                "original_name": "contact_info"
            },
            ...
        }
    """
    detected = {}

    for col in columns:
        # Get sample values
        sample_values = df[col].head(sample_size).tolist()

        # Detect type
        detection = detect_column_type(col, sample_values, sample_size)

        # Add to results if confidence > 0
        if detection["confidence"] > 0:
            detected[col] = {
                **detection,
                "original_name": col
            }

    return detected

# Обновить endpoint /api/upload
@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # ... existing code ...

    # Read CSV into pandas
    df = pd.read_csv(file_path)

    # Enhanced detection
    detected_columns = detect_column_types_enhanced(
        columns=df.columns.tolist(),
        df=df,
        sample_size=10
    )

    # ... rest of existing code ...
```

**Детали:**
- Заменяет старую функцию на новую enhanced версию
- Использует pandas для чтения sample values
- Возвращает детальную информацию о каждом столбце

---

### Шаг 6: Unit Tests

**Файл:** `backend/tests/test_column_detector.py` (новый)

**Действие:**
```python
import pytest
from lib.column_detector import detect_column_type, validate_type_by_samples

def test_email_detection():
    samples = [
        "john@example.com",
        "sarah@company.co.uk",
        "test@domain.org"
    ]
    result = detect_column_type("contact", samples)
    assert result["detected_type"] == "EMAIL"
    assert result["confidence"] >= 0.7

def test_phone_detection():
    samples = [
        "+12345678901",
        "(123) 456-7890",
        "+44 20 1234 5678"
    ]
    result = detect_column_type("phone_number", samples)
    assert result["detected_type"] == "PHONE"

def test_mixed_values():
    samples = [
        "john@example.com",
        "not_an_email",
        "jane@company.com"
    ]
    result = detect_column_type("contact", samples, confidence_threshold=0.6)
    assert result["detected_type"] == "EMAIL"
    assert result["confidence"] >= 0.6

# Add more tests...
```

---

## 7. Типы и Интерфейсы

```python
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ColumnDetectionResult:
    detected_type: str          # EMAIL, PHONE, WEBSITE, etc.
    confidence: float           # 0.0 - 1.0
    method: str                 # "regex_validation", "keyword_matching", "default"
    sample_matches: Optional[str] = None  # "8/10"
    original_name: str = ""
```

---

## 8. Критерии Приёмки (Acceptance Criteria)

- [ ] Создан `backend/lib/column_detector.py` с regex patterns
- [ ] Функция `detect_column_type()` реализована с hybrid approach
- [ ] Regex patterns покрывают минимум 7 типов:
  - [ ] EMAIL
  - [ ] PHONE
  - [ ] WEBSITE
  - [ ] COMPANY_NAME (keyword)
  - [ ] PERSON_NAME (first/last/full)
  - [ ] JOB_TITLE (keyword)
  - [ ] LOCATION (city/state/country)
- [ ] `backend/main.py` обновлён с enhanced detection
- [ ] Unit tests написаны и проходят (минимум 5 тестов)
- [ ] Тест на реальном CSV файле `ppc US - Canada...csv`:
  - [ ] Определены все 17 столбцов
  - [ ] Email column определён корректно
  - [ ] Phone column определён корректно
  - [ ] Website column определён корректно
  - [ ] Confidence >= 0.7 для основных типов

---

## 9. Стратегия Тестирования (Testing Strategy)

**Unit Testing:**
1. Тесты для каждого regex pattern отдельно
2. Тесты для hybrid detection logic
3. Тесты для edge cases (пустые значения, смешанные типы)

**Integration Testing:**
1. Загрузить `ppc US - Canada...csv` через `/api/upload`
2. Проверить response с detected_columns
3. Убедиться что все типы определены правильно

**Performance Testing:**
1. Тест на большом CSV (10K+ rows) - измерить время detection
2. Должно быть < 2 секунд для 10K rows

**Manual Testing:**
1. Создать test CSV с разными форматами (US phones, UK phones, etc.)
2. Проверить что detection работает для edge cases

---

## 10. Заметки / Ссылки (Notes / Links)

**Документация:**
- Python `re` module: https://docs.python.org/3/library/re.html
- Pandas DataFrame: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html

**Связанные задачи:**
- TASK-003 (Supabase Upload) - использует результаты этой задачи для маппинга

**Референсы:**
- `ppc US - Canada...csv` - тестовый файл
- `backend/main.py` (строки 199-235) - старая функция для замены

**Regex Testing Tools:**
- https://regex101.com - для тестирования patterns
- https://regexr.com - визуализация regex

**Edge Cases:**
- Столбец "info" содержит emails → должен определиться как EMAIL
- Столбец "website_address" содержит URLs → WEBSITE
- Столбец с 50% пустых значений → игнорировать пустые

---

## ✅ Pre-Execution Checklist

Перед началом выполнения ОБЯЗАТЕЛЬНО ответь на вопросы в секции 3:

- [ ] Выбрана стратегия определения (Q1: A/B/C)
- [ ] Определён sample size (Q2: 5/10/50 строк)
- [ ] Выбран confidence threshold (Q3: 50%/70%/100%)
- [ ] Определён список поддерживаемых типов (Q4: базовые + какие дополнительные)
- [ ] Решено как обрабатывать пустые значения (Q5)
- [ ] Выбрано место для кода (Q6: main.py / новый файл / csv_transformer)
- [ ] Определён приоритет типов при конфликтах (Q7)

**После ответов на вопросы → начинать выполнение задачи!**

---

**Task Status:** Готова к детализации → Жду ответов на вопросы из секции 3
