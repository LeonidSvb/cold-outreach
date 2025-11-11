# Lead Enrichment Strategy Summary

## Current State

```
Total Leads: 6,149
├── With Email: 1,894 (30.8%)
│   ├── Has homepage content: 1,894 ✓
│   └── AI enriched: 0 ✗
│
└── Without Email: 4,255 (69.2%)
    ├── Has website: 4,255
    └── Homepage only scraped: YES
```

---

## Proposed Strategy: Two-Phase Enrichment

### Phase 1: AI Content Analysis
**Target:** 1,894 leads (already have email + content)

```
INPUT: enriched_final_latest.parquet
  └── Filter: email IS NOT NULL AND content_length > 500
      └── 1,894 leads with ~4,000 chars each

PROCESS: OpenAI GPT-4o-mini Structured Extraction
  ├── Business Profile (type, size, area)
  ├── Pain Points (call handling, staffing)
  ├── Ideal Customer (residential/commercial)
  ├── Tech Readiness (online booking, automation)
  └── Personalization Hooks (2-3 sentences)

OUTPUT: enriched_leads_YYYYMMDD.parquet
  └── 1,894 leads with 20+ new AI-extracted columns

COST: ~$28 (1,894 × $0.015)
TIME: 30-45 minutes
```

### Phase 2: Multi-Page Email Scraping
**Target:** 4,255 leads (no email yet)

```
INPUT: enriched_final_latest.parquet
  └── Filter: email IS NULL AND website IS NOT NULL
      └── 4,255 leads to process

STRATEGY: Sitemap-First with Pattern Fallback

  Step 1: Sitemap Discovery (70-80% have sitemap)
    ├── Check robots.txt → Extract sitemap URL
    ├── Try /sitemap.xml, /sitemap_index.xml
    └── Parse XML → Extract all URLs

  Step 2: Filter Contact Pages
    └── Keywords: contact, about, quote, schedule
        └── Top 10 relevant pages

  Step 3: Scrape & Extract
    ├── Fetch each page
    ├── Extract emails with regex
    └── STOP on first email found ✓

  Fallback: Pattern Guessing (if no sitemap)
    └── Try: /contact, /about, /get-quote, etc.

OUTPUT: multipage_enriched_YYYYMMDD.parquet
  └── 600-1,000 NEW emails found (15-25% success)

COST: FREE (no API costs)
TIME: 2-3 hours (50 parallel workers)
```

---

## Expected Results

### Before Enrichment:
```
6,149 leads
└── 1,894 emails (30.8%)
    └── 0 AI enriched
```

### After Phase 1 (AI):
```
6,149 leads
└── 1,894 emails (30.8%)
    └── 1,894 AI enriched ✓
        ├── Business profile extracted
        ├── Pain points identified
        └── Personalization hooks ready
```

### After Phase 2 (Email Scraping):
```
6,149 leads
├── 2,500-2,900 emails (40-47%) ✓
│   └── 1,894 AI enriched
│       └── (+600-1,000 new emails need AI enrichment)
│
└── 3,200-3,600 still no email
    └── Consider: Apollo API enrichment ($100-200)
```

---

## Sitemap vs Pattern Strategy Comparison

### Sitemap-First Approach (Recommended)
```
Pros:
✓ 70-80% websites have sitemap.xml
✓ Finds ALL pages (even non-standard URLs)
✓ No 404 errors (only scrape existing pages)
✓ Intelligent prioritization
✓ 5-10 pages per site (cost efficient)

Cons:
✗ 20-30% sites have no sitemap (fallback needed)
✗ Some sitemaps have 1000+ URLs (need filter)
```

### Pattern Guessing (Fallback)
```
Pros:
✓ Works for sites without sitemap
✓ Fast (pre-defined URL list)
✓ Good coverage of common patterns

Cons:
✗ Misses non-standard URLs (/reach-us, /get-a-quote)
✗ More 404 errors (guessing pages)
✗ Only covers 50-60% of sites
```

### Hybrid Strategy (What We Use)
```
1. Try sitemap.xml FIRST
   └── Success (70-80% of sites)
       └── Scrape filtered contact pages

2. Fallback to patterns
   └── No sitemap (20-30% of sites)
       └── Try common URLs: /contact, /about, etc.

Result: 80-85% coverage with minimal HTTP requests
```

---

## Voice AI Personalization Examples

### Example 1: Emergency Service Business
```
AI Extracted:
- has_emergency_service: true
- call_handling_issues: "24/7 calls, overwhelmed"
- has_online_booking: false

Personalized Pitch:
"I noticed you offer 24/7 emergency HVAC service. Voice AI can handle
after-hours calls automatically, so you never miss an emergency lead
while still getting sleep."
```

### Example 2: Family-Owned Business
```
AI Extracted:
- business_type: "family-owned"
- company_size_signals: "small team"
- growth_signals: "hiring, expanding"

Personalized Pitch:
"As a growing family business, voice AI helps your small team compete
with big corporate competitors by answering every call professionally,
24/7, without hiring more staff."
```

### Example 3: Tech-Ready Business
```
AI Extracted:
- has_online_booking: true
- automation_tools: "CRM, dispatch software"
- growth_signals: "investing in technology"

Personalized Pitch:
"I see you're already using online booking and dispatch software. Voice
AI integrates seamlessly to handle phone calls - the last missing piece
of your automation stack."
```

---

## Cost-Benefit Analysis

### Investment:
```
Phase 1 (AI):     $28    | 45 minutes
Phase 2 (Email):  $0     | 3 hours
Total:            $28    | ~4 hours
```

### Returns:
```
+600-1,000 new verified emails
+1,894 leads with AI-extracted personalization
+20+ new data columns per lead

Value per lead:
- Manual research: 10-15 min/lead = 300+ hours saved
- Personalized outreach: +200% reply rate improvement
- ROI: $28 investment vs $30,000+ in manual research time
```

---

## Next Actions

### Ready to Start?

**Test Mode (2 minutes):**
```bash
# AI enrichment test
py modules/openai/scripts/enrich_leads_with_ai.py
# (Edit script: add .head(10) at line 245)

# Email scraping test
py modules/scraping/scripts/email_finder_multipage.py --limit 10
```

**Production Mode:**
```bash
# Phase 1
py modules/openai/scripts/enrich_leads_with_ai.py

# Phase 2
py modules/scraping/scripts/email_finder_multipage.py
```

**Full Documentation:**
- Detailed guide: `modules/scraping/EXECUTION_PLAN.md`
- Quick start: `QUICK_START.md`
