# SQL Migrations для Supabase

## 🎯 Migration Strategy

### Multiple Files Approach (Industry Standard)
We use **separate numbered migration files** instead of a single file:

**Benefits:**
- Easy to track what's applied (001 done, 002 done, 003 pending...)
- Git history shows database evolution clearly
- Can rollback individual migrations without affecting others
- Each file has single responsibility (one purpose)
- Team collaboration is easier (no merge conflicts)

**Naming Convention:**
```
migrations/001_users_table.sql
migrations/002_instantly_raw_layer.sql
migrations/003_csv_imports_raw.sql
migrations/004_offers.sql
...
```

**Location:** All migration files are in `/migrations/` folder in project root (industry standard)

### How to Track Applied Migrations

**Check what tables exist:**
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

**Check specific table:**
```sql
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name = 'offers'
);
```

---

## 📐 Database Architecture

### Two-Layer Design

**RAW LAYER** (Migrations 001-002):
- Preserves full API responses in JSONB
- Never modified after insert
- Source of truth for external data
- Tables: `instantly_campaigns_raw`, `instantly_accounts_raw`, etc.

**NORMALIZED LAYER** (Migrations 003-009):
- Structured business logic tables
- Foreign keys and relationships
- Optimized for queries and reports
- Tables: `offers`, `companies`, `leads`, `campaigns`, `events`

**Why separate layers?**
- Raw layer protects against data loss
- Normalized layer optimized for application logic
- Can reprocess normalized data from raw if schema changes

---

## 📊 Complete Migration Map

| Migration | Table | Purpose | Status |
|-----------|-------|---------|--------|
| 001 | users | Single user, multi-user ready | ✅ Applied |
| 002 | instantly_*_raw | Raw Instantly API data | ✅ Applied |
| 003 | csv_imports_raw | Preserve original CSV uploads | ⏳ Pending |
| 004 | offers | What we sell | ⏳ Pending |
| 005 | companies | Deduplicated company data | ⏳ Pending |
| 006 | leads | People to contact | ⏳ Pending |
| 007 | campaigns | Email/call campaigns | ⏳ Pending |
| 008 | campaign_leads | M2M workflow tracking | ⏳ Pending |
| 009 | events | Multi-source event timeline | ⏳ Pending |

---

## 📋 Порядок выполнения

### Migration 001: Users Table
**Файл:** `migrations/001_users_table.sql`
**Что делает:**
- Создаёт таблицу `users` (single-user mode)
- Добавляет дефолтного пользователя
- Настраивает RLS для будущего multi-user

**Запуск:**
1. Открой Supabase Dashboard → SQL Editor
2. Скопируй весь код из `migrations/001_users_table.sql`
3. Нажми "Run"
4. Проверь: `SELECT * FROM users;` — должен быть 1 пользователь

---

### Migration 002: Instantly Raw Layer
**Файл:** `migrations/002_instantly_raw_layer.sql`
**Что делает:**
- Создаёт 4 таблицы для сырых данных из Instantly:
  - `instantly_campaigns_raw` (кампании)
  - `instantly_accounts_raw` (почтовые аккаунты)
  - `instantly_daily_analytics_raw` (дневная статистика)
  - `instantly_emails_raw` (email события - пустая пока)

**Запуск:**
1. Supabase Dashboard → SQL Editor
2. Скопируй весь код из `migrations/002_instantly_raw_layer.sql`
3. Нажми "Run"
4. Проверь: `SELECT table_name FROM information_schema.tables WHERE table_schema='public';`

---

### Migration 003: CSV Imports Raw
**Файл:** `migrations/003_csv_imports_raw.sql`
**Что делает:**
- Создаёт таблицу `csv_imports_raw`
- Сохраняет полные CSV файлы в JSONB (для reprocessing)
- Отслеживает статус импорта и ошибки

**Зачем:**
- Можно переобработать данные если схема поменялась
- История всех загрузок
- Leads ссылаются на csv_import_id (откуда взялся lead)

**Запуск:**
1. Supabase Dashboard → SQL Editor
2. Скопируй код из `migrations/003_csv_imports_raw.sql`
3. Run
4. Проверь: `SELECT file_name, total_rows, import_status FROM csv_imports_raw;`

---

### Migration 004: Offers
**Файл:** `migrations/004_offers.sql`
**Что делает:**
- Создаёт таблицу `offers`
- Описывает что мы продаём (services, products)
- Pricing, target audience, messaging templates

**Зачем:**
- Один offer можно использовать в нескольких campaigns
- Вся информация о продукте в одном месте
- Auto-seed: создаёт example offer "AI Automation Services"

