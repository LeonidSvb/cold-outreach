# Data Folder

## Structure

```
/data/
  /projects/    ✅ Production Parquet files (single source of truth)
  /exports/     ✅ Final CSV exports for campaigns
```

## Rules

1. **NEVER** create CSV files directly in this folder
2. **ALWAYS** use `ParquetManager` from `modules/shared/parquet_manager.py`
3. **Production data** → `/projects/` (Parquet only)
4. **Campaign exports** → `/exports/` (CSV only)

## Usage

```python
from modules.shared.parquet_manager import ParquetManager

# Work with projects
manager = ParquetManager(project='soviet_boots_europe')
df = manager.load()

# Export for campaign
manager.export_csv('exports/my_campaign.csv')
```

## Learn More

See **DATA_ARCHITECTURE.md** in project root for full documentation.
