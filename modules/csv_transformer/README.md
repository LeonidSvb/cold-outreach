# CSV Transformer Module

**Priority:** High
**Status:** Production Ready
**Used In:** Sprint 01 - CSV normalization and column transformation

---

## Quick Info

**Purpose:** AI-powered CSV column transformation with custom prompt library

**Scripts:** 1 main script + API wrapper
**Dependencies:** OpenAI API key

---

## Scripts

### csv_column_transformer.py
**Purpose:** Interactive AI-powered CSV column transformation system
**Features:**
- Automatic column detection and type analysis
- Interactive prompt selection from library
- Custom prompt application with placeholders
- Batch processing with backup creation
- New column generation with AI transformations

**Usage:**
```bash
cd modules/csv_transformer
python csv_column_transformer.py
```

**Configuration:** Edit CONFIG section in script
```python
CONFIG = {
    "OPENAI": {
        "MODEL": "gpt-3.5-turbo",
        "TEMPERATURE": 0.1,
        "MAX_TOKENS": 20
    },
    "BATCH_SIZE": 20
}
```

**Output:** Transformed CSV with new column + backup

---

### api_wrapper.py
**Purpose:** API integration layer for backend integration
**Features:**
- `analyze_csv_file()` - Column analysis and type detection
- `transform_csv()` - Execute transformation via API

**Used By:** backend/main.py for CSV transformation endpoints

---

### prompts.md
**Purpose:** Centralized prompt library for transformations
**Format:** Markdown sections parsed by transformer
**Examples:**
- Company Name Normalizer (remove suffixes, CAPS to Title)
- City Normalizer (abbreviations to full names)
- Custom prompts (user-defined transformations)

**Usage:** Add new prompts as markdown sections

---

## Data Structure

```
modules/csv_transformer/
├── csv_column_transformer.py  # Main script
├── api_wrapper.py             # Backend integration
├── prompts.md                 # Prompt library
└── results/                   # Transformed CSVs (timestamped)
```

---

## Configuration

**Required API Keys:**
- `OPENAI_API_KEY` - For AI transformations

**Location:** Root `.env` file

**Supported Column Types:**
- Email detection
- URL/website detection
- Phone number detection
- Text fields (various lengths)

---

## Performance Metrics

**Processing Speed:**
- 20 rows per batch (optimal)
- ~2-3 seconds per batch
- Cost: $0.0023 per 4-company batch

**Accuracy:**
- 10.0/10 for company name normalization
- 100% success rate on test data

---

## Transformation Examples

**Company Name Normalization:**
```
Input: "The Think Tank (TTT)" → Output: "TTT"
Input: "MEDIAFORCE Digital Marketing" → Output: "Mediaforce"
Input: "Canspan BMG Inc." → Output: "Canspan"
```

**City Normalization:**
```
Input: "NYC" → Output: "New York City"
Input: "LA" → Output: "Los Angeles"
```

---

## Documentation

**Related ADRs:**
- ADR-0002: Dialogue-Style Prompting System

**Sprint Docs:**
- Sprint 01: CSV normalization pipeline
- docs/sprints/01-first-campaign-launch/

**Knowledge Base:**
- docs/prompting-knowledge-base.md - Complete prompting methodology

---

**Last Updated:** 2025-10-03
