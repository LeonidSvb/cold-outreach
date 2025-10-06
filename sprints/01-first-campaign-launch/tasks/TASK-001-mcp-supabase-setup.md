# TASK-001: MCP Supabase Setup & Testing

---

## Metadata

```yaml
id: "TASK-001"
title: "MCP Supabase Setup & Complete Tool Testing"
status: "in_progress"
priority: "P1"
labels: ["infrastructure", "mcp", "database", "testing"]
dependencies: []
created: "2025-10-03"
updated: "2025-10-03"
assignee: "AI Agent"
```

**Progress Notes:**
- ✅ Q1-Q5 answered by user
- ✅ `.mcp.json` updated with Supabase MCP config
- ✅ SUPABASE_ACCESS_TOKEN added to `.env` (sbp_10b4ce3e77c2fb770870a579e64536a15c90fb79)
- ✅ `.mcp.json` configured with correct ACCESS_TOKEN env variable
- ✅ Local test passed - MCP server starts successfully
- ⏳ Waiting for Claude Code restart to connect and test tools
- 📝 Note: Required SUPABASE_ACCESS_TOKEN instead of SERVICE_ROLE_KEY for MCP

---

## 1. Цель (High-Level Objective)

Настроить Supabase MCP server в Cursor, протестировать все 17 доступных инструментов, создать детальную документацию по работе с каждым tool для будущего использования.

---

## 2. Контекст (Background)

**Проблема:**
- Текущий `.mcp.json` содержит только shadcn, github, filesystem, neon
- Нет Supabase MCP интеграции для прямой работы с БД через AI
- Нет документации какие tools доступны и как их использовать

**Почему важно:**
- Supabase MCP даёт 17 инструментов для управления БД через AI
- Можем создавать таблицы, выполнять SQL, проверять логи прямо в Cursor
- Упростит загрузку CSV → Supabase в следующих задачах

**Документация:**
- GitHub: https://github.com/supabase-community/supabase-mcp
- Supabase MCP URL: `https://mcp.supabase.com/mcp`

---

## 3. 🤔 ВОПРОСЫ ДЛЯ ДЕТАЛИЗАЦИИ (ответить перед началом)

### Перед началом выполнения ответь на эти вопросы:

**Q1: Режим доступа к БД**
- Использовать `read_only=true` (безопасно, только чтение)?
- Или `read_only=false` (полный доступ для записи)?
- **Рекомендация:** Начать с `read_only=true`, потом переключить

**Q2: Скопирование проекта**
- Включить `project_ref=tzxoinrwarvnjmplyevv` в URL?
- Или оставить доступ ко всем проектам?
- **Рекомендация:** Ограничить одним проектом для безопасности

**Q3: Какие feature groups включить?**
Доступны: `account, docs, database, debugging, development, functions, branching, storage`
- Включить все?
- Или только `database,docs,debugging` для начала?
- **Рекомендация:** Минимальный набор `database,docs` для MVP

**Q4: OAuth авторизация**
- У тебя готов браузер для OAuth login через Supabase?
- Какая организация в Supabase нужна (если несколько)?

**Q5: Тестирование**
- Протестировать все 17 tools или только базовые (5-7)?
- Создать test queries для каждого tool?
- **Рекомендация:** Базовые tools обязательно, остальные опционально

---

## 4. Допущения и Ограничения

