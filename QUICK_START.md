# Quick Start: Lead Enrichment Pipeline

## TL;DR

**Two powerful scripts ready to run:**

1. **AI Content Enrichment** → Extract personalization hooks from existing content
   - Cost: ~$28 | Time: 30-45 min | Result: 1,894 enriched leads

2. **Multi-Page Email Scraping** → Find 600-1,000 new emails
   - Cost: FREE | Time: 2-3 hours | Result: 40-47% email coverage

---

## Quick Commands

### Test Mode (2 minutes, $0.15)
```bash
cd "C:\Users\79818\Desktop\Outreach - new"

# Test AI enrichment (edit script: add .head(10) at line 245)
py modules/openai/scripts/enrich_leads_with_ai.py

# Test email scraping
py modules/scraping/scripts/email_finder_multipage.py --limit 10
```

### Production Mode
```bash
# Phase 1: AI Enrichment (30-45 min, $28)
py modules/openai/scripts/enrich_leads_with_ai.py

# Phase 2: Email Scraping (2-3 hours, FREE)
py modules/scraping/scripts/email_finder_multipage.py
```

---

## What You Get

### AI Enrichment Output:
```
business_type: "family-owned"
has_emergency_service: true
call_handling_issues: "24/7 calls, busy season"
has_online_booking: false
personalization_hooks: [
  "You offer 24/7 service - voice AI handles after-hours without staff",
  "Family business competing with big companies - AI levels playing field"
]
```

### Email Scraping Output:
```
Before: 1,894 emails (30.8%)
After:  2,500-2,900 emails (40-47%)
New:    600-1,000 emails found

Strategy: Sitemap-first (70-80%) → Pattern fallback (20-30%)
```

---

## Files Created

- `modules/openai/scripts/enrich_leads_with_ai.py` - AI enrichment
- `modules/scraping/scripts/email_finder_multipage.py` - Email scraping
- `modules/scraping/lib/sitemap_utils.py` - Sitemap utilities
- `modules/scraping/EXECUTION_PLAN.md` - Detailed guide

---

## Prerequisites

```bash
# Set OpenAI API key in .env
OPENAI_API_KEY=sk-...

# Install dependencies (if needed)
pip install openai pandas pyarrow requests beautifulsoup4
```

---

## Results Location

```
# AI Enrichment
modules/openai/results/enriched_leads_YYYYMMDD_HHMMSS.parquet
modules/openai/results/enriched_leads_YYYYMMDD_HHMMSS_sample.csv

# Email Scraping
modules/scraping/results/multipage_enriched_YYYYMMDD_HHMMSS.parquet
modules/scraping/results/multipage_stats_YYYYMMDD_HHMMSS.csv
```

---

## Use Cases

### Personalized Email Campaigns:
```
Hi {{name}},

I noticed you're a {{business_type}} business offering {{services}}.

{{personalization_hook_1}}

Voice AI can help by...
```

### Lead Scoring:
```python
# High priority leads
priority = (
    (growth_signals != '') &
    (has_online_booking == False) &
    (has_emergency_service == True)
)
```

### Segmentation:
- **Quick wins:** Emergency service + no online booking
- **Tech-ready:** Already using automation tools
- **Budget-conscious:** Family-owned + competitive pricing

---

See `modules/scraping/EXECUTION_PLAN.md` for detailed documentation.
