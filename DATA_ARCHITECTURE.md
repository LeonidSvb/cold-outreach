# Data Architecture (Updated: 2025-11-11)

## 🏗️ NEW CLEAN ARCHITECTURE

**IMPORTANT:** This project migrated to a Parquet-based single source of truth architecture.
**DO NOT** create CSV files in module folders anymore!

---

## 📁 Directory Structure

```
/data/
  /projects/          # ✅ PRODUCTION DATA (Parquet only)
    soviet_boots_europe.parquet
    hvac_usa.parquet
    australia_field_services.parquet

  /exports/           # ✅ FINAL CSV EXPORTS (for campaigns)
    soviet_boots_email_outreach.csv
    soviet_boots_phone_outreach.csv

/modules/
  /shared/
    parquet_manager.py    # ✅ Central data access layer

  /google_maps/scripts/   # ✅ Code only
  /scraping/scripts/      # ✅ Code only
  /openai/scripts/        # ✅ Code only
  /apify/scripts/         # ✅ Code only

/archive/                 # 💾 Old backups (not in git)
```

---

## ✅ CORRECT WAY (New Architecture)

### **Step 1: Use ParquetManager**

```python
from modules.shared.parquet_manager import ParquetManager

# Initialize for your project
manager = ParquetManager(project='soviet_boots_europe')
```

### **Step 2: Load data**

```python
# Load all columns
df = manager.load()

# Load specific columns (faster!)
df = manager.load(columns=['name', 'emails', 'website'])
```

### **Step 3: Add new columns (incremental!)**

```python
# Example: Add scraping results
scraping_data = pd.DataFrame({
    'place_id': [...],
    'emails': [...],
    'scraped_content': [...]
})

manager.add_columns(scraping_data, key='place_id')
# Data automatically merged into existing Parquet file
```

### **Step 4: Export CSV (only for final campaigns)**

```python
# Export filtered data
manager.export_csv(
    output='my_campaign.csv',
    columns=['name', 'emails', 'summary'],
    filters={'contact_status': 'with_emails', 'relevance_score': '>=7'}
)
```

---

## ❌ WRONG WAY (Old Architecture - DON'T USE!)

**DON'T DO THIS:**
```python
# ❌ Writing CSV to module folder
df.to_csv('modules/scraping/results/enriched.csv')

# ❌ Creating duplicate data in each module
pd.read_csv('modules/google_maps/results/places.csv')
scraped = scrape(places)
scraped.to_csv('modules/scraping/results/scraped.csv')  # DUPLICATE!

# ❌ Multiple versions of same data
# modules/google_maps/results/european_leads.csv      (duplicate 1)
# modules/scraping/results/european_enriched.csv      (duplicate 2)
# modules/openai/results/european_with_ai.csv         (duplicate 3)
```

**Why this is wrong:**
- Creates duplicates (322 MB for 2,928 leads!)
- Data scattered across modules
- No single source of truth
- Hard to track versions

---

## 🚀 Data Flow (New Architecture)

```
1. Google Places API
   ↓ manager.add_columns(google_data)

2. Web Scraping
   ↓ manager.add_columns(scraping_data)

3. AI Analysis
   ↓ manager.add_columns(ai_data)

4. Export Campaign CSV
   ↓ manager.export_csv('campaign.csv')
```

**Result:** One Parquet file with ALL columns, no duplicates!

---

## 📊 Benefits

### **Before (Old Architecture):**
- 322 MB duplicated across 6 folders
- Same data stored 5-10 times
- CSV format (slow, large)
- No central management

### **After (New Architecture):**
- 7.7 MB in 3 Parquet files (97.6% savings!)
- Each dataset exactly once
- Parquet format (fast, compressed)
- ParquetManager - unified interface

### **Performance:**
- Parquet read/write: **10-50x faster** than CSV
- Columnar storage: read only needed columns
- Incremental updates: no full rewrites

---

## 🔍 Finding Existing Projects

