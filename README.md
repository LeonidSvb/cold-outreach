# Outreach - Cold Outreach Automation Platform

**Modular, scalable, efficient.** Lead enrichment platform with Parquet-based data architecture.

## 🚨 NEW ARCHITECTURE (2025-11-11)

**IMPORTANT:** This project uses a **Parquet-based single source of truth** architecture.

📖 **Read this first:** [DATA_ARCHITECTURE.md](DATA_ARCHITECTURE.md)

## Quick Start

```python
from modules.shared.parquet_manager import ParquetManager

# Load project data
manager = ParquetManager(project='soviet_boots_europe')
df = manager.load()

# Add new columns (incremental)
manager.add_columns(enrichment_data, key='place_id')

# Export for campaign
manager.export_csv('exports/my_campaign.csv')
```

## Project Structure

```
Outreach/
├── data/
│   ├── projects/          # ✅ Production data (Parquet, single source of truth)
│   └── exports/           # ✅ Final CSV exports for campaigns
│
├── modules/
│   ├── shared/
│   │   └── parquet_manager.py   # ✅ Central data access layer (USE THIS!)
│   ├── google_maps/scripts/     # Google Places API
│   ├── scraping/scripts/        # Website scraping
│   ├── openai/scripts/          # AI enrichment
│   └── apify/scripts/           # Apify automation
│
├── archive/               # Old backups (gitignored)
├── frontend/              # Next.js UI (WIP)
├── .env                   # API keys
└── CLAUDE.md              # Coding conventions
```

## 📚 Documentation

- 🏗️ [**DATA_ARCHITECTURE.md**](docs/DATA_ARCHITECTURE.md) - **READ THIS FIRST!**
- 🔄 [MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) - Update old scripts
- 📋 [REFACTORING_PLAN.md](docs/REFACTORING_PLAN.md) - Architecture details
- 🚀 [QUICK_START.md](docs/QUICK_START.md) - Quick start guide

## Core Features

### 1. **OpenAI Mass Processing**
- Batch process CSVs through OpenAI API
- Generate personalized icebreakers
- AI-powered content analysis
- Smart icebreaker generation with personality

**Main scripts:**
- `openai_mass_processor.py` - Batch processing
- `openai_icebreaker_generator.py` - Icebreaker generation
- `openai_smart_icebreaker_generator.py` - Advanced icebreakers

### 2. **Website Scraping**
- Extract emails from websites
- Parallel website processing
- Website content personalization
- HTTP-only (no external dependencies)

**Main scripts:**
- `scraping_parallel_website_email_extractor.py` - Email extraction
- `scraping_website_personalization_enricher.py` - Content enrichment
- `scraping_extract_emails_from_websites.py` - Email finder

## Usage Workflow

### Step 1: Prepare Input
```bash
# Put your CSV in results/raw/
cp my_leads.csv results/raw/
```

### Step 2: Process with OpenAI
```bash
# Run mass processor
python scripts/openai_mass_processor.py

# Results saved to results/openai/
```

### Step 3: Enrich with Website Data
```bash
# Extract emails from websites
python scripts/scraping_parallel_website_email_extractor.py

# Results saved to results/scraping/
```

### Step 4: Get Final Output
```bash
# Check results/processed/ for final CSVs
ls results/processed/
```

## Configuration

All configuration via `.env` file:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Google (if using Google Sheets)
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Other API keys as needed
```

## Logging

Universal logger automatically tracks all script execution:

```python
from logger.universal_logger import get_logger

logger = get_logger(__name__)
logger.info("Processing started")
```

Logs saved to `logger/logs/YYYY-MM-DD.log`

## Frontend (Optional)

Next.js UI preserved for future refactoring:

```bash
cd frontend
npm install
npm run dev
# Visit http://localhost:3000
```

## Documentation

- **CLAUDE.md** - Coding conventions and rules
- **docs/ADR.md** - Architecture Decision Records (ADR-0013: Structure Simplification)
- **results/** - All processing outputs

## Key Principles

1. **Simplicity First** - Flat structure, no nested modules
2. **Centralized Results** - All outputs in one place
3. **Clear Naming** - Prefix pattern (openai_*, scraping_*, shared_*)
4. **Real Data Only** - No mocks, only production-ready scripts
5. **Preserved History** - Git history and infrastructure intact

## Migration from Old Structure

**Old:**
```
modules/apollo/
modules/instantly/
modules/openai/
modules/scraping/
modules/sheets/
backend/
```

**New (ULTRA-CLEAN):**
```
scripts/          # All scripts
results/          # All results
logger/           # Universal logger
frontend/         # Preserved
```

See **ADR-0013** in docs/ADR.md for full decision rationale.

## Common Tasks

```bash
# List all available scripts
ls scripts/

# Find OpenAI scripts
ls scripts/openai_*.py

# Find scraping scripts
ls scripts/scraping_*.py

# View logs
tail -f logger/logs/$(date +%Y-%m-%d).log

# Clean old results
rm results/openai/*.json
rm results/scraping/*.json
```

## Support

For questions or issues, check:
1. **CLAUDE.md** - Coding standards
2. **docs/ADR.md** - Architecture decisions
3. Script headers - Usage instructions

---

**Version:** 1.0.0 (Ultra-Clean Architecture)
**Last Updated:** 2025-11-07
**ADR:** ADR-0013 Project Structure Simplification
