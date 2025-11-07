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

---

## 🎯 NORMALIZED LAYER (Migrations 003-009)

```
┌─────────────────────────────────────────────────────────────┐
│                    NORMALIZED DATA LAYER                     │
│           (Business Logic & Application Tables)              │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐
│  csv_imports_raw (003)           │
├──────────────────────────────────┤
│  id (PK)                         │
│  file_name                       │
│  raw_data (JSONB) ★              │ ← Full CSV as JSON array
│  total_rows                      │
│  import_status                   │ ← uploaded, processing, completed
│  uploaded_by → users.id          │
└──────────────────────────────────┘
        │
        │ Source for CSV imports
        ├──────────────────────┐
        ↓                      ↓
┌──────────────────────────────────┐    ┌──────────────────────────────────┐
│  companies (005)                 │    │  leads (006)                     │
├──────────────────────────────────┤    ├──────────────────────────────────┤
│  id (PK)                         │    │  id (PK)                         │
│  company_name                    │    │  first_name                      │
│  company_domain (UNIQUE) ★       │    │  last_name                       │
│  industry                        │    │  email                           │
│  company_size                    │    │  job_title                       │
│  apollo_data (JSONB) ★           │    │  seniority                       │
│  first_seen_in_csv_id → (003)    │    │  company_id → companies.id       │
└──────────────────────────────────┘    │  csv_import_id → (003)           │
        ↑                                │  apollo_data (JSONB) ★           │
        │                                │  lead_status                     │
        └────────────────────────────────┴──────────────────────────────────┘
                                                 │
                                                 │
┌──────────────────────────────────┐            │
│  offers (004)                    │            │
├──────────────────────────────────┤            │
│  id (PK)                         │            │
│  offer_name                      │            │
│  offer_type                      │            │
│  price_min                       │            │
│  price_max                       │            │
│  target_industries []            │            │
│  value_proposition               │            │
│  created_by → users.id           │            │
└──────────────────────────────────┘            │
        │                                       │
        │                                       │
        ↓                                       │
┌──────────────────────────────────┐            │
│  campaigns (007)                 │            │
├──────────────────────────────────┤            │
│  id (PK)                         │            │
│  campaign_name                   │            │
│  offer_id → offers.id            │            │
│  uses_email                      │            │
│  uses_calls                      │            │
│  uses_linkedin                   │            │
│  instantly_campaign_id (opt)     │ ← Links to instantly_campaigns_raw
│  vapi_campaign_id (opt)          │ ← Future VAPI integration
│  campaign_status                 │            │
│  email_body_template             │            │
│  created_by → users.id           │            │
└──────────────────────────────────┘            │
        │                                       │
        │ Many-to-Many                          │
        ↓                                       │
┌──────────────────────────────────┐            │
│  campaign_leads (008)            │ ←──────────┘
├──────────────────────────────────┤
│  id (PK)                         │
│  campaign_id → campaigns.id      │
│  lead_id → leads.id              │
│  UNIQUE(campaign_id, lead_id) ★  │ ← One lead only once per campaign
│                                  │
│  email_status                    │ ← pending, sent, opened, replied
│  email_sent_at                   │
│  email_replied_at                │
│                                  │
│  call_status                     │ ← not_scheduled, completed, voicemail
│  call_scheduled_at               │
│  call_completed_at               │
│                                  │
│  linkedin_status                 │ ← Future: connection_sent, replied
│  overall_status                  │ ← active, replied, converted
│  sequence_step                   │ ← 1, 2, 3 (email sequence)
│  next_followup_at                │
└──────────────────────────────────┘
        │
        │ Timeline of all interactions
        ↓
┌──────────────────────────────────┐
│  events (009)                    │
├──────────────────────────────────┤
│  id (PK)                         │
│  event_source ★                  │ ← instantly, vapi, linkedin, manual
│  event_type                      │ ← email_sent, call_completed, etc.
│  lead_id → leads.id              │
│  campaign_id → campaigns.id      │
│  campaign_lead_id → (008)        │
│  event_timestamp                 │
│                                  │
│  --- Email fields (instantly) ---│
│  email_subject                   │
│  email_body                      │
│  instantly_email_id → (raw)      │
│                                  │
│  --- Call fields (vapi) ---------│
│  call_duration_seconds           │
│  call_recording_url              │
│  call_transcript                 │
│  vapi_call_id                    │
│                                  │
│  --- LinkedIn fields (future) ---│
│  linkedin_message_text           │
│                                  │
│  --- Manual events --------------│
│  note_text                       │
│  performed_by → users.id         │
│                                  │
│  raw_data (JSONB) ★              │ ← Full event data from source
└──────────────────────────────────┘
```

---

## 🔗 Relationships Summary

### RAW LAYER → NORMALIZED LAYER
```
instantly_campaigns_raw.instantly_campaign_id
  ← campaigns.instantly_campaign_id (optional link)

instantly_emails_raw.instantly_email_id
  ← events.instantly_email_id (optional link)
```

### NORMALIZED LAYER (Full Relationships)
```
users (1)
  ├─→ csv_imports_raw.uploaded_by (N)
  ├─→ offers.created_by (N)
  ├─→ campaigns.created_by (N)
  └─→ events.performed_by (N) [manual events]

csv_imports_raw (1)
  ├─→ companies.first_seen_in_csv_id (N)
  └─→ leads.csv_import_id (N)

companies (1)
  └─→ leads.company_id (N)  ★ Deduplication: multiple leads per company

offers (1)
  └─→ campaigns.offer_id (N)

campaigns (1)
  └─→ campaign_leads.campaign_id (N)

leads (1)
  ├─→ campaign_leads.lead_id (N)
  └─→ events.lead_id (N)

campaign_leads (1)
  └─→ events.campaign_lead_id (N)
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

| Migration | Table | Status | Dependencies |
|-----------|-------|--------|--------------|
| 001 | users | ✅ Applied | None |
| 002 | instantly_*_raw (4 tables) | ✅ Applied | 001 |
| 003 | csv_imports_raw | ⏳ Ready to apply | 001 |
| 004 | offers | ⏳ Ready to apply | 001 |
| 005 | companies | ⏳ Ready to apply | 003 |
| 006 | leads | ⏳ Ready to apply | 003, 005 |
| 007 | campaigns | ⏳ Ready to apply | 004 |
| 008 | campaign_leads | ⏳ Ready to apply | 006, 007 |
| 009 | events | ⏳ Ready to apply | 006, 007, 008 |

**Apply in order:** 003 → 004 → 005 → 006 → 007 → 008 → 009

**Recommended batches:**
- **Batch 1:** 003-006 (CSV imports + leads foundation)
- **Batch 2:** 007-008 (Campaigns + workflow)
- **Batch 3:** 009 (Unified events timeline)