**ДОПУЩЕНИЯ:**
- Supabase credentials уже есть в `.env` (NEXT_PUBLIC_SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
- Cursor установлен и работает
- Все 9 миграций уже применены в Supabase (из CHANGELOG.md)

**ОГРАНИЧЕНИЯ:**
- Free tier Supabase (512MB)
- MCP требует перезагрузки Cursor после изменения `.mcp.json`
- OAuth может потребовать доступ к браузеру

---

## 5. Plan Контекста (Context Plan)

### В начале (добавить в контекст AI):
- `.mcp.json` _(будет изменён)_
- `.env` _(read-only для SUPABASE_URL)_
- `migrations/*.sql` _(read-only для понимания схемы БД)_

### В конце (должно быть создано):
- `.mcp.json` - обновлён с Supabase MCP
- `docs/mcp/SUPABASE_MCP_GUIDE.md` - полная документация
- `docs/mcp/TOOL_TESTING_RESULTS.md` - результаты тестов каждого tool

---

## 6. Пошаговый План (Low-Level Steps)

### Шаг 1: Обновление `.mcp.json`

**Файл:** `.mcp.json`

**Действие:**
```json
{
  "mcpServers": {
    "shadcn": { ... },
    "github": { ... },
    "filesystem": { ... },
    "neon": { ... },
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp?read_only=true&project_ref=tzxoinrwarvnjmplyevv&features=database,docs,debugging"
    }
  }
}
```

**Детали:**
- Добавить supabase в mcpServers
- URL параметры: `read_only=true`, `project_ref=<твой_проект>`, `features=database,docs,debugging`
- **ВАЖНО:** После изменения перезагрузить Cursor (Cmd/Ctrl+Shift+P → Reload Window)

---

### Шаг 2: OAuth Авторизация

**Действие:**
1. После перезагрузки Cursor появится prompt для OAuth login
2. Открыть браузер → Login to Supabase
3. Выбрать организацию с проектом `tzxoinrwarvnjmplyevv`
4. Подтвердить доступ для MCP client

**Ожидаемый результат:**
- Cursor показывает "Supabase MCP connected"
- В контекстном меню доступны новые tools

---

### Шаг 3: Проверка доступных tools

**Команда:**
```
# В Cursor запросить у AI:
"List all available Supabase MCP tools"
```

**Ожидаемый результат:**
```
Available tools (17):
- list_projects
- get_project
- list_tables
- execute_sql
- apply_migration
- get_logs
- get_advisors
- generate_typescript_types
... (и другие)
```

---

### Шаг 4: Тестирование базовых tools

**Tool 1: list_tables**
```sql
-- Запрос через MCP:
list_tables()

-- Ожидаемый результат:
Tables: users, csv_imports_raw, offers, companies, leads, campaigns, campaign_leads, events, instantly_campaigns_raw, instantly_accounts_raw, instantly_daily_analytics_raw, instantly_emails_raw
```

**Tool 2: execute_sql (read-only)**
```sql
-- Запрос через MCP:
execute_sql("SELECT COUNT(*) FROM users;")

-- Ожидаемый результат:
{ "count": 1 } -- default user
```

**Tool 3: get_project**
```
get_project()

-- Ожидаемый результат:
Project info: name, region, database status
```

**Tool 4: get_logs**
```
get_logs(service_type="postgres", limit=10)

-- Ожидаемый результат:
Recent PostgreSQL logs
```

**Tool 5: generate_typescript_types**
```
generate_typescript_types()

-- Ожидаемый результат:
TypeScript interfaces для всех таблиц
```

---

### Шаг 5: Создание документации

**Файл:** `docs/mcp/SUPABASE_MCP_GUIDE.md`

**Структура:**
```markdown
# Supabase MCP Guide

## Setup
- Configuration in .mcp.json
- OAuth authorization steps

## Available Tools (17)

### Account Tools
- list_projects
- get_project
- ...

### Database Tools
- list_tables
- execute_sql
- apply_migration
- ...

### Debugging Tools
- get_logs
- get_advisors
- ...

## Examples
### Example 1: Query data
```sql
execute_sql("SELECT * FROM companies LIMIT 5;")
```

### Example 2: Create table
```sql
apply_migration("CREATE TABLE test (...)")
```

## Troubleshooting
...
```

---

### Шаг 6: Testing Results Document

**Файл:** `docs/mcp/TOOL_TESTING_RESULTS.md`

**Формат:**
```markdown
# Supabase MCP Tool Testing Results

Tested: 2025-10-03

## Tool: list_tables
- Status: ✅ Success
- Response time: 0.5s
- Result: 12 tables found

## Tool: execute_sql
- Status: ✅ Success
- Query: SELECT COUNT(*) FROM users
- Result: {"count": 1}

... (для каждого протестированного tool)
```

---

## 7. Типы и Интерфейсы

**MCP Configuration:**
```typescript
interface SupabaseMCPConfig {
  type: "http";
  url: string; // https://mcp.supabase.com/mcp?params
}

interface MCPServers {
  supabase: SupabaseMCPConfig;
  // ... other servers
}
```

---

## 8. Критерии Приёмки (Acceptance Criteria)

**Setup & Configuration:**
- [x] `.mcp.json` содержит Supabase MCP конфигурацию
- [x] `SUPABASE_ACCESS_TOKEN` добавлен в `.env`
- [x] `.mcp.json` использует правильную env переменную
- [x] Локальный тест MCP сервера пройден (server starts)
- [x] Claude Code restart выполнен
- [x] Supabase MCP сервер подключен в Claude Code (status: connected)

**Tool Testing:**
- [x] Claude Code показывает доступные Supabase MCP tools
- [x] Минимум 5 базовых tools протестированы:
  - [x] `list_projects` - вернул 2 проекта (Outreach Engine + leo's Project)
  - [x] `list_tables` - вернул 13 таблиц в public schema
  - [x] `execute_sql` - выполнил SELECT query (COUNT users = 1)
  - [x] `get_project` - вернул project info (status: ACTIVE_HEALTHY)
  - [x] `get_project_url` - вернул API URL (https://tzxoinrwarvnjmplyevv.supabase.co)
  - [x] `get_logs` - показал PostgreSQL connection logs (15 записей)
  - [x] `generate_typescript_types` - сгенерировал полные типы для всех таблиц

**Test Results Summary:**
- Project ID: `tzxoinrwarvnjmplyevv` (Outreach Engine)
- Database Version: PostgreSQL 17.6.1.008
- Tables Found: 13 (users, companies, leads, campaigns, offers, instantly_*, csv_imports_raw, etc.)
- TypeScript Types: Successfully generated with full Database interface
- Logs Access: Working (показывает real-time PostgreSQL logs)
- SQL Execution: Working (SELECT queries tested successfully)

**Documentation:**
- [ ] `docs/mcp/SUPABASE_MCP_GUIDE.md` создан с примерами
- [ ] `docs/mcp/TOOL_TESTING_RESULTS.md` содержит результаты всех тестов
- [ ] Документация содержит troubleshooting секцию

---

## 9. Стратегия Тестирования (Testing Strategy)

**Manual Testing:**
1. После setup запросить у AI: "Use Supabase MCP to list all tables"
2. Проверить что возвращаются таблицы из миграций
3. Выполнить простой SELECT query через `execute_sql`
4. Проверить read-only mode (попытка INSERT должна быть запрещена)

**Integration Testing:**
1. Убедиться что MCP работает с существующими таблицами
2. Проверить что можно читать данные
3. Проверить что `generate_typescript_types` создаёт валидные типы

**Documentation Testing:**
1. Проверить что все примеры в GUIDE.md работают
2. Убедиться что troubleshooting секция содержит решения частых проблем

---

## 10. Заметки / Ссылки (Notes / Links)

**Документация:**
- Supabase MCP GitHub: https://github.com/supabase-community/supabase-mcp
- MCP Protocol: https://modelcontextprotocol.io
- Supabase Dashboard: https://supabase.com/dashboard/project/tzxoinrwarvnjmplyevv

**Связанные задачи:**
- TASK-003 (Supabase Upload Backend) - будет использовать знания из этой задачи

**Референсы:**
- `.env` - Supabase credentials
- `migrations/*.sql` - Схема БД для тестирования queries

**Security Note:**
- Не коммитить API keys в `.mcp.json` (они уже в `.env`)
- Read-only mode для безопасности при первом тестировании

---

## ✅ Pre-Execution Checklist

Перед началом выполнения ОБЯЗАТЕЛЬНО ответь на вопросы в секции 3:

- [ ] Определён режим доступа (read_only true/false)
- [ ] Выбран project_ref или access to all projects
- [ ] Выбраны feature groups для URL
- [ ] Готов браузер для OAuth login
- [ ] Определён объём тестирования (все 17 или базовые 5-7 tools)

**После ответов на вопросы → начинать выполнение задачи!**

---

**Task Status:** Готова к детализации → Жду ответов на вопросы из секции 3
