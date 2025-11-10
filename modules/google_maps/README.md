# Google Maps API Module

**Version:** 3.0.0
**Purpose:** Collect HVAC leads from Google Maps using Official API
**Status:** Production Ready

---

## Overview

This module collects HVAC contractor leads across USA using Google Places API with tier-based grid coverage strategy.

### Key Features

- **Tier-based grid coverage** (auto-scales for city size)
- **Full area coverage** with 30-40% overlap (no missing zones)
- **Parallel city processing** (5 workers per state)
- **Smart deduplication** (removes overlapping results)
- **Dual output format** (RAW + FILTERED data)
- **Cost-optimized** for free tier ($200/month)
- **Universal** - works for any country/city size

---

## Economics

### Free Tier

```
Google Places API Free Tier: $200/month (renews monthly)

Cost per lead (tier-based grid):
- Nearby Search: $0.032 per 60 results = $0.0005 per business
- Place Details: $0.023 per business (FILTERED only)
- Deduplication: ~50% overlap (optimal efficiency)
- TOTAL: ~$0.04 per qualified lead
```

### Real Results (4 Cold States)

```
States: New York, Illinois, Michigan, Pennsylvania
Cities: 21 total (5-6 per state)
Filter: 30-800 reviews, 4.0+ rating

Results:
- Filtered leads: 1,016 (ready for outreach)
- Raw leads: 1,707 (can re-filter later)
- Cost: $40.23 (20% of free tier)
- Time: ~7.6 minutes
- Cost per lead: $0.0396
```

---

## Usage

### Prerequisites

1. Get Google Cloud API key:
   - Go to https://console.cloud.google.com
   - Create project
   - Enable "Places API"
   - Create API key
   - Add to `.env`: `GOOGLE_PLACES_API_KEY=your_key`

### Run State-wide Collection

**Full state (all cities, recommended):**

```bash
python modules/google_maps/scripts/texas_hvac_scraper.py \
  --state "New York" \
  --keyword "HVAC contractors" \
  --min-reviews 30 \
  --max-reviews 800 \
  --min-rating 4.0 \
  --parallel
```

**Single city test:**

```bash
python modules/google_maps/scripts/texas_hvac_scraper.py \
  --city "Chicago, IL" \
  --keyword "HVAC contractors" \
  --min-reviews 30 \
  --max-reviews 800 \
  --min-rating 4.0
```

**Multiple states (batch processing):**

```bash
# New York
python modules/google_maps/scripts/texas_hvac_scraper.py --state "New York" --keyword "HVAC contractors" --min-reviews 30 --max-reviews 800 --min-rating 4.0 --parallel

# Illinois
python modules/google_maps/scripts/texas_hvac_scraper.py --state "Illinois" --keyword "HVAC contractors" --min-reviews 30 --max-reviews 800 --min-rating 4.0 --parallel

# Michigan
python modules/google_maps/scripts/texas_hvac_scraper.py --state "Michigan" --keyword "HVAC contractors" --min-reviews 30 --max-reviews 800 --min-rating 4.0 --parallel

# Pennsylvania
python modules/google_maps/scripts/texas_hvac_scraper.py --state "Pennsylvania" --keyword "HVAC contractors" --min-reviews 30 --max-reviews 800 --min-rating 4.0 --parallel
```

### Output

Two files are generated per run:

1. **FILTERED data** (ready for outreach): `modules/google_maps/results/{state}/hvac_YYYYMMDD_HHMMSS.json`
2. **RAW data** (for re-filtering): `modules/google_maps/results/{state}/hvac_raw_YYYYMMDD_HHMMSS.json`

Output format:
```json
{
  "metadata": {
    "timestamp": "20251110_151426",
    "state": "new_york",
    "niche": "hvac",
    "cities_processed": 5,
    "total_filtered_places": 291,
    "filters": {
      "min_reviews": 30,
      "max_reviews": 800,
      "min_rating": 4.0
    },
    "note": "FILTERED data with phone/website - ready for outreach"
  },
  "results_by_city": [
    {
      "city": "New York, NY",
      "filtered_places": [
        {
          "place_id": "ChIJ...",
          "name": "ABC Air Conditioning",
          "phone": "(555) 123-4567",
          "website": "https://abc-ac.com",
          "address": "123 Main St, New York, NY 10001",
          "rating": 4.8,
          "user_ratings_total": 342
        }
      ]
    }
  ]
}
```

---

## How It Works

### Tier-Based Grid Coverage Strategy

The scraper automatically selects grid density based on city population:

**Tier 1: Large Cities (>500k population)**
```
Examples: NYC, Chicago, Philadelphia, Detroit
Grid: 5x5 or 6x5 = 25-30 search points
Spacing: 8km between grid points
Circle radius: 6km per point
Overlap: ~40% (ensures full coverage)
Results: 100-150 leads per city
```

