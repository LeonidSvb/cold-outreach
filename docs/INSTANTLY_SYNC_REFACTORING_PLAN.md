# Instantly Sync Refactoring Plan

Based on Shadi project architecture (HubSpot sync implementation)

---

## Current State (Instantly)

### Architecture
```
modules/instantly/scripts/
├── init_database.py       - Database initialization
├── collect_data.py        - Monolithic sync script
└── (no modular structure)

data/
└── instantly.db           - SQLite database
```

### Issues
- ❌ Monolithic script (all logic in one file)
- ❌ No incremental sync (always full sync)
- ❌ No modular transforms
- ❌ Basic logging (print statements)
- ❌ No batch tracking (sync_batch_id)
- ❌ No CLI flexibility (no --from, --last, etc.)
- ❌ No GitHub Actions / Vercel Cron automation
- ❌ Manual execution only

---

## Target State (After Refactoring)

### Inspired by Shadi Architecture

```
modules/instantly/
├── lib/
│   ├── sync/
│   │   ├── transform.py       - Transform functions (Instantly → DB)
│   │   ├── upsert.py          - Smart upsert with MERGE logic
│   │   ├── logger.py          - 3-tier logging (console + JSON + DB)
│   │   ├── cli.py             - CLI argument parser
│   │   └── api.py             - Instantly API client
│   └── database/
│       └── client.py          - SQLite connection wrapper
├── scripts/
│   ├── sync.py                - Main sync orchestrator
│   └── init_database.py       - Database initialization (keep)
├── data/
│   └── instantly.db           - SQLite database
└── logs/
    ├── 2025-11-01.jsonl       - Daily JSON logs (rotation)
    └── errors/
        └── 2025-11-01.log     - Error-only logs
```

---

## Refactoring Steps

### Phase 1: Modular Architecture (1-2 hours)

#### 1.1 Create lib/sync/transform.py

**Purpose:** Convert Instantly API responses to database format

```python
def transform_campaign(campaign_data, batch_id):
    """Transform campaign from Instantly API to DB format"""
    return {
        'instantly_campaign_id': campaign_data['campaign_id'],
        'campaign_name': campaign_data.get('campaign_name'),
        'campaign_status': campaign_data.get('campaign_status'),
        'leads_count': campaign_data.get('leads_count', 0),
        'emails_sent_count': campaign_data.get('emails_sent_count', 0),
        'reply_count': campaign_data.get('reply_count', 0),
        'raw_json': json.dumps(campaign_data),
        'sync_batch_id': batch_id,
    }

def transform_lead(lead_data, campaign_id, batch_id):
    """Transform lead from Instantly API to DB format"""
    # Similar pattern

def transform_step(step_data, campaign_id, batch_id):
    """Transform step analytics"""
    # Similar pattern

# ... other transforms
```

#### 1.2 Create lib/sync/upsert.py

