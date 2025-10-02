# SQL Migrations для Supabase

## 📋 Порядок выполнения

### Migration 001: Users Table
**Файл:** `001_users_table.sql`
**Что делает:**
- Создаёт таблицу `users` (single-user mode)
- Добавляет дефолтного пользователя
- Настраивает RLS для будущего multi-user

**Запуск:**
1. Открой Supabase Dashboard → SQL Editor
2. Скопируй весь код из `001_users_table.sql`
3. Нажми "Run"
4. Проверь: `SELECT * FROM users;` — должен быть 1 пользователь

---

### Migration 002: Instantly Raw Layer
**Файл:** `002_instantly_raw_layer.sql`
**Что делает:**
- Создаёт 4 таблицы для сырых данных из Instantly:
  - `instantly_campaigns_raw` (кампании)
  - `instantly_accounts_raw` (почтовые аккаунты)
  - `instantly_daily_analytics_raw` (дневная статистика)
  - `instantly_emails_raw` (email события - пустая пока)

**Запуск:**
1. Supabase Dashboard → SQL Editor
2. Скопируй весь код из `002_instantly_raw_layer.sql`
3. Нажми "Run"
4. Проверь: `SELECT table_name FROM information_schema.tables WHERE table_schema='public';`

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
3. **Если что-то сломалось:**
   ```sql
   DROP TABLE IF EXISTS table_name CASCADE;
   -- Потом запусти миграцию заново
   ```

---

## 📈 Следующие шаги

После выполнения 001 и 002:
1. ✅ Таблицы созданы
2. 🔄 Создать Python скрипт для синхронизации (Instantly API → Supabase)
3. 🗂️ Спланировать нормализованный слой (campaigns, leads, events)
4. 🚀 Подключить backend к Supabase
