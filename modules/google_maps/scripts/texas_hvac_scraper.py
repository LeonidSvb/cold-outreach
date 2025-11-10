#!/usr/bin/env python3
"""
=== GOOGLE PLACES STATEWIDE SCRAPER ===
Version: 5.0.0 | Created: 2025-11-09 | Updated: 2025-11-10

BIDIRECTIONAL ADAPTIVE RADIUS:
- Too few results (< 15) → INCREASE radius (sparse desert area)
- Optimal (15-55) → USE results
- Too many (> 55) → DECREASE radius (dense city area)

STATEWIDE STRATEGY:
- Scrape multiple cities in parallel
- Each city uses adaptive radius
- Auto-discovers optimal coverage

NEW IN v5.0.0:
- Saves BOTH raw and filtered data (can re-filter later without API calls)
- Organized folder structure: results/{state}/{niche}_{timestamp}.json
- Support for Texas and Florida states
- Raw data saved without phone/website to save API costs

USAGE:
# Single state (all major cities):
python texas_hvac_scraper.py --state "Texas" --keyword "HVAC contractors" --min-reviews 30 --max-reviews 500 --parallel

python texas_hvac_scraper.py --state "Florida" --keyword "plumbers" --min-reviews 20 --max-reviews 800 --parallel

# Custom city list:
python texas_hvac_scraper.py --cities "Houston, TX,Dallas, TX" --keyword "HVAC" --min-reviews 30 --max-reviews 500

OUTPUT:
- RAW file: modules/google_maps/results/{state}/{niche}_raw_{timestamp}.json
- FILTERED file: modules/google_maps/results/{state}/{niche}_{timestamp}.json
"""

import os
import sys
import json
import time
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import math

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from logger.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

load_dotenv()

CONFIG = {
    "API_KEY": os.getenv("GOOGLE_PLACES_API_KEY"),
    "GEOCODE_URL": "https://maps.googleapis.com/maps/api/geocode/json",
    "NEARBY_SEARCH_URL": "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
    "PLACE_DETAILS_URL": "https://maps.googleapis.com/maps/api/place/details/json",
    "OUTPUT_DIR": "modules/google_maps/results",
    "DELAY_BETWEEN_REQUESTS": 0.5,

    # Parallel processing
    "MAX_WORKERS": 5,              # Process 5 cities simultaneously
}

# TIER-BASED GRID COVERAGE STRATEGY
TIER_STRATEGIES = {
    "tier_1": {  # Large cities (>500k population)
        "population_min": 500000,
        "grid_step_km": 8,           # 8km between grid points
        "circle_radius_km": 6,       # 6km radius per circle
        "overlap_percent": 40,       # ~40% overlap
        "description": "Dense grid coverage for large metro areas"
    },
    "tier_2": {  # Medium cities (100k-500k)
        "population_min": 100000,
        "grid_step_km": 12,          # 12km between points
        "circle_radius_km": 8,       # 8km radius
        "overlap_percent": 30,       # ~30% overlap
        "description": "Medium grid coverage"
    },
    "tier_3": {  # Small cities (<100k)
        "population_min": 0,
        "grid_step_km": None,        # No grid - just center point
        "circle_radius_km": 15,      # 15km from center
        "overlap_percent": 0,
        "description": "Simple center coverage"
    }
}

# City population database (approximate)
CITY_POPULATIONS = {
    # New York
    "New York, NY": 8_800_000,
    "Buffalo, NY": 278_000,
    "Rochester, NY": 211_000,
    "Yonkers, NY": 211_000,
    "Syracuse, NY": 148_000,

    # Illinois
    "Chicago, IL": 2_700_000,
    "Aurora, IL": 180_000,
    "Naperville, IL": 149_000,
    "Joliet, IL": 150_000,
    "Rockford, IL": 148_000,

    # Michigan
    "Detroit, MI": 639_000,
    "Grand Rapids, MI": 198_000,
    "Warren, MI": 139_000,
    "Sterling Heights, MI": 134_000,
    "Ann Arbor, MI": 123_000,
    "Lansing, MI": 112_000,

    # Pennsylvania
    "Philadelphia, PA": 1_600_000,
    "Pittsburgh, PA": 303_000,
    "Allentown, PA": 125_000,
    "Erie, PA": 95_000,
    "Reading, PA": 95_000
}

