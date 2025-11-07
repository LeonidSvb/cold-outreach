# Module Template - Industry Standard Structure

**Reference Implementation:** `modules/instantly/`

This document describes the ideal module structure used in this project. Use it as a template for creating new modules (Apollo, OpenAI, Scraping, etc.).

---

## 📁 Standard Module Structure

```
modules/{module_name}/
├── docs/                      # Documentation
│   ├── README.md              # Main documentation (CAPS)
│   ├── api-guide.md           # API usage guide (lowercase)
│   ├── troubleshooting.md     # Common issues & solutions
│   └── usage.md               # Usage examples
├── scripts/                   # Executable Python scripts
│   ├── sources.py             # Data loading & extraction
│   ├── transform.py           # Data transformation for Supabase
│   ├── upload.py              # Upload to Supabase
│   └── collector.py           # Data collection from API
├── tests/                     # Test files
│   ├── test_integration.py    # Integration tests with real data
│   └── test_unit.py           # Unit tests
├── results/                   # JSON outputs from API/scripts
│   └── {script_name}_{YYYYMMDD_HHMMSS}.json
├── data/                      # Input data & cache
│   ├── input/                 # CSV files, manual inputs
│   └── cache/                 # Cached API responses
└── __pycache__/               # Python cache (git ignored)
```

---

## 🎯 Core Principles

### 1. Separation of Concerns

**Code ≠ Data ≠ Docs ≠ Tests**

Each folder has ONE clear purpose:
- `docs/` - Human-readable documentation
- `scripts/` - Executable production code
- `tests/` - Verification code
- `results/` - Script outputs (generated)
- `data/` - Script inputs (manually created or cached)

### 2. No Redundant Prefixes

**❌ Bad:**
```
modules/instantly/
├── instantly_sources.py
├── instantly_transform.py
└── instantly_upload.py
```

**✅ Good:**
```
modules/instantly/scripts/
├── sources.py
├── transform.py
└── upload.py
```

**Why:** We're already in `instantly/` folder - prefix is redundant!

### 3. Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| **Folders** | `lowercase/` | `docs/`, `scripts/`, `tests/` |
| **Main README** | `README.md` (CAPS) | Industry standard |
| **Other docs** | `lowercase.md` | `api-guide.md`, `usage.md` |
| **Python scripts** | `snake_case.py` | `sources.py`, `transform.py` |
| **Test files** | `test_*.py` | `test_integration.py` |
| **Results** | `{name}_{timestamp}.json` | `raw_data_20250103_143022.json` |

### 4. File Organization

**Keep files focused:**
- Files under 200-300 lines
- One responsibility per file
- Clear, descriptive names

---

## 📋 Standard Files (Every Module)

### 1. `docs/README.md` - Main Documentation

**Template:**
```markdown
# {Module Name} Module

Brief description of what this module does.

## Quick Links
- [API Guide](api-guide.md)
- [Troubleshooting](troubleshooting.md)
- [Usage Examples](usage.md)

## Module Structure
[Show folder tree]

## Quick Start
[Basic usage commands]

## Data Pipeline
[Show data flow diagram]
```

### 2. `scripts/sources.py` - Data Loading

**Purpose:** Load and extract data from JSON/API responses

**Key functions:**
```python
def load_from_json(file_path: str) -> Dict[str, Any]:
    """Load data from JSON file"""

def extract_campaigns(data: Dict) -> List[Dict]:
    """Extract campaigns from loaded data"""

def extract_accounts(data: Dict) -> List[Dict]:
    """Extract accounts from loaded data"""
```

### 3. `scripts/transform.py` - Data Transformation

**Purpose:** Transform data to Supabase table format

**Key functions:**
```python
def transform_campaigns(campaigns: List[Dict]) -> List[Dict[str, Any]]:
    """Transform campaigns for {module}_campaigns_raw table"""

def validate_transformed_data(table: str, rows: List[Dict]) -> Dict[str, Any]:
    """Validate data before upload"""
```

**Critical:** Each row must include:
- Primary key field(s)
- `raw_json` JSONB column (preserves full API response)
- Timestamps: `synced_at`, `created_at`, `updated_at`

### 4. `scripts/upload.py` - Upload to Supabase

**Purpose:** Upload transformed data to Supabase

**Key functions:**
```python
def upload_campaigns(file_path: str) -> Dict[str, Any]:
    """Upload campaigns to Supabase"""

def upload_all(file_path: str) -> Dict[str, Any]:
    """Upload all data types"""
```

### 5. `tests/test_integration.py` - Integration Tests

**Purpose:** Test with real data

**Template:**
```python
#!/usr/bin/env python3
"""
Integration test for {Module} data pipeline
Tests with real data from results/
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'scripts'))

from sources import load_from_json, extract_campaigns
from transform import transform_campaigns, validate_transformed_data

def test_campaigns_transformation():
    """Test campaign transformation with real data"""
    # Load real data
    result = load_from_json('results/data.json')

    # Extract & transform
    campaigns = extract_campaigns(result['data'])
    transformed = transform_campaigns(campaigns)

    # Validate
    validation = validate_transformed_data('table_name', transformed)
    assert validation['valid'] == True
```

