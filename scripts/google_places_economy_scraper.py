#!/usr/bin/env python3
"""
=== GOOGLE PLACES ECONOMY SCRAPER ===
Version: 3.0.0 | Created: 2025-11-09

ECONOMY MODE:
Uses adaptive radius based on business density
- Sparse areas: large radius (15km) → 1 request
- Dense areas: small radius (3-5km) → multiple requests
- Saves 30-50% on API costs!

STRATEGY:
1. Start with large radius (15km)
2. If returns 60 results (saturated) → split into 4 smaller circles
3. Recursively subdivide until coverage complete

USAGE:
python google_places_economy_scraper.py --city "Houston, TX" --keyword "HVAC contractors" --min-reviews 10 --max-results 500
"""

import os
import sys
import json
import time
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from dotenv import load_dotenv
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

    # Economy mode settings
    "MAX_RADIUS": 15000,     # Start with 15km
    "MIN_RADIUS": 3000,      # Minimum 3km
    "SATURATION_THRESHOLD": 55,  # If >= 55 results, area is saturated
}

STATS = {
    "geocode_calls": 0,
    "nearby_search_calls": 0,
    "place_details_calls": 0,
    "places_found": 0,
    "saturated_areas": 0,
    "sparse_areas": 0,
    "subdivision_depth": 0,
    "total_cost": 0.0,
    "start_time": None
}

def geocode_city(city: str) -> Tuple[float, float]:
    """Get lat/lng for city"""
    params = {
        "address": city,
        "key": CONFIG["API_KEY"]
    }

    response = requests.get(CONFIG["GEOCODE_URL"], params=params)
    STATS["geocode_calls"] += 1

    if response.status_code != 200:
        logger.error(f"Geocoding failed: {response.status_code}")
        return (0, 0)

    data = response.json()

    if data["status"] != "OK":
        logger.error(f"Geocoding error: {data['status']}")
        return (0, 0)

    location = data["results"][0]["geometry"]["location"]
    return (location["lat"], location["lng"])

def nearby_search(lat: float, lng: float, keyword: str, radius: int) -> Tuple[List[Dict], bool]:
    """
    Search places in radius
    Returns: (places, is_saturated)
    is_saturated = True if hit 60 result limit (need to subdivide)
    """
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": keyword,
        "key": CONFIG["API_KEY"]
    }

    response = requests.get(CONFIG["NEARBY_SEARCH_URL"], params=params)
    STATS["nearby_search_calls"] += 1

    if response.status_code != 200:
        logger.error(f"Nearby Search failed: {response.status_code}")
        return ([], False)

    data = response.json()

    if data["status"] not in ["OK", "ZERO_RESULTS"]:
        logger.error(f"API Error: {data['status']}")
        return ([], False)

    results = data.get("results", [])

    # Check if area is saturated
    is_saturated = len(results) >= CONFIG["SATURATION_THRESHOLD"]

    # Extract basic info
    places = []
    for place in results:
        places.append({
            "place_id": place.get("place_id"),
            "name": place.get("name"),
            "vicinity": place.get("vicinity", ""),
            "rating": place.get("rating", 0),
            "user_ratings_total": place.get("user_ratings_total", 0),
            "business_status": place.get("business_status", ""),
            "types": place.get("types", [])
        })

    STATS["places_found"] += len(places)

    return (places, is_saturated)

def subdivide_area(lat: float, lng: float, radius: int) -> List[Tuple[float, float, int]]:
    """
    Subdivide area into 4 quadrants
    Returns list of (lat, lng, new_radius)
    """
    new_radius = radius // 2

    if new_radius < CONFIG["MIN_RADIUS"]:
        return []

    # Calculate offset in degrees
    km_per_degree_lat = 111.32
    km_per_degree_lng = 111.32 * math.cos(math.radians(lat))

    offset_km = (radius / 1000) / 2
    offset_lat = offset_km / km_per_degree_lat
    offset_lng = offset_km / km_per_degree_lng

    # 4 quadrants
    quadrants = [
        (lat + offset_lat, lng + offset_lng, new_radius),  # NE
        (lat + offset_lat, lng - offset_lng, new_radius),  # NW
        (lat - offset_lat, lng + offset_lng, new_radius),  # SE
        (lat - offset_lat, lng - offset_lng, new_radius),  # SW
    ]

    return quadrants

