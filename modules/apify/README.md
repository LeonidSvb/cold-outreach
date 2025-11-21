# Apify Module - Lead Generation Actors

Organized collection of Apify actor integrations for B2B lead generation.

## Structure

```
modules/apify/
├── actors/
│   └── google-maps-leads/          # Google Maps business leads scraper
│       ├── scripts/                # Scraping scripts
│       ├── results/                # CSV output files
│       ├── data/                   # Reference data (categories, countries)
│       └── docs/                   # Documentation & strategies
├── shared/                          # Shared utilities across actors
└── README.md                        # This file
```

## Available Actors

### 1. Google Maps Leads (google-maps-leads/)

**Actor:** xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps

**Cost:** $0.0019/lead (Gold tier)

**Coverage:**
- **Categories:** 1,041 business types
- **Countries:** 27 countries (US, GB, AU, CA, FR, IT, etc.)
- **Data Quality:** 75-85% email coverage, 95%+ phone coverage

**Quick Start:**
```bash
cd actors/google-maps-leads

# 1. Test single category (30 seconds, $0.02)
py scripts/test_hospitality_category.py

# 2. Scrape hospitality leads (2-3 hours, $5.70)
py scripts/premium_hospitality_scraper.py
```

**Reference Data:**
- data/ALL_CATEGORIES.txt - All 1,041 categories
- data/SUPPORTED_COUNTRIES.txt - 27 supported countries  
- data/hospitality_categories_validated.txt - 87 hospitality categories

**Documentation:**
- docs/HOSPITALITY_STRATEGY.md - Restaurant/hotel lead strategy
- docs/EUROPE_STRATEGY.md - European markets
- docs/AVAILABLE_RICH_MARKETS.md - High GDP targets

## Environment Setup

```bash
# Add to .env
APIFY_API_KEY=your_key_here
```

## Cost Optimization

**Free Tier:**
- Apify gives $5 free monthly credit
- Perfect for testing before scaling

**Pricing:**
- 1,000 leads = $1.90 (Gold tier)
- 10,000 leads = $19.00
- 100,000 leads = $190.00
