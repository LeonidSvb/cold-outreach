# OpenAI Module

**Priority:** High
**Status:** Production Ready
**Used In:** Sprint 01 - Icebreaker generation, content analysis

---

## Quick Info

**Purpose:** Mass parallel OpenAI API processing for lead enrichment

**Scripts:** 2 production scripts
**Dependencies:** OpenAI API key

---

## Scripts

### openai_mass_processor.py
**Purpose:** Mass parallel OpenAI API batch processing
**Features:**
- 10+ concurrent requests for maximum throughput
- Cost tracking per operation
- Batch processing optimization
- Real-time progress monitoring
- Token usage analytics

**Usage:**
```bash
cd modules/openai
python openai_mass_processor.py
```

**Configuration:** Edit CONFIG section in script
```python
CONFIG = {
    "OPENAI": {
        "MODEL": "gpt-3.5-turbo",
        "MAX_TOKENS": 150,
        "TEMPERATURE": 0.7
    },
    "PROCESSING": {
        "BATCH_SIZE": 10,
        "MAX_WORKERS": 10
    }
}
```

**Output:** `results/openai_mass_processor_YYYYMMDD_HHMMSS.json`

---

### openai_content_analyzer.py
**Purpose:** Analyze website content for personalization
**Features:**
- Content intelligence extraction
- Personalization opportunity identification
- B2B outreach insights

**Status:** Legacy (archived functionality)

---

## Data Structure

```
modules/openai/
├── openai_mass_processor.py    # Main production script
├── openai_content_analyzer.py  # Legacy analyzer
└── results/                    # Processing results (timestamped)
```

---

## Configuration

**Required API Keys:**
- `OPENAI_API_KEY` - For all AI operations

**Location:** Root `.env` file

**Cost Optimization:**
- Use gpt-3.5-turbo for cost efficiency
- Batch processing reduces overhead
- Token limits prevent runaway costs

---

## Performance Metrics

**Processing Speed:**
- 10 concurrent requests
- ~2-3 seconds per batch
- Typical cost: $0.001-0.01 per request

**Icebreaker Generation (Example):**
- $0.0007 per icebreaker
- 100% generation success rate
- 2-3 seconds per contact

---

## Use Cases

**Lead Enrichment:**
- Icebreaker generation from CSV data
- Company name normalization
- Content summarization

**Content Analysis:**
- Website intelligence extraction
- Personalization insights
- Industry classification

**Batch Operations:**
- Mass lead processing
- CSV column transformation
- Data enrichment pipelines

---

## Integration

**Used By:**
- modules/csv_transformer/ - Column transformations
- modules/scraping/ - Page prioritization
- backend/main.py - API endpoints

**Shared With:**
- Dialogue-style prompting system (ADR-0002)
- Centralized prompt management

---

## Documentation

**Related ADRs:**
- ADR-0002: Dialogue-Style Prompting System

**Sprint Docs:**
- Sprint 01: Icebreaker generation pipeline
- docs/sprints/01-first-campaign-launch/

**Cost Tracking:**
- Auto-logging via modules/shared/logger.py
- Real-time cost monitoring

---

**Last Updated:** 2025-10-03
