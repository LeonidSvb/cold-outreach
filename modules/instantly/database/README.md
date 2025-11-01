# Instantly SQLite Database

Complete local database solution for Instantly API raw data storage.

---

## Quick Start

### 1. Initialize Database

```bash
cd modules/instantly/scripts
python init_database.py
```

**What it does:**
- Creates `data/instantly.db` file
- Applies complete schema (7 tables)
- Verifies all tables created

**Expected output:**
```
================================================================================
  INSTANTLY DATABASE INITIALIZATION
================================================================================

>>> Creating data directory...
  SUCCESS: Directory ready: C:\...\data

>>> Creating database and applying schema...
  SUCCESS: Database created: C:\...\data\instantly.db

>>> Verifying tables...
  Tables created:
    ✓ instantly_campaigns_raw
    ✓ instantly_leads_raw
    ✓ instantly_steps_raw
    ✓ instantly_accounts_raw
    ✓ instantly_emails_raw
    ✓ instantly_daily_analytics_raw
    ✓ instantly_overview_raw
```

---

### 2. Collect Data from Instantly API

```bash
python collect_data.py
```

**What it does:**
- Connects to Instantly API v2
- Collects data from all endpoints
- Stores raw JSON + extracted fields
- Updates existing records (upsert logic)

**Expected output:**
```
================================================================================
  INSTANTLY DATA COLLECTION
================================================================================

>>> Collecting campaigns...
  ✓ Campaigns collected: 5

>>> Collecting leads for 5 campaigns...
  ✓ Leads collected: 234

>>> Collecting steps for 5 campaigns...
  ✓ Steps collected: 15

>>> Collecting accounts...
  ✓ Accounts collected: 3

>>> Collecting emails...
  ✓ Emails collected: 450

>>> Collecting daily analytics...
  ✓ Daily records collected: 30

>>> Collecting overview...
  ✓ Overview collected

================================================================================
  COLLECTION COMPLETE
================================================================================

  Records Collected:
    Campaigns:           5
    Leads:             234
    Steps:              15
    Accounts:            3
    Emails:            450
    Daily Analytics:    30
    Overview:            1

  Errors:                0
```

---

### 3. View Database Statistics

```bash
python init_database.py --stats
```

**Shows:**
- Record counts per table
- Last sync timestamps
- Database size

---

## Install DB Browser for SQLite

Visual GUI tool to explore your database.

### Download

**Windows:**
1. Go to: https://sqlitebrowser.org/dl/
2. Download: `DB.Browser.for.SQLite-v3.12.2-win64.msi`
3. Install (next → next → finish)

**macOS:**
```bash
brew install --cask db-browser-for-sqlite
```

**Linux:**
```bash
sudo apt install sqlitebrowser
```

### Open Database

1. Launch DB Browser for SQLite
2. Click **"Open Database"**
3. Navigate to: `C:\Users\...\Desktop\Outreach - new\data\instantly.db`
4. Click **Open**

**Interface:**
- **Database Structure** tab - See all tables, columns, indexes
- **Browse Data** tab - View table data (like Excel)
- **Execute SQL** tab - Run custom queries
- **DB Schema** tab - Visual diagram

---

## Database Schema

### Tables Overview

| Table | Purpose | Source Endpoint |
|-------|---------|----------------|
| `instantly_campaigns_raw` | Campaign analytics | `/campaigns/analytics` |
| `instantly_leads_raw` | Lead data | `/leads/list` |
| `instantly_steps_raw` | Step analytics | `/campaigns/analytics/steps` |
| `instantly_accounts_raw` | Email accounts | `/accounts` |
| `instantly_emails_raw` | Email details | `/emails` |
| `instantly_daily_analytics_raw` | Daily metrics | `/campaigns/analytics/daily` |
| `instantly_overview_raw` | Account overview | `/campaigns/analytics/overview` |

### Common Fields (All Tables)

- `id` - Primary key (auto-generated)
- `raw_json` - Complete JSON from API (preserves ALL data)
- `synced_at` - When record was last synced
- `created_at` - When record was first created
- `updated_at` - When record was last modified

### Foreign Keys

```
instantly_campaigns_raw (campaign_id)
  ↓
  ├── instantly_leads_raw (campaign_id)
  ├── instantly_steps_raw (campaign_id)
  └── instantly_emails_raw (campaign_id)
```

---

## Usage Examples

### Query in DB Browser

**Get all campaigns with stats:**
```sql
SELECT
    campaign_name,
    leads_count,
    emails_sent_count,
    reply_count,
    ROUND(reply_count * 100.0 / emails_sent_count, 2) as reply_rate
FROM instantly_campaigns_raw
WHERE campaign_status = 1  -- Active campaigns only
ORDER BY emails_sent_count DESC;
```

