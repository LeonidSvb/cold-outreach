# Database Structure Overview

## 🏗️ RAW LAYER (Instantly Data)

```
┌─────────────────────────────────────────────────────────────┐
│                      RAW DATA LAYER                          │
│              (Instantly API → Supabase)                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐
│  instantly_campaigns_raw         │
├──────────────────────────────────┤
│  instantly_campaign_id (PK)      │ ← Instantly campaign ID
│  campaign_name                   │
│  campaign_status                 │
│  leads_count                     │
│  contacted_count                 │
│  reply_count                     │
│  emails_sent_count               │
│  raw_json (JSONB) ★              │ ← Full API response
│  synced_at                       │
│  created_at                      │
│  updated_at                      │
└──────────────────────────────────┘
        │
        │ Source: /api/v2/campaigns/analytics
        │ Contains: Campaign overview, metrics
        │


┌──────────────────────────────────┐
│  instantly_accounts_raw          │
├──────────────────────────────────┤
│  email (PK)                      │ ← Unique sender email
│  first_name                      │
│  last_name                       │
│  account_status                  │
│  warmup_status                   │
│  warmup_score                    │
│  raw_json (JSONB) ★              │ ← Full API response
│  synced_at                       │
│  created_at                      │
│  updated_at                      │
└──────────────────────────────────┘
        │
        │ Source: /api/v2/accounts
        │ Contains: Email account details, warmup info
        │


┌──────────────────────────────────┐
│  instantly_daily_analytics_raw   │
├──────────────────────────────────┤
│  id (PK)                         │
│  analytics_date                  │ ← UNIQUE per date
│  instantly_campaign_id (opt)     │
│  sent                            │
│  opened                          │
│  unique_opened                   │
│  replies                         │
│  unique_replies                  │
│  clicks                          │
│  unique_clicks                   │
│  raw_json (JSONB) ★              │ ← Full API response
│  synced_at                       │
│  created_at                      │
└──────────────────────────────────┘
        │
        │ Source: /api/v2/campaigns/analytics/daily
        │ Contains: Aggregated daily metrics
        │


┌──────────────────────────────────┐
│  instantly_emails_raw            │
├──────────────────────────────────┤
│  id (PK)                         │
│  instantly_email_id (unique)     │
│  instantly_campaign_id           │
│  email_address                   │
│  event_type                      │ ← sent, opened, replied...
│  event_date                      │
│  raw_json (JSONB) ★              │ ← Full API response
│  synced_at                       │
│  created_at                      │
└──────────────────────────────────┘
        │
        │ Source: /api/v2/emails
        │ Contains: Individual email events
        │ Status: Empty for now (prepared for future)


┌──────────────────────────────────┐
│  users                           │
├──────────────────────────────────┤
│  id (PK)                         │
│  email (unique)                  │
│  full_name                       │
│  organization                    │
│  created_at                      │
│  updated_at                      │
└──────────────────────────────────┘
        │
        │ Current: 1 user (single-user mode)
        │ Future: Multi-user with Supabase Auth
        │
```

---

## 📊 JSONB Storage Strategy

### Why JSONB for `raw_json`?

**Advantages:**
- ✅ Never lose any data from API
- ✅ Instantly API changes don't break our DB
- ✅ Can query nested JSON fields
- ✅ Historical data preservation

**Example Query:**
```sql
-- Get campaigns with more than 500 leads
SELECT
    campaign_name,
    (raw_json->>'leads_count')::integer as leads,
    (raw_json->>'reply_count')::integer as replies
FROM instantly_campaigns_raw
WHERE (raw_json->>'leads_count')::integer > 500;
```

---

## 🔗 Relationships (Current)

```
users (1)
  └─→ (Future: will own campaigns, leads, etc.)

instantly_campaigns_raw (independent)
instantly_accounts_raw (independent)
instantly_daily_analytics_raw (independent)
instantly_emails_raw (independent)
```

**Note:** Raw layer is intentionally disconnected.
Relationships will be in normalized layer (migration 003+).

---

## 📈 Next Layer: NORMALIZED (To be designed)

```
Future structure:

users (1)
  ├─→ offers (N)
  ├─→ leads (N)
  ├─→ batches (N)
  ├─→ campaigns (N)
  └─→ events (N)

campaigns
  ├─→ instantly_campaigns_raw (FK instantly_campaign_id)
  └─→ Normalized: offer, batch, analytics

email_accounts
  └─→ instantly_accounts_raw (FK email)

events
  └─→ instantly_emails_raw (FK instantly_email_id)
```

---

## 🎯 Design Decisions

### 1. Raw vs Normalized Separation
**Decision:** Keep raw layer separate from business logic
**Reason:** API data should never be modified

### 2. Extracted Columns
**Decision:** Key fields as columns + full JSON
**Reason:** Fast queries + data preservation

### 3. Single vs Multiple Raw Tables
**Decision:** Separate table per data type
**Reason:** Better performance, clearer structure

### 4. UNIQUE Constraints
**Decision:** Primary keys on Instantly IDs
**Reason:** Prevent duplicate syncs

---

## 🔍 Indexes Summary

### instantly_campaigns_raw
- `instantly_campaign_id` (PRIMARY KEY)
- `campaign_name` (INDEX)
- `campaign_status` (INDEX)
- `synced_at DESC` (INDEX)

### instantly_accounts_raw
- `email` (PRIMARY KEY)
- `account_status` (INDEX)
- `warmup_score DESC` (INDEX)

### instantly_daily_analytics_raw
- `id` (PRIMARY KEY)
- `analytics_date` (UNIQUE INDEX)
- `analytics_date + instantly_campaign_id` (UNIQUE INDEX)
- `instantly_campaign_id` (INDEX)

### instantly_emails_raw
- `id` (PRIMARY KEY)
- `instantly_email_id` (UNIQUE INDEX)
- `instantly_campaign_id` (INDEX)
- `event_type` (INDEX)
- `event_date DESC` (INDEX)
- `email_address` (INDEX)

---

## 📝 Migration Status

- ✅ Migration 001: Users table
- ✅ Migration 002: Instantly raw layer
- ⏳ Migration 003: Offers table (planned)
- ⏳ Migration 004: Leads table (planned)
- ⏳ Migration 005: Campaigns normalized (planned)
- ⏳ Migration 006: Events table (planned)
