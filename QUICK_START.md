# Instantly SQLite Database - Quick Start

Everything you need to start working with your Instantly data.

---

## What Was Created

### 1. SQLite Database ✅
- **Location:** `data/instantly.db`
- **Tables:** 7 (campaigns, leads, steps, accounts, emails, daily_analytics, overview)
- **Current data:** Synced at 15:21 (Nov 1, 2025)
- **Size:** 0.20 MB

### 2. Python Scripts ✅
- `modules/instantly/scripts/init_database.py` - Create/reset database
- `modules/instantly/scripts/collect_data.py` - Sync data from Instantly API

### 3. Documentation ✅
- `INSTALL_DB_BROWSER.md` - How to install DB Browser for SQLite
- `modules/instantly/database/README.md` - Complete database guide
- `docs/INSTANTLY_SYNC_REFACTORING_PLAN.md` - Future architecture plan

---

## 5-Minute Quick Start

### 1. View Your Data (Right Now!)

**Download DB Browser for SQLite:**
1. Go to: https://sqlitebrowser.org/dl/
2. Download: `DB.Browser.for.SQLite-v3.13.1-win64.msi`
3. Install (2 minutes)
4. Open database: `C:\Users\79818\Desktop\Outreach - new\data\instantly.db`

**See this file for details:** `INSTALL_DB_BROWSER.md`

---

### 2. Sync Fresh Data

```bash
cd "C:\Users\79818\Desktop\Outreach - new\modules\instantly\scripts"

# Sync now
python collect_data.py

# Check stats
python init_database.py --stats
```

**Last sync:** 15:21 (8 hours ago)

---

### 3. View Statistics

```bash
python init_database.py --stats
```

**Current data:**
```
Campaigns:       4
Leads:           0
Steps:           9
Accounts:       10
Emails:          0
Daily Analytics: 1
Overview:        1
```

---

## What's Next?

### Option A: Use Current Setup (Simple)

**You have everything working:**
- SQLite database with all Instantly data
- Sync script (run manually when needed)
- DB Browser to explore data

**Daily workflow:**
1. Run: `python collect_data.py`
2. Open DB Browser
3. Query your data
4. Export to CSV if needed

---

### Option B: Implement Refactoring (Advanced)

**Why refactor?**
- Incremental sync (faster, only new data)
- Flexible CLI (--all, --from, --last=7d)
- Better logging (3-tier: console + JSON + DB)
- Automation (GitHub Actions or Vercel Cron)
- Modular architecture (easier to maintain)

**See detailed plan:** `docs/INSTANTLY_SYNC_REFACTORING_PLAN.md`

**Time needed:** 10-12 hours

**I can implement it for you** if you want!

---

## Common Tasks

### Sync Data
```bash
python modules/instantly/scripts/collect_data.py
```

### View Stats
```bash
python modules/instantly/scripts/init_database.py --stats
```

### Reset Database (Fresh Start)
```bash
python modules/instantly/scripts/init_database.py --force
python modules/instantly/scripts/collect_data.py
```

### Query in DB Browser

**Top campaigns by reply rate:**
```sql
SELECT
    campaign_name,
    emails_sent_count,
    reply_count,
    ROUND(reply_count * 100.0 / emails_sent_count, 2) as reply_rate
FROM instantly_campaigns_raw
WHERE campaign_status = 1
ORDER BY reply_rate DESC;
```

**Accounts by warmup score:**
```sql
SELECT
    email,
    stat_warmup_score,
    warmup_status
FROM instantly_accounts_raw
ORDER BY stat_warmup_score DESC;
```

---

## Files Created

```
C:\Users\79818\Desktop\Outreach - new\
├── data/
│   └── instantly.db                    # SQLite database (your data!)
├── migrations/
│   └── sqlite_instantly_init.sql       # Database schema
├── modules/instantly/
│   ├── scripts/
│   │   ├── init_database.py            # Initialize DB
│   │   └── collect_data.py             # Sync from API
│   └── database/
│       └── README.md                   # Full database guide
├── docs/
│   └── INSTANTLY_SYNC_REFACTORING_PLAN.md  # Future architecture
├── INSTALL_DB_BROWSER.md               # DB Browser install guide
└── QUICK_START.md                      # This file
```

---

## Automation Options

### Option 1: Windows Task Scheduler (PC must be on)

**Setup:**
1. Win + R → `taskschd.msc`
2. Create Basic Task → "Instantly Sync"
3. Trigger: Daily at 9:00 AM
4. Action: Start program
   - Program: `python.exe`
   - Arguments: `C:\Users\79818\Desktop\Outreach - new\modules\instantly\scripts\collect_data.py`
5. Done!

**Result:** Syncs automatically every morning

---

### Option 2: GitHub Actions (PC can be off)

**After refactoring**, data syncs on GitHub servers 24/7.

See: `docs/INSTANTLY_SYNC_REFACTORING_PLAN.md` → Phase 4

---

## Questions?

### "How do I see my data?"
→ Install DB Browser (see `INSTALL_DB_BROWSER.md`)
→ Open `data/instantly.db`
→ Browse tables

### "How do I sync fresh data?"
→ Run: `python modules/instantly/scripts/collect_data.py`

### "How do I export to CSV?"
→ DB Browser → Execute SQL → Run query → Export button

### "Should I refactor now or later?"
→ **Later** if current setup works for you
→ **Now** if you want automation + incremental sync

### "Can you implement the refactoring?"
→ **Yes!** Just say the word and I'll create all the modular files.

---

## Next Steps - Choose Your Path

### Path A: Simple (5 minutes)
1. Download DB Browser
2. Open `data/instantly.db`
3. Start exploring your data
4. Run `collect_data.py` when you need fresh data

### Path B: Automated (30 minutes)
1. Set up Windows Task Scheduler
2. Runs daily automatically
3. You just open DB Browser to see data

### Path C: Advanced (ask me to implement)
1. I'll refactor to modular architecture
2. Incremental sync + automation
3. Production-ready system
4. Takes 10-12 hours (I do it all)

---

**Which path do you choose?** 😊

---

**Created:** 2025-11-01
**Status:** ✅ Everything working, ready to use
**Your data:** `data/instantly.db` (synced 15:21)
