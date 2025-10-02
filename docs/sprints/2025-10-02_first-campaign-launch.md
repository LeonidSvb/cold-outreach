# Sprint: First Campaign Launch

**Date:** 2025-10-02
**Timeline:** 2-3 days
**Goal:** Launch first real campaign with 1500 leads through complete pipeline

---

## 1. SPRINT GOAL

### Main Objective
Launch first real Instantly campaign with 1500 leads through full pipeline:
```
CSV upload → Column detection → Normalization → Icebreaker generation → Batch splitting → Upload to Instantly
```

### Success Criteria
- ✅ 1500 leads successfully uploaded to Instantly
- ✅ All leads normalized (company_name, city)
- ✅ Each lead has icebreaker
- ✅ Leads split into batches of 200-300 for A/B testing
- ✅ 2-3 offers assigned to different batches
- ✅ Campaign launched and running in Instantly
- ✅ (Bonus) Event sync from Instantly to Supabase

---

## 2. SCOPE

### 2.1. Backend (Python FastAPI + Scripts)

#### A. CSV Processing
- ✅ Upload CSV to Supabase Storage (already works from v8.2.0)
- ✅ Parse CSV and save rows to `leads` table
- ✅ Column detection and mapping (auto-detect email, company_name, city, etc.)
- ✅ Manual column selection in UI

#### B. Normalization Scripts

**normalize_company_name.py**
- OpenAI-based normalization (remove Inc., LLC, make readable)
- Integration with Supabase (read from leads, update normalized fields)

**normalize_city.py**
- OpenAI-based normalization (shorten long city names)
- Save to `leads.normalized_city`

#### C. Icebreaker Generation

**generate_icebreakers.py**
- OpenAI icebreaker generation (NO website scraping this week)
- Use only CSV data (company, city, industry if available)
- Save to `leads.icebreaker` field

#### D. Batch Splitting

**split_into_batches.py**
- Split leads into batches of 200-300
- Configurable batch size
- Save batches to `batches` table with links to leads

#### E. Instantly Upload

**instantly_uploader.py**
- Adapt existing `instantly_csv_uploader_curl.py` for Supabase integration
- Read from `leads` table (normalized + icebreaker)
- Upload to Instantly campaign via curl (bypass Cloudflare)
- Save `instantly_lead_id` back to Supabase
- Add `offer_code` to custom field in Instantly for tracking

#### F. Instantly Sync (Bonus)

**sync_instantly_events.py**
- Pull events (send, open, click, reply, bounce)
- Incremental sync (cursor-based, only new events)
- Save to `events` table
- Cron job (every 5-10 minutes)

---

### 2.2. Database Schema (Supabase)

#### Users Table (Multi-user foundation)
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default user for single-user mode
INSERT INTO users (id, email)
VALUES ('00000000-0000-0000-0000-000000000001', 'default@user.com');
```

#### Offers Table
```sql
CREATE TABLE offers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  value_prop TEXT,
  angle TEXT,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Leads Table
```sql
CREATE TABLE leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
  file_id UUID REFERENCES file_metadata(id),
  source TEXT DEFAULT 'csv',

  -- Original fields
  email TEXT NOT NULL,
  company_name TEXT,
  first_name TEXT,
  last_name TEXT,
  city TEXT,
  country TEXT,
  website TEXT,

  -- Normalized fields
  normalized_company_name TEXT,
  normalized_city TEXT,
  icebreaker TEXT,

  -- Flexible fields
  metadata JSONB DEFAULT '{}',
  raw_data JSONB,

  -- Relations
  offer_id UUID REFERENCES offers(id),
  batch_id UUID,
  status TEXT DEFAULT 'pending',
  instantly_lead_id TEXT,

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_batch ON leads(batch_id);
CREATE INDEX idx_leads_user ON leads(user_id);
```

#### Batches Table
```sql
CREATE TABLE batches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
  file_id UUID REFERENCES file_metadata(id),
  name TEXT,
  offer_id UUID REFERENCES offers(id),
  size INT,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Campaigns Table
```sql
CREATE TABLE campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
  instantly_campaign_id TEXT UNIQUE,
  name TEXT,
  offer_id UUID REFERENCES offers(id),
  status TEXT DEFAULT 'draft',
  metadata JSONB DEFAULT '{}',
  raw_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Events Table
```sql
CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
  lead_id UUID REFERENCES leads(id),
  campaign_id UUID REFERENCES campaigns(id),
  event_type TEXT NOT NULL,
  event_time TIMESTAMPTZ NOT NULL,
  instantly_event_id TEXT UNIQUE,
  metadata JSONB DEFAULT '{}',
  raw_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_lead ON events(lead_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_time ON events(event_time DESC);
CREATE INDEX idx_events_user ON events(user_id);
```

