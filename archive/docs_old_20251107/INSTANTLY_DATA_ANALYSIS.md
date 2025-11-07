# Instantly Data Analysis & Recommendations

**Created:** 2025-10-03
**Status:** Analysis Complete

---

## 1. What Data We Have (Source JSON)

**File:** `modules/instantly/results/raw_data_20250921_125555.json` (104 KB)

### Top-level Keys:
- `campaigns_overview` - Basic campaign info
- `campaigns_detailed` - Detailed campaign data
- `daily_analytics_all` - Aggregated daily metrics (all campaigns)
- `daily_analytics_by_campaign` - Daily metrics per campaign
- `steps_analytics` - Email sequence step analytics
- `accounts` - Email sending accounts
- `emails_sample` - Individual email events (sent emails)
- `campaigns_with_real_metrics` - Campaigns with calculated metrics

### Data Counts:
- **Campaigns:** 4
- **Email Accounts:** 10
- **Daily Analytics (all):** 17 records
- **Email Events (sent):** ~30+ individual emails

---

## 2. What We Uploaded to Supabase

### ✅ UPLOADED (RAW Layer):
1. **instantly_campaigns_raw** - 4 campaigns
2. **instantly_accounts_raw** - 10 email accounts
3. **instantly_daily_analytics_raw** - 17 daily metrics

### ❌ NOT UPLOADED (Missing):
1. **instantly_emails_raw** - 0 emails (SHOULD upload ~30 emails from `emails_sample`)
2. **daily_analytics_by_campaign** - NOT uploaded (campaign-specific daily data)
3. **steps_analytics** - NOT uploaded (sequence step performance)

---

## 3. Database Structure (Current)

### RAW LAYER (Migration 001-002) - ✅ Applied

```
users (1 user)
  ├─ leonid@systemhustle.com

instantly_campaigns_raw (4 rows)
  ├─ Independent (no FK)
  └─ Stores: campaign_id, name, status, metrics, raw_json

instantly_accounts_raw (10 rows)
  ├─ Independent (no FK)
  └─ Stores: email (PK), warmup info, raw_json

instantly_daily_analytics_raw (17 rows)
  ├─ Optional FK to campaigns (can be NULL)
  └─ Stores: date, metrics, raw_json

instantly_emails_raw (0 rows) ← EMPTY!
  ├─ Should contain individual email events
  └─ Fields: email_id, campaign_id, event_type, date
```

### NORMALIZED LAYER (Migration 003-009) - ⏳ NOT Applied Yet

```
csv_imports_raw → companies → leads → campaigns → campaign_leads → events
```

---

## 4. Relationships Analysis

### Current (RAW Layer):
**INTENTIONALLY DISCONNECTED** ✅

Why?
- RAW layer = historical snapshot
- No FK constraints = can load data even if references broken
- All data preserved in `raw_json` JSONB

### Future (NORMALIZED Layer):
**CONNECTED via Foreign Keys**

```
companies (domain UNIQUE)
  └─→ leads (company_id FK)
       └─→ campaign_leads (lead_id FK)
            ├─→ campaigns (campaign_id FK)
            └─→ events (lead_id FK, campaign_id FK)
                 └─ Source: instantly/vapi/linkedin/manual
```

---

## 5. Missing Data Problem

### Issue:
`instantly_emails_raw` table is EMPTY but we have email data in JSON!

### Email Events in JSON:
```json
{
  "emails_sample": {
    "items": [
      {
        "id": "019958cd-b086-7f38-828a-b214f6728227",
        "campaign_id": "8ad64aaf-8294-4538-8400-4a99dcf016e8",
        "from_address_email": "zoe@alphamicroltd.org",
        "to_address_email_list": "mark@kingstreetmedia.ca",
        "subject": "Mark, 12 appointments / month - interested?",
        "timestamp_email": "2025-09-17T17:51:39.000Z",
        "ue_type": 1,
        "step": "0_0_0"
      },
      ... (~30 more emails)
    ]
  }
}
```

### This data shows:
- ✅ **campaign_id** - links to campaigns!
- ✅ **from_address_email** - links to accounts!
- ✅ **to_address_email** - recipient (lead)
- ✅ **timestamp** - when sent
- ✅ **step** - sequence step
- ✅ **ue_type** - event type (1 = sent)

**THIS IS VALUABLE EVENT DATA!**

---

## 6. Recommendations

### Priority 1: Upload Missing Email Events ⚠️

**Action:**
1. Create `extract_emails()` function in `instantly_sources.py`
2. Create `transform_emails()` function in `instantly_transform.py`
3. Upload to `instantly_emails_raw` table

**Why:**
- Email events show actual outreach activity
- Links campaigns → accounts → recipients
- Needed for event timeline analysis

### Priority 2: Keep RAW Layer Disconnected ✅

**Current approach is CORRECT:**
- No FK constraints in RAW layer
- All relationships via IDs (not enforced)
- Full data in `raw_json`

**Why:**
- Historical snapshots may have broken references
- Instantly API can return inconsistent data
- We can still JOIN on IDs in queries

### Priority 3: Plan NORMALIZED Layer 📋

**When to build:**
- After all RAW data loaded
- When need to deduplicate companies/leads
- When building unified event timeline

**Order:**
1. Migration 003-006 (CSV, companies, leads)
2. Migration 007-008 (Campaigns, workflow)
3. Migration 009 (Unified events)

---

## 7. SQL Query Examples (Current Data)

### Find campaigns and their email accounts:
```sql
SELECT
  c.campaign_name,
  e.email_address,
  e.event_type,
  e.event_date
FROM instantly_campaigns_raw c
LEFT JOIN instantly_emails_raw e
  ON e.instantly_campaign_id = c.instantly_campaign_id
WHERE c.campaign_status = 2  -- Active campaigns
ORDER BY e.event_date DESC;
```

### Daily performance by campaign:
```sql
SELECT
  c.campaign_name,
  d.analytics_date,
  d.sent,
  d.opened,
  d.replies
FROM instantly_campaigns_raw c
LEFT JOIN instantly_daily_analytics_raw d
  ON d.instantly_campaign_id = c.instantly_campaign_id
ORDER BY d.analytics_date DESC;
```

---

## 8. Action Plan

### Immediate (Today):
1. ✅ Upload email events to `instantly_emails_raw`
2. ✅ Verify all RAW data loaded
3. ✅ Document relationships (this file)

### Short-term (This Week):
1. ⏳ Reorganize `modules/instantly/` folder
2. ⏳ Create TASK-009 sync service
3. ⏳ Setup automated sync (daily/weekly)

### Medium-term (Next Sprint):
1. ⏳ Apply migrations 003-009 (normalized layer)
2. ⏳ Build ETL: RAW → NORMALIZED
3. ⏳ Create unified event timeline

---

## 9. Summary

### What's Working:
- ✅ RAW layer structure is correct
- ✅ Campaigns, accounts, daily analytics uploaded
- ✅ JSONB preserves all API data
- ✅ Independent tables (no broken FKs)

### What's Missing:
- ❌ Email events not uploaded (~30 emails)
- ❌ Campaign-specific daily analytics
- ❌ Step analytics data

### Architecture Decision:
- ✅ **RAW Layer:** Keep disconnected (current approach)
- ✅ **NORMALIZED Layer:** Add FK constraints (future)
- ✅ **Two-layer design:** Correct for data warehouse

**Conclusion:** Structure is sound. Just need to upload missing email events.
