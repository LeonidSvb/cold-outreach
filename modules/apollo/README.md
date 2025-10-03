# Apollo Module

**Priority:** Low
**Status:** Production Ready (not used in current sprint)
**Used In:** On-demand lead collection (future)

---

## Quick Info

**Purpose:** Collect leads from Apollo API with mass parallel processing

**Scripts:** 1 production script
**Dependencies:** Apollo API key

---

## Scripts

### apollo_lead_collector.py
**Purpose:** 50+ concurrent Apollo API requests for lead collection
**Features:**
- Mass parallel API requests
- Batch processing optimization
- Advanced search filters
- JSON export with metadata
- Real-time progress tracking

**Usage:**
```bash
cd modules/apollo
python apollo_lead_collector.py
```

**Configuration:** Edit CONFIG section in script
```python
CONFIG = {
    "API_SETTINGS": {
        "MAX_RESULTS": 1000,
        "CONCURRENT_REQUESTS": 50
    },
    "SEARCH_FILTERS": {
        "industry": "marketing",
        "company_size": "1-50"
    }
}
```

**Output:** `results/apollo_leads_YYYYMMDD_HHMMSS.json`

---

## Data Structure

```
modules/apollo/
├── apollo_lead_collector.py    # Main collector script
└── results/                    # Lead collection results (timestamped)
```

---

## Configuration

**Required API Keys:**
- `APOLLO_API_KEY` - For API access

**Location:** Root `.env` file

**Search Capabilities:**
- Industry filtering
- Company size targeting
- Location-based search
- Title/seniority filtering

---

## Performance Metrics

**Processing Speed:**
- 50+ concurrent requests
- Fast batch collection
- Efficient API usage

**Cost:**
- Apollo credit usage per search
- Export limits based on plan

---

## Use Cases

**Lead Generation:**
- Bulk company/contact collection
- Industry-specific searches
- Geographic targeting
- Seniority-based filtering

**Data Export:**
- JSON format with full details
- CSV-ready output
- Integration with CSV transformer

---

## Integration

**Pipeline Position:**
- Lead source for cold outreach
- Alternative to manual CSV uploads
- Enrichment source for existing data

**Output Compatible With:**
- modules/csv_transformer/ - Normalization
- modules/instantly/ - Campaign upload
- data/raw/ - CSV processing pipeline

---

## Documentation

**Related ADRs:**
- None yet (established functionality)

**Sprint Docs:**
- Not in current sprint (low priority)

**Future Use:**
- Alternative lead source
- Data enrichment
- ICP validation

---

**Last Updated:** 2025-10-03