#### Email Accounts Table
```sql
CREATE TABLE email_accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) DEFAULT '00000000-0000-0000-0000-000000000001',
  instantly_account_id TEXT UNIQUE,
  email TEXT,
  domain TEXT,
  status TEXT,
  warmup_enabled BOOLEAN,
  bounce_rate NUMERIC,
  spam_rate NUMERIC,
  metadata JSONB DEFAULT '{}',
  raw_data JSONB,
  last_synced_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

### 2.3. Frontend (Next.js)

#### Wizard UI Steps (Script Runner)

**Step-by-step flow:**

1. **Upload CSV** ✅ (already works)
2. **Column Detection** - auto-detect + manual selection
3. **Preview Data** - show first 50 rows
4. **Select Columns for Processing** - checkboxes for normalization
5. **Normalize** - button "Normalize Data" → calls API
6. **Generate Icebreakers** - button → calls API
7. **Review Normalized** - show normalized data with icebreakers
8. **Assign Offer** - dropdown to select offer
9. **Split into Batches** - configure batch size (default 250)
10. **Upload to Instantly** - button → calls API
11. **Job Status** - show progress, errors, success

#### Offers Management Page

**Path:** `/offers`

**Features:**
- List all offers (table view)
- Create new offer (modal form)
  - Fields: code, name, value_prop, angle
- Edit offer
- Delete offer
- Assign offer to batch (in wizard)

---

### 2.4. API Endpoints

#### Backend (FastAPI)

**POST /api/parse-csv**
```json
{
  "file_id": "uuid",
  "column_mapping": {
    "email": "Email",
    "company_name": "Company Name",
    "city": "City"
  }
}
```

**POST /api/normalize-company**
```json
{
  "file_id": "uuid",
  "column": "company_name"
}
```

**POST /api/normalize-city**
```json
{
  "file_id": "uuid",
  "column": "city"
}
```

**POST /api/generate-icebreakers**
```json
{
  "file_id": "uuid",
  "offer_id": "uuid"
}
```

**POST /api/split-batches**
```json
{
  "file_id": "uuid",
  "batch_size": 250
}
```

**POST /api/upload-to-instantly**
```json
{
  "batch_id": "uuid",
  "campaign_id": "instantly_campaign_id"
}
```

**GET /api/sync-instantly**
```json
{}
```

#### Frontend (Next.js API Routes - Proxy)

```typescript
// src/app/api/normalize-csv/route.ts
export async function POST(request: NextRequest) {
  const { file_id, column } = await request.json();

  const response = await fetch('http://localhost:8000/api/normalize-company', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id, column })
  });

  return NextResponse.json(await response.json());
}
```

---

### 2.5. Instantly Integration

#### Upload Strategy

```python
# For each lead in batch:
lead_data = {
    "email": lead.email,
    "first_name": lead.first_name or "Business",
    "last_name": lead.last_name or "Owner",
    "company_name": lead.normalized_company_name,
    "custom_fields": {
        "offer_code": offer.code,  # "A1", "B2" for tracking
        "icebreaker": lead.icebreaker,
        "city": lead.normalized_city
    }
}

# Upload via curl (bypass Cloudflare)
instantly_api.create_lead(campaign_id, lead_data)

# Save instantly_lead_id
supabase.update_lead(lead.id, {
    "instantly_lead_id": response['id'],
    "status": "uploaded"
})
```

#### Metadata Field

- Add `offer_code` to custom field in Instantly
- This allows tracking which offer each lead received
- Analytics: GROUP BY offer_code to see performance

---

## 3. OUT OF SCOPE (NOT THIS WEEK)

❌ Website scraping for icebreakers (next week)
❌ Advanced segmentation (by seniority, industry)
❌ Multi-user authentication (prepared in DB, not implemented)
❌ Row Level Security (RLS) in Supabase
❌ Complex A/B testing UI
❌ Dashboard analytics visualizations
❌ Email sequence creation via API (use Instantly UI)

---

## 4. TECHNICAL DECISIONS

### 4.1. Column Mapping Strategy

**Hybrid approach:**
- Auto-detect common columns (email, company_name, city, country)
- Manual selection in UI for ambiguous cases
- Save mapping to `file_metadata.column_mapping` JSONB field

```python
def auto_detect_columns(csv_columns: list) -> dict:
    mapping = {}

    # Email detection
    email_patterns = ['email', 'e-mail', 'email address', 'contact email']
    for col in csv_columns:
        if col.lower() in email_patterns:
            mapping['email'] = col
            break

    # Company detection
    company_patterns = ['company', 'company name', 'organization', 'company_name']
    for col in csv_columns:
        if col.lower() in company_patterns:
            mapping['company_name'] = col
            break

    return mapping
