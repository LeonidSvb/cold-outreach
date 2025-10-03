# Task Template

**ИНСТРУКЦИЯ:** Этот файл - шаблон для создания задач. Копируй его и заполняй для каждой новой задачи.

---

## Metadata

```yaml
id: "TASK-XXX"              # Например: TASK-001, TASK-002
title: "{{НАЗВАНИЕ_ЗАДАЧИ}}"  # Например: "Setup Supabase Database Schema"
status: "planned"           # planned | in_progress | blocked | completed
priority: "P1"              # P0 (critical) | P1 (high) | P2 (medium) | P3 (low)
labels: ["backend", "database"]  # Теги для категоризации
dependencies: []            # Список task-файлов, которые должны быть выполнены первыми
created: "2025-10-02"
updated: "2025-10-02"       # Последнее обновление (обновляется при каждом изменении)
assignee: "AI Agent"        # Кто выполняет (обычно AI Agent или твоё имя)
```

**Progress Notes:**
_(AI Agent автоматически обновляет эту секцию по мере выполнения)_
- ✅ Completed step 1
- ✅ Completed step 2
- ⏳ In progress step 3
- ⚠️ Blocked by issue X
- 🔄 Requires restart/reload (e.g., Claude Code, backend server)

**AI Agent Instructions:**
- Update `status` field as work progresses
- Update `updated` timestamp on every change
- Mark checkboxes `[ ]` → `[x]` in Acceptance Criteria when completed
- Add Progress Notes after metadata block
- Note any blockers, restarts needed, or manual steps required

---

## 1. Цель (High-Level Objective)

**Что нужно сделать одним предложением:**

{{КРАТКОЕ_ОПИСАНИЕ_ЦЕЛИ}}

Например: "Создать и выполнить SQL миграции для настройки базы данных Supabase с таблицами для хранения сырых данных из Instantly API"

---

## 2. Контекст (Background)

**Почему это важно? Какая проблема решается?**

{{КОНТЕКСТ_И_ОБОСНОВАНИЕ}}

Например: "Текущая система не имеет базы данных для хранения данных кампаний. CSV файлы теряются при редеплое на Vercel. Нужна постоянная база данных для аналитики и отслеживания метрик."

---

## 3. Допущения и Ограничения

**Что мы предполагаем? Какие есть ограничения?**

- **ДОПУЩЕНИЕ:** {{ДОПУЩЕНИЕ_1}}
- **ОГРАНИЧЕНИЕ:** {{ОГРАНИЧЕНИЕ_1}}
- **ОГРАНИЧЕНИЕ:** {{ОГРАНИЧЕНИЕ_2}}

Например:
- **ДОПУЩЕНИЕ:** Supabase уже создан и credentials доступны в .env
- **ОГРАНИЧЕНИЕ:** Free tier Supabase (512MB)
- **ОГРАНИЧЕНИЕ:** Используем PostgreSQL 15

---

## 4. Зависимости (Dependencies)

**Какие другие задачи или файлы должны существовать?**

- [ ] {{ЗАВИСИМОСТЬ_1}}
- [ ] {{ЗАВИСИМОСТЬ_2}}

Например:
- [ ] Supabase project создан
- [ ] Environment variables настроены (.env файл)
- [ ] `docs/sql/README.md` прочитан

---

## 5. Plan Контекста (Context Plan)

**Какие файлы нужны в начале? Что должно существовать в конце?**

### В начале (добавить в контекст AI):
- `{{ФАЙЛ_1}}` _(read-only для справки)_
- `{{ФАЙЛ_2}}` _(будет изменён)_

Например:
- `docs/sql/001_users_table.sql` _(read-only)_
- `docs/sql/002_instantly_raw_layer.sql` _(read-only)_
- `.env` _(read-only для SUPABASE_URL)_

### В конце (должно быть создано/изменено):
- `{{ВЫХОДНОЙ_ФАЙЛ_1}}`
- `{{ВЫХОДНОЙ_ФАЙЛ_2}}`

Например:
- Таблицы созданы в Supabase
- `backend/lib/supabase_client.py` создан
- Тестовые данные вставлены

---