---

## 🔄 Standard Data Pipeline

Every module should follow this flow:

```
External API/Source
     ↓
collector.py (fetch & save raw)
     ↓
results/{script}_{timestamp}.json (raw data)
     ↓
sources.py (load & extract)
     ↓
transform.py (format for Supabase)
     ↓
upload.py (upsert to DB)
     ↓
Supabase RAW tables
```

---

## 🗄️ Database Layer Pattern

### RAW Layer Tables

Every module gets RAW tables in Supabase:

```sql
CREATE TABLE {module}_{entity}_raw (
    -- Primary key (from external system)
    {module}_{entity}_id TEXT PRIMARY KEY,

    -- Extracted fields for quick queries
    name TEXT,
    status INTEGER,

    -- Full API response (CRITICAL!)
    raw_json JSONB NOT NULL,

    -- Sync tracking
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Examples:**
- `instantly_campaigns_raw`
- `apollo_leads_raw`
- `openai_responses_raw`

**Key principles:**
- NO foreign key constraints in RAW layer
- ALL data preserved in `raw_json`
- Extracted fields are for indexing/performance only

---

## 📦 Dependencies Pattern

**Each module has consistent imports:**

```python
# Standard library
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add paths
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

# Project imports
from lib.supabase_client import upsert_rows, query_table, get_supabase
```

**No external config files:**
- Embed CONFIG in scripts (CONFIG dict at top)
- Use environment variables for secrets (.env)
- Never hardcode credentials

---

## ✅ Quality Checklist

Before considering a module "complete":

**Structure:**
- [ ] Has `docs/`, `scripts/`, `tests/`, `results/`, `data/` folders
- [ ] `docs/README.md` exists and is complete
- [ ] No redundant module name prefixes in filenames
- [ ] All MD files use correct naming (README.md CAPS, others lowercase)

**Code:**
- [ ] `sources.py` - loads and extracts data
- [ ] `transform.py` - transforms to Supabase format
- [ ] `upload.py` - uploads to Supabase
- [ ] All functions have type hints
- [ ] All functions have docstrings
- [ ] Files under 300 lines

**Tests:**
- [ ] Integration test with real data exists
- [ ] All tests pass
- [ ] Tests use real data (no mocks in production code)

**Database:**
- [ ] RAW tables created in Supabase
- [ ] All tables have `raw_json` JSONB column
- [ ] Timestamps present: `synced_at`, `created_at`, `updated_at`

**Documentation:**
- [ ] `docs/README.md` explains module purpose
- [ ] API guide exists (if applicable)
- [ ] Usage examples exist
- [ ] Data flow documented

---

## 🎓 Learning from `instantly` Module

**Perfect reference implementation:**
```
modules/instantly/
```

**What makes it perfect:**
1. ✅ Clean folder separation
2. ✅ No redundant prefixes
3. ✅ Proper naming conventions
4. ✅ Complete documentation
5. ✅ Working tests with real data
6. ✅ Production-ready upload script
7. ✅ All data uploaded to Supabase successfully

**When creating new module:**
```bash
# Just copy the structure
cp -r modules/instantly modules/new_module
# Then adapt the code
```

---

## 🚀 Quick Module Creation Guide

### Step 1: Create Structure
```bash
mkdir -p modules/{module_name}/{docs,scripts,tests,results,data/input,data/cache}
```

### Step 2: Create Core Files
```bash
# Documentation
touch modules/{module_name}/docs/README.md
touch modules/{module_name}/docs/api-guide.md
touch modules/{module_name}/docs/usage.md

# Scripts
touch modules/{module_name}/scripts/sources.py
touch modules/{module_name}/scripts/transform.py
touch modules/{module_name}/scripts/upload.py

# Tests
touch modules/{module_name}/tests/test_integration.py
```

### Step 3: Follow This Template
1. Copy code structure from `modules/instantly/`
2. Adapt to your specific API/data source
3. Create RAW tables in Supabase
4. Write integration tests
5. Document everything

---

## 📊 Module Examples

### Current Modules
- ✅ **instantly** - Instantly.ai email campaigns (reference implementation)

### Planned Modules
- ⏳ **apollo** - Apollo.io lead generation
- ⏳ **openai** - OpenAI API processing
- ⏳ **scraping** - Web scraping utilities
- ⏳ **sheets** - Google Sheets operations

**All will follow this exact template.**

---

## 💡 Key Takeaways

1. **Consistency > Perfection** - Use same structure everywhere
2. **Documentation > Comments** - Write docs, not just code comments
3. **Real Data > Mocks** - Test with actual data
4. **Simple > Complex** - KISS principle
5. **DRY > WET** - Don't Repeat Yourself

---

## 📝 References

- **Live Example:** `/modules/instantly/`
- **Project Guidelines:** `/CLAUDE.md`
- **Database Docs:** `/docs/sql/README.md`

**When in doubt, look at `modules/instantly/` - it's the gold standard.**

---

**Template Version:** 1.0
**Last Updated:** 2025-10-03
**Based on:** `modules/instantly/` structure