**Get leads with most recent sync:**
```sql
SELECT
    email,
    first_name,
    last_name,
    company_name,
    lead_status,
    synced_at
FROM instantly_leads_raw
ORDER BY synced_at DESC
LIMIT 100;
```

**Daily analytics trend:**
```sql
SELECT
    date,
    sent,
    unique_replies,
    ROUND(unique_replies * 100.0 / sent, 2) as reply_rate
FROM instantly_daily_analytics_raw
ORDER BY date DESC
LIMIT 30;
```

### Export to CSV

**In DB Browser:**
1. Run your query in **Execute SQL** tab
2. Click **Export** button
3. Choose **CSV format**
4. Save file

**Alternative (Python):**
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('data/instantly.db')
df = pd.read_sql_query("SELECT * FROM instantly_leads_raw", conn)
df.to_csv('leads_export.csv', index=False)
```

---

## Automation

### Windows Task Scheduler

**Run data collection daily at 9:00 AM:**

1. Open Task Scheduler (Win + R → `taskschd.msc`)
2. Create Basic Task
3. Name: "Instantly Data Sync"
4. Trigger: Daily at 9:00 AM
5. Action: Start a program
   - Program: `python.exe`
   - Arguments: `C:\...\modules\instantly\scripts\collect_data.py`
   - Start in: `C:\...\modules\instantly\scripts`
6. Finish

**Result:** Data syncs automatically every morning, even if you're sleeping.

### Auto-run on PC Startup

**Option 1: Startup folder**
1. Win + R → `shell:startup`
2. Create shortcut to: `collect_data.py`
3. Edit shortcut target:
   ```
   python.exe "C:\...\modules\instantly\scripts\collect_data.py"
   ```

**Option 2: Task Scheduler**
- Same as above, but trigger: "At startup"

---

## Troubleshooting

### Database locked error

**Cause:** Another program (DB Browser) has database open

**Fix:**
1. Close DB Browser
2. Run script again

### API timeout

**Cause:** Instantly API slow response

**Fix:**
- Script automatically retries
- Increase timeout in `collect_data.py` (line 80)

### Cloudflare 403 error

**Cause:** Python requests blocked

**Fix:**
- Already handled! Script uses `curl` to bypass
- Ensure `curl` installed (comes with Windows 10+)

### Empty response

**Cause:** API endpoint returned no data

**Fix:**
- Check API key is valid
- Verify endpoint in Instantly docs
- Some endpoints may be empty (e.g., no emails sent yet)

---

## Migration to Cloud (Later)

When ready to deploy 24/7:

### Export to PostgreSQL (Supabase)

```bash
# Install pgloader
pgloader sqlite://data/instantly.db postgresql://[supabase-url]/postgres
```

**What happens:**
- All data transferred automatically
- Schema converted (SQLite → PostgreSQL)
- Foreign keys preserved
- Takes ~5-10 minutes for typical dataset

### Update scripts

Change connection from:
```python
conn = sqlite3.connect('data/instantly.db')
```

To:
```python
import psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
```

**Migration time:** ~1 hour total

---

## File Structure

```
modules/instantly/
├── database/
│   └── README.md (this file)
├── scripts/
│   ├── init_database.py      - Initialize database
│   ├── collect_data.py        - Collect from API
│   └── (other scripts)
├── docs/
│   └── api-guide.md           - API documentation
└── results/
    └── (JSON files)

data/
└── instantly.db               - SQLite database (created by init)

migrations/
└── sqlite_instantly_init.sql  - Database schema
```

---

## Best Practices

### Data Collection

✅ **DO:**
- Run collection daily (Task Scheduler)
- Check `--stats` after collection
- Keep database file backed up (cloud storage)
- Export important queries to CSV

❌ **DON'T:**
- Run collection too frequently (API rate limits)
- Edit `raw_json` fields manually (breaks data integrity)
- Delete records (keep historical data)

### Database Maintenance

**Backup:**
```bash
# Simple - just copy the file
copy data\instantly.db data\instantly_backup_2025-11-01.db
```

**Vacuum (optimize size):**
```sql
VACUUM;
```

**Check integrity:**
```sql
PRAGMA integrity_check;
```

---

## Next Steps

1. ✅ Initialize database
2. ✅ Collect initial data
3. ✅ Install DB Browser
4. ✅ Explore your data
5. 🔄 Set up daily automation (optional)
6. 📊 Build visualizations (later)
7. ☁️ Migrate to cloud (when needed)

---

## Support

**Issues?**
- Check Troubleshooting section above
- Review logs in console output
- Verify API key in `.env`
- Ensure database not locked

**Migration help?**
- See "Migration to Cloud" section
- Estimated time: 1 hour
- Zero data loss

---

**Created:** 2025-11-01
**Database:** SQLite 3.38+
**Python:** 3.8+
