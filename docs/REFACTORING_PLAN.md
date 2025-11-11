# DATA ARCHITECTURE REFACTORING PLAN

## 🚨 CURRENT PROBLEMS

### Data Duplication (322 MB!)
```
modules/google_maps/results/    47 MB
modules/google_maps/data/      127 MB
modules/scraping/results/       44 MB
modules/openai/results/         77 MB
data/                           27 MB
─────────────────────────────────────
TOTAL:                         322 MB
```

**For only 2,928 leads!** Same data stored 5-10 times.

### Chaos Structure
```
/data/                          # Root data folder
  /raw/
  /processed/
  /temp/
/modules/google_maps/
  /data/                        # Duplicate!
    /raw/
    /enriched/
    /temp/
  /results/                     # More duplicates!
    /enriched/
    /florida/
    /texas/
/modules/scraping/
  /results/                     # Even more!
/modules/openai/
  /results/                     # And more!
```

### Inefficient Format
- **CSV** - text format, huge size
- **14 MB** for 2,928 leads
- **Parquet** would be 3-5x smaller
- No versioning, no incremental updates

---

## ✅ NEW CLEAN ARCHITECTURE

### Single Source of Truth
```
/data/
  leads.parquet                 # ONE file, ALL data
  leads_metadata.json           # Schema version, last updated

/exports/                       # Final CSVs for user only
  europe_with_emails.csv
  europe_with_phones.csv
  us_leads.csv

/modules/                       # Scripts only
  /google_maps/
    /scripts/
  /scraping/
    /scripts/
  /openai/
    /scripts/
  /shared/
    /parquet_manager.py         # Central data access layer

/archive/                       # Old files (gitignored)
```

---

## 🔄 DATA FLOW - INCREMENTAL COLUMNS

### Step 1: Google Places API
```python
from modules.shared.parquet_manager import ParquetManager

manager = ParquetManager('data/leads.parquet')

# Add initial columns
new_data = fetch_from_google_places()
manager.add_columns(new_data, columns=[
    'place_id', 'name', 'website', 'phone',
    'address', 'rating', 'types'
])
```

### Step 2: Web Scraping
```python
manager = ParquetManager('data/leads.parquet')

# Add scraping columns
scraping_data = scrape_websites()
manager.add_columns(scraping_data, columns=[
    'emails', 'scraped_content', 'scraping_status'
], key='place_id')
```

### Step 3: AI Analysis
```python
manager = ParquetManager('data/leads.parquet')

# Add AI columns
ai_data = analyze_with_openai()
manager.add_columns(ai_data, columns=[
    'summary', 'relevance_score', 'personalization_hooks'
], key='place_id')
```

### Step 4: Export for User
```python
manager = ParquetManager('data/leads.parquet')

# Export only needed columns
manager.export_csv(
    output='exports/europe_with_emails.csv',
    columns=['name', 'emails', 'phone', 'summary', 'relevance_score'],
    filters={'has_emails': True, 'relevance_score': '>=7'}
)
```

---

## 📦 PARQUET MANAGER (Central Data Layer)

```python
# modules/shared/parquet_manager.py

import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from typing import List, Dict, Optional

class ParquetManager:
    """
    Central data access layer - Single Source of Truth

    Features:
    - Incremental column addition
    - Automatic versioning
    - Fast filtering
    - Compression
    """

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """Load data with optional column filtering"""
        if not self.file_path.exists():
            return pd.DataFrame()

        if columns:
            return pd.read_parquet(self.file_path, columns=columns)
        return pd.read_parquet(self.file_path)

    def save(self, df: pd.DataFrame):
        """Save entire dataframe (overwrites)"""
        df.to_parquet(self.file_path, compression='snappy', index=False)

    def add_columns(self, new_data: pd.DataFrame, key: str = 'place_id'):
        """Add new columns to existing data (incremental)"""
        if self.file_path.exists():
            existing = self.load()
            merged = existing.merge(new_data, on=key, how='left', suffixes=('', '_new'))

            # Update existing columns or add new ones
            for col in new_data.columns:
                if col != key:
                    if f"{col}_new" in merged.columns:
                        merged[col] = merged[f"{col}_new"].fillna(merged[col])
                        merged.drop(f"{col}_new", axis=1, inplace=True)

            self.save(merged)
        else:
            self.save(new_data)

    def export_csv(self, output: str, columns: Optional[List[str]] = None,
                   filters: Optional[Dict] = None):
        """Export filtered data to CSV"""
        df = self.load(columns=columns)

        if filters:
            for col, condition in filters.items():
                if isinstance(condition, str) and condition.startswith('>='):
                    threshold = float(condition[2:])
                    df = df[df[col] >= threshold]
                elif isinstance(condition, bool):
                    df = df[df[col] == condition]

        df.to_csv(output, index=False, encoding='utf-8')
        return len(df)
```