**Purpose:** Smart upsert with JSONB merge (don't overwrite old data!)

```python
def upsert_with_merge(conn, table_name, records, batch_id):
    """
    UPSERT with raw_json MERGE

    - New records: INSERT
    - Existing records: UPDATE + MERGE raw_json
    - Batch size: 500
    """

    BATCH_SIZE = 500
    cursor = conn.cursor()

    # Get existing records with raw_json
    ids = [r['instantly_campaign_id'] for r in records]
    cursor.execute(f"""
        SELECT instantly_campaign_id, raw_json
        FROM {table_name}
        WHERE instantly_campaign_id IN ({','.join(['?'] * len(ids))})
    """, ids)

    existing_map = {row[0]: json.loads(row[1]) for row in cursor.fetchall()}

    # Merge for existing records
    merged_records = []
    for record in records:
        campaign_id = record['instantly_campaign_id']
        existing = existing_map.get(campaign_id)

        if existing:
            # MERGE: old properties + new properties
            merged_json = {**existing, **json.loads(record['raw_json'])}
            record['raw_json'] = json.dumps(merged_json)

        merged_records.append(record)

    # Batch UPSERT
    stats = {'inserted': 0, 'updated': 0, 'failed': 0}

    for i in range(0, len(merged_records), BATCH_SIZE):
        batch = merged_records[i:i + BATCH_SIZE]

        for record in batch:
            try:
                cursor.execute(f"""
                    INSERT INTO {table_name} (...)
                    VALUES (...)
                    ON CONFLICT(instantly_campaign_id) DO UPDATE SET
                        ... = excluded....,
                        updated_at = datetime('now')
                """, (...))

                if cursor.rowcount == 1:
                    stats['updated'] += 1
                else:
                    stats['inserted'] += 1

            except Exception as e:
                logger.error(f"Upsert failed: {e}")
                stats['failed'] += 1

        conn.commit()

    return stats
```

#### 1.3 Create lib/sync/logger.py

**Purpose:** 3-tier logging (console + JSON files + DB)

```python
import json
from pathlib import Path
from datetime import datetime

class SyncLogger:
    """
    3-tier logging inspired by Shadi architecture

    1. Console - always (for engineer)
    2. JSON file - always (for debugging)
    3. Database - only important (for client/monitoring)
    """

    def __init__(self, batch_id, db_conn=None):
        self.batch_id = batch_id
        self.db_conn = db_conn

        # Daily log rotation
        today = datetime.now().strftime('%Y-%m-%d')
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)

        self.log_file = self.log_dir / f"{today}.jsonl"
        self.error_file = self.log_dir / 'errors' / f"{today}.log"
        self.error_file.parent.mkdir(exist_ok=True)

    def log(self, level, step, message, meta=None):
        """Log to all 3 tiers"""

        log_entry = {
            'batch_id': self.batch_id,
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'step': step,
            'message': message,
            'meta': meta or {}
        }

        # 1. Console (always)
        print(f"[{level}] {step}: {message}")

        # 2. JSON file (always - raw stream)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')

        # 3. Database (only important - no noise!)
        if level in ['ERROR', 'WARNING'] or step in ['START', 'END', 'TIMEOUT']:
            if self.db_conn:
                cursor = self.db_conn.cursor()
                cursor.execute("""
                    INSERT INTO sync_logs (batch_id, level, step, message, meta)
                    VALUES (?, ?, ?, ?, ?)
                """, (self.batch_id, level, step, message, json.dumps(meta)))
                self.db_conn.commit()

        # Error file (errors only)
        if level == 'ERROR':
            with open(self.error_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] {step}: {message}\n")

    def info(self, step, message, meta=None):
        self.log('INFO', step, message, meta)

    def error(self, step, message, meta=None):
        self.log('ERROR', step, message, meta)

    def warning(self, step, message, meta=None):
        self.log('WARNING', step, message, meta)
```

#### 1.4 Create lib/sync/cli.py

**Purpose:** Flexible CLI arguments (like Shadi)

```python
import argparse
from datetime import datetime, timedelta

def parse_args():
    """
    Parse CLI arguments for flexible sync options

    Examples:
    - python sync.py                      # Incremental (default)
    - python sync.py --all                # Full sync
    - python sync.py --from=2025-10-20    # From date
    - python sync.py --last=7d            # Last 7 days
    - python sync.py --rollback=2025-10-25 # Resync from date
    """

    parser = argparse.ArgumentParser(description='Instantly Data Sync')

    parser.add_argument('--all', action='store_true',
                       help='Full sync (all records)')

    parser.add_argument('--from', dest='from_date', type=str,
                       help='Sync from specific date (YYYY-MM-DD)')

    parser.add_argument('--to', dest='to_date', type=str,
                       help='Sync to specific date (YYYY-MM-DD)')

    parser.add_argument('--last', type=str,
                       help='Sync last N days/hours (7d, 24h, 1w, 1m)')

    parser.add_argument('--rollback', type=str,
                       help='Resync from specific date (YYYY-MM-DD)')

    args = parser.parse_args()

    # Process --last flag
    if args.last:
        units = {'h': 'hours', 'd': 'days', 'w': 'weeks', 'm': 'months'}
        match = re.match(r'(\d+)([hdwm])', args.last)
        if match:
            num, unit = match.groups()
            delta_args = {units[unit]: int(num)}
            args.from_date = (datetime.now() - timedelta(**delta_args)).strftime('%Y-%m-%d')

    # Process --rollback
    if args.rollback:
        args.from_date = args.rollback

    return args
```

#### 1.5 Create lib/sync/api.py

**Purpose:** Instantly API client wrapper

```python
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class InstantlyAPI:
    """
    Instantly API client using curl (bypass Cloudflare)
    """

    def __init__(self):
        self.api_key = os.getenv('INSTANTLY_API_KEY')
        self.base_url = "https://api.instantly.ai/api/v2"

    def _call_api(self, endpoint, method="GET", data=None):
        """Call API using curl"""

        url = f"{self.base_url}{endpoint}"

        cmd = [
            "curl", "-s",
            "-H", f"Authorization: Bearer {self.api_key}",
            "-H", "Content-Type: application/json"
        ]

        if method == "POST":
            cmd.extend(["-X", "POST"])
            if data:
                cmd.extend(["-d", json.dumps(data)])

        cmd.append(url)

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            raise Exception(f"API call failed: {result.stderr}")

        return json.loads(result.stdout)

    def get_campaigns(self):
        """Fetch all campaigns"""
        return self._call_api("/campaigns/analytics")

    def get_leads(self, campaign_id, limit=1000):
        """Fetch leads for campaign"""
        return self._call_api("/leads/list", method="POST", data={
            "campaign_id": campaign_id,
            "limit": limit
        })

    # ... other API methods
```

---

### Phase 2: Main Sync Script (1 hour)

#### 2.1 Create scripts/sync.py

**Purpose:** Orchestrate sync using modular components

```python
#!/usr/bin/env python3
"""
Instantly Data Sync - Modular Architecture

Usage:
    python sync.py                      # Incremental (default)
    python sync.py --all                # Full sync
    python sync.py --from=2025-10-20    # From date
    python sync.py --last=7d            # Last 7 days
"""

import sys
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import modular components
from lib.sync.cli import parse_args
from lib.sync.logger import SyncLogger
from lib.sync.api import InstantlyAPI
from lib.sync.transform import (
    transform_campaign,
    transform_lead,
    transform_step,
    # ... other transforms
)
from lib.sync.upsert import upsert_with_merge

# Config
DB_PATH = Path(__file__).parent.parent / "data" / "instantly.db"

def sync_campaigns(api, conn, logger, batch_id):
    """Sync campaigns"""

    logger.info('CAMPAIGNS_START', 'Fetching campaigns from Instantly API')

    # Fetch from API
    campaigns_data = api.get_campaigns()
    logger.info('CAMPAIGNS_FETCH', f'Fetched {len(campaigns_data)} campaigns')

    # Transform
    transformed = [transform_campaign(c, batch_id) for c in campaigns_data]

    # Upsert
    stats = upsert_with_merge(conn, 'instantly_campaigns_raw', transformed, batch_id)

    logger.info('CAMPAIGNS_END', f'Inserted: {stats["inserted"]}, Updated: {stats["updated"]}', stats)

    return [c['campaign_id'] for c in campaigns_data]

def sync_leads(api, conn, logger, batch_id, campaign_ids):
    """Sync leads for campaigns"""

    logger.info('LEADS_START', f'Syncing leads for {len(campaign_ids)} campaigns')

    total_stats = {'inserted': 0, 'updated': 0, 'failed': 0}

    for campaign_id in campaign_ids:
        leads_data = api.get_leads(campaign_id)
        transformed = [transform_lead(l, campaign_id, batch_id) for l in leads_data]

        stats = upsert_with_merge(conn, 'instantly_leads_raw', transformed, batch_id)

        total_stats['inserted'] += stats['inserted']
        total_stats['updated'] += stats['updated']
        total_stats['failed'] += stats['failed']

    logger.info('LEADS_END', f'Total leads synced', total_stats)

    return total_stats

# ... similar for steps, accounts, emails, etc.

def main():
    """Main sync orchestrator"""

    # Parse CLI args
    args = parse_args()

    # Generate batch ID
    batch_id = str(uuid.uuid4())

    # Connect to database
    conn = sqlite3.connect(DB_PATH)

    # Initialize logger
    logger = SyncLogger(batch_id, conn)

    logger.info('START', f'Sync started (batch_id: {batch_id})', {
        'mode': 'full' if args.all else 'incremental',
        'from_date': args.from_date if hasattr(args, 'from_date') else None
    })

    try:
        # Initialize API client
        api = InstantlyAPI()

        # Sync campaigns
        campaign_ids = sync_campaigns(api, conn, logger, batch_id)

        # Parallel sync (or sequential if preferred)
        sync_leads(api, conn, logger, batch_id, campaign_ids)
        sync_steps(api, conn, logger, batch_id, campaign_ids)
        sync_accounts(api, conn, logger, batch_id)
        sync_emails(api, conn, logger, batch_id)
        sync_daily_analytics(api, conn, logger, batch_id)
        sync_overview(api, conn, logger, batch_id)

        logger.info('END', 'Sync completed successfully')

    except Exception as e:
        logger.error('FATAL', f'Sync failed: {e}')
        raise

    finally:
        conn.close()

if __name__ == "__main__":
    main()
```

---

### Phase 3: Database Enhancements (30 minutes)

#### 3.1 Add sync_logs table

```sql
-- Migration: add_sync_logs.sql

CREATE TABLE IF NOT EXISTS sync_logs (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    batch_id TEXT NOT NULL,

    level TEXT NOT NULL,  -- INFO, WARNING, ERROR
    step TEXT NOT NULL,   -- START, END, CAMPAIGNS_FETCH, etc.
    message TEXT NOT NULL,
    meta TEXT,            -- JSON metadata

    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX idx_sync_logs_batch ON sync_logs(batch_id);
CREATE INDEX idx_sync_logs_level ON sync_logs(level);
CREATE INDEX idx_sync_logs_created ON sync_logs(created_at DESC);
```

#### 3.2 Add sync_batch_id to all tables

```sql
-- Migration: add_sync_batch_id.sql

ALTER TABLE instantly_campaigns_raw ADD COLUMN sync_batch_id TEXT;
ALTER TABLE instantly_leads_raw ADD COLUMN sync_batch_id TEXT;
ALTER TABLE instantly_steps_raw ADD COLUMN sync_batch_id TEXT;
-- ... for all tables

CREATE INDEX idx_campaigns_batch ON instantly_campaigns_raw(sync_batch_id);
CREATE INDEX idx_leads_batch ON instantly_leads_raw(sync_batch_id);
-- ... for all tables
```

---

### Phase 4: Automation Options (Choose one or both)

#### Option A: GitHub Actions (Recommended for Local)

**Purpose:** Run sync daily even if PC is off (GitHub servers)

Create `.github/workflows/instantly-sync.yml`:

```yaml
name: Instantly Data Sync

on:
  schedule:
    - cron: '0 9 * * *'  # Every day at 9:00 AM UTC
  workflow_dispatch:      # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run sync
        env:
          INSTANTLY_API_KEY: ${{ secrets.INSTANTLY_API_KEY }}
        run: |
          python modules/instantly/scripts/sync.py

      - name: Upload database artifact
        uses: actions/upload-artifact@v3
        with:
          name: instantly-db
          path: data/instantly.db

      - name: Upload logs
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: sync-logs
          path: logs/
```

**Setup:**
1. Add INSTANTLY_API_KEY to GitHub Secrets
2. Commit workflow file
3. Push to GitHub
4. Runs automatically daily

#### Option B: Vercel Cron (If migrating to cloud later)

Create `app/api/sync/route.ts`:

```typescript
import { NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function POST(request: Request) {
  try {
    // Run Python sync script
    const { stdout, stderr } = await execAsync(
      'python modules/instantly/scripts/sync.py',
      { cwd: process.cwd() }
    );

    return NextResponse.json({
      success: true,
      output: stdout,
      errors: stderr
    });

  } catch (error) {
    return NextResponse.json({
      success: false,
      error: error.message
    }, { status: 500 });
  }
}

export const runtime = 'nodejs';
export const maxDuration = 300; // 5 minutes
```

Add to `vercel.json`:

```json
{
  "crons": [{
    "path": "/api/sync",
    "schedule": "0 9 * * *"
  }]
}
```

---

## Implementation Timeline

### Week 1: Modular Architecture
- Day 1-2: lib/sync/{transform, upsert, logger, cli, api}.py
- Day 3: scripts/sync.py orchestrator
- Day 4: Testing & debugging
- Day 5: Database migrations (sync_logs, sync_batch_id)

### Week 2: Automation & Polish
- Day 1-2: GitHub Actions setup
- Day 3: Documentation (README updates)
- Day 4-5: Testing incremental sync, CLI options

**Total time:** 10-12 hours of focused work

---

## Benefits After Refactoring

### Architecture
- ✅ Modular, maintainable code
- ✅ Reusable components (transform, upsert, logger)
- ✅ Easy to test individual modules
- ✅ Clear separation of concerns

### Features
- ✅ **Incremental sync** (only new/changed data)
- ✅ **Flexible CLI** (--all, --from, --last, --rollback)
- ✅ **Smart JSONB merge** (don't lose old data!)
- ✅ **3-tier logging** (console + JSON + DB)
- ✅ **Batch tracking** (sync_batch_id for monitoring)
- ✅ **Automation ready** (GitHub Actions / Vercel Cron)

### Performance
- ✅ Faster syncs (incremental mode)
- ✅ Better logging (easy debugging)
- ✅ Batch processing (500 records at a time)
- ✅ Error recovery (failed batches don't break entire sync)

### Monitoring
- ✅ Sync history in database
- ✅ Daily JSON logs for debugging
- ✅ Error-only logs for quick issues
- ✅ Batch tracking for rollback

---

## Migration Strategy

### Option 1: Big Bang (Recommended)
1. Create new modular structure in parallel
2. Test thoroughly
3. Switch from old script to new
4. Archive old collect_data.py

### Option 2: Gradual
1. Start with lib/sync/logger.py
2. Refactor collect_data.py to use logger
3. Gradually extract transform, upsert, etc.
4. Finally split into modular architecture

**Recommendation:** Option 1 (cleaner, less risk of breaking existing)

---

## Post-Refactoring Workflow

### Daily Use:

```bash
# Incremental sync (default)
python modules/instantly/scripts/sync.py

# Full sync (rare, when needed)
python modules/instantly/scripts/sync.py --all

# Sync last 7 days
python modules/instantly/scripts/sync.py --last=7d

# Rollback and resync from Oct 25
python modules/instantly/scripts/sync.py --rollback=2025-10-25
```

### Monitoring:

```sql
-- View recent syncs
SELECT * FROM sync_logs
WHERE step IN ('START', 'END')
ORDER BY created_at DESC
LIMIT 10;

-- Check errors
SELECT * FROM sync_logs
WHERE level = 'ERROR'
ORDER BY created_at DESC;

-- Batch statistics
SELECT
    batch_id,
    COUNT(*) as total_logs,
    SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) as errors
FROM sync_logs
GROUP BY batch_id
ORDER BY created_at DESC;
```

---

## Questions to Decide

### 1. Automation Strategy

**A. GitHub Actions (PC can be off)**
- ✅ Runs on GitHub servers
- ✅ Free (2000 minutes/month)
- ✅ Database stored as artifacts
- ❌ Need to download artifact manually

**B. Local Cron/Task Scheduler (PC must be on)**
- ✅ Database always on PC
- ✅ No download needed
- ❌ PC must be running at 9 AM

**C. Vercel Cron (when migrating to cloud)**
- ✅ 24/7 availability
- ✅ No PC needed
- ❌ Need PostgreSQL/Supabase (not SQLite)

**Recommendation:** Start with B (local), migrate to C when ready for cloud

### 2. Sync Frequency

- Daily at 9 AM? (recommended)
- Every 6 hours?
- Manual only?

### 3. Data Retention

- Keep all sync_logs forever?
- Rotate logs after 30 days?
- Archive old logs?

---

## Next Steps

Ready to implement? I can:

1. **Create all modular files** (lib/sync/*.py)
2. **Write migrations** (sync_logs, sync_batch_id)
3. **Build scripts/sync.py** orchestrator
4. **Set up GitHub Actions** or local automation
5. **Test full workflow** with your Instantly data

**What do you want to start with?**
- Full implementation now?
- Just create the structure and you'll fill in?
- Start with one module (e.g., logger) as proof of concept?

---

**Created:** 2025-11-01
**Based on:** Shadi project (HubSpot sync architecture)
**Estimated time:** 10-12 hours for full implementation
