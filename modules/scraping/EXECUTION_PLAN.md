# Lead Enrichment Execution Plan

## Overview

Two-phase strategy for enriching 6,149 leads:
- **Phase 1:** AI enrichment for 1,894 leads with emails (existing content)
- **Phase 2:** Multi-page scraping for 4,255 leads without emails

---

## Phase 1: AI Content Analysis (1,894 leads)

### What it does:
- Analyzes existing homepage content with OpenAI
- Extracts structured business intelligence for personalization
- Identifies pain points, tech readiness, unique hooks

### Cost & Time:
- **Cost:** ~$28 (1,894 leads × $0.015)
- **Time:** 30-45 minutes
- **Model:** gpt-4o-mini

### Output:
Structured JSON for each lead:
```json
{
  "business_type": "family-owned",
  "has_emergency_service": true,
  "call_handling_issues": "24/7 calls, busy season",
  "target_markets": "residential, commercial",
  "has_online_booking": false,
  "growth_signals": "hiring, expanding",
  "personalization_hooks": [
    "You mention 24/7 service - voice AI can handle after-hours without staff",
    "Family business with 15+ years - AI helps small teams compete"
  ]
}
```

### Execution:

```bash
# 1. Set OpenAI API key in .env
OPENAI_API_KEY=sk-...

# 2. Run enrichment
cd "C:\Users\79818\Desktop\Outreach - new"
py modules/openai/scripts/enrich_leads_with_ai.py

# 3. Results
# - modules/openai/results/enriched_leads_YYYYMMDD_HHMMSS.parquet
# - modules/openai/results/enriched_leads_YYYYMMDD_HHMMSS_sample.csv
```

### Use Cases:
- **Personalized cold emails:** "I noticed you're family-owned with 24/7 service..."
- **Voice AI pitch customization:** "You handle emergency calls - AI never sleeps"
- **Lead scoring:** Priority = high growth signals + low tech readiness
- **Segmentation:** Residential vs commercial, premium vs budget

---

## Phase 2: Multi-Page Email Scraping (4,255 leads)

### What it does:
- Sitemap-first discovery (70-80% have sitemap.xml)
- Scrapes contact/about pages intelligently
- Pattern guessing fallback if no sitemap
- Stops on first email found (efficient)

### Expected Results:
- **New emails:** 600-1,000 (15-25% of 4,255)
- **Total email coverage:** 30.8% → 45-55%
- **Time:** 2-3 hours (50 parallel workers)
- **Cost:** FREE (no API costs)

### Execution:

```bash
# Full production run
py modules/scraping/scripts/email_finder_multipage.py \
  --input modules/google_maps/data/enriched/enriched_final_latest.parquet \
  --workers 50 \
  --timeout 10

# Test mode (10 leads)
py modules/scraping/scripts/email_finder_multipage.py \
  --input modules/google_maps/data/enriched/enriched_final_latest.parquet \
  --limit 10

# Results:
# - modules/scraping/results/multipage_enriched_YYYYMMDD_HHMMSS.parquet
# - modules/scraping/results/multipage_stats_YYYYMMDD_HHMMSS.csv
```

### Strategy Details:

**Sitemap-First (70-80% success):**
1. Check robots.txt for sitemap location
2. Try common paths: /sitemap.xml, /sitemap_index.xml
3. Parse XML and extract all URLs
4. Filter contact-related keywords: contact, about, quote, etc.
5. Scrape top 10 relevant pages
6. Stop on first email found

**Pattern Fallback (20-30%):**
If no sitemap, try common patterns:
- /contact, /contact-us, /contactus
- /about, /about-us
- /get-quote, /request-quote
- /schedule, /reach-us

---

## Complete Workflow

### Step 1: Test Mode (Recommended)
```bash
# Test AI enrichment (10 leads)
# MANUALLY EDIT enrich_leads_with_ai.py:
# Line ~245: Add .head(10) before processing

py modules/openai/scripts/enrich_leads_with_ai.py
# Cost: ~$0.15
# Time: 1-2 minutes

# Test multi-page scraping (10 leads)
py modules/scraping/scripts/email_finder_multipage.py --limit 10
# Cost: FREE
# Time: 1-2 minutes
```

### Step 2: Review Test Results
Check outputs:
- AI enrichment quality (personalization hooks make sense?)
- Email scraping success rate (how many new emails?)
- No errors/crashes?

### Step 3: Production Run
```bash
# Phase 1: AI Enrichment
py modules/openai/scripts/enrich_leads_with_ai.py
# Wait 30-45 minutes
# Cost: ~$28

# Phase 2: Multi-Page Scraping
py modules/scraping/scripts/email_finder_multipage.py
# Wait 2-3 hours
# Cost: FREE
```

### Step 4: Consolidate Results
```bash
# Merge AI enrichment + new emails into final dataset
# TODO: Create consolidation script if needed
```

---

## Expected Final Results

| Metric | Before | After Phase 1 | After Phase 2 |
|--------|--------|---------------|---------------|
| Total Leads | 6,149 | 6,149 | 6,149 |
| Leads with Email | 1,894 (30.8%) | 1,894 (30.8%) | 2,500-2,900 (40-47%) |
| AI Enriched | 0 | 1,894 | 1,894 |
| Personalization Hooks | 0 | 1,894 | 1,894 |

**Total Investment:**
- Cost: ~$28 (OpenAI API)
- Time: 3-4 hours
- Result: 600-1,000 new emails + full AI enrichment

---

## Files Created

### AI Enrichment:
- `modules/openai/scripts/enrich_leads_with_ai.py` - Main enrichment script

### Multi-Page Scraping:
- `modules/scraping/lib/sitemap_utils.py` - Sitemap parsing utilities
- `modules/scraping/scripts/email_finder_multipage.py` - Main scraping script

### Documentation:
- `modules/scraping/EXECUTION_PLAN.md` - This file

---

## Troubleshooting

### Issue: OpenAI API rate limit exceeded
**Solution:** Script already has 1.2s delay (50 req/min). If still hitting limits, increase `RATE_LIMIT_DELAY` in script.

### Issue: Too slow / timeout errors
**Solution:** Reduce `--workers` from 50 to 25 or increase `--timeout` from 10 to 15.

### Issue: Low email discovery rate (< 10%)
**Solution:** Check `sitemap_found` ratio in stats CSV. If < 50%, sitemaps may be blocked. Try adding more pattern URLs.

### Issue: Out of memory during processing
**Solution:** Process in batches. Add `--limit 1000` and run multiple times with different offsets.

---

## Next Steps After Enrichment

1. **Export to CSV for cold outreach tools:**
   - Instantly.ai
   - Smartlead
   - Lemlist

2. **Create personalized email templates:**
   - Use `personalization_hooks` column
   - Segment by `business_type`, `target_markets`

3. **Lead scoring:**
   - High priority: `growth_signals` + low `automation_tools`
   - Quick wins: `has_emergency_service` + no online booking

4. **Voice AI pitch customization:**
   - Emergency service → "AI handles after-hours calls"
   - Family-owned → "Compete with big companies"
   - Busy season mentions → "Scale instantly during peak"

---

## Questions?

Check logs:
- AI enrichment: `data/logs/modules.openai.scripts.enrich_leads_with_ai.log`
- Multi-page scraping: `data/logs/modules.scraping.scripts.email_finder_multipage.log`
