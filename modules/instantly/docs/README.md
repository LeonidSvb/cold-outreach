# Instantly Module Documentation

Complete documentation for Instantly API integration and data pipeline.

---

## Quick Links

- **[API Guide](api-guide.md)** - Instantly API endpoints and usage
- **[API Troubleshooting](api-troubleshooting.md)** - Common issues and solutions
- **[Transform Usage](transform-usage.md)** - Data transformation guide

---

## Module Structure

```
modules/instantly/
├── docs/                      # Documentation (you are here)
│   ├── README.md              # This file
│   ├── api-guide.md
│   ├── api-troubleshooting.md
│   └── transform-usage.md
├── scripts/                   # Executable scripts
│   ├── sources.py             # Load JSON from files
│   ├── transform.py           # Transform to Supabase format
│   ├── upload_all.py          # Upload all data to Supabase
│   ├── campaign_optimizer.py  # Campaign optimization
│   ├── csv_uploader_curl.py   # CSV upload via curl
│   └── universal_collector.py # Universal data collector
├── tests/                     # Test files
│   ├── test_transform_integration.py
│   └── check_tables.py
├── results/                   # JSON outputs from API
└── data/                      # Cache and input files
```

---

## Quick Start

### 1. Upload Data to Supabase

```bash
cd modules/instantly/scripts
python upload_all.py
```

### 2. Run Tests

```bash
cd modules/instantly/tests
python test_transform_integration.py
```

### 3. Check Supabase Tables

```bash
cd modules/instantly/tests
python check_tables.py
```

---

## Data Pipeline

```
Instantly API
     ↓
JSON files (results/)
     ↓
sources.py (load & extract)
     ↓
transform.py (format for Supabase)
     ↓
upload_all.py (upsert to DB)
     ↓
Supabase RAW tables
```

---

## Naming Conventions

- **Scripts:** `sources.py` (no instantly_ prefix)
- **Documentation:** `api-guide.md` (lowercase)
- **Tests:** `test_*.py` (pytest standard)
- **Results:** `raw_data_YYYYMMDD_HHMMSS.json` (timestamped)

---

## See Also

- **SQL Documentation:** /docs/sql/README.md
- **Project Guidelines:** /CLAUDE.md
- **Database Structure:** /docs/sql/STRUCTURE.md