**Запуск:**
1. Supabase Dashboard → SQL Editor
2. Скопируй код из `migrations/004_offers.sql`
3. Run
4. Проверь: `SELECT offer_name, price_min, price_max FROM offers;`

---

### Migration 005: Companies
**Файл:** `migrations/005_companies.sql`
**Что делает:**
- Создаёт таблицу `companies`
- UNIQUE constraint на `company_domain` (предотвращает дубликаты)
- Хранит Apollo data, технологии, location

**Зачем:**
- 26% leads работают в одинаковых компаниях (доказано анализом CSV)
- Избегаем дублирования company data
- Один lead = одна company (leads.company_id FK)

**Запуск:**
1. Supabase Dashboard → SQL Editor
2. Скопируй код из `migrations/005_companies.sql`
3. Run
4. Проверь: `SELECT company_name, company_domain, industry FROM companies;`

---

### Migration 006: Leads
**Файл:** `migrations/006_leads.sql`
**Что делает:**
- Создаёт таблицу `leads`
- FK к `companies` (company_id)
- FK к `csv_imports_raw` (csv_import_id)
- Полная информация о человеке: email, phone, job_title, seniority

**Зачем:**
- Люди, которым мы пишем
- Связь с company (multiple leads → one company)
- Apollo data preserved в JSONB
- Lead scoring и lifecycle status

**Запуск:**
1. Supabase Dashboard → SQL Editor
2. Скопируй код из `migrations/006_leads.sql`
3. Run
4. Проверь:
```sql
SELECT l.full_name, l.email, c.company_name
FROM leads l
JOIN companies c ON l.company_id = c.id;
```

---

### Migration 007: Campaigns
**Файл:** `migrations/007_campaigns.sql`
**Что делает:**
- Создаёт таблицу `campaigns`
- FK к `offers` (offer_id)
- Поддержка multi-channel: email, calls, LinkedIn
- Instantly integration (instantly_campaign_id)
- VAPI integration (vapi_campaign_id)

**Зачем:**
- Наши внутренние campaigns (не привязаны к Instantly)
- Один campaign может использовать Instantly + VAPI + LinkedIn
- Email/call templates
- Auto-seed: создаёт example campaign

**Запуск:**
1. Supabase Dashboard → SQL Editor
2. Скопируй код из `migrations/007_campaigns.sql`
3. Run
4. Проверь:
```sql
SELECT c.campaign_name, o.offer_name, c.uses_email, c.uses_calls
FROM campaigns c
JOIN offers o ON c.offer_id = o.id;
```

---

### Migration 008: Campaign Leads (M2M)
**Файл:** `migrations/008_campaign_leads.sql`
**Что делает:**
- Создаёт таблицу `campaign_leads`
- Many-to-Many: campaigns ↔ leads
- UNIQUE constraint: один lead только один раз в одном campaign
- Workflow statuses: `email_status`, `call_status`, `linkedin_status`
- Sequence tracking (step 1, 2, 3...)

**Зачем:**
- Отслеживание Email → No reply → Call workflow
- Engagement scoring
- Next followup tracking
- One lead can be in multiple campaigns (different offers)

**Запуск:**
1. Supabase Dashboard → SQL Editor
2. Скопируй код из `migrations/008_campaign_leads.sql`
3. Run
4. Проверь:
```sql
SELECT
    c.campaign_name,
    l.full_name,
    cl.email_status,
    cl.call_status,
    cl.sequence_step
FROM campaign_leads cl
JOIN campaigns c ON cl.campaign_id = c.id
JOIN leads l ON cl.lead_id = l.id;
```

---

### Migration 009: Events (Multi-Source)
**Файл:** `migrations/009_events.sql`
**Что делает:**
- Создаёт таблицу `events`
- Unified timeline всех взаимодействий с leads
- `event_source`: instantly, vapi, linkedin, manual, system
- Service-specific fields: email_subject, call_duration, linkedin_message_text
- Helper functions: `get_lead_timeline()`, `get_campaign_event_stats()`

**Зачем:**
- Один lead = один timeline (все events в хронологии)
- Легко добавить новые sources (просто новое значение event_source)
- Не нужны UNION queries по разным таблицам
- Full-text search по email/call transcripts

**Запуск:**
1. Supabase Dashboard → SQL Editor
2. Скопируй код из `migrations/009_events.sql`
3. Run
4. Проверь:
```sql
-- Event distribution by source
SELECT event_source, event_type, COUNT(*)
FROM events
GROUP BY event_source, event_type;

-- Lead timeline (example)
SELECT * FROM get_lead_timeline(
    (SELECT id FROM leads LIMIT 1)
);
```