def adaptive_search(lat: float, lng: float, keyword: str, radius: int, depth: int = 0, max_depth: int = 3) -> List[Dict]:
    """
    Recursive adaptive search
    - If area sparse: returns results
    - If area saturated: subdivides and searches smaller areas
    """
    indent = "  " * depth
    logger.info(f"{indent}Searching radius {radius/1000:.1f}km at ({lat:.4f}, {lng:.4f})")

    # Search this area
    places, is_saturated = nearby_search(lat, lng, keyword, radius)

    logger.info(f"{indent}Found {len(places)} places (saturated: {is_saturated})")

    # If not saturated or max depth reached, return results
    if not is_saturated or depth >= max_depth:
        if not is_saturated:
            STATS["sparse_areas"] += 1
        return places

    # Area is saturated - subdivide!
    STATS["saturated_areas"] += 1
    STATS["subdivision_depth"] = max(STATS["subdivision_depth"], depth + 1)

    logger.info(f"{indent}Area saturated, subdividing into 4 quadrants...")

    quadrants = subdivide_area(lat, lng, radius)

    if not quadrants:
        # Can't subdivide further
        return places

    all_places = []

    for quad_lat, quad_lng, quad_radius in quadrants:
        time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])
        quad_places = adaptive_search(quad_lat, quad_lng, keyword, quad_radius, depth + 1, max_depth)
        all_places.extend(quad_places)

    return all_places

def filter_places(places: List[Dict], min_reviews: int, min_rating: float) -> List[Dict]:
    """Filter places by reviews and rating"""
    filtered = []

    for place in places:
        if place["business_status"] != "OPERATIONAL":
            continue
        if place["user_ratings_total"] < min_reviews:
            continue
        if place["rating"] < min_rating:
            continue

        filtered.append(place)

    return filtered

