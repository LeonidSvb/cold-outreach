# Architecture Levels and Data Flow Documentation

**Created:** 2025-10-02
**Sprint:** First Campaign Launch
**Status:** Architecture Planning Phase

---

## 📋 Table of Contents

1. [Complete Architecture Hierarchy (5 Levels)](#complete-architecture-hierarchy)
2. [Level Interactions and Data Flow](#level-interactions-and-data-flow)
3. [Why Separate Services from Endpoints](#why-separate-services-from-endpoints)
4. [Modules vs Backend Services](#modules-vs-backend-services)
5. [Next.js API Routes - Do We Need Them?](#nextjs-api-routes)
6. [Implementation Plan](#implementation-plan)

---

## 🏗️ Complete Architecture Hierarchy

### 5-Level System Overview

```
LEVEL 0: EXTERNAL SERVICES
    ├─ Supabase (PostgreSQL Database)
    ├─ Instantly API
    ├─ Apollo API
    └─ OpenAI API

        ▲ API calls / Database queries
        │

LEVEL 1: SCRIPTS (Low-level bricks)
    modules/
    ├─ instantly/
    │   ├─ instantly_sources.py           # Load from JSON or API
    │   ├─ instantly_transform.py         # Transform data
    │   ├─ instantly_universal_collector.py
    │   └─ instantly_campaign_optimizer.py
    ├─ apollo/
    │   ├─ apollo_lead_collector.py
    │   └─ apollo_enrichment.py
    └─ shared/
        └─ logger.py

        ▲ import statements
        │

LEVEL 2: MODULES (Logical grouping)
    modules/instantly/   ← MODULE (folder with related scripts)
    modules/apollo/      ← MODULE
    modules/openai/      ← MODULE

        ▲ Backend imports individual scripts
        │

LEVEL 3: BACKEND SERVICES (Orchestration)
    backend/
    ├─ services/
    │   ├─ instantly_sync.py       # Combines: instantly_sources +
    │   │                          #           instantly_transform +
    │   │                          #           supabase_client
    │   ├─ lead_enrichment.py      # Combines: apollo_enrichment +
    │   │                          #           openai_processor +
    │   │                          #           supabase_client
    │   └─ campaign_launcher.py    # Combines: lead_selector +
    │                              #           icebreaker_generator +
    │                              #           instantly_uploader
    └─ lib/
        └─ supabase_client.py      # Supabase connection (shared)

        ▲ HTTP requests
        │

LEVEL 4: BACKEND API ENDPOINTS (FastAPI routers)
    backend/
    ├─ main.py                     # FastAPI app
    └─ routers/
        ├─ instantly.py            # POST /api/instantly/sync
        │                          # GET /api/instantly/campaigns
        ├─ leads.py                # POST /api/leads/enrich
        │                          # GET /api/leads
        └─ campaigns.py            # POST /api/campaigns/launch
                                   # GET /api/campaigns

        ▲ HTTP requests (fetch)
        │

LEVEL 5: FRONTEND (User Interface)
    frontend/src/app/
    ├─ dashboard/page.tsx          # Displays campaigns
    ├─ leads/page.tsx              # Displays leads
    └─ (No Next.js API routes needed - direct Backend calls)
```

---

## 🔄 Level Interactions and Data Flow

### Complete Flow: User Action → Database

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA FLOW                                 │
└─────────────────────────────────────────────────────────────────┘

1. USER ACTION (Level 5)
   Frontend button click: "Sync Instantly Data"
        ↓

2. FRONTEND → BACKEND (Level 5 → Level 4)
   HTTP POST http://localhost:8000/api/instantly/sync
        ↓

3. ENDPOINT RECEIVES REQUEST (Level 4)
   backend/routers/instantly.py
   @router.post("/sync")
   def sync_endpoint():
        ↓

4. ENDPOINT CALLS SERVICE (Level 4 → Level 3)
   return sync_instantly_data()  # Calls service layer
        ↓

5. SERVICE ORCHESTRATES (Level 3 → Level 1)
   backend/services/instantly_sync.py
   - Imports modules: instantly_sources, instantly_transform
   - Loads data: load_from_json()
   - Transforms: transform_campaigns()
        ↓

6. MODULES EXECUTE (Level 1)
   modules/instantly/instantly_sources.py - loads JSON
   modules/instantly/instantly_transform.py - normalizes data
        ↓

7. SERVICE WRITES TO DB (Level 3 → Level 0)
   backend/lib/supabase_client.py
   supabase.table('instantly_campaigns_raw').upsert(data)
        ↓

8. SUPABASE STORES DATA (Level 0)
   PostgreSQL database tables updated
        ↓

9. RESPONSE FLOWS BACK (Level 0 → Level 5)
   Service → Endpoint → Frontend
   {'success': True, 'synced': 100}
        ↓

10. FRONTEND DISPLAYS RESULT (Level 5)
    "Successfully synced 100 campaigns"
```

---

## 🤔 Why Separate Services (Level 3) from Endpoints (Level 4)?

### Question: Can't endpoints BE the orchestrators?

**Answer:** You CAN, but it's a bad practice. Here's why:

### ❌ BAD: Endpoint = Orchestrator (All logic in endpoint)

```python
# backend/routers/instantly.py
from fastapi import APIRouter
from supabase import create_client
import sys
sys.path.append('../../modules')
from instantly.instantly_sources import load_from_json
from instantly.instantly_transform import transform_campaigns

router = APIRouter(prefix="/api/instantly")

@router.post("/sync")
def sync_endpoint(source: str = 'json'):
    # ALL LOGIC DIRECTLY IN ENDPOINT

    # Load
    raw_data = load_from_json('results/raw_data.json')

    # Transform
    campaigns = transform_campaigns(raw_data['campaigns'])
    accounts = transform_accounts(raw_data['accounts'])

    # Upload
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase.table('instantly_campaigns_raw').upsert(campaigns).execute()
    supabase.table('instantly_accounts_raw').upsert(accounts).execute()

    return {'success': True, 'synced': len(campaigns)}
```

**Problems:**
1. ❌ **Cannot reuse** - If you need sync without HTTP (CLI, cron job), must copy code
2. ❌ **Hard to test** - Need to mock HTTP requests
3. ❌ **Mixed concerns** - Business logic + HTTP handling in one place
4. ❌ **Cannot call from other endpoints** - Logic locked in HTTP context

---

### ✅ GOOD: Service Layer (Separated)

```python
# ===================================
# backend/services/instantly_sync.py
# LEVEL 3: Business Logic (pure function)
# ===================================

def sync_instantly_data(source='json', file_path=None):
    """
    Pure business logic - can be called from anywhere:
    - HTTP endpoint
    - CLI command
    - Cron job
    - Another service
    """

    # Load
    raw_data = load_from_json(file_path)

    # Transform
    campaigns = transform_campaigns(raw_data['campaigns'])

    # Upload
    supabase = get_supabase()
    supabase.table('instantly_campaigns_raw').upsert(campaigns).execute()

    return {'success': True, 'synced': len(campaigns)}


# ===================================
# backend/routers/instantly.py
# LEVEL 4: HTTP Endpoint (thin wrapper)
# ===================================

from services.instantly_sync import sync_instantly_data

@router.post("/sync")
def sync_endpoint(source: str = 'json', file_path: str = None):
    """
    HTTP wrapper - just calls service and returns response
    """
    try:
        result = sync_instantly_data(source, file_path)
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

**Advantages:**
1. ✅ **Reusable** - Can call from CLI, cron, other endpoints
2. ✅ **Easy to test** - Simple Python function
3. ✅ **Clean architecture** - Business logic separate from HTTP
4. ✅ **Flexible** - Same logic, multiple entry points

---

### Real-World Use Cases: Why Separation Matters

#### Use Case 1: HTTP Endpoint (for Frontend)
```python
# frontend/dashboard/page.tsx
fetch('http://localhost:8000/api/instantly/sync', { method: 'POST' })
    ↓
# backend/routers/instantly.py
@router.post("/sync")
def sync_endpoint():
    return sync_instantly_data()  # ← Calls service
```

#### Use Case 2: CLI Command (manual execution)
```python
# backend/cli.py
import sys
from services.instantly_sync import sync_instantly_data

if __name__ == '__main__':
    result = sync_instantly_data(source='json')  # ← Same service
    print(f"Synced: {result}")
```

```bash
# Run from terminal without HTTP server
python backend/cli.py
```

#### Use Case 3: Cron Job (automatic hourly sync)
```python
# backend/cron/hourly_sync.py
from services.instantly_sync import sync_instantly_data

# Runs every hour automatically
sync_instantly_data(source='api')  # ← Same service
```

#### Use Case 4: Called from another endpoint
```python
# backend/routers/campaigns.py
from services.instantly_sync import sync_instantly_data

@router.post("/campaigns/launch")
def launch_campaign():
    # First sync latest data
    sync_instantly_data()  # ← Same service

    # Then launch campaign
    # ...
```

**See?** One function `sync_instantly_data()` used in 4 different places.

If logic was in endpoint → would need to copy code 4 times.

---

### Architecture Rule: Thin Endpoints, Thick Services

```
┌─────────────────────────────────────┐
│  ENDPOINT (thin)                    │
│  - Receives HTTP request            │
│  - Validates input                  │
│  - Calls service                    │
│  - Returns HTTP response            │
└─────────────────────────────────────┘
         │
         │ Calls
         ▼
┌─────────────────────────────────────┐
│  SERVICE (thick)                    │
│  - All business logic               │
│  - Orchestration                    │
│  - Database operations              │
│  - Can be called from anywhere      │
└─────────────────────────────────────┘
```

---

## 🧱 Modules vs Backend Services

### Key Understanding

**Question:** Backend orchestrates individual SCRIPTS, not entire modules?

**Answer:** YES! Exactly.

### Modules = Folders (Just Organization)

```
modules/instantly/  ← MODULE (just a folder for convenience)
    ├─ instantly_sources.py              ← SCRIPT 1
    ├─ instantly_transform.py            ← SCRIPT 2
    ├─ instantly_universal_collector.py  ← SCRIPT 3
    └─ instantly_campaign_optimizer.py   ← SCRIPT 4
```

**Backend can use:**
- Only SCRIPT 1 and 2 (for sync)
- Only SCRIPT 3 (for manual collection)
- Only SCRIPT 4 (for optimization)
- Any combination!

### Backend Imports Individual Scripts

```python
# Backend DOES NOT import entire module
# ❌ from instantly import *  # NO!

# Backend imports INDIVIDUAL SCRIPTS
# ✅ from instantly.instantly_sources import load_from_json  # YES!
# ✅ from apollo.apollo_enrichment import enrich_lead      # YES!
# ✅ from openai.icebreaker_generator import generate      # YES!
```

### Example: Combining Scripts from Different Modules

```python
# backend/services/lead_enrichment.py
# ====================================
# Combines scripts from 3 different modules!

from apollo.apollo_lead_collector import get_company_info      # Apollo module
from openai.icebreaker_generator import generate_icebreaker    # OpenAI module
from shared.logger import log_operation                        # Shared module
from lib.supabase_client import get_supabase                   # Backend lib


def enrich_lead(email):
    """
    ORCHESTRATION across multiple modules
    """

    # Step 1: Get company data (Apollo module)
    company = get_company_info(email)

    # Step 2: Generate icebreaker (OpenAI module)
    icebreaker = generate_icebreaker(company)

    # Step 3: Log (Shared module)
    log_operation('lead_enriched', email)

    # Step 4: Save to DB (Backend lib)
    supabase = get_supabase()
    supabase.table('leads').update({
        'company_name': company['name'],
        'icebreaker': icebreaker
    }).eq('email', email).execute()

    return {'success': True}
```

**Modules (folders) are just organization for convenience.**

**Backend works with individual scripts.**

---

## 🌐 Next.js API Routes - Do We Need Them?

### Option A: Frontend → Backend Python (Direct) ✅ RECOMMENDED

```typescript
// frontend/src/app/dashboard/page.tsx
async function syncData() {
    const response = await fetch('http://localhost:8000/api/instantly/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
    return response.json();
}
```

**Setup Required:**
```python
# backend/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_methods=["*"],
    allow_headers=["*"]
)
```

**Pros:**
- ✅ Simpler (less code)
- ✅ Faster (no extra layer)
- ✅ CORS easy to configure

**Cons:**
- ⚠️ Need CORS configuration
- ⚠️ Hardcoded backend URL

---

### Option B: Frontend → Next.js API → Backend Python ❌ NOT NEEDED

```typescript
// frontend/src/app/api/instantly/sync/route.ts
export async function POST(request: Request) {
    // Next.js API route acts as proxy
    const response = await fetch('http://localhost:8000/api/instantly/sync', {
        method: 'POST'
    });

    const data = await response.json();
    return Response.json(data);
}
```

```typescript
// frontend/src/app/dashboard/page.tsx
async function syncData() {
    // Frontend calls Next.js API (same domain, no CORS)
    const response = await fetch('/api/instantly/sync', {
        method: 'POST'
    });
    return response.json();
}
```

**Pros:**
- ✅ No CORS issues
- ✅ Can add auth middleware
- ✅ Environment variables on backend

**Cons:**
- ❌ Extra layer (slower)
- ❌ More code
- ❌ Redundant (Backend Python already handles server logic)

---

### When to Use Next.js API Routes?

**Use when you need:**
- Auth middleware (token verification)
- Rate limiting
- Request transformation
- Server-side secrets (but we have Backend Python for this)

**For our project:** Backend Python already handles server logic, so Next.js API routes are redundant.

**Decision:** Use Option A (Frontend → Backend Python direct with CORS)

---

## 📊 Complete Architecture Diagram

```
┌─────────────────────────────────────┐
│  Frontend (Next.js)                 │
│  Port: 3000                         │
└─────────────────────────────────────┘
         │
         │ HTTP fetch (with CORS)
         │ http://localhost:8000/api/instantly/sync
         ▼
┌─────────────────────────────────────┐
│  Backend Python (FastAPI)           │
│  Port: 8000                         │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ ROUTERS (Level 4)             │ │
│  │ routers/instantly.py          │ │
│  │   @router.post("/sync")       │ │
│  │   def sync_endpoint():        │ │
│  │       return service.sync()   │ │ ← Thin layer
│  └───────────────────────────────┘ │
│         │                           │
│         │ calls                     │
│         ▼                           │
│  ┌───────────────────────────────┐ │
│  │ SERVICES (Level 3)            │ │
│  │ services/instantly_sync.py    │ │
│  │   def sync_instantly_data():  │ │
│  │       # Load from modules     │ │
│  │       # Transform              │ │ ← All logic here
│  │       # Upload to Supabase    │ │
│  └───────────────────────────────┘ │
│         │                           │
│         │ imports                   │
│         ▼                           │
│  ┌───────────────────────────────┐ │
│  │ MODULES (Level 1-2)           │ │
│  │ modules/instantly/            │ │
│  │   instantly_sources.py        │ │
│  │   instantly_transform.py      │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
         │
         │ Database queries
         ▼
┌─────────────────────────────────────┐
│  Supabase (PostgreSQL)              │
└─────────────────────────────────────┘
```

---

## 🎯 Key Takeaways

### Architecture Levels Summary

1. ✅ **Modules** = folders with scripts (for organization)
2. ✅ **Backend services** = orchestrate individual scripts from any module
3. ✅ **Backend lib/** = shared utilities (Supabase client)
4. ✅ **Backend routers** = HTTP endpoints (FastAPI)
5. ✅ **Frontend** = calls endpoints, displays results

### Critical Principles

**User Quote:**
> "Backend does orchestration with scripts, but which are structured by modules just for convenience"

**✅ EXACTLY CORRECT!**

**Backend:**
- Imports individual scripts (not entire modules)
- Combines scripts from different modules
- Services contain reusable business logic
- Endpoints are thin HTTP wrappers

**Modules:**
- Just folders for organization
- Backend can use any combination of scripts
- No module is used "as a whole"

---

## 📋 Implementation Plan

### Phase 1: Database Setup (CURRENT)
1. ✅ Create SQL migrations
   - `001_users_table.sql`
   - `002_instantly_raw_layer.sql`
2. ⏳ Execute migrations in Supabase
3. ⏳ Test with sample data inserts

### Phase 2: Scripts (Level 1)
1. Create `modules/instantly/instantly_sources.py`
   - `load_from_json(file_path)`
   - `load_from_api(api_key, since=None)`
2. Create `modules/instantly/instantly_transform.py`
   - `transform_campaigns(raw_campaigns)`
   - `transform_accounts(raw_accounts)`
   - `transform_daily_analytics(raw_daily)`

### Phase 3: Backend Infrastructure
1. Create `backend/lib/supabase_client.py`
   - Singleton Supabase connection
   - Reusable across all services
2. Create `backend/services/instantly_sync.py`
   - Orchestrates modules
   - Uploads to Supabase
3. Create `backend/routers/instantly.py`
   - POST `/api/instantly/sync`
   - GET `/api/instantly/campaigns`

### Phase 4: Testing
1. Test sync from JSON file
2. Test API endpoints
3. Verify data in Supabase

### Phase 5: Frontend Integration
1. Add CORS to Backend
2. Create sync button in Dashboard
3. Display synced data

---

## 🗂️ File Structure

### Complete Project Structure

```
Outreach - new/
├── backend/
│   ├── main.py                        # FastAPI app
│   ├── routers/
│   │   ├── instantly.py               # POST /sync, GET /campaigns
│   │   ├── leads.py                   # Lead endpoints
│   │   └── campaigns.py               # Campaign endpoints
│   ├── services/
│   │   ├── instantly_sync.py          # Sync orchestration
│   │   ├── lead_enrichment.py         # Lead processing
│   │   └── campaign_launcher.py       # Campaign launch
│   ├── lib/
│   │   └── supabase_client.py         # Supabase connection
│   └── requirements.txt
│
├── modules/
│   ├── instantly/
│   │   ├── instantly_sources.py       # Load JSON/API
│   │   ├── instantly_transform.py     # Transform data
│   │   ├── instantly_universal_collector.py
│   │   └── instantly_campaign_optimizer.py
│   ├── apollo/
│   │   ├── apollo_lead_collector.py
│   │   └── apollo_enrichment.py
│   ├── openai/
│   │   └── icebreaker_generator.py
│   └── shared/
│       └── logger.py
│
├── frontend/
│   └── src/app/
│       ├── dashboard/page.tsx         # Dashboard UI
│       └── leads/page.tsx             # Leads UI
│
└── docs/
    └── sql/
        ├── 001_users_table.sql
        └── 002_instantly_raw_layer.sql
```

---

## ✅ Summary

### What We Learned

1. **5-Level Architecture**
   - Level 0: External services (Supabase, APIs)
   - Level 1: Scripts (individual .py files)
   - Level 2: Modules (folders grouping scripts)
   - Level 3: Services (orchestration)
   - Level 4: Endpoints (HTTP wrappers)
   - Level 5: Frontend (UI)

2. **Services vs Endpoints**
   - Services = reusable business logic
   - Endpoints = thin HTTP wrappers
   - Services can be called from anywhere
   - Endpoints only handle HTTP

3. **Modules Are Just Folders**
   - Backend imports individual scripts
   - Not entire modules
   - Can combine scripts from different modules

4. **Next.js API Routes Not Needed**
   - Frontend → Backend Python direct
   - CORS configuration sufficient
   - Simpler and faster

### Next Steps

1. ✅ Create Supabase tables (migrations ready)
2. ⏳ Execute migrations in Supabase
3. ⏳ Create Level 1 scripts (modules/instantly/)
4. ⏳ Create Backend infrastructure (services, routers)
5. ⏳ Test sync with JSON file
6. ⏳ Connect Frontend

---

**Document Status:** Architecture Planning Complete
**Ready for:** Database Setup → Script Implementation → Backend Setup → Frontend Integration
