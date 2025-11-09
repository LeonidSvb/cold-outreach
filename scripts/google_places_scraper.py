#!/usr/bin/env python3
"""
=== GOOGLE PLACES API SCRAPER ===
Version: 1.0.0 | Created: 2025-11-09

STRATEGY:
1. Text Search - find businesses (20 results per request)
2. Place Details - get phone + website for each place

PRICING:
- Text Search: $32/1000 = $0.032 per request (20 results)
- Place Details: $23/1000 = $0.023 per request
- Cost per lead: ~$0.0246

FREE TIER:
$200/month = ~8,130 leads FREE!

USAGE:
python google_places_scraper.py --query "HVAC contractors Houston TX" --max-results 100
"""

import os
import sys
import json
import time
import requests
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

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
    "TEXT_SEARCH_URL": "https://maps.googleapis.com/maps/api/place/textsearch/json",
    "PLACE_DETAILS_URL": "https://maps.googleapis.com/maps/api/place/details/json",
    "OUTPUT_DIR": "data/processed",
    "DELAY_BETWEEN_REQUESTS": 0.5
}

STATS = {
    "text_search_calls": 0,
    "place_details_calls": 0,
    "total_cost": 0.0,
    "places_found": 0,
    "places_with_phone": 0,
    "places_with_website": 0,
    "start_time": None
}

def text_search(query: str, max_results: int = 100) -> List[str]:
    """
    Step 1: Find places using Text Search
    Returns list of place_ids
    """
    logger.info(f"Text Search: {query}")

    place_ids = []
    next_page_token = None

    while len(place_ids) < max_results:
        params = {
            "query": query,
            "key": CONFIG["API_KEY"]
        }

        if next_page_token:
            params["pagetoken"] = next_page_token
            time.sleep(2)  # Required delay for pagetoken

        response = requests.get(CONFIG["TEXT_SEARCH_URL"], params=params)
        STATS["text_search_calls"] += 1

        if response.status_code != 200:
            logger.error(f"Text Search failed: {response.status_code}")
            logger.error(response.text)
            break

        data = response.json()

        if data["status"] != "OK" and data["status"] != "ZERO_RESULTS":
            logger.error(f"API Error: {data['status']}")
            if "error_message" in data:
                logger.error(f"Message: {data['error_message']}")
            break

        results = data.get("results", [])

        for place in results:
            place_ids.append(place["place_id"])
            if len(place_ids) >= max_results:
                break

        logger.info(f"  Found {len(results)} places (total: {len(place_ids)})")

        next_page_token = data.get("next_page_token")
        if not next_page_token or len(place_ids) >= max_results:
            break

        time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])

    STATS["places_found"] = len(place_ids)
    return place_ids[:max_results]

def get_place_details(place_id: str) -> Dict:
    """
    Step 2: Get place details including phone and website
    """
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,geometry,types",
        "key": CONFIG["API_KEY"]
    }

    response = requests.get(CONFIG["PLACE_DETAILS_URL"], params=params)
    STATS["place_details_calls"] += 1

    if response.status_code != 200:
        logger.error(f"Place Details failed: {response.status_code}")
        return {}

    data = response.json()

    if data["status"] != "OK":
        logger.error(f"API Error: {data['status']}")
        return {}

    result = data.get("result", {})

    # Track stats
    if result.get("formatted_phone_number"):
        STATS["places_with_phone"] += 1
    if result.get("website"):
        STATS["places_with_website"] += 1

    return {
        "place_id": place_id,
        "name": result.get("name", ""),
        "address": result.get("formatted_address", ""),
        "phone": result.get("formatted_phone_number", ""),
        "website": result.get("website", ""),
        "rating": result.get("rating", 0),
        "reviews": result.get("user_ratings_total", 0),
        "lat": result.get("geometry", {}).get("location", {}).get("lat", 0),
        "lng": result.get("geometry", {}).get("location", {}).get("lng", 0),
        "types": ", ".join(result.get("types", []))
    }

def calculate_cost():
    """Calculate total API cost"""
    text_search_cost = (STATS["text_search_calls"] / 1000) * 32
    place_details_cost = (STATS["place_details_calls"] / 1000) * 23
    STATS["total_cost"] = text_search_cost + place_details_cost

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Google Places API Scraper")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--max-results", type=int, default=100, help="Max results")
    args = parser.parse_args()

    logger.info("=== GOOGLE PLACES SCRAPER ===")

    if not CONFIG["API_KEY"]:
        logger.error("GOOGLE_PLACES_API_KEY not found in .env")
        print("\nPlease add to .env:")
        print("GOOGLE_PLACES_API_KEY=your_key_here")
        return

    STATS["start_time"] = time.time()

    print(f"\n{'='*70}")
    print(f"GOOGLE PLACES API TEST")
    print(f"{'='*70}")
    print(f"Query:        {args.query}")
    print(f"Max results:  {args.max_results}")
    print(f"{'='*70}\n")

    # Step 1: Text Search
    print("Step 1: Finding places with Text Search...")
    place_ids = text_search(args.query, args.max_results)

    if not place_ids:
        logger.error("No places found")
        return

    print(f"Found {len(place_ids)} places\n")

    # Step 2: Get details for each place
    print(f"Step 2: Getting details for {len(place_ids)} places...")

    all_places = []

    for idx, place_id in enumerate(place_ids, 1):
        print(f"  [{idx}/{len(place_ids)}] Getting details...", end='\r')

        details = get_place_details(place_id)

        if details:
            all_places.append(details)

        time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])

    print(f"\nCompleted {len(all_places)} places")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(CONFIG["OUTPUT_DIR"])
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"google_places_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_places, f, indent=2, ensure_ascii=False)

    # Calculate costs
    calculate_cost()
    elapsed = (time.time() - STATS["start_time"]) / 60

    # Summary
    print(f"\n{'='*70}")
    print(f"SCRAPING COMPLETED")
    print(f"{'='*70}")
    print(f"Places found:       {STATS['places_found']}")
    print(f"Details retrieved:  {len(all_places)}")
    print(f"With phone:         {STATS['places_with_phone']} ({STATS['places_with_phone']/len(all_places)*100:.1f}%)")
    print(f"With website:       {STATS['places_with_website']} ({STATS['places_with_website']/len(all_places)*100:.1f}%)")
    print(f"\nAPI Calls:")
    print(f"  Text Search:      {STATS['text_search_calls']}")
    print(f"  Place Details:    {STATS['place_details_calls']}")
    print(f"\nCost breakdown:")
    print(f"  Text Search:      ${(STATS['text_search_calls']/1000)*32:.4f}")
    print(f"  Place Details:    ${(STATS['place_details_calls']/1000)*23:.4f}")
    print(f"  TOTAL COST:       ${STATS['total_cost']:.4f}")
    print(f"\nFree tier remaining: ${200 - STATS['total_cost']:.2f}")
    print(f"Time elapsed:        {elapsed:.1f} min")
    print(f"Output file:         {output_file}")
    print(f"{'='*70}\n")

    # Show samples
    if all_places:
        print("=== SAMPLE RESULTS ===\n")
        for place in all_places[:5]:
            print(f"{place['name']}")
            print(f"  Address: {place['address']}")
            print(f"  Phone:   {place['phone'] or 'N/A'}")
            print(f"  Website: {place['website'] or 'N/A'}")
            print(f"  Rating:  {place['rating']} ({place['reviews']} reviews)")
            print()

    logger.info("=== COMPLETED ===")

if __name__ == "__main__":
    main()