# Major Texas cities for statewide scraping
TEXAS_CITIES = [
    "Houston, TX", "Dallas, TX", "Austin, TX", "San Antonio, TX",
    "Fort Worth, TX", "El Paso, TX", "Arlington, TX", "Corpus Christi, TX",
    "Plano, TX", "Laredo, TX", "Lubbock, TX", "Irving, TX",
    "Garland, TX", "Frisco, TX", "McKinney, TX", "Amarillo, TX",
    "Grand Prairie, TX", "Brownsville, TX", "Pasadena, TX", "Mesquite, TX"
]

# Major Florida cities for statewide scraping (56 cities total)
FLORIDA_CITIES = [
    # Original 20 major cities
    "Miami, FL", "Tampa, FL", "Orlando, FL", "Jacksonville, FL",
    "St. Petersburg, FL", "Hialeah, FL", "Port St. Lucie, FL", "Cape Coral, FL",
    "Tallahassee, FL", "Fort Lauderdale, FL", "Pembroke Pines, FL", "Hollywood, FL",
    "Miramar, FL", "Coral Springs, FL", "Clearwater, FL", "Miami Gardens, FL",
    "Palm Bay, FL", "West Palm Beach, FL", "Pompano Beach, FL", "Gainesville, FL",

    # Phase 1 expansion: Medium cities (50k-150k)
    "Lakeland, FL", "Kissimmee, FL", "Deltona, FL", "Palm Coast, FL",
    "Melbourne, FL", "Daytona Beach, FL", "Boca Raton, FL", "Boynton Beach, FL",
    "Port Charlotte, FL", "Sarasota, FL", "Ocala, FL", "Deerfield Beach, FL",
    "Sunrise, FL", "Plantation, FL", "Bonita Springs, FL",

    # Phase 2 expansion: Smaller cities (30k-80k) for maximum coverage
    "Fort Myers, FL", "Spring Hill, FL", "Homestead, FL", "North Port, FL",
    "Lehigh Acres, FL", "Davie, FL", "Wellington, FL", "Aventura, FL",
    "Apopka, FL", "Largo, FL", "Pinellas Park, FL", "Brandon, FL",
    "Altamonte Springs, FL", "Winter Haven, FL", "Coconut Creek, FL", "Lauderhill, FL",
    "Palm Beach Gardens, FL", "St. Cloud, FL", "Panama City, FL", "Jupiter, FL",
    "Naples, FL"
]

# COLD STATES - HVAC HEATING SEASON (November-March)
NEW_YORK_CITIES = [
    "New York, NY", "Buffalo, NY", "Rochester, NY", "Yonkers, NY", "Syracuse, NY"
]

ILLINOIS_CITIES = [
    "Chicago, IL", "Aurora, IL", "Naperville, IL", "Joliet, IL", "Rockford, IL"
]

MICHIGAN_CITIES = [
    "Detroit, MI", "Grand Rapids, MI", "Warren, MI", "Sterling Heights, MI", "Ann Arbor, MI", "Lansing, MI"
]

PENNSYLVANIA_CITIES = [
    "Philadelphia, PA", "Pittsburgh, PA", "Allentown, PA", "Erie, PA", "Reading, PA"
]

STATE_CITIES = {
    "Texas": TEXAS_CITIES,
    "Florida": FLORIDA_CITIES,
    "New York": NEW_YORK_CITIES,
    "Illinois": ILLINOIS_CITIES,
    "Michigan": MICHIGAN_CITIES,
    "Pennsylvania": PENNSYLVANIA_CITIES,
}

STATS = {
    "total_api_calls": 0,
    "radius_increases": 0,
    "radius_decreases": 0,
    "optimal_searches": 0,
    "cities_processed": 0,
    "total_cost": 0.0,
}