```python
from modules.shared.parquet_manager import list_projects

# List all available projects
projects = list_projects()
print(f"Available projects: {projects}")

# Get stats for a project
manager = ParquetManager(project='soviet_boots_europe')
stats = manager.get_stats()
print(f"Total rows: {stats['total_rows']}")
print(f"Columns: {stats['columns']}")
print(f"File size: {stats['file_size_mb']} MB")
```

---

## 🛠️ For Script Authors

### **When creating new enrichment scripts:**

1. **Import ParquetManager:**
   ```python
   from modules.shared.parquet_manager import ParquetManager
   ```

2. **Load project data:**
   ```python
   manager = ParquetManager(project='my_project')
   df = manager.load()
   ```

3. **Process data:**
   ```python
   df['new_column'] = process(df)
   ```

4. **Add columns back:**
   ```python
   manager.add_columns(df[['place_id', 'new_column']], key='place_id')
   ```

5. **Export if needed:**
   ```python
   manager.export_csv('exports/final.csv')
   ```

### **Module folder usage:**

- `modules/*/scripts/` - ✅ Your code here
- `modules/*/results/` - 📁 Empty (temp files during execution, gitignored)
- `modules/*/data/` - 📁 Empty (temp files during execution, gitignored)

**Temporary files are OK during script execution, but:**
- They should be deleted after processing
- They are gitignored (never committed)
- Production data goes to `/data/projects/`

---

## 📝 Examples

### **Example 1: Add new project**

```python
from modules.shared.parquet_manager import ParquetManager
import pandas as pd

# Create new project
manager = ParquetManager(project='new_project')

# Initial data from API
initial_data = pd.DataFrame({
    'place_id': ['1', '2', '3'],
    'name': ['Business A', 'Business B', 'Business C'],
    'website': ['a.com', 'b.com', 'c.com']
})

manager.save(initial_data)
print("Project created!")
```

### **Example 2: Enrich existing project**

```python
# Load existing project
manager = ParquetManager(project='hvac_usa')
df = manager.load(columns=['place_id', 'website'])

# Scrape emails
emails_data = scrape_emails(df['website'])

# Add emails column
manager.add_columns(emails_data, key='place_id')
print("Emails added!")
```

### **Example 3: Export campaign list**

```python
manager = ParquetManager(project='soviet_boots_europe')

# Export high-value leads with emails
count = manager.export_csv(
    output='high_value_campaign.csv',
    columns=['name', 'emails', 'phone', 'summary', 'relevance_score'],
    filters={
        'contact_status': 'with_emails',
        'relevance_score': '>=8'
    }
)

print(f"Exported {count} high-value leads")
```

---

## 🔒 What's Gitignored

```gitignore
# Production data (not committed)
data/projects/*.parquet
data/projects/*_metadata.json
data/exports/*.csv

# Module temporary files
modules/*/results/*
modules/*/data/*

# Old backups
archive/
```

**Why:**
- Data files can be large (>100 MB)
- Contains business data (privacy)
- Can be regenerated from scripts

---

## 📚 Additional Resources

- **ParquetManager Code:** `modules/shared/parquet_manager.py`
- **Full Refactoring Plan:** `REFACTORING_PLAN.md`
- **Module Template:** `docs/MODULE_TEMPLATE.md`

---

## ❓ FAQ

**Q: Can I still use CSV for input data?**
A: Yes! Load CSV, process it, then save to Parquet:
```python
df = pd.read_csv('input.csv')
manager = ParquetManager(project='my_project')
manager.save(df)
```

**Q: What if I need CSV output?**
A: Use `manager.export_csv()` - it's designed for final campaign exports.

**Q: Can I read Parquet directly?**
A: Yes, but prefer ParquetManager for consistency:
```python
# Direct (OK)
df = pd.read_parquet('data/projects/my_project.parquet')

# Better (recommended)
manager = ParquetManager(project='my_project')
df = manager.load()
```

**Q: Where do temporary files go during script execution?**
A: `modules/*/results/` or `modules/*/data/` - they're gitignored and should be cleaned up after.

**Q: What happened to old data?**
A: Safely archived in `/archive/` folder (gitignored, 295 MB backup).

---

**Last Updated:** 2025-11-11
**Architecture Version:** 2.0 (Parquet-based)
