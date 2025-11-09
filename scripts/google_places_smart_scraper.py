#!/usr/bin/env python3
"""
=== GOOGLE PLACES SMART SCRAPER ===
Version: 2.0.0 | Created: 2025-11-09

FEATURES:
1. Geographic Grid Coverage - covers entire area with overlapping circles
2. Two-Stage Filtering - filter BEFORE expensive Place Details calls
3. Cost Optimization - save ~50% by filtering early

STRATEGY:
Stage 1: Nearby Search (cheap)
  - Get basic info: name, rating, reviews count
  - Filter by: min reviews, min rating, business status
  - Cost: $32/1000 requests

Stage 2: Place Details (expensive)
  - Only for filtered places
  - Get: phone, website
  - Cost: $23/1000 requests

USAGE:
python google_places_smart_scraper.py --city "Houston, TX" --keyword "HVAC contractors" --min-reviews 10 --min-rating 4.0 --max-results 500
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
    "RADIUS_METERS": 5000,  # 5km radius per search
    "GRID_OVERLAP": 0.7     # 30% overlap between circles
}

STATS = {
    "geocode_calls": 0,
    "nearby_search_calls": 0,
    "place_details_calls": 0,
    "places_found": 0,
    "places_filtered_out": 0,
    "places_with_details": 0,
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

def create_search_grid(center_lat: float, center_lng: float, radius_km: int = 10) -> List[Tuple[float, float]]:
    """
    Create grid of search points to cover area

    Returns list of (lat, lng) coordinates
    """
    search_radius_km = CONFIG["RADIUS_METERS"] / 1000
    step_km = search_radius_km * CONFIG["GRID_OVERLAP"]

    # Calculate grid size
    km_per_degree_lat = 111.32
    km_per_degree_lng = 111.32 * math.cos(math.radians(center_lat))

    step_lat = step_km / km_per_degree_lat
    step_lng = step_km / km_per_degree_lng

    grid_points = []

    # Create grid
    lat = center_lat - (radius_km / km_per_degree_lat)
    while lat <= center_lat + (radius_km / km_per_degree_lat):
        lng = center_lng - (radius_km / km_per_degree_lng)
        while lng <= center_lng + (radius_km / km_per_degree_lng):
            grid_points.append((lat, lng))
            lng += step_lng
        lat += step_lat

    logger.info(f"Created grid with {len(grid_points)} search points")
    return grid_points

def nearby_search(lat: float, lng: float, keyword: str) -> List[Dict]:
    """
    Stage 1: Get basic place info using Nearby Search
    Returns: Basic info including rating and reviews
    """
    params = {
        "location": f"{lat},{lng}",
        "radius": CONFIG["RADIUS_METERS"],
        "keyword": keyword,
        "key": CONFIG["API_KEY"]
    }

    response = requests.get(CONFIG["NEARBY_SEARCH_URL"], params=params)
    STATS["nearby_search_calls"] += 1

    if response.status_code != 200:
        logger.error(f"Nearby Search failed: {response.status_code}")
        return []

    data = response.json()

    if data["status"] not in ["OK", "ZERO_RESULTS"]:
        logger.error(f"API Error: {data['status']}")
        return []

    results = data.get("results", [])

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
    return places

def filter_places(places: List[Dict], min_reviews: int, min_rating: float) -> List[Dict]:
    """
    Filter places by reviews and rating BEFORE calling Place Details
    Saves money on Place Details calls!
    """
    filtered = []

    for place in places:
        # Filter by business status
        if place["business_status"] != "OPERATIONAL":
            STATS["places_filtered_out"] += 1
            continue

        # Filter by reviews count
        if place["user_ratings_total"] < min_reviews:
            STATS["places_filtered_out"] += 1
            continue

        # Filter by rating
        if place["rating"] < min_rating:
            STATS["places_filtered_out"] += 1
            continue

        filtered.append(place)

    return filtered

def get_place_details(place_id: str) -> Dict:
    """
    Stage 2: Get detailed info (phone, website) only for filtered places
    """
    params = {
        "place_id": place_id,
        "fields": "formatted_phone_number,website,formatted_address",
        "key": CONFIG["API_KEY"]
    }

    response = requests.get(CONFIG["PLACE_DETAILS_URL"], params=params)
    STATS["place_details_calls"] += 1

    if response.status_code != 200:
        logger.error(f"Place Details failed: {response.status_code}")
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
    """Remove duplicate places by place_id"""
    seen = set()
    unique = []

    for place in places:
        place_id = place.get("place_id")
        if place_id and place_id not in seen:
            seen.add(place_id)
            unique.append(place)

    logger.info(f"Deduplication: {len(places)} → {len(unique)} unique places")
    return unique

def calculate_cost():
    """Calculate total API cost"""
    geocode_cost = (STATS["geocode_calls"] / 1000) * 5
    nearby_cost = (STATS["nearby_search_calls"] / 1000) * 32
    details_cost = (STATS["place_details_calls"] / 1000) * 23
    STATS["total_cost"] = geocode_cost + nearby_cost + details_cost

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Google Places Smart Scraper")
    parser.add_argument("--city", type=str, required=True, help="City name (e.g., 'Houston, TX')")
    parser.add_argument("--keyword", type=str, required=True, help="Search keyword (e.g., 'HVAC contractors')")
    parser.add_argument("--min-reviews", type=int, default=10, help="Minimum reviews (default: 10)")
    parser.add_argument("--min-rating", type=float, default=4.0, help="Minimum rating (default: 4.0)")
    parser.add_argument("--max-results", type=int, default=500, help="Max results (default: 500)")
    parser.add_argument("--radius-km", type=int, default=10, help="Search radius from city center (km)")
    args = parser.parse_args()

    logger.info("=== GOOGLE PLACES SMART SCRAPER ===")

    if not CONFIG["API_KEY"]:
        logger.error("GOOGLE_PLACES_API_KEY not found in .env")
        return

    STATS["start_time"] = time.time()

    print(f"\n{'='*70}")
    print(f"GOOGLE PLACES SMART SCRAPER")
    print(f"{'='*70}")
    print(f"City:         {args.city}")
    print(f"Keyword:      {args.keyword}")
    print(f"Filters:")
    print(f"  Min reviews:  {args.min_reviews}")
    print(f"  Min rating:   {args.min_rating}")
    print(f"Max results:  {args.max_results}")
    print(f"Radius:       {args.radius_km} km")
    print(f"{'='*70}\n")

    # Step 1: Geocode city
    print(f"Step 1: Geocoding '{args.city}'...")
    center_lat, center_lng = geocode_city(args.city)

    if center_lat == 0:
        logger.error("Failed to geocode city")
        return

    print(f"  Center: {center_lat:.4f}, {center_lng:.4f}\n")

    # Step 2: Create search grid
    print(f"Step 2: Creating geographic search grid...")
    grid_points = create_search_grid(center_lat, center_lng, args.radius_km)
    print(f"  Grid points: {len(grid_points)}\n")

    # Step 3: Nearby Search for each grid point
    print(f"Step 3: Searching {len(grid_points)} grid points...")
    all_places = []

    for idx, (lat, lng) in enumerate(grid_points, 1):
        print(f"  [{idx}/{len(grid_points)}] Searching {lat:.4f}, {lng:.4f}...", end='\r')

        places = nearby_search(lat, lng, args.keyword)
        all_places.extend(places)

        time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])

        # Stop if we have enough
        if len(all_places) >= args.max_results * 2:  # 2x buffer for filtering
            break

    print(f"\n  Found {len(all_places)} places (with duplicates)\n")

    # Step 4: Deduplicate
    print("Step 4: Removing duplicates...")
    unique_places = deduplicate_places(all_places)
    print(f"  Unique places: {len(unique_places)}\n")

    # Step 5: Filter by reviews and rating
    print(f"Step 5: Filtering (min {args.min_reviews} reviews, {args.min_rating}+ rating)...")
    filtered_places = filter_places(unique_places, args.min_reviews, args.min_rating)
    print(f"  After filtering: {len(filtered_places)}")
    print(f"  Filtered out: {STATS['places_filtered_out']}\n")

    # Limit to max results
    filtered_places = filtered_places[:args.max_results]

    # Step 6: Get Place Details only for filtered places
    print(f"Step 6: Getting details for {len(filtered_places)} filtered places...")

    final_results = []

    for idx, place in enumerate(filtered_places, 1):
        print(f"  [{idx}/{len(filtered_places)}] {place['name'][:40]:<40}", end='\r')

        details = get_place_details(place["place_id"])

        if details:
            final_results.append({
                **place,
                **details
            })
            STATS["places_with_details"] += 1

        time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])

    print(f"\n  Retrieved details: {len(final_results)}\n")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(CONFIG["OUTPUT_DIR"])
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"google_places_smart_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)

    # Calculate costs
    calculate_cost()
    elapsed = (time.time() - STATS["start_time"]) / 60

    # Summary
    print(f"{'='*70}")
    print(f"SCRAPING COMPLETED")
    print(f"{'='*70}")
    print(f"Search points:      {len(grid_points)}")
    print(f"Places found:       {STATS['places_found']}")
    print(f"After dedup:        {len(unique_places)}")
    print(f"After filtering:    {len(filtered_places)}")
    print(f"With details:       {len(final_results)}")
    print(f"\nFiltering saved:")
    print(f"  Filtered out:     {STATS['places_filtered_out']}")
    print(f"  Details saved:    ${STATS['places_filtered_out'] * 0.023:.2f}")
    print(f"\nAPI Calls:")
    print(f"  Geocoding:        {STATS['geocode_calls']}")
    print(f"  Nearby Search:    {STATS['nearby_search_calls']}")
    print(f"  Place Details:    {STATS['place_details_calls']}")
    print(f"\nCost breakdown:")
    print(f"  Geocoding:        ${(STATS['geocode_calls']/1000)*5:.4f}")
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