def get_city_tier(city: str) -> str:
    """Determine city tier based on population"""
    population = CITY_POPULATIONS.get(city, 50000)

    if population >= TIER_STRATEGIES["tier_1"]["population_min"]:
        return "tier_1"
    elif population >= TIER_STRATEGIES["tier_2"]["population_min"]:
        return "tier_2"
    else:
        return "tier_3"

def create_grid_points(center_lat: float, center_lng: float, tier: str, city_name: str = "") -> List[Tuple[float, float]]:
    """
    Create grid of search points to cover entire city
    Returns list of (lat, lng) tuples
    """
    strategy = TIER_STRATEGIES[tier]

    # Tier 3: just use center point
    if strategy["grid_step_km"] is None:
        logger.info(f"[{city_name}] {tier.upper()}: Single center point (r={strategy['circle_radius_km']}km)")
        return [(center_lat, center_lng)]

    # Tier 1 & 2: create grid
    grid_step_km = strategy["grid_step_km"]
    radius_km = strategy["circle_radius_km"]

    # Estimate city bounding box (simplified)
    # For tier 1 cities: ~40km x 40km, tier 2: ~25km x 25km
    bbox_size_km = 40 if tier == "tier_1" else 25

    # Convert km to degrees
    km_per_degree_lat = 111.32
    km_per_degree_lng = 111.32 * math.cos(math.radians(center_lat))

    half_size_lat = (bbox_size_km / 2) / km_per_degree_lat
    half_size_lng = (bbox_size_km / 2) / km_per_degree_lng
    step_lat = grid_step_km / km_per_degree_lat
    step_lng = grid_step_km / km_per_degree_lng

    # Generate grid points
    grid_points = []
    lat = center_lat - half_size_lat
    while lat <= center_lat + half_size_lat:
        lng = center_lng - half_size_lng
        while lng <= center_lng + half_size_lng:
            grid_points.append((lat, lng))
            lng += step_lng
        lat += step_lat

    logger.info(f"[{city_name}] {tier.upper()}: {len(grid_points)} grid points (step={grid_step_km}km, r={radius_km}km, overlap={strategy['overlap_percent']}%)")
    return grid_points

def geocode_city(city: str) -> Tuple[float, float]:
    """Get lat/lng for city"""
    params = {"address": city, "key": CONFIG["API_KEY"]}
    response = requests.get(CONFIG["GEOCODE_URL"], params=params)

    if response.status_code != 200 or response.json()["status"] != "OK":
        return (0, 0)

    location = response.json()["results"][0]["geometry"]["location"]
    return (location["lat"], location["lng"])

def nearby_search(lat: float, lng: float, keyword: str, radius: int) -> List[Dict]:
    """Search places in radius with pagination (up to 60 results - 3 pages)"""
    all_results = []
    next_page_token = None
    page = 1

    while page <= 3:
        params = {
            "location": f"{lat},{lng}",
            "radius": radius,
            "keyword": keyword,
            "key": CONFIG["API_KEY"]
        }

        if next_page_token:
            params = {"pagetoken": next_page_token, "key": CONFIG["API_KEY"]}

        response = requests.get(CONFIG["NEARBY_SEARCH_URL"], params=params)
        STATS["total_api_calls"] += 1

        if response.status_code != 200:
            break

        data = response.json()
        if data["status"] not in ["OK", "ZERO_RESULTS"]:
            break

        results = data.get("results", [])
        all_results.extend([{
            "place_id": p.get("place_id"),
            "name": p.get("name"),
            "vicinity": p.get("vicinity", ""),
            "rating": p.get("rating", 0),
            "user_ratings_total": p.get("user_ratings_total", 0),
            "business_status": p.get("business_status", ""),
        } for p in results])

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

        page += 1
        time.sleep(2)

    return all_results

def adaptive_radius_search(
    lat: float,
    lng: float,
    keyword: str,
    initial_radius: int,
    city_name: str = "",
    depth: int = 0
) -> Tuple[List[Dict], int]:
    """
    BIDIRECTIONAL adaptive radius search
    Returns: (places, final_radius_used)
    """
    radius = initial_radius
    indent = "  " * depth

    logger.info(f"{indent}[{city_name}] Trying radius {radius/1000:.1f}km...")

    places = nearby_search(lat, lng, keyword, radius)
    num_results = len(places)

    logger.info(f"{indent}[{city_name}] Found {num_results} results")

    # CASE 1: Too few results → INCREASE radius (sparse area)
    if num_results < CONFIG["MIN_RESULTS_THRESHOLD"]:
        if radius < CONFIG["MAX_RADIUS"]:
            new_radius = int(radius * 1.5)
            if new_radius > CONFIG["MAX_RADIUS"]:
                new_radius = CONFIG["MAX_RADIUS"]

            logger.info(f"{indent}[{city_name}] TOO SPARSE ({num_results} < {CONFIG['MIN_RESULTS_THRESHOLD']})")
            logger.info(f"{indent}[{city_name}] Increasing radius: {radius/1000:.1f}km → {new_radius/1000:.1f}km")

            STATS["radius_increases"] += 1
            time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])

            return adaptive_radius_search(lat, lng, keyword, new_radius, city_name, depth + 1)

    # CASE 2: Too many results → DECREASE radius (dense area)
    elif num_results > CONFIG["MAX_RESULTS_THRESHOLD"]:
        if radius > CONFIG["MIN_RADIUS"]:
            new_radius = radius // 2
            if new_radius < CONFIG["MIN_RADIUS"]:
                new_radius = CONFIG["MIN_RADIUS"]

            logger.info(f"{indent}[{city_name}] TOO DENSE ({num_results} > {CONFIG['MAX_RESULTS_THRESHOLD']})")
            logger.info(f"{indent}[{city_name}] Need to subdivide area")

            STATS["radius_decreases"] += 1

            # Subdivide into 4 quadrants
            quadrants = subdivide_area(lat, lng, radius)
            all_places = []

            for quad_lat, quad_lng, quad_radius in quadrants:
                time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])
                quad_places, _ = adaptive_radius_search(
                    quad_lat, quad_lng, keyword, quad_radius, city_name, depth + 1
                )
                all_places.extend(quad_places)

            return (all_places, new_radius)

    # CASE 3: OPTIMAL range → use results
    logger.info(f"{indent}[{city_name}] OPTIMAL range ({num_results} results with {radius/1000:.1f}km radius)")
    STATS["optimal_searches"] += 1

    return (places, radius)

def subdivide_area(lat: float, lng: float, radius: int) -> List[Tuple[float, float, int]]:
    """Subdivide area into 4 quadrants"""
    new_radius = radius // 2

    km_per_degree_lat = 111.32
    km_per_degree_lng = 111.32 * math.cos(math.radians(lat))

    offset_km = (radius / 1000) / 2
    offset_lat = offset_km / km_per_degree_lat
    offset_lng = offset_km / km_per_degree_lng

    return [
        (lat + offset_lat, lng + offset_lng, new_radius),  # NE
        (lat + offset_lat, lng - offset_lng, new_radius),  # NW
        (lat - offset_lat, lng + offset_lng, new_radius),  # SE
        (lat - offset_lat, lng - offset_lng, new_radius),  # SW
    ]

def scrape_city(city: str, keyword: str, min_reviews: int, min_rating: float, max_reviews: int = None) -> Dict:
    """Scrape single city with TIER-BASED GRID coverage - saves both raw and filtered data"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing city: {city}")
    logger.info(f"{'='*60}")

    # Geocode
    lat, lng = geocode_city(city)
    if lat == 0:
        logger.error(f"Failed to geocode {city}")
        return {
            "city": city,
            "raw_places": [],
            "filtered_places": [],
            "error": "geocoding_failed",
            "stats": {
                "total_found": 0,
                "unique": 0,
                "filtered": 0,
                "with_details": 0,
                "grid_points": 0,
                "tier": "unknown"
            }
        }

    logger.info(f"Center: {lat:.4f}, {lng:.4f}")

    # Determine tier and create grid
    tier = get_city_tier(city)
    grid_points = create_grid_points(lat, lng, tier, city)
    strategy = TIER_STRATEGIES[tier]
    radius_meters = strategy["circle_radius_km"] * 1000

    # Search all grid points
    all_places = []
    for i, (grid_lat, grid_lng) in enumerate(grid_points, 1):
        logger.info(f"  Grid point {i}/{len(grid_points)}: ({grid_lat:.4f}, {grid_lng:.4f})")
        places = nearby_search(grid_lat, grid_lng, keyword, radius_meters)
        all_places.extend(places)
        logger.info(f"    Found {len(places)} results")

        if i < len(grid_points):
            time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])

    logger.info(f"\n{city} Summary:")
    logger.info(f"  Grid points: {len(grid_points)}")
    logger.info(f"  Total places found: {len(all_places)}")

    # Deduplicate - THIS IS RAW DATA (before filtering)
    unique_places = deduplicate_places(all_places)
    logger.info(f"  Unique places: {len(unique_places)}")

    # Filter
    filtered = filter_places(unique_places, min_reviews, min_rating, max_reviews)
    logger.info(f"  After filter: {len(filtered)}")

    # Get details ONLY for filtered places (to save API calls)
    detailed_places = []
    for place in filtered:
        details = get_place_details(place["place_id"])
        if details:
            detailed_places.append({**place, **details})
        time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])

    STATS["cities_processed"] += 1

    # Return BOTH raw (unique_places) and filtered (detailed_places)
    return {
        "city": city,
        "raw_places": unique_places,          # RAW data (no phone/website)
        "filtered_places": detailed_places,   # FILTERED data (with phone/website)
        "stats": {
            "total_found": len(all_places),
            "unique": len(unique_places),
            "filtered": len(filtered),
            "with_details": len(detailed_places),
            "grid_points": len(grid_points),
            "tier": tier,
            "radius_km": strategy["circle_radius_km"]
        }
    }

def deduplicate_places(places: List[Dict]) -> List[Dict]:
    """Remove duplicates by place_id"""
    seen = set()
    unique = []
    for place in places:
        place_id = place.get("place_id")
        if place_id and place_id not in seen:
            seen.add(place_id)
            unique.append(place)
    return unique

def filter_places(places: List[Dict], min_reviews: int, min_rating: float, max_reviews: int = None) -> List[Dict]:
    """Filter by reviews and rating"""
    filtered = []
    for p in places:
        if p["business_status"] != "OPERATIONAL":
            continue
        if p["user_ratings_total"] < min_reviews:
            continue
        if p["rating"] < min_rating:
            continue
        if max_reviews and p["user_ratings_total"] > max_reviews:
            continue
        filtered.append(p)
    return filtered

def get_place_details(place_id: str) -> Dict:
    """Get phone and website"""
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,website,formatted_address",
        "key": CONFIG["API_KEY"]
    }

    response = requests.get(CONFIG["PLACE_DETAILS_URL"], params=params)
    STATS["total_api_calls"] += 1

    if response.status_code != 200 or response.json()["status"] != "OK":
        return {}

    result = response.json().get("result", {})
    return {
        "phone": result.get("formatted_phone_number", ""),
        "website": result.get("website", ""),
        "address": result.get("formatted_address", "")
    }

def extract_state_from_cities(cities: List[str]) -> str:
    """Detect state from city list"""
    if not cities:
        return "unknown"

    first_city = cities[0]
    if ", TX" in first_city:
        return "texas"
    elif ", FL" in first_city:
        return "florida"
    elif ", NY" in first_city:
        return "new_york"
    elif ", IL" in first_city:
        return "illinois"
    elif ", MI" in first_city:
        return "michigan"
    elif ", PA" in first_city:
        return "pennsylvania"

    return "unknown"

def extract_niche_from_keyword(keyword: str) -> str:
    """Extract niche name from keyword"""
    keyword_lower = keyword.lower()

    if "hvac" in keyword_lower:
        return "hvac"
    elif "plumb" in keyword_lower:
        return "plumbers"
    elif "electric" in keyword_lower:
        return "electricians"
    elif "locksmith" in keyword_lower:
        return "locksmiths"
    elif "towing" in keyword_lower or "tow service" in keyword_lower:
        return "towing"
    elif "garage" in keyword_lower or "door" in keyword_lower:
        return "garage_door"

    # Fallback: sanitize keyword
    return keyword_lower.replace(" ", "_")

def main():
    parser = argparse.ArgumentParser(description="Google Places Statewide Scraper")
    parser.add_argument("--city", type=str, help="Single city to scrape")
    parser.add_argument("--cities", type=str, help="Comma-separated cities")
    parser.add_argument("--state", type=str, choices=["Texas", "Florida", "New York", "Illinois", "Michigan", "Pennsylvania"], help="Scrape entire state")
    parser.add_argument("--keyword", type=str, required=True, help="Search keyword")
    parser.add_argument("--min-reviews", type=int, default=10, help="Min reviews")
    parser.add_argument("--max-reviews", type=int, default=None, help="Max reviews (optional)")
    parser.add_argument("--min-rating", type=float, default=4.0, help="Min rating")
    parser.add_argument("--max-results", type=int, default=5000, help="Max total results")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel processing")
    args = parser.parse_args()

    if not CONFIG["API_KEY"]:
        logger.error("GOOGLE_PLACES_API_KEY not found")
        return

    # Determine cities to scrape
    if args.city:
        cities = [args.city]
    elif args.cities:
        cities = [c.strip() for c in args.cities.split(",")]
    elif args.state:
        cities = STATE_CITIES.get(args.state, [])
        if not cities:
            logger.error(f"No cities defined for state: {args.state}")
            return
    else:
        logger.error("Must specify --city, --cities, or --state")
        return

    print(f"\n{'='*70}")
    print(f"GOOGLE PLACES STATEWIDE SCRAPER")
    print(f"{'='*70}")
    print(f"Cities to process: {len(cities)}")
    print(f"Keyword:           {args.keyword}")
    print(f"Parallel mode:     {'ON' if args.parallel else 'OFF'}")
    print(f"Filters:")
    print(f"  Min reviews:     {args.min_reviews}")
    print(f"  Max reviews:     {args.max_reviews if args.max_reviews else 'No limit'}")
    print(f"  Min rating:      {args.min_rating}")
    print(f"\nAdaptive radius:")
    print(f"  Initial:         {CONFIG['INITIAL_RADIUS']/1000}km")
    print(f"  Range:           {CONFIG['MIN_RADIUS']/1000}km - {CONFIG['MAX_RADIUS']/1000}km")
    print(f"  Sparse (<15):    INCREASE radius")
    print(f"  Optimal (15-55): USE results")
    print(f"  Dense (>55):     DECREASE radius")
    print(f"{'='*70}\n")

    start_time = time.time()

    # Scrape cities
    results_by_city = []

    if args.parallel and len(cities) > 1:
        print(f"Processing {len(cities)} cities in PARALLEL (max {CONFIG['MAX_WORKERS']} workers)...\n")

        with ThreadPoolExecutor(max_workers=CONFIG['MAX_WORKERS']) as executor:
            futures = {
                executor.submit(scrape_city, city, args.keyword, args.min_reviews, args.min_rating, args.max_reviews): city
                for city in cities
            }

            for future in as_completed(futures):
                city = futures[future]
                try:
                    result = future.result()
                    results_by_city.append(result)
                except Exception as e:
                    logger.error(f"Error processing {city}: {e}")
    else:
        print(f"Processing {len(cities)} cities SEQUENTIALLY...\n")

        for city in cities:
            result = scrape_city(city, args.keyword, args.min_reviews, args.min_rating, args.max_reviews)
            results_by_city.append(result)

    # Detect state and niche for organized folders
    state = extract_state_from_cities(cities)
    niche = extract_niche_from_keyword(args.keyword)

    # Aggregate RAW and FILTERED data separately
    all_raw_places = []
    all_filtered_places = []

    for city_result in results_by_city:
        all_raw_places.extend(city_result.get("raw_places", []))
        all_filtered_places.extend(city_result.get("filtered_places", []))

    # Global deduplication for both datasets
    all_raw_places = deduplicate_places(all_raw_places)
    all_filtered_places = deduplicate_places(all_filtered_places)

    # Create organized folder structure
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(CONFIG["OUTPUT_DIR"]) / state
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save RAW data (no phone/website, can re-filter later)
    raw_file = output_dir / f"{niche}_raw_{timestamp}.json"
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "timestamp": timestamp,
                "state": state,
                "niche": niche,
                "cities_processed": len(cities),
                "total_raw_places": len(all_raw_places),
                "note": "RAW data before filtering - no phone/website to save API costs",
                "stats": STATS
            },
            "results_by_city": [
                {
                    "city": r["city"],
                    "raw_places": r.get("raw_places", []),
                    "stats": r["stats"]
                }
                for r in results_by_city
            ],
            "all_raw_places": all_raw_places
        }, f, indent=2, ensure_ascii=False)

    # Save FILTERED data (with phone/website)
    filtered_file = output_dir / f"{niche}_{timestamp}.json"
    with open(filtered_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "timestamp": timestamp,
                "state": state,
                "niche": niche,
                "cities_processed": len(cities),
                "total_filtered_places": len(all_filtered_places),
                "filters": {
                    "min_reviews": args.min_reviews,
                    "max_reviews": args.max_reviews,
                    "min_rating": args.min_rating
                },
                "note": "FILTERED data with phone/website - ready for outreach",
                "stats": STATS
            },
            "results_by_city": [
                {
                    "city": r["city"],
                    "filtered_places": r.get("filtered_places", []),
                    "stats": r["stats"]
                }
                for r in results_by_city
            ],
            "all_filtered_places": all_filtered_places
        }, f, indent=2, ensure_ascii=False)

    # Summary
    elapsed = (time.time() - start_time) / 60
    STATS["total_cost"] = (STATS["total_api_calls"] / 1000) * 27.5  # Avg cost

    print(f"\n{'='*70}")
    print(f"STATEWIDE SCRAPING COMPLETED")
    print(f"{'='*70}")
    print(f"State:               {state.upper()}")
    print(f"Niche:               {niche.upper()}")
    print(f"Cities processed:    {len(cities)}")
    print(f"\nData collected:")
    print(f"  RAW places:        {len(all_raw_places)} (can re-filter later)")
    print(f"  FILTERED places:   {len(all_filtered_places)} (ready for outreach)")
    print(f"\nAdaptive strategy:")
    print(f"  Radius increases:  {STATS['radius_increases']}")
    print(f"  Radius decreases:  {STATS['radius_decreases']}")
    print(f"  Optimal searches:  {STATS['optimal_searches']}")
    print(f"\nAPI calls:           {STATS['total_api_calls']}")
    print(f"Estimated cost:      ${STATS['total_cost']:.2f}")
    print(f"Free tier left:      ${200 - STATS['total_cost']:.2f}")
    print(f"Time elapsed:        {elapsed:.1f} min")
    print(f"\nOutput files:")
    print(f"  RAW data:          {raw_file}")
    print(f"  FILTERED data:     {filtered_file}")
    print(f"{'='*70}\n")

    # City breakdown
    print("=== CITY BREAKDOWN (Top 10) ===\n")
    sorted_cities = sorted(results_by_city, key=lambda x: x['stats']['with_details'], reverse=True)
    for city_result in sorted_cities[:10]:
        raw_count = len(city_result.get('raw_places', []))
        filtered_count = city_result['stats']['with_details']
        print(f"{city_result['city']:<25} RAW: {raw_count:>4}  |  FILTERED: {filtered_count:>4}  (radius: {city_result['stats']['final_radius_km']:.1f}km)")

if __name__ == "__main__":
    main()