---

## 🔍 Проверка миграций

### Список всех таблиц
```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Ожидаемый результат:
- `users`
- `instantly_campaigns_raw`
- `instantly_accounts_raw`
- `instantly_daily_analytics_raw`
- `instantly_emails_raw`

---

## 📊 Тестовая вставка данных

### Test: Insert user
```sql
INSERT INTO users (email, full_name, organization)
VALUES ('test@example.com', 'Test User', 'Test Org');
```

### Test: Insert raw campaign
```sql
INSERT INTO instantly_campaigns_raw (
    instantly_campaign_id,
    campaign_name,
    campaign_status,
    raw_json
) VALUES (
    'test-campaign-123',
    'Test Campaign',
    2,
    '{"campaign_name": "Test", "leads_count": 100}'::jsonb
);
```

### Test: Query JSONB
```sql
-- Все кампании с более 500 leads
SELECT
    campaign_name,
    (raw_json->>'leads_count')::integer as leads
FROM instantly_campaigns_raw
WHERE (raw_json->>'leads_count')::integer > 500;
```

---

## 🛠️ Добавление новых колонок (в будущем)

Если нужно добавить колонку:

```sql
ALTER TABLE instantly_campaigns_raw
ADD COLUMN new_field TEXT;
```

**Безопасно:** Все данные хранятся в `raw_json`, новые колонки — только для удобства query.

---

## ⚠️ Важно

1. **Всегда запускай миграции по порядку** (001 → 002 → 003...)
2. **Не меняй `raw_json` вручную** — это священное поле с полными данными из API
3. **Dependencies:** Некоторые миграции зависят от других:
   - 005-009 зависят от 003 (csv_imports_raw)
   - 006 зависит от 005 (companies)
   - 007 зависит от 004 (offers)
   - 008 зависит от 006, 007 (leads, campaigns)
   - 009 зависит от 006, 007, 008 (leads, campaigns, campaign_leads)
4. **Проверяй перед каждой миграцией:**
   ```sql
   -- Список существующих таблиц
   SELECT table_name FROM information_schema.tables
   WHERE table_schema='public' ORDER BY table_name;
   ```

---

## 🔄 Rollback (если нужно откатить миграцию)

### Откат одной таблицы
```sql
DROP TABLE IF EXISTS table_name CASCADE;
```
**Важно:** `CASCADE` удалит все зависимые объекты (foreign keys, indexes)

### Откат migration 009 (Events)
```sql
DROP FUNCTION IF EXISTS get_lead_timeline(UUID);
DROP FUNCTION IF EXISTS get_campaign_event_stats(UUID);
DROP TABLE IF EXISTS events CASCADE;
```

### Откат migration 008 (Campaign Leads)
```sql
DROP TABLE IF EXISTS campaign_leads CASCADE;
```

### Откат migration 007 (Campaigns)
```sql
DROP TABLE IF EXISTS campaigns CASCADE;
```

### Откат migration 006 (Leads)
```sql
DROP TABLE IF EXISTS leads CASCADE;
```

### Откат migration 005 (Companies)
```sql
DROP TABLE IF EXISTS companies CASCADE;
```

### Откат migration 004 (Offers)
```sql
DROP FUNCTION IF EXISTS update_offers_updated_at();
DROP TABLE IF EXISTS offers CASCADE;
```

### Откат migration 003 (CSV Imports Raw)
```sql
DROP TABLE IF EXISTS csv_imports_raw CASCADE;
```

**Порядок отката:** Всегда откатывай в обратном порядке (009 → 008 → 007 → ... → 001)

---

## 📈 Следующие шаги

### После выполнения migrations 001-002 (Raw Layer)
1. ✅ Raw data tables готовы
2. 🔄 Создать `modules/instantly/` sync scripts
3. 🧪 Тестировать sync на sample JSON data

### После выполнения migrations 003-009 (Normalized Layer)
1. ✅ Все таблицы созданы
2. 📊 Создать Python script для CSV import (CSV → csv_imports_raw → companies + leads)
3. 🔄 Создать Instantly sync service (instantly_raw → events)
4. 🚀 Подключить backend FastAPI к Supabase
5. 🎨 Создать Frontend dashboards для campaigns/leads
6. 📞 Интегрировать VAPI для calls (events с event_source='vapi')

### Приоритет выполнения (рекомендация)
1. Migrations 003-006 (CSV imports, offers, companies, leads) — **основа данных**
2. Migration 007 (campaigns) — **для запуска кампаний**
3. Migration 008 (campaign_leads) — **workflow tracking**
4. Migration 009 (events) — **unified timeline**
