# SQL Migrations для Supabase

## 📊 Migration Status

| Migration | Table | Status | Dependencies |
|-----------|-------|--------|--------------|
| 001 | users | ✅ Applied | None |
| 002 | instantly_*_raw (4 tables) | ✅ Applied | 001 |
| 003 | csv_imports_raw | ⏳ Ready | None |
| 004 | offers | ⏳ Ready | None |
| 005 | companies | ⏳ Ready | None |
| 006 | leads | ⏳ Ready | 005 |
| 007 | campaigns | ⏳ Ready | 004 |
| 008 | campaign_leads | ⏳ Ready | 006, 007 |
| 009 | events | ⏳ Ready | 006, 007, 008 |

## 🚀 How to Apply

**Order:** 003 → 004 → 005 → 006 → 007 → 008 → 009

**Steps:**
1. Open Supabase Dashboard → SQL Editor
2. Copy code from `migrations/00X_*.sql`
3. Run
4. Check table created: `SELECT * FROM table_name LIMIT 1;`

**Recommended batches:**
- Batch 1: 003-006 (CSV + companies + leads)
- Batch 2: 007-008 (Campaigns + workflow)
- Batch 3: 009 (Events timeline)

## 🔄 Rollback

```sql
-- Reverse order: 009 → 008 → 007 → 006 → 005 → 004 → 003
DROP TABLE IF EXISTS table_name CASCADE;
```

## 📐 Architecture

**RAW LAYER** (001-002):
- `users` - Single user (multi-user ready)
- `instantly_campaigns_raw` - Campaign data from Instantly API
- `instantly_accounts_raw` - Email accounts
- `instantly_daily_analytics_raw` - Daily metrics
- `instantly_emails_raw` - Email events (empty for now)

**NORMALIZED LAYER** (003-009):
- `csv_imports_raw` - Original CSV uploads (JSONB)
- `offers` - What we sell
- `companies` - Deduplicated companies (UNIQUE domain)
- `leads` - People to contact (FK to companies)
- `campaigns` - Email/call campaigns (FK to offers)
- `campaign_leads` - M2M: which leads in which campaigns + workflow status
- `events` - Unified timeline (instantly, vapi, linkedin, manual)

**Key patterns:**
- `source_type` + `source_id` + `raw_data` JSONB = universal source tracking
- `company_domain` UNIQUE = deduplication (26% of leads share companies)
- `event_source` = multi-channel timeline (instantly/vapi/linkedin/manual)

## 📝 Track Applied Migrations

```sql
-- List all tables
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' ORDER BY table_name;

-- Check specific table exists
SELECT EXISTS (
    SELECT FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = 'offers'
);
```

---

**All migration files:** `/migrations/001_*.sql` to `/migrations/009_*.sql`

**Detailed structure:** See `STRUCTURE.md`
