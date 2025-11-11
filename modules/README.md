# Modules Folder

## Structure

```
/modules/
  /shared/
    parquet_manager.py    ✅ Central data access layer (USE THIS!)

  /google_maps/
    /scripts/             ✅ Executable code only
    /results/             📁 Empty (temp files, gitignored)
    /data/                📁 Empty (temp files, gitignored)

  /scraping/scripts/      ✅ Code only
  /openai/scripts/        ✅ Code only
  /apify/scripts/         ✅ Code only
```

## Rules

### ✅ DO:
- Write code in `/scripts/` folders
- Use `ParquetManager` for data access
- Create temp files in `results/` or `data/` during execution
- Delete temp files after processing

### ❌ DON'T:
- Store production data in module folders
- Create CSV files in `results/` or `data/` for permanent storage
- Duplicate data across modules
- Commit temporary files to git

## Correct Data Flow

```python
from modules.shared.parquet_manager import ParquetManager

# 1. Load from central storage
manager = ParquetManager(project='my_project')
df = manager.load()

# 2. Process data
df['new_column'] = process(df)

# 3. Save back to central storage
manager.add_columns(df[['place_id', 'new_column']], key='place_id')
```

**Result:** One Parquet file in `/data/projects/`, no duplicates!

## Learn More

See [DATA_ARCHITECTURE.md](../docs/DATA_ARCHITECTURE.md) for full documentation.
