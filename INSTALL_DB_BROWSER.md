# DB Browser for SQLite - Installation Guide

## Windows Installation

### Method 1: Direct Download (Recommended)

1. **Download installer:**
   - Go to: https://sqlitebrowser.org/dl/
   - Click: **DB Browser for SQLite - Windows**
   - Download: `DB.Browser.for.SQLite-v3.13.1-win64.msi` (latest version)
   - File size: ~40 MB

2. **Install:**
   - Double-click the `.msi` file
   - Click "Next" → "Next" → "Install"
   - Wait 30 seconds
   - Click "Finish"

3. **Launch:**
   - Start Menu → Search "DB Browser"
   - Or desktop icon (if created)

### Method 2: Portable Version (No Install)

1. **Download ZIP:**
   - Same page: https://sqlitebrowser.org/dl/
   - Download: `DB.Browser.for.SQLite-v3.13.1-win64.zip`

2. **Extract:**
   - Right-click → Extract All
   - Choose location (e.g., `C:\Tools\DB Browser`)

3. **Run:**
   - Open extracted folder
   - Double-click `DB Browser for SQLite.exe`

---

## Open Your Database

### Step-by-step:

1. **Launch DB Browser**

2. **Open Database:**
   - Click **"Open Database"** button (or File → Open Database)
   - Navigate to: `C:\Users\79818\Desktop\Outreach - new\data\instantly.db`
   - Click **"Open"**

3. **You'll see:**
   - **Database Structure** tab - All 7 tables listed
   - **Browse Data** tab - View records like Excel
   - **Execute SQL** tab - Run custom queries
   - **DB Schema** tab - Visual diagram

---

## Quick Guide to Interface

### Tabs:

**1. Database Structure**
```
├── Tables (7)
│   ├── instantly_campaigns_raw
│   ├── instantly_leads_raw
│   ├── instantly_steps_raw
│   ├── instantly_accounts_raw
│   ├── instantly_emails_raw
│   ├── instantly_daily_analytics_raw
│   └── instantly_overview_raw
├── Indexes
└── Triggers
```

**2. Browse Data**
- Select table from dropdown
- See data in table format
- Filter, sort, search
- Edit cells (be careful!)

**3. Execute SQL**
```sql
-- Example: Get campaigns with best reply rate
SELECT
    campaign_name,
    emails_sent_count,
    reply_count,
    ROUND(reply_count * 100.0 / emails_sent_count, 2) as reply_rate
FROM instantly_campaigns_raw
WHERE campaign_status = 1
ORDER BY reply_rate DESC;
```

**4. DB Schema**
- Visual diagram of tables
- See relationships (foreign keys)
- Export as image

---

## Useful Features

### Export to CSV

1. Go to **Execute SQL** tab
2. Run your query
3. Click **Export** button (top right)
4. Choose **CSV format**
5. Save file

### View JSON Data

- Click on any `raw_json` column
- JSON will display in pretty format
- Copy/paste as needed

### Search Across Tables

- Edit → Preferences → General
- Enable "Search all tables"
- Ctrl+F to search

---

## Keyboard Shortcuts

```
Ctrl+O     Open database
Ctrl+W     Close database
Ctrl+N     New database
Ctrl+T     Execute SQL tab
Ctrl+E     Edit pragma
F5         Refresh
Ctrl+F     Find
```

---

## Common Queries

### 1. View all campaigns with stats

```sql
SELECT
    campaign_name,
    leads_count,
    contacted_count,
    emails_sent_count,
    reply_count,
    bounced_count,
    ROUND(reply_count * 100.0 / emails_sent_count, 2) as reply_rate,
    synced_at
FROM instantly_campaigns_raw
ORDER BY synced_at DESC;
```

### 2. Get accounts with best warmup score

```sql
SELECT
    email,
    stat_warmup_score,
    warmup_status,
    status,
    organization
FROM instantly_accounts_raw
ORDER BY stat_warmup_score DESC;
```

### 3. Daily performance trend

```sql
SELECT
    date,
    sent,
    unique_opened,
    unique_replies,
    ROUND(unique_replies * 100.0 / sent, 2) as reply_rate,
    ROUND(unique_opened * 100.0 / sent, 2) as open_rate
FROM instantly_daily_analytics_raw
ORDER BY date DESC
LIMIT 30;
```

### 4. View raw JSON for specific campaign

```sql
SELECT raw_json
FROM instantly_campaigns_raw
WHERE campaign_name LIKE '%your_campaign_name%';
```

---

## Troubleshooting

### "Database is locked"

**Cause:** Another program (Python script) is using the database

**Fix:**
1. Close any running Python scripts
2. Try again

### "Cannot open database file"

**Cause:** File path is wrong or file doesn't exist

**Fix:**
1. Check path: `C:\Users\79818\Desktop\Outreach - new\data\instantly.db`
2. Run `python init_database.py` if file missing

### "Permission denied"

**Cause:** File is read-only or no write permissions

**Fix:**
1. Right-click file → Properties
2. Uncheck "Read-only"
3. Click OK

---

## Tips

1. **Read-only mode:** File → Open Database Read Only (safer for exploring)
2. **Backup before editing:** Copy `instantly.db` before making changes
3. **Auto-refresh:** Edit → Preferences → Data Browser → Enable auto-refresh
4. **Theme:** Edit → Preferences → General → Choose dark/light theme

---

## Next Steps After Install

1. Open `instantly.db`
2. Browse **instantly_campaigns_raw** table
3. Try running sample queries
4. Export data to CSV for analysis
5. Explore JSON data in `raw_json` columns

---

**Installation time:** 2 minutes
**Database location:** `C:\Users\79818\Desktop\Outreach - new\data\instantly.db`
**Official website:** https://sqlitebrowser.org/