**Tier 2: Medium Cities (100k-500k)**
```
Examples: Buffalo, Rochester, Pittsburgh, Grand Rapids
Grid: 3x3 = 9 search points
Spacing: 12km between grid points
Circle radius: 8km per point
Overlap: ~30%
Results: 30-70 leads per city
```

**Tier 3: Small Cities (<100k)**
```
Examples: Erie, Reading
Grid: Single center point
Circle radius: 15km
Overlap: 0% (one circle covers entire area)
Results: 15-25 leads per city
```

### Why Grid Strategy Works

1. **Full Coverage:** Overlapping circles guarantee no missing zones
2. **Auto-Scaling:** Tier automatically selected by city population
3. **Efficient Deduplication:** ~50% overlap = optimal cost/coverage ratio
4. **Universal:** Works for any country/city without manual tuning
5. **Cost-Effective:** API calls scale with city size, not trial-and-error

### Parallel Processing

- Processes 5 cities simultaneously per state
- ThreadPoolExecutor for concurrency
- Deduplication removes overlapping results from grid circles
- Saves both RAW and FILTERED data

### Filters

- **Min reviews:** 30 (established business)
- **Max reviews:** 800 (not too large, likely needs services)
- **Min rating:** 4.0 (quality service)
- **Business status:** OPERATIONAL only

---

## Coverage Strategy

### Supported States

The scraper includes built-in city lists for cold weather states (high HVAC demand):

**Currently Configured:**
- **New York** (5 cities): NYC, Buffalo, Rochester, Yonkers, Syracuse
- **Illinois** (5 cities): Chicago, Aurora, Naperville, Joliet, Rockford
- **Michigan** (6 cities): Detroit, Grand Rapids, Warren, Sterling Heights, Ann Arbor, Lansing
- **Pennsylvania** (5 cities): Philadelphia, Pittsburgh, Allentown, Erie, Reading

**Add More States:**
Edit `STATES` dict in `texas_hvac_scraper.py`:
```python
STATES = {
    "Ohio": ["Columbus, OH", "Cleveland, OH", "Cincinnati, OH", ...],
    "Wisconsin": ["Milwaukee, WI", "Madison, WI", ...],
    # Add any state/country
}
```

### Real Results by City (Top 10)

Based on actual scraping from 4 cold states:

| City | Tier | Grid Points | Filtered Leads | Cost |
|------|------|-------------|----------------|------|
| Philadelphia, PA | 1 | 30 | 134 | $3.69 |
| New York, NY | 1 | 25 | 153 | $4.21 |
| Chicago, IL | 1 | 25 | 100 | $2.75 |
| Naperville, IL | 2 | 9 | 96 | $2.64 |
| Detroit, MI | 1 | 25 | 84 | $2.31 |
| Yonkers, NY | 2 | 9 | 73 | $2.01 |
| Sterling Heights, MI | 2 | 9 | 67 | $1.84 |
| Warren, MI | 2 | 9 | 63 | $1.73 |
| Aurora, IL | 2 | 9 | 59 | $1.62 |
| Pittsburgh, PA | 2 | 9 | 58 | $1.60 |

---

## File Structure

```
modules/google_maps/
├── README.md                      # This file
├── docs/
│   └── google-maps-api-guide.md  # Complete API guide
├── scripts/
│   └── texas_hvac_scraper.py     # Main scraper (bidirectional adaptive)
└── results/
    └── google_statewide_*.json   # Output files
```

---

## Changelog

### v3.0.0 (2025-11-10) - BREAKING CHANGE

**Tier-Based Grid Coverage (replaces adaptive radius)**

Major improvements:
- 3.9x more leads per city (vs adaptive radius)
- Full city area coverage (no missing zones)
- Auto-scaling grid density by city population
- Dual output format (RAW + FILTERED)
- Multi-state support (NY, IL, MI, PA)
- Universal strategy (works for any country)

Technical changes:
- Added `TIER_STRATEGIES` config (3-tier system)
- Added `CITY_POPULATIONS` database
- New `create_grid_points()` function
- New `get_city_tier()` function
- Replaced `--cities` with `--state` flag
- Deduplication optimized for grid overlap

Results from 4 states:
- 1,016 filtered leads (30-800 reviews, 4.0+ rating)
- Cost: $40.23 ($0.04/lead)
- Time: 7.6 minutes

### v2.0.0 (2025-11-09)
- Added --max-reviews filter (30-500 range)
- Renamed to texas_hvac_scraper.py (focused on HVAC only)
- Moved to modules/google_maps/ structure
- Removed outdated scripts (basic, smart, economy, Apify-based)

### v1.0.0 (2025-11-09)
- Initial bidirectional adaptive radius implementation
- Parallel city processing
- Built-in Texas cities list
- Cost-optimized for free tier

---

## Next Steps

1. Run test collection (3 cities)
2. Verify data quality
3. Run full collection (37 cities)
4. Export to CSV for outreach
5. Use voice agents for outreach!

---

## Support

See `docs/google-maps-api-guide.md` for complete API documentation and pricing details.
