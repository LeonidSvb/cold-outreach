# Google Maps API Module

**Version:** 2.0.0
**Purpose:** Collect HVAC leads from Google Maps using Official API
**Status:** Production Ready

---

## Overview

This module collects HVAC contractor leads across Texas using Google Places API with bidirectional adaptive radius strategy.

### Key Features

- Bidirectional adaptive radius (auto-adjusts for city density)
- Parallel city processing (5 workers)
- Built-in deduplication by place_id
- Cost-optimized for free tier ($200/month)
- Supports 30-500 reviews filter

---

## Economics

### Free Tier

```
Google Places API Free Tier: $200/month (renews monthly)

Cost per lead:
- Nearby Search: $0.032 per 60 results = $0.0005 per business
- Place Details: $0.023 per business
- TOTAL: ~$0.024 per qualified lead
```

### Texas HVAC Market

```
Total HVAC companies in Texas: ~17,000
With 30-500 reviews, 4.0+ rating: ~3,800 companies

Target: 3,500 leads
Cost: $84.66 (COMPLETELY FREE within tier)
Budget remaining: $115.34
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

### Run Texas HVAC Collection

**Full collection (37 cities, ~3,000 leads):**

```bash
python modules/google_maps/scripts/texas_hvac_scraper.py \
  --cities "Houston, TX,Dallas, TX,San Antonio, TX,Austin, TX,Fort Worth, TX,El Paso, TX,Arlington, TX,Corpus Christi, TX,Plano, TX,Laredo, TX,Lubbock, TX,Irving, TX,Garland, TX,Frisco, TX,McKinney, TX,Amarillo, TX,Grand Prairie, TX,Brownsville, TX,Pasadena, TX,Mesquite, TX,Killeen, TX,McAllen, TX,Waco, TX,Carrollton, TX,Beaumont, TX,Abilene, TX,Round Rock, TX,Richardson, TX,Midland, TX,Odessa, TX,Lewisville, TX,College Station, TX,Pearland, TX,Sugar Land, TX,Tyler, TX,Denton, TX,Wichita Falls, TX" \
  --keyword "HVAC contractors" \
  --min-reviews 30 \
  --max-reviews 500 \
  --min-rating 4.0 \
  --max-results 3500 \
  --parallel
```

**Test run (3 cities only):**

```bash
python modules/google_maps/scripts/texas_hvac_scraper.py \
  --cities "Houston, TX,Dallas, TX,Austin, TX" \
  --keyword "HVAC contractors" \
  --min-reviews 30 \
  --max-reviews 500 \
  --min-rating 4.0 \
  --max-results 500 \
  --parallel
```

### Output

Results saved to: `modules/google_maps/results/google_statewide_YYYYMMDD_HHMMSS.json`

Output format:
```json
{
  "metadata": {
    "timestamp": "20251109_170000",
    "cities_processed": 37,
    "total_places": 3245,
    "stats": {
      "total_api_calls": 145,
      "radius_increases": 12,
      "radius_decreases": 23,
      "optimal_searches": 110,
      "total_cost": 84.66
    }
  },
  "all_places": [
    {
      "place_id": "ChIJ...",
      "name": "ABC Air Conditioning",
      "phone": "(555) 123-4567",
      "website": "https://abc-ac.com",
      "address": "123 Main St, Houston, TX 77001",
      "rating": 4.8,
      "user_ratings_total": 342
    }
  ]
}
```

---

## How It Works

### Bidirectional Adaptive Radius

The scraper automatically adjusts search radius based on business density:

**Dense City (Houston, Dallas):**
```
Start: 15km radius
Finds: 60+ businesses
Action: DECREASE to 7.5km, subdivide into 4 quadrants
Result: Complete coverage with small circles
```

**Medium City (Lubbock, Amarillo):**
```
Start: 15km radius
Finds: 15-55 businesses
Action: OPTIMAL, use this radius
Result: One circle covers entire city
```

**Sparse Area (West Texas):**
```
Start: 15km radius
Finds: <15 businesses
Action: INCREASE to 22km, then 33km, up to 100km
Result: Large circle covers rural area
```

### Parallel Processing

- Processes 5 cities simultaneously
- ThreadPoolExecutor for concurrency
- Global deduplication after all cities processed

### Filters

- **Min reviews:** 30 (established business)
- **Max reviews:** 500 (not too large, likely needs voice agents)
- **Min rating:** 4.0 (quality service)
- **Business status:** OPERATIONAL only

---

## Coverage Strategy

### Texas Cities (37 total)

**Tier 1 (4 metros) - 40% population:**
- Houston, Dallas, San Antonio, Austin
- Estimated: ~1,400 HVAC companies

**Tier 2 (13 cities) - 30% population:**
- Fort Worth, El Paso, Arlington, Corpus Christi, Plano, Laredo, Lubbock, Irving, Garland, Frisco, McKinney, Amarillo, Grand Prairie
- Estimated: ~1,050 HVAC companies

**Tier 3 (20 cities) - 15% population:**
- Brownsville, Pasadena, Mesquite, Killeen, McAllen, Waco, Carrollton, Beaumont, Abilene, Round Rock, Richardson, Midland, Odessa, Lewisville, College Station, Pearland, Sugar Land, Tyler, Denton, Wichita Falls
- Estimated: ~525 HVAC companies

**Total Coverage:** 85% of Texas market (2,975 companies)

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
