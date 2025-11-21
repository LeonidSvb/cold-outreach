# Google Maps Leads - Quick Start

Fast track to collecting business leads from Google Maps.

## TL;DR

```bash
# Test (30 seconds, $0.02)
py scripts/test_hospitality_category.py

# Production (2-3 hours, $5.70 for 1,500 leads)
py scripts/premium_hospitality_scraper.py
```

## Prerequisites

1. **Apify Account:**
   - Sign up: https://apify.com
   - Get $5 free credit (no card required)
   - Copy API key

2. **Environment Variable:**
   ```bash
   # Add to .env file in project root
   APIFY_API_KEY=your_key_here
   ```

## Reference Data (Already Prepared!)

**No need to look these up - we extracted them via API:**

### Categories (1,041 total)
- `data/ALL_CATEGORIES.txt` - Full list A-Z
- `data/hospitality_categories_validated.txt` - 87 hospitality
- `data/valid_categories.json` - Programmatic access

### Countries (27 supported)
- `data/SUPPORTED_COUNTRIES.txt` - With names
- `data/supported_countries.json` - With ISO codes

**Top markets:**
- English: US, GB, AU, CA, IE
- Europe: FR, IT, ES, NL, BE, SE, NO, DK, FI
- Asia: JP, KR, IN, TH

## Usage Examples

### 1. Test Run (Recommended First!)

```bash
py scripts/test_hospitality_category.py
```

**What it does:**
- Tests 1 category (restaurant) in Australia
- Gets 10 sample leads
- Shows data quality stats
- **Cost:** ~$0.02
- **Time:** 30 seconds

### 2. Hospitality Collection

```bash
py scripts/premium_hospitality_scraper.py
```

**What you get:**
- 15 premium categories (hotels, restaurants, cafes)
- Australia + New Zealand
- ~1,500 total leads
- **Cost:** ~$2.85
- **Time:** 2-3 hours

### 3. Custom Scraper

**Create your own based on templates:**

```python
#!/usr/bin/env python3
import os
from dotenv import load_dotenv

load_dotenv()

# Your categories
CATEGORIES = {
    'United States': [
        {'category': 'software_company', 'max_results': 100},
        {'category': 'marketing_agency', 'max_results': 100},
        {'category': 'accounting_firm', 'max_results': 100},
    ]
}

COUNTRY_CODES = {'United States': 'US'}

# Use run_actor() function from test script
# Full example in scripts/premium_hospitality_scraper.py
```

## Category Selection Tips

### By Industry

**Tech & Software (19 categories):**
```
software_company
computer_consultant
web_hosting_service
website_designer
```

**Professional Services (30 categories):**
```
accounting_firm
law_firm
marketing_agency
advertising_agency
consulting
```

**Healthcare (54 categories):**
```
dental_clinic
medical_clinic
physiotherapy_center
chiropractor
```

**Hospitality (87 categories):**
```
restaurant
hotel
cafe
bar
```

### By Business Size

**Enterprise/SMB:**
- software_company
- manufacturer
- distributor

**Small Business:**
- restaurant
- retail_store
- hair_salon

**Professional:**
- lawyer
- accountant
- consultant

## Cost Calculator

| Leads | Free Tier ($0.0035) | Gold Tier ($0.0019) |
|-------|---------------------|---------------------|
| 100 | $0.35 | $0.19 |
| 500 | $1.75 | $0.95 |
| 1,000 | $3.50 | $1.90 |
| 5,000 | $17.50 | $9.50 |
| 10,000 | $35.00 | $19.00 |

**Strategy:** Use $5 free credit for testing, then upgrade for volume.

## Output Format

**CSV file saved to results/:**
```
premium_hospitality_YYYYMMDD_HHMMSS.csv
```

**Columns:**
- name - Business name
- email - Email address (75-85% coverage)
- phone_number - Phone (95%+ coverage)
- url - Website URL (80-90% coverage)
- address - Full address
- city - City
- country_code - ISO code (AU, NZ, US, etc.)
- source_country - Which country run
- source_category - Which category run
- review_score - Google rating (1-5)
- reviews_number - Total reviews
- google_maps_url - Direct Google Maps link

## Data Quality Expectations

**Email Coverage:**
- Restaurants/Cafes: 75-85%
- Hotels: 80-90%
- Professional Services: 70-80%
- Retail: 60-70%

**Phone Coverage:**
- All categories: 95-98%

**Website Coverage:**
- Hotels/Restaurants: 85-95%
- Professional Services: 80-90%
- Retail: 70-80%

## Validation

**Before running, validate your categories:**

```python
import json

with open('data/valid_categories.json') as f:
    valid = set(json.load(f)['categories'])

my_cats = ['hotel', 'hostel', 'bistro']  # Check these
invalid = [c for c in my_cats if c not in valid]

if invalid:
    print(f"Invalid: {invalid}")
    # Output: ['hostel', 'bistro'] - use alternatives!
```

## Troubleshooting

**"Invalid category" error:**
- Check `data/ALL_CATEGORIES.txt` for exact spelling
- Categories are snake_case (e.g., `steak_house` not `steakhouse`)

**"Invalid country" error:**
- Check `data/SUPPORTED_COUNTRIES.txt`
- Use ISO 2-letter codes (US, GB, AU, etc.)

**"No results" but no error:**
- Category exists but has 0 businesses in that region
- Try different country or category

**Script runs but takes forever:**
- Normal! Each category takes ~3 minutes
- 15 categories = 45 minutes minimum
- Use `max_results: 50` instead of 100 to speed up

## Next Steps

1. **Run test script** to verify setup
2. **Check sample data** quality
3. **Customize categories** for your niche
4. **Run production** scraper
5. **Validate emails** (Hunter.io, ZeroBounce)
6. **Start outreach!**

## Documentation

- `docs/HOSPITALITY_STRATEGY.md` - Full hospitality guide
- `docs/EUROPE_STRATEGY.md` - European market strategy
- `docs/AVAILABLE_RICH_MARKETS.md` - High GDP targets
- `../README.md` - Module overview

## Support

**Questions?**
- Check `data/` reference files first
- Review existing scripts in `scripts/`
- Apify actor page: https://apify.com/xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps
