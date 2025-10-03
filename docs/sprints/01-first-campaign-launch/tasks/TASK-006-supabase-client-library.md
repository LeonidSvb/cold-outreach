# TASK-006: Supabase Client Library Setup

---

## Metadata

```yaml
id: "TASK-006"
title: "Create Supabase Client Library for Backend Services"
status: "done"
priority: "P1"
labels: ["backend", "database", "infrastructure"]
dependencies: []
created: "2025-10-03"
completed: "2025-10-03"
assignee: "AI Agent"
```

---

## 1. Цель (High-Level Objective)

Создать переиспользуемую Python библиотеку для подключения к Supabase из всех backend services с единой точкой конфигурации и error handling.

---

## 2. Контекст (Background)

**Проблема:**
- Нет централизованного способа подключения к Supabase из Python
- Каждый скрипт будет дублировать код подключения

**Почему важно:**
- Все backend services нуждаются в Supabase client
- DRY principle - одна библиотека для всех

---

## 3. Допущения и Ограничения

**ДОПУЩЕНИЯ:**
- `.env` файл содержит `NEXT_PUBLIC_SUPABASE_URL` и `SUPABASE_SERVICE_ROLE_KEY`
- Python 3.12 установлен

**ОГРАНИЧЕНИЯ:**
- Free tier Supabase (512MB)
- Синхронный API

---

## 4. Зависимости (Dependencies)

- [ ] `.env` файл с Supabase credentials
- [ ] `backend/requirements.txt` существует

---

## 5. Plan Контекста (Context Plan)

### В начале:
- `.env` _(read-only)_
- `backend/requirements.txt` _(будет изменён)_

### В конце:
- `backend/lib/supabase_client.py`
- `backend/lib/__init__.py`

---

## 6. Пошаговый План (Low-Level Steps)

### Шаг 1: Create lib structure

**Действие:**
```bash
mkdir -p backend/lib
touch backend/lib/__init__.py
```

### Шаг 2: Add dependency

**Файл:** `backend/requirements.txt`
```txt
supabase==2.3.4
python-dotenv==1.0.0
```

### Шаг 3: Create client library

**Файл:** `backend/lib/supabase_client.py`

```python
import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_client: Optional[Client] = None

def get_supabase() -> Client:
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not found in environment")

    _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client

def upsert_rows(table: str, rows: List[Dict[str, Any]],
                on_conflict: str = "id") -> Dict[str, Any]:
    try:
        supabase = get_supabase()
        response = supabase.table(table).upsert(rows, on_conflict=on_conflict).execute()

        return {
            "success": True,
            "upserted": len(rows),
            "data": response.data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def query_table(table: str, filters: Optional[Dict] = None,
                limit: int = 100) -> Dict[str, Any]:
    try:
        supabase = get_supabase()
        query = supabase.table(table).select("*")

        if filters:
            for col, val in filters.items():
                query = query.eq(col, val)

        response = query.limit(limit).execute()

        return {
            "success": True,
            "count": len(response.data),
            "data": response.data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### Шаг 4: Test connection

**Команда:**
```bash
cd backend
python -c "from lib.supabase_client import get_supabase; print(get_supabase())"
```

---

## 7. Критерии Приёмки

- [x] `backend/lib/supabase_client.py` создан
- [x] `get_supabase()` подключается успешно
- [x] `upsert_rows()` и `query_table()` работают
- [x] Test connection passes

---

## 8. Стратегия Тестирования

**Manual Test:**
```python
from lib.supabase_client import get_supabase, query_table

result = query_table('users', limit=1)
assert result['success'] == True
```

---

## 9. Результаты Выполнения

**Дата завершения:** 2025-10-03

**Что создано:**
- `backend/lib/__init__.py` - init файл для модуля
- `backend/lib/supabase_client.py` - централизованная библиотека подключения к Supabase

**Обновлено:**
- `backend/requirements.txt`: добавлены `supabase>=2.20.0`, `pydantic>=2.11.9`

**Тесты пройдены:**
- ✅ Подключение к Supabase: https://tzxoinrwarvnjmplyevv.supabase.co
- ✅ Запрос к таблице users: вернул 1 запись
- ✅ Singleton pattern работает (переиспользование подключения)
- ✅ Error handling для missing credentials работает

**Команда для проверки:**
```bash
cd backend
py lib/supabase_client.py
```

**Готово к использованию в:** TASK-007, TASK-008, TASK-009

---

**Task Version:** 1.0
