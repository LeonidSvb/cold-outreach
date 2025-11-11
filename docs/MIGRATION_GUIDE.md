# Migration Guide: Old → New Architecture

## 📋 Scripts Requiring Updates

**Found 28 scripts using old data paths** that need migration to ParquetManager.

---

## 🚨 HIGH PRIORITY (Active Scripts)

### **Production Scripts (update first):**

1. `modules/openai/scripts/enrich_leads_with_ai.py`
   - Uses: `modules/scraping/results/`, `modules/openai/results/`
   - **Action:** Migrate to `ParquetManager.add_columns()`

2. `modules/scraping/scripts/email_finder_multipage.py`
   - Uses: `modules/scraping/results/`
   - **Action:** Migrate to `ParquetManager.add_columns()`

3. `modules/google_maps/scripts/enrich_places_details_v2.py`
   - Uses: `modules/google_maps/results/enriched/`
   - **Action:** Migrate to `ParquetManager.save()`

4. `modules/apify/scripts/australia_business_scraper.py`
   - Uses: `modules/apify/results/`
   - **Action:** Save directly to `ParquetManager`

5. `modules/apify/scripts/europe_business_scraper.py`
   - Uses: `modules/apify/results/`
   - **Action:** Save directly to `ParquetManager`

---

## 📊 MEDIUM PRIORITY (Utility Scripts)

### **Analysis & Visualization:**

6. `modules/google_maps/scripts/create_heatmap.py`
   - Uses: `modules/google_maps/results/`, `data/processed/`
   - **Action:** Load from `ParquetManager.load()`

7. `modules/google_maps/scripts/create_combined_heatmap.py`
   - Uses: `modules/google_maps/results/`, `data/processed/`
   - **Action:** Load from `ParquetManager.load()`

8. `modules/google_maps/scripts/consolidate_to_parquet.py`
   - Uses: `data/raw/`, `data/processed/`
   - **Action:** Already converts to Parquet - update paths to `/data/projects/`

### **UI/Streamlit Apps:**

9. `modules/google_maps/ui/streamlit_app.py`
   - Uses: `modules/google_maps/results/`
   - **Action:** Load from `ParquetManager.load()`

10. `modules/scraping/ui/streamlit_app.py`
    - Uses: `modules/scraping/results/`
    - **Action:** Load from `ParquetManager.load()`

---

## 🔧 LOW PRIORITY (Old/Unused Scripts)

### **Root scripts/ folder (legacy):**

11. `scripts/scraping_website_personalization_enricher.py`
12. `scripts/scraping_parallel_website_email_extractor.py`
13. `scripts/hvac_website_scraper.py`
14. `scripts/texas_hvac_scraper.py`
15. `scripts/hvac_scraper_optimized.py`
16. `scripts/hvac_email_scraper_final.py`
17. `scripts/hvac_full_pipeline.py`
18. `scripts/create_hvac_viewer.py`
19. `scripts/test_gmaps_search.py`
20. `scripts/test_google_maps_places.py`
21. `scripts/test_hvac_scraper.py`
22. `scripts/apify_content_crawler_email_extractor.py`

**Action:** Move to `/archive/old_root_scripts/` or delete if obsolete

### **scripts/unused/ folder:**

23. `scripts/unused/scraping_extract_emails_from_websites.py`
24. `scripts/unused/openai_smart_icebreaker_generator.py`

**Action:** Already marked as unused - move to archive

### **scripts/extra/ folder:**

25. `scripts/extra/openai_categorize_and_icebreaker_generator.py`

**Action:** Migrate if still used, otherwise archive

---

## 🔄 Migration Patterns

### **Pattern 1: Output CSV → Add Columns**

**BEFORE (wrong):**
```python
# Old script writing CSV
df = process_data()
df.to_csv('modules/scraping/results/enriched.csv')
```

**AFTER (correct):**
```python
from modules.shared.parquet_manager import ParquetManager

df = process_data()
manager = ParquetManager(project='soviet_boots_europe')
manager.add_columns(df, key='place_id')
```

---

### **Pattern 2: Input CSV → Load from Parquet**

**BEFORE (wrong):**
```python
# Old script reading CSV
df = pd.read_csv('modules/google_maps/results/enriched/places.csv')
```

**AFTER (correct):**
```python
from modules.shared.parquet_manager import ParquetManager

manager = ParquetManager(project='soviet_boots_europe')
df = manager.load()
# or load specific columns:
df = manager.load(columns=['place_id', 'name', 'website'])
```

---

### **Pattern 3: Chain of CSVs → Single Parquet**

