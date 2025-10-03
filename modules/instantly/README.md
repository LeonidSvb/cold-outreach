# Instantly Module

**Priority:** High
**Status:** Production Ready
**Used In:** Sprint 01 - CSV to Instantly pipeline, Campaign analytics

---

## Quick Info

**Purpose:** Complete Instantly API integration for campaign management, analytics collection, and lead upload

**Scripts:** 3 production scripts
**Dependencies:** Instantly API key (2 keys in .env)

---

## Scripts

### instantly_universal_collector.py
**Purpose:** Comprehensive Instantly API data collection system
**Features:**
- Campaign analytics and overview
- Email account status and health
- Daily analytics with date ranges
- Reply analysis (real vs fake detection)

**Usage:**
```bash
python instantly_universal_collector.py
```

**Configuration:** Edit CONFIG section in script
```python
CONFIG = {
    "DATE_RANGE": {"start_date": "auto", "end_date": "today"},
    "COLLECT": {"campaigns_overview": True, "daily_analytics": True}
}
```

**Output:** `results/instantly_universal_collector_YYYYMMDD_HHMMSS.json`

---

### instantly_campaign_optimizer.py
**Purpose:** Campaign performance analysis with real vs fake reply detection
**Features:**
- Real reply rate calculation (filters out-of-office)
- Cost tracking per campaign
- Success rate analysis
- Campaign comparison metrics

**Usage:**
```bash
python instantly_campaign_optimizer.py
```

**Output:** Markdown reports with campaign insights

---

### instantly_csv_uploader_curl.py
**Purpose:** Upload leads to Instantly campaigns from CSV files
**Features:**
- Bulk CSV lead upload
- Campaign assignment
- Domain-to-email generation (info@, contact@, hello@)
- Bypasses Cloudflare using curl subprocess

**Usage:**
```bash
python instantly_csv_uploader_curl.py
```

**Configuration:** Edit campaign_id and CSV path in script

**Output:** `results/instantly_csv_upload_YYYYMMDD_HHMMSS.json`

---

## Data Structure

```
modules/instantly/
├── data/
│   ├── cache/           # API response cache
│   ├── campaigns/       # Campaign configurations
│   └── input/          # CSV files for upload
└── results/            # Processing results with timestamps
```

---

## Configuration

**Required API Keys:**
- `INSTANTLY_API_KEY` - Main API key
- `INSTANTLY_API_KEY_2` - Secondary API key (optional)

**Location:** Root `.env` file

**Authentication Method:** Raw base64 API keys with curl (Python requests blocked by Cloudflare)

---

## Performance Metrics

**Campaign Analytics:**
- 4 active campaigns tracked
- 1,668 total emails sent
- 0.78% formal reply rate
- 0.24-0.36% real positive reply rate (after filtering out-of-office)

**Account Health:**
- 5 active accounts (100% health)
- 5 inactive accounts (OAuth issues)

---

## Documentation

**Related ADRs:**
- None yet (API integration established in CHANGELOG v6.2.0)

**Sprint Docs:**
- Sprint 01: CSV to Instantly upload pipeline
- docs/sprints/01-first-campaign-launch/

**API Guide:**
- See CHANGELOG.md [6.2.0] for complete Instantly API documentation

---

**Last Updated:** 2025-10-03
