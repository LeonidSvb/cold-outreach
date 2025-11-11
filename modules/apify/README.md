# Apify Module

**Version:** 1.0.0
**Purpose:** Collect business leads from Australia & New Zealand using Apify
**Status:** Production Ready

---

## Overview

This module uses Apify actor "9+ Million Business Leads With Emails" to automatically scrape field service businesses in Australia and New Zealand for voice agent outreach.

### Key Features

- **Automated API-based scraping** (no manual runs needed)
- **1,500+ leads** across AU + NZ
- **12 field service categories** (HVAC, plumbers, electricians, etc.)
- **Auto-aggregation** to single CSV
- **Cost tracking** and progress monitoring
- **Batch processing** with retries

---

## Economics

### Apify Actor Pricing

```
Actor: xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps
Cost: $1.90 per 1,000 leads

Our target:
- 1,500 leads total
- Cost: ~$2.85
- Time: ~30-60 minutes (actor processing)
```

### Budget Breakdown

```
Australia (1,050 leads):
  - HVAC: 150 leads ($0.29)
  - Air Conditioning: 120 leads ($0.23)
  - Electricians: 120 leads ($0.23)
  - Plumbers: 120 leads ($0.23)
  - Landscaping: 100 leads ($0.19)
  - Pest Control: 90 leads ($0.17)
  - Roofing: 80 leads ($0.15)
  - Locksmiths: 70 leads ($0.13)
  - Garage Door: 60 leads ($0.11)
  - Tree Service: 60 leads ($0.11)
  - Pool Maintenance: 50 leads ($0.10)
  - Towing: 30 leads ($0.06)

New Zealand (450 leads):
  - 11 categories, 15-60 leads each
  - Cost: ~$0.86

Total: $2.85 (well under $5 budget!)
```

---

## Usage

### Prerequisites

1. **Apify API Key** in `.env`:
   ```bash
   APIFY_API_KEY=your_api_key_here
   ```

2. **Python dependencies**:
   ```bash
   py -m pip install apify-client requests python-dotenv
   ```

### Quick Test (Recommended First)

Test with 10 leads to verify everything works:

```bash
python modules/apify/scripts/test_apify_actor.py
```

**Expected output:**
- 10 plumber leads from Australia
- Sample data displayed
- All fields shown
- Takes ~30 seconds

### Full Collection

Collect all 1,500 leads:

```bash
python modules/apify/scripts/australia_business_scraper.py
```

**Expected output:**
- 23 actor runs (12 AU + 11 NZ categories)
- Progress shown for each run
- ~30-60 minutes total time
- Final CSV with all 1,500 leads

### Output Files

```
modules/apify/results/
├── australia_nz_combined_20251111_HHMMSS.csv    # Main output - all leads
└── australia_nz_detailed_20251111_HHMMSS.json   # Detailed with metadata
```

---

## Output Format

### CSV Columns (main fields)

```csv
name,email,phone,website,address,city,country,source_country,source_category
ABC Plumbing,info@abc.com,0400123456,abc.com.au,"123 Main St",Sydney,AU,Australia,plumber
XYZ Electric,contact@xyz.co.nz,021234567,xyz.co.nz,"456 Queen St",Auckland,NZ,New Zealand,electrician
```

### All Available Fields

The actor provides rich data for each lead:
- `name` - Business name
- `email` - Email address
- `phone` - Phone number
- `website` / `url` - Website URL
- `address` - Full address
- `city` - City
- `country` - Country code (AU/NZ)
- `street` - Street address
- `google_maps_url` - Google Maps link
- `review_score` - Average rating
- `reviews_number` - Total reviews
- `facebook` - Facebook URL (if available)
- `instagram` - Instagram URL (if available)
- `linkedin` - LinkedIn URL (if available)
- `google_business_categories` - Business categories

Plus metadata:
- `source_country` - Which country run
- `source_category` - Which category run

---

## Categories

### Field Service Categories (Voice Agent Perfect Fit)

**Why these categories?**
- Local businesses with phones
- Appointment-heavy businesses
- Repetitive customer inquiries
- High ROI for voice automation

**Full list (12 categories):**

1. **HVAC Contractors** - AC repair, heating, ventilation
2. **Air Conditioning** - AC specialists (high demand in AU)
3. **Electricians** - Electrical services
4. **Plumbers** - Plumbing services
5. **Landscaping** - Lawn care, gardening
6. **Pest Control** - Pest removal, termite control
7. **Roofing** - Roof repairs, installation
8. **Locksmiths** - Lock services, security
9. **Garage Door Repair** - Garage door services
10. **Tree Service** - Tree removal, trimming
11. **Pool Maintenance** - Pool cleaning, repairs (AU specific)
12. **Towing** - Tow truck services

---

## Script Details

### `test_apify_actor.py`

**Purpose:** Quick test before full run

**What it does:**
- Tests API connection
- Runs 1 category (plumbers, AU)
- Fetches 10 leads
- Shows sample results
- Displays all available fields

**Runtime:** ~30 seconds
**Cost:** ~$0.02 (practically free)

### `australia_business_scraper.py`

**Purpose:** Full automated collection

**What it does:**
- Processes 23 categories (12 AU + 11 NZ)
- Fetches 1,500 total leads
- Monitors progress in real-time
- Tracks cost per run
- Aggregates all to single CSV
- Saves detailed JSON backup

**Runtime:** 30-60 minutes
**Cost:** ~$2.85

**Features:**
- ✅ Automatic retries on failure
- ✅ Progress tracking
- ✅ Cost monitoring
- ✅ Duplicate handling
- ✅ Metadata addition
- ✅ Error logging

---

## Customization

### Add More Categories

Edit `australia_business_scraper.py`:

```python
CATEGORIES = {
    'Australia': [
        {'category': 'your_category', 'max_results': 100},
        # Add more...
    ]
}
```

### Change Distribution

Current: 70% AU, 30% NZ

To change:
```python
# 80% AU, 20% NZ
'Australia': [...],  # Increase max_results
'New Zealand': [...],  # Decrease max_results
```

### Add Countries

Currently supports AU + NZ. To add more:

```python
CATEGORIES = {
    'Singapore': [
        {'category': 'hvac', 'max_results': 100},
    ]
}

COUNTRY_CODES = {
    'Singapore': 'SG'
}
```

---

## Troubleshooting

### "Failed to start run: 401"

❌ **Problem:** Invalid API key
✅ **Solution:** Check APIFY_API_KEY in .env

### "Run failed: FAILED"

❌ **Problem:** Actor input invalid
✅ **Solution:** Run test script first to check

### "No results returned"

❌ **Problem:** Category has no data for that country
✅ **Solution:** Try different category or country

### "Rate limit exceeded"

❌ **Problem:** Too many requests
✅ **Solution:** Add delays between runs (already in script)

---

## Next Steps

1. **Run test:** `python modules/apify/scripts/test_apify_actor.py`
2. **Verify results:** Check sample data looks good
3. **Run full collection:** `python modules/apify/scripts/australia_business_scraper.py`
4. **Wait 30-60 minutes:** Script runs automatically
5. **Get CSV:** Find in `modules/apify/results/`
6. **Enrich data:** Ready for voice agent outreach!

---

## Support

See existing US data structure in:
- `modules/google_maps/results/florida/`
- `modules/google_maps/results/texas/`

For Apify actor details:
- https://apify.com/xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps
