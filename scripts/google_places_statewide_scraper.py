#!/usr/bin/env python3
"""
=== GOOGLE PLACES STATEWIDE SCRAPER ===
Version: 4.0.0 | Created: 2025-11-09

BIDIRECTIONAL ADAPTIVE RADIUS:
- Too few results (< 15) → INCREASE radius (sparse desert area)
- Optimal (15-55) → USE results
- Too many (> 55) → DECREASE radius (dense city area)

STATEWIDE STRATEGY:
- Scrape multiple cities in parallel
- Each city uses adaptive radius
- Auto-discovers optimal coverage

USAGE:
# Single city:
python google_places_statewide_scraper.py --city "Houston, TX" --keyword "HVAC" --max-results 500

# Multiple cities (parallel):
python google_places_statewide_scraper.py --state "Texas" --keyword "HVAC" --max-results 5000

# Custom city list:
python google_places_statewide_scraper.py --cities "Houston,Dallas,Austin" --keyword "HVAC"
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
    "OUTPUT_DIR": "data/processed",
    "DELAY_BETWEEN_REQUESTS": 0.5,

    # Bidirectional adaptation thresholds
    "MIN_RESULTS_THRESHOLD": 15,   # If < 15, increase radius
    "MAX_RESULTS_THRESHOLD": 55,   # If > 55, decrease radius
    "OPTIMAL_RANGE": (15, 55),     # Optimal results range

    # Radius limits
    "INITIAL_RADIUS": 15000,       # Start with 15km
    "MIN_RADIUS": 3000,            # Minimum 3km
    "MAX_RADIUS": 100000,          # Maximum 100km (for sparse desert)

    # Parallel processing
    "MAX_WORKERS": 5,              # Process 5 cities simultaneously
}

# Major Texas cities for statewide scraping
TEXAS_CITIES = [
    "Houston, TX", "Dallas, TX", "Austin, TX", "San Antonio, TX",
    "Fort Worth, TX", "El Paso, TX", "Arlington, TX", "Corpus Christi, TX",
    "Plano, TX", "Laredo, TX", "Lubbock, TX", "Irving, TX",
    "Garland, TX", "Frisco, TX", "McKinney, TX", "Amarillo, TX",
    "Grand Prairie, TX", "Brownsville, TX", "Pasadena, TX", "Mesquite, TX"
]

STATS = {
    "total_api_calls": 0,
    "radius_increases": 0,
    "radius_decreases": 0,
    "optimal_searches": 0,
    "cities_processed": 0,
    "total_cost": 0.0,
}

def geocode_city(city: str) -> Tuple[float, float]:
    """Get lat/lng for city"""
    params = {"address": city, "key": CONFIG["API_KEY"]}
    response = requests.get(CONFIG["GEOCODE_URL"], params=params)

    if response.status_code != 200 or response.json()["status"] != "OK":
        return (0, 0)

    location = response.json()["results"][0]["geometry"]["location"]
    return (location["lat"], location["lng"])

def nearby_search(lat: float, lng: float, keyword: str, radius: int) -> List[Dict]:
    """Search places in radius"""
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": CONFIG["API_KEY"]
    }

    response = requests.get(CONFIG["NEARBY_SEARCH_URL"], params=params)
    STATS["total_api_calls"] += 1

    if response.status_code != 200:
        return []

    data = response.json()
    if data["status"] not in ["OK", "ZERO_RESULTS"]:
        return []

    results = data.get("results", [])

    return [{
        "place_id": p.get("place_id"),
        "name": p.get("name"),
        "vicinity": p.get("vicinity", ""),
        "rating": p.get("rating", 0),
        "user_ratings_total": p.get("user_ratings_total", 0),
        "business_status": p.get("business_status", ""),
    } for p in results]

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

def scrape_city(city: str, keyword: str, min_reviews: int, min_rating: float) -> Dict:
    """Scrape single city with adaptive radius"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing city: {city}")
    logger.info(f"{'='*60}")

    # Geocode
    lat, lng = geocode_city(city)
    if lat == 0:
        logger.error(f"Failed to geocode {city}")
        return {"city": city, "places": [], "error": "geocoding_failed"}

    logger.info(f"Center: {lat:.4f}, {lng:.4f}")

    # Adaptive search
    places, final_radius = adaptive_radius_search(
        lat, lng, keyword, CONFIG["INITIAL_RADIUS"], city
    )

    logger.info(f"\n{city} Summary:")
    logger.info(f"  Places found: {len(places)}")
    logger.info(f"  Final radius: {final_radius/1000:.1f}km")

    # Deduplicate
    unique_places = deduplicate_places(places)

    # Filter
    filtered = filter_places(unique_places, min_reviews, min_rating)

    logger.info(f"  After filter: {len(filtered)}")

    # Get details
    detailed_places = []
    for place in filtered:
        details = get_place_details(place["place_id"])
        if details:
            detailed_places.append({**place, **details})
        time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])

    STATS["cities_processed"] += 1

    return {
        "city": city,
        "places": detailed_places,
        "stats": {
            "total_found": len(places),
            "unique": len(unique_places),
            "filtered": len(filtered),
            "with_details": len(detailed_places),
            "final_radius_km": final_radius / 1000
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

def filter_places(places: List[Dict], min_reviews: int, min_rating: float) -> List[Dict]:
    """Filter by reviews and rating"""
    return [p for p in places
            if p["business_status"] == "OPERATIONAL"
            and p["user_ratings_total"] >= min_reviews
            and p["rating"] >= min_rating]

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

def main():
    parser = argparse.ArgumentParser(description="Google Places Statewide Scraper")
    parser.add_argument("--city", type=str, help="Single city to scrape")
    parser.add_argument("--cities", type=str, help="Comma-separated cities")
    parser.add_argument("--state", type=str, choices=["Texas"], help="Scrape entire state")
    parser.add_argument("--keyword", type=str, required=True, help="Search keyword")
    parser.add_argument("--min-reviews", type=int, default=10, help="Min reviews")
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
    elif args.state == "Texas":
        cities = TEXAS_CITIES
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
                executor.submit(scrape_city, city, args.keyword, args.min_reviews, args.min_rating): city
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
            result = scrape_city(city, args.keyword, args.min_reviews, args.min_rating)
            results_by_city.append(result)

    # Aggregate all places
    all_places = []
    for city_result in results_by_city:
        all_places.extend(city_result["places"])

    # Global dedup
    all_places = deduplicate_places(all_places)

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(CONFIG["OUTPUT_DIR"]) / f"google_statewide_{timestamp}.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "metadata": {
                "timestamp": timestamp,
                "cities_processed": len(cities),
                "total_places": len(all_places),
                "stats": STATS
            },
            "results_by_city": results_by_city,
            "all_places": all_places
        }, f, indent=2, ensure_ascii=False)

    # Summary
    elapsed = (time.time() - start_time) / 60
    STATS["total_cost"] = (STATS["total_api_calls"] / 1000) * 27.5  # Avg cost

    print(f"\n{'='*70}")
    print(f"STATEWIDE SCRAPING COMPLETED")
    print(f"{'='*70}")
    print(f"Cities processed:    {len(cities)}")
    print(f"Total places:        {len(all_places)}")
    print(f"\nAdaptive strategy:")
    print(f"  Radius increases:  {STATS['radius_increases']}")
    print(f"  Radius decreases:  {STATS['radius_decreases']}")
    print(f"  Optimal searches:  {STATS['optimal_searches']}")
    print(f"\nAPI calls:           {STATS['total_api_calls']}")
    print(f"Estimated cost:      ${STATS['total_cost']:.2f}")
    print(f"Free tier left:      ${200 - STATS['total_cost']:.2f}")
    print(f"Time elapsed:        {elapsed:.1f} min")
    print(f"Output file:         {output_file}")
    print(f"{'='*70}\n")

    # City breakdown
    print("=== CITY BREAKDOWN ===\n")
    for city_result in results_by_city[:10]:
        print(f"{city_result['city']:<25} {city_result['stats']['with_details']:>4} places (radius: {city_result['stats']['final_radius_km']:.1f}km)")

if __name__ == "__main__":
    main()