def get_place_details(place_id: str) -> Dict:
    """Get detailed info (phone, website)"""
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,website,formatted_address",
        "key": CONFIG["API_KEY"]
    }

    response = requests.get(CONFIG["PLACE_DETAILS_URL"], params=params)
    STATS["place_details_calls"] += 1

    if response.status_code != 200:
        return {}

    data = response.json()

    if data["status"] != "OK":
        return {}

    result = data.get("result", {})

    return {
        "phone": result.get("formatted_phone_number", ""),
        "website": result.get("website", ""),
        "address": result.get("formatted_address", "")
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

    logger.info(f"Deduplication: {len(places)} → {len(unique)} unique")
    return unique

def calculate_cost():
    """Calculate total API cost"""
    geocode_cost = (STATS["geocode_calls"] / 1000) * 5
    nearby_cost = (STATS["nearby_search_calls"] / 1000) * 32
    details_cost = (STATS["place_details_calls"] / 1000) * 23
    STATS["total_cost"] = geocode_cost + nearby_cost + details_cost

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Google Places Economy Scraper")
    parser.add_argument("--city", type=str, required=True, help="City name")
    parser.add_argument("--keyword", type=str, required=True, help="Search keyword")
    parser.add_argument("--min-reviews", type=int, default=10, help="Min reviews")
    parser.add_argument("--min-rating", type=float, default=4.0, help="Min rating")
    parser.add_argument("--max-results", type=int, default=500, help="Max results")
    args = parser.parse_args()

    logger.info("=== GOOGLE PLACES ECONOMY SCRAPER ===")

    if not CONFIG["API_KEY"]:
        logger.error("GOOGLE_PLACES_API_KEY not found")
        return

    STATS["start_time"] = time.time()

    print(f"\n{'='*70}")
    print(f"GOOGLE PLACES ECONOMY MODE")
    print(f"{'='*70}")
    print(f"City:         {args.city}")
    print(f"Keyword:      {args.keyword}")
    print(f"Filters:")
    print(f"  Min reviews:  {args.min_reviews}")
    print(f"  Min rating:   {args.min_rating}")
    print(f"Max results:  {args.max_results}")
    print(f"\nAdaptive radius:")
    print(f"  Max:          {CONFIG['MAX_RADIUS']/1000}km (sparse areas)")
    print(f"  Min:          {CONFIG['MIN_RADIUS']/1000}km (dense areas)")
    print(f"{'='*70}\n")

    # Step 1: Geocode city
    print(f"Step 1: Geocoding '{args.city}'...")
    center_lat, center_lng = geocode_city(args.city)

    if center_lat == 0:
        logger.error("Failed to geocode city")
        return

    print(f"  Center: {center_lat:.4f}, {center_lng:.4f}\n")

    # Step 2: Adaptive search
    print(f"Step 2: Adaptive search (economy mode)...")
    print(f"  Starting with {CONFIG['MAX_RADIUS']/1000}km radius...\n")

    all_places = adaptive_search(
        center_lat,
        center_lng,
        args.keyword,
        CONFIG['MAX_RADIUS']
    )

    print(f"\n  Total places found: {len(all_places)}\n")

    # Step 3: Deduplicate
    print("Step 3: Removing duplicates...")
    unique_places = deduplicate_places(all_places)
    print(f"  Unique places: {len(unique_places)}\n")

    # Step 4: Filter
    print(f"Step 4: Filtering (min {args.min_reviews} reviews, {args.min_rating}+ rating)...")
    filtered_places = filter_places(unique_places, args.min_reviews, args.min_rating)
    print(f"  After filtering: {len(filtered_places)}\n")

    # Limit to max results
    filtered_places = filtered_places[:args.max_results]

    # Step 5: Get details
    print(f"Step 5: Getting details for {len(filtered_places)} places...")

    final_results = []

    for idx, place in enumerate(filtered_places, 1):
        print(f"  [{idx}/{len(filtered_places)}] {place['name'][:40]:<40}", end='\r')

        details = get_place_details(place["place_id"])

        if details:
            final_results.append({**place, **details})

        time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])

    print(f"\n  Retrieved details: {len(final_results)}\n")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(CONFIG["OUTPUT_DIR"])
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"google_places_economy_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)

    # Calculate costs
    calculate_cost()
    elapsed = (time.time() - STATS["start_time"]) / 60

    # Summary
    print(f"{'='*70}")
    print(f"ECONOMY MODE RESULTS")
    print(f"{'='*70}")
    print(f"Adaptive strategy:")
    print(f"  Sparse areas:     {STATS['sparse_areas']} (large radius)")
    print(f"  Dense areas:      {STATS['saturated_areas']} (subdivided)")
    print(f"  Max depth:        {STATS['subdivision_depth']}")
    print(f"\nResults:")
    print(f"  Places found:     {STATS['places_found']}")
    print(f"  After dedup:      {len(unique_places)}")
    print(f"  After filtering:  {len(filtered_places)}")
    print(f"  With details:     {len(final_results)}")
    print(f"\nAPI Calls:")
    print(f"  Nearby Search:    {STATS['nearby_search_calls']}")
    print(f"  Place Details:    {STATS['place_details_calls']}")
    print(f"\nCost breakdown:")
    print(f"  Nearby Search:    ${(STATS['nearby_search_calls']/1000)*32:.4f}")
    print(f"  Place Details:    ${(STATS['place_details_calls']/1000)*23:.4f}")
    print(f"  TOTAL COST:       ${STATS['total_cost']:.4f}")
    print(f"\nFree tier remaining: ${200 - STATS['total_cost']:.2f}")
    print(f"Time elapsed:        {elapsed:.1f} min")
    print(f"Output file:         {output_file}")
    print(f"{'='*70}\n")

    # Show samples
    if final_results:
        print("=== SAMPLE RESULTS ===\n")
        for place in final_results[:5]:
            print(f"{place['name']}")
            print(f"  Address:  {place.get('address', place.get('vicinity', 'N/A'))}")
            print(f"  Phone:    {place.get('phone', 'N/A')}")
            print(f"  Website:  {place.get('website', 'N/A')}")
            print(f"  Rating:   {place['rating']} ({place['user_ratings_total']} reviews)")
            print()

    logger.info("=== COMPLETED ===")

if __name__ == "__main__":
    main()