**BEFORE (wrong):**
```python
# Step 1: Google Places
places = fetch_places()
places.to_csv('modules/google_maps/results/places.csv')

# Step 2: Scraping (load previous)
places = pd.read_csv('modules/google_maps/results/places.csv')
scraped = scrape(places)
merged = places.merge(scraped)
merged.to_csv('modules/scraping/results/enriched.csv')  # DUPLICATE!

# Step 3: AI (load previous)
enriched = pd.read_csv('modules/scraping/results/enriched.csv')
ai_results = analyze(enriched)
final = enriched.merge(ai_results)
final.to_csv('modules/openai/results/final.csv')  # MORE DUPLICATES!
```

**AFTER (correct):**
```python
from modules.shared.parquet_manager import ParquetManager

manager = ParquetManager(project='my_project')

# Step 1: Google Places
places = fetch_places()
manager.save(places)

# Step 2: Scraping (incremental)
scraped = scrape(manager.load(columns=['website']))
manager.add_columns(scraped, key='place_id')

# Step 3: AI (incremental)
ai_results = analyze(manager.load(columns=['scraped_content']))
manager.add_columns(ai_results, key='place_id')

# Step 4: Export final CSV (optional)
manager.export_csv('exports/final_campaign.csv')
```

**Result:** One Parquet file, no duplicates!

---

### **Pattern 4: Temp Files in module folders**

**BEFORE (wrong):**
```python
# Intermediate results stored permanently
temp_df.to_csv('modules/scraping/results/temp_step1.csv')
temp_df2.to_csv('modules/scraping/results/temp_step2.csv')
# These files pile up and get committed!
```

**AFTER (correct):**
```python
# Option 1: Use in-memory processing (best)
temp_df = process_step1()
temp_df2 = process_step2(temp_df)
final_df = process_step3(temp_df2)

# Option 2: If you MUST save temp files:
temp_file = 'modules/scraping/results/temp_processing.csv'
temp_df.to_csv(temp_file)
# ... process ...
os.remove(temp_file)  # DELETE after use!
```

---

## 📝 Step-by-Step Migration

### **For each script:**

1. **Identify data flow:**
   - What data does it read?
   - What data does it produce?
   - Is it initial data or enrichment?

2. **Choose project name:**
   - Existing: `soviet_boots_europe`, `hvac_usa`, `australia_field_services`
   - New: Create descriptive name

3. **Replace file I/O:**
   - `pd.read_csv()` → `manager.load()`
   - `df.to_csv()` → `manager.add_columns()` or `manager.export_csv()`

4. **Test:**
   - Run script
   - Verify data in `/data/projects/`
   - Check no files in `modules/*/results/`

5. **Commit:**
   ```bash
   git add <script_file>
   git commit -m "refactor(script): migrate to ParquetManager"
   ```

---

## 🎯 Quick Wins (Start Here)

**Easiest scripts to migrate first:**

1. ✅ **enrich_leads_with_ai.py** - Already processes existing data
2. ✅ **email_finder_multipage.py** - Adds email columns
3. ✅ **consolidate_to_parquet.py** - Already uses Parquet, just update paths

**These 3 scripts cover most use cases!**

---

## 🚫 What NOT to Do

**DON'T:**
- ❌ Keep writing CSV to `modules/*/results/`
- ❌ Create duplicate copies of data
- ❌ Mix old and new architecture in same script
- ❌ Commit temp files to git

**DO:**
- ✅ Use ParquetManager for all data access
- ✅ Save to `/data/projects/` only
- ✅ Export CSVs to `/data/exports/` when needed
- ✅ Clean up temp files after processing

---

## 📚 Resources

- **Main Documentation:** `DATA_ARCHITECTURE.md`
- **ParquetManager Code:** `modules/shared/parquet_manager.py`
- **Module Template:** `docs/MODULE_TEMPLATE.md`

---

## 💬 Need Help?

If unsure how to migrate a specific script:

1. Check `DATA_ARCHITECTURE.md` for examples
2. Look at `modules/shared/parquet_manager.py` docstrings
3. Review this migration guide patterns
4. Test with small dataset first

---

**Migration Priority:**
1. 🔴 HIGH: Active production scripts (5 scripts)
2. 🟡 MEDIUM: Utility & UI scripts (5 scripts)
3. 🟢 LOW: Old/unused scripts (18 scripts) - archive or delete

**Estimated Time:**
- HIGH priority: 2-3 hours
- MEDIUM priority: 1-2 hours
- LOW priority: Archive/delete (30 min)

**Total: ~4-6 hours for complete migration**