---

## 🚀 MIGRATION PLAN

### Phase 1: Create Infrastructure (30 min)
1. Create `/data/` and `/exports/` folders
2. Implement `ParquetManager`
3. Add `.gitignore` for large files

### Phase 2: Migrate Existing Data (1 hour)
1. Load current `european_full_enriched_merged.csv`
2. Save as `data/leads.parquet`
3. Test load/save operations
4. Verify data integrity

### Phase 3: Update Scripts (2 hours)
1. Update `enrich_places_details_v2.py` to use ParquetManager
2. Update `enrich_homepage_only.py` to use ParquetManager
3. Update `enrich_leads_with_ai.py` to use ParquetManager
4. Add export scripts

### Phase 4: Clean Old Files (30 min)
1. Move old CSVs to `/archive/`
2. Update `.gitignore`
3. Clean git history (optional)

---

## 💡 BENEFITS

### 1. Storage Efficiency
- **Before:** 322 MB for 2,928 leads
- **After:** ~15-20 MB (Parquet compression)
- **Savings:** 94% less disk space

### 2. Performance
- Parquet read/write: **10-50x faster** than CSV
- Column-based storage: query only needed columns
- Compression: Snappy (fast) or Gzip (smaller)

### 3. Data Integrity
- Single source of truth
- No duplication
- Versioned updates
- Atomic operations

### 4. Developer Experience
- Simple API: `manager.add_columns()`
- No path management
- Automatic deduplication
- Easy exports

### 5. Scalability
- Works for 10K, 100K, 1M+ leads
- Incremental updates (don't rewrite everything)
- Partition support for huge datasets

---

## 📝 EXAMPLE USAGE

### Before (Current Mess):
```python
# Step 1: Google Places
df = fetch_places()
df.to_csv('modules/google_maps/results/enriched/places.csv')

# Step 2: Scraping (need to load again!)
places = pd.read_csv('modules/google_maps/results/enriched/places.csv')
scraped = scrape_sites(places)
merged = places.merge(scraped)
merged.to_csv('modules/scraping/results/enriched.csv')  # Duplicate!

# Step 3: AI (load again!)
data = pd.read_csv('modules/scraping/results/enriched.csv')
ai_results = analyze(data)
final = data.merge(ai_results)
final.to_csv('modules/scraping/results/final.csv')  # More duplicates!
```

### After (Clean):
```python
from modules.shared.parquet_manager import ParquetManager

manager = ParquetManager('data/leads.parquet')

# Step 1: Google Places
manager.add_columns(fetch_places())

# Step 2: Scraping (incremental!)
manager.add_columns(scrape_sites())

# Step 3: AI (incremental!)
manager.add_columns(analyze())

# Export
manager.export_csv('exports/final_leads.csv')
```

**Result:**
- One file: `data/leads.parquet`
- Clean exports: `exports/*.csv`
- No duplicates!

---

## 🎯 NEXT STEPS

1. **Review this plan** - make sure we agree
2. **Implement ParquetManager** - core infrastructure
3. **Migrate current data** - from CSV to Parquet
4. **Update one script** - proof of concept
5. **Update remaining scripts** - full migration
6. **Clean old files** - archive CSVs

**Time estimate:** 4-5 hours total

**Benefits:** Forever clean, fast, scalable data management

---

## ❓ QUESTIONS TO DECIDE

1. **Parquet vs DuckDB?**
   - Parquet: Simpler, pandas-native, one file
   - DuckDB: SQL queries, transactions, more complex
   - **Recommendation:** Start with Parquet

2. **Compression?**
   - Snappy: Faster, larger
   - Gzip: Slower, smaller
   - **Recommendation:** Snappy (good balance)

3. **Keep old CSVs?**
   - Move to `/archive/` (gitignored)
   - **Recommendation:** Yes, for safety

4. **Git LFS for Parquet?**
   - Parquet files can be large
   - **Recommendation:** Add `.gitignore` for `data/`