## 6. Пошаговый План (Low-Level Steps)

**Конкретные, атомарные шаги с точными путями, командами, кодом.**

### Шаг 1: {{НАЗВАНИЕ_ШАГА_1}}

**Файл:** `{{ПУТЬ_К_ФАЙЛУ}}`

**Действие:**
```sql
-- Пример для SQL задачи
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL
);
```

**Детали:**
- {{ДЕТАЛЬ_1}}
- {{ДЕТАЛЬ_2}}

---

### Шаг 2: {{НАЗВАНИЕ_ШАГА_2}}

**Файл:** `{{ПУТЬ_К_ФАЙЛУ}}`

**Действие:**
```python
# Пример для Python задачи
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)
```

**Детали:**
- {{ДЕТАЛЬ_1}}
- {{ДЕТАЛЬ_2}}

---

### Шаг 3: Тестирование

**Команда:**
```bash
# Пример команды для проверки
python backend/test_supabase_connection.py
```

**Ожидаемый результат:**
- {{РЕЗУЛЬТАТ_1}}
- {{РЕЗУЛЬТАТ_2}}

---

## 7. Типы и Интерфейсы (если применимо)

**Определить типы данных, интерфейсы, схемы.**

```typescript
// Для TypeScript задач
export interface Campaign {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'stopped';
}
```

```python
# Для Python задач
from dataclasses import dataclass

@dataclass
class Campaign:
    id: str
    name: str
    status: str
```

---

## 8. Критерии Приёмки (Acceptance Criteria)

**Как проверить что задача выполнена? Конкретные, проверяемые условия.**

- [ ] {{КРИТЕРИЙ_1}}
- [ ] {{КРИТЕРИЙ_2}}
- [ ] {{КРИТЕРИЙ_3}}

Например:
- [ ] Все SQL миграции выполнены без ошибок
- [ ] `SELECT * FROM users;` возвращает таблицу с default user
- [ ] `backend/lib/supabase_client.py` экспортирует `get_supabase()` функцию
- [ ] Тестовый запрос `supabase.table('users').select('*').execute()` работает

---

## 9. Стратегия Тестирования (Testing Strategy)

**Как тестировать? Интеграционные тесты, unit тесты, ручное тестирование?**

- {{ПОДХОД_К_ТЕСТИРОВАНИЮ_1}}
- {{ПОДХОД_К_ТЕСТИРОВАНИЮ_2}}

Например:
- Ручное тестирование: выполнить SQL queries в Supabase SQL Editor
- Интеграционный тест: запустить Python скрипт для проверки подключения
- Проверить через Supabase UI: таблицы видны в Database section

---

## 10. Заметки / Ссылки (Notes / Links)

**Дополнительная информация, ссылки на спецификации, связанные задачи.**

- **Документация:** {{ССЫЛКА_НА_DOCS}}
- **Связанные задачи:** {{СВЯЗАННЫЕ_ТАСКИ}}
- **Референсы:** {{ПОЛЕЗНЫЕ_ССЫЛКИ}}

Например:
- **Документация:** `docs/sql/README.md`
- **Связанные задачи:** TASK-002 (Supabase Client)
- **Референсы:** [Supabase SQL Editor](https://supabase.com/docs/guides/database)

---

## ✅ Checklist для создания задачи

Перед сохранением задачи убедись что:

- [ ] Заполнен metadata блок (id, title, status, priority)
- [ ] Цель описана одним предложением
- [ ] Контекст объясняет "почему"
- [ ] Допущения и ограничения указаны
- [ ] Зависимости перечислены
- [ ] Context Plan содержит файлы in/out
- [ ] Пошаговый план конкретен (файлы, команды, код)
- [ ] Критерии приёмки проверяемы
- [ ] Стратегия тестирования ясна
- [ ] Названия файлов точные (полные пути)
- [ ] Код примеры синтаксически корректны

---

## 🎯 Пример заполненной задачи

Смотри файл: `01-setup-supabase-database.md` (когда будет создан)

Или используй этот шаблон как базу и заполняй секции по мере создания задачи.

---

**Template Version:** 1.0
**Last Updated:** 2025-10-02