```

### 4.2. Batch Splitting Logic

```python
def split_into_batches(file_id: str, batch_size: int = 250) -> list:
    leads = supabase.get_leads_by_file(file_id)

    batches = []
    for i in range(0, len(leads), batch_size):
        batch = {
            "name": f"Batch {i//batch_size + 1}",
            "file_id": file_id,
            "size": len(leads[i:i+batch_size])
        }
        batch_id = supabase.create_batch(batch)

        # Update leads with batch_id
        for lead in leads[i:i+batch_size]:
            supabase.update_lead(lead['id'], {"batch_id": batch_id})

        batches.append(batch_id)

    return batches
```

### 4.3. Incremental Sync from Instantly

```python
def sync_instantly_events():
    # Get last sync cursor
    cursor = supabase.get_sync_cursor('events')

    # Fetch new events from Instantly
    events = instantly_api.get_events(updated_after=cursor)

    for event in events:
        # Find lead by instantly_lead_id
        lead = supabase.get_lead_by_instantly_id(event['lead_id'])

        if lead:
            supabase.insert_event({
                "lead_id": lead['id'],
                "event_type": event['type'],
                "event_time": event['timestamp'],
                "instantly_event_id": event['id'],
                "raw_data": event
            })

    # Update cursor
    supabase.update_sync_cursor('events', max(e['timestamp'] for e in events))
```

---

## 5. IMPLEMENTATION PLAN

### Phase 1: Database Setup
1. Create all SQL tables in Supabase
2. Insert default user
3. Create sample offers (A1, A2, B1)
4. Test schema with manual inserts

### Phase 2: Backend Scripts
1. Write `parse_csv.py` - CSV to leads table
2. Write `normalize_company_name.py` - OpenAI normalization
3. Write `normalize_city.py` - OpenAI normalization
4. Write `generate_icebreakers.py` - OpenAI icebreakers
5. Write `split_into_batches.py` - Batch creation
6. Adapt `instantly_uploader.py` - Supabase integration

### Phase 3: FastAPI Endpoints
1. Create `/api/parse-csv` endpoint
2. Create `/api/normalize-company` endpoint
3. Create `/api/normalize-city` endpoint
4. Create `/api/generate-icebreakers` endpoint
5. Create `/api/split-batches` endpoint
6. Create `/api/upload-to-instantly` endpoint
7. Test all endpoints with Postman

### Phase 4: Frontend UI
1. Create Wizard UI component
2. Add column detection step
3. Add normalization steps
4. Add icebreaker generation step
5. Add batch splitting step
6. Add Instantly upload step
7. Create Offers management page

### Phase 5: Integration Testing
1. Test with 10 leads CSV
2. Test normalization quality
3. Test icebreaker quality
4. Test Instantly upload
5. Verify data in Supabase

### Phase 6: Launch
1. Upload 1500 leads CSV
2. Run full pipeline
3. Upload to Instantly campaign
4. Monitor and fix issues

### Phase 7: Sync (Bonus)
1. Write `sync_instantly_events.py`
2. Test incremental sync
3. Setup cron job (every 5-10 minutes)

---

## 6. TIMELINE (2-3 Days)

### Day 1: Database + Backend Scripts
- ✅ Create SQL schema in Supabase
- ✅ Write Python scripts (parse, normalize, icebreakers, batches, upload)
- ✅ Create FastAPI endpoints
- ✅ Test with Postman

### Day 2: Frontend + Integration
- ✅ Create Wizard UI
- ✅ Create Offers page
- ✅ Create Next.js API routes
- ✅ Test full flow on 10 leads

### Day 3: Launch + Sync
- ✅ Launch campaign with 1500 leads
- ✅ Implement Instantly sync
- ✅ Setup cron job
- ✅ Monitor and fix issues

---

## 7. RISKS & MITIGATION

| Risk                            | Mitigation                                      |
|---------------------------------|-------------------------------------------------|
| OpenAI API rate limits          | Batch processing with delays, retry logic       |
| Instantly API Cloudflare blocks | Use curl method (already working)               |
| Large CSV parsing fails         | Stream processing, chunk by chunk               |
| UI complexity delays            | Simple MVP UI first, polish later               |
| Sync breaks after launch        | Comprehensive error logging, manual fallback    |

---

## 8. SUCCESS METRICS

### Technical Metrics
- ✅ 100% leads parsed from CSV
- ✅ 95%+ successful normalization rate
- ✅ 100% icebreaker generation coverage
- ✅ 100% successful upload to Instantly
- ✅ <5 minutes total processing time for 1500 leads

### Business Metrics
- ✅ Campaign launched in Instantly
- ✅ 2-3 offers A/B tested across batches
- ✅ Event sync working (bonus)
- ✅ Ready for scaling to 10K+ leads/month

---

## NEXT SPRINT

After this sprint completes, next priorities:
1. Website scraping for enhanced icebreakers
2. Advanced segmentation (seniority, industry)
3. Multi-user authentication + RLS
4. Dashboard analytics visualizations
5. Email sequence builder
