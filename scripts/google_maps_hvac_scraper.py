#!/usr/bin/env python3
"""
=== GOOGLE MAPS HVAC BUSINESS SCRAPER ===
Version: 1.0.0 | Created: 2025-11-09

PURPOSE:
Scrape 5000+ HVAC businesses from Google Maps using Apify API
Generates CSV with company data ready for email extraction

FEATURES:
- Apify Google Maps Scraper integration
- Automated search across US cities
- Progress tracking and resumable runs
- CSV output with all business details

USAGE:
1. Ensure APIFY_API_KEY in .env
2. Configure CONFIG section (search queries, max results)
3. Run: python google_maps_hvac_scraper.py
4. Results saved to data/raw/hvac_google_maps_TIMESTAMP.csv

COST ESTIMATE:
~$3-5 for 5000 results (Apify credits)

IMPROVEMENTS:
v1.0.0 - Initial version with US-wide HVAC search
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
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
    "APIFY_API_KEY": os.getenv("APIFY_API_KEY"),
    "ACTOR_ID": "nwua9Gu5YrADL7ZDj",

    # Search configuration
    "SEARCH_QUERIES": [
        "HVAC companies in New York, NY",
        "HVAC companies in Los Angeles, CA",
        "HVAC companies in Chicago, IL",
        "HVAC companies in Houston, TX",
        "HVAC companies in Phoenix, AZ",
        "HVAC companies in Philadelphia, PA",
        "HVAC companies in San Antonio, TX",
        "HVAC companies in San Diego, CA",
        "HVAC companies in Dallas, TX",
        "HVAC companies in San Jose, CA",
        "HVAC companies in Austin, TX",
        "HVAC companies in Jacksonville, FL",
        "HVAC companies in Fort Worth, TX",
        "HVAC companies in Columbus, OH",
        "HVAC companies in Charlotte, NC",
        "HVAC companies in San Francisco, CA",
        "HVAC companies in Indianapolis, IN",
        "HVAC companies in Seattle, WA",
        "HVAC companies in Denver, CO",
        "HVAC companies in Boston, MA",
        "HVAC companies in Nashville, TN",
        "HVAC companies in Oklahoma City, OK",
        "HVAC companies in Las Vegas, NV",
        "HVAC companies in Portland, OR",
        "HVAC companies in Memphis, TN",
        "HVAC companies in Louisville, KY",
        "HVAC companies in Baltimore, MD",
        "HVAC companies in Milwaukee, WI",
        "HVAC companies in Albuquerque, NM",
        "HVAC companies in Tucson, AZ",
        "HVAC companies in Fresno, CA",
        "HVAC companies in Mesa, AZ",
        "HVAC companies in Sacramento, CA",
        "HVAC companies in Atlanta, GA",
        "HVAC companies in Kansas City, MO",
        "HVAC companies in Colorado Springs, CO",
        "HVAC companies in Miami, FL",
        "HVAC companies in Raleigh, NC",
        "HVAC companies in Omaha, NE",
        "HVAC companies in Long Beach, CA",
        "HVAC companies in Virginia Beach, VA",
        "HVAC companies in Oakland, CA",
        "HVAC companies in Minneapolis, MN",
        "HVAC companies in Tampa, FL",
        "HVAC companies in Tulsa, OK",
        "HVAC companies in Arlington, TX",
        "HVAC companies in New Orleans, LA",
        "HVAC companies in Wichita, KS",
        "HVAC companies in Cleveland, OH",
        "HVAC companies in Bakersfield, CA",
    ],

    "MAX_RESULTS_PER_QUERY": 100,
    "TOTAL_TARGET": 5000,

    "OUTPUT_DIR": "data/raw"
}

STATS = {
    "queries_processed": 0,
    "total_results": 0,
    "unique_results": 0,
    "duplicates_removed": 0,
    "start_time": None
}

def validate_config():
    """Validate configuration before starting"""
    if not CONFIG["APIFY_API_KEY"]:
        raise ValueError("APIFY_API_KEY not found in .env file")

    logger.info("Configuration validated successfully")

def run_apify_scraper(search_query: str, max_results: int = 100) -> List[Dict]:
    """
    Run Apify Google Maps Scraper for a single search query

    Args:
        search_query: Google Maps search query
        max_results: Maximum results to retrieve

    Returns:
        List of business data dictionaries
    """
    logger.info(f"Starting Apify scraper for: '{search_query}'")

    # Prepare actor input
    actor_input = {
        "searchStringsArray": [search_query],
        "maxCrawledPlacesPerSearch": max_results,
        "language": "en",
        "exportPlaceUrls": False,
        "maxImages": 0,
        "maxReviews": 0,
        "maxQuestions": 0,
        "scrapeReviewId": False,
        "scrapeReviewUrl": False,
        "scrapeReviewerId": False,
        "scrapeReviewerUrl": False,
        "scrapeReviewerName": False,
        "scrapeReviewerPhotoUrl": False,
        "scrapeResponseFrom": False,
        "scrapeResponseDate": False,
        "onlyDataFromSearchPage": False,

        # Company contacts enrichment - extracts emails and social profiles
        "scrapeCompanyContactsInfo": True
    }

    # Start actor run
    api_url = f"https://api.apify.com/v2/acts/{CONFIG['ACTOR_ID']}/runs"
    headers = {
        "Content-Type": "application/json"
    }
    params = {
        "token": CONFIG["APIFY_API_KEY"]
    }

    logger.info("Sending request to Apify...")
    response = requests.post(api_url, json=actor_input, headers=headers, params=params)

    if response.status_code != 201:
        logger.error(f"Failed to start Apify run: {response.status_code} - {response.text}")
        return []

    run_data = response.json()
    run_id = run_data["data"]["id"]

    logger.info(f"Apify run started: {run_id}")
    logger.info("Waiting for scraper to complete...")

    # Poll for completion
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"

    while True:
        time.sleep(10)

        status_response = requests.get(status_url, params=params)
        status_data = status_response.json()

        status = status_data["data"]["status"]
        logger.info(f"Status: {status}")

        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break

    if status != "SUCCEEDED":
        logger.error(f"Apify run failed with status: {status}")
        return []

    # Get results
    dataset_id = status_data["data"]["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"

    logger.info("Downloading results...")
    results_response = requests.get(dataset_url, params=params)

    if results_response.status_code != 200:
        logger.error(f"Failed to download results: {results_response.status_code}")
        return []

    results = results_response.json()
    logger.info(f"Retrieved {len(results)} results")

    return results

def normalize_business_data(raw_data: Dict) -> Dict:
    """
    Normalize Apify result to standard format

    Args:
        raw_data: Raw data from Apify

    Returns:
        Normalized business dictionary
    """
    # Extract social profiles from enrichment
    instagram = ""
    facebook = ""
    linkedin = ""
    twitter = ""

    if "instagrams" in raw_data and raw_data["instagrams"]:
        instagram = raw_data["instagrams"][0] if isinstance(raw_data["instagrams"], list) else raw_data["instagrams"]

    if "facebooks" in raw_data and raw_data["facebooks"]:
        facebook = raw_data["facebooks"][0] if isinstance(raw_data["facebooks"], list) else raw_data["facebooks"]

    if "linkedIns" in raw_data and raw_data["linkedIns"]:
        linkedin = raw_data["linkedIns"][0] if isinstance(raw_data["linkedIns"], list) else raw_data["linkedIns"]

    if "twitters" in raw_data and raw_data["twitters"]:
        twitter = raw_data["twitters"][0] if isinstance(raw_data["twitters"], list) else raw_data["twitters"]

    return {
        "company_name": raw_data.get("title", ""),
        "address": raw_data.get("address", ""),
        "city": raw_data.get("city", ""),
        "state": raw_data.get("state", ""),
        "zip": raw_data.get("postalCode", ""),
        "country": "USA",
        "phone": raw_data.get("phoneUnformatted", "") or raw_data.get("phone", ""),
        "website": raw_data.get("website", ""),
        "category": raw_data.get("categoryName", ""),
        "rating": raw_data.get("totalScore", ""),
        "reviews_count": raw_data.get("reviewsCount", 0),
        "google_maps_url": raw_data.get("url", ""),
        "place_id": raw_data.get("placeId", ""),
        "latitude": raw_data.get("location", {}).get("lat", ""),
        "longitude": raw_data.get("location", {}).get("lng", ""),

        # Enriched contact data
        "instagram": instagram,
        "facebook": facebook,
        "linkedin": linkedin,
        "twitter": twitter,
        "email": ""
    }

def remove_duplicates(businesses: List[Dict]) -> List[Dict]:
    """
    Remove duplicate businesses based on place_id or phone

    Args:
        businesses: List of business dictionaries

    Returns:
        Deduplicated list
    """
    seen_ids = set()
    seen_phones = set()
    unique_businesses = []

    for business in businesses:
        place_id = business.get("place_id", "")
        phone = business.get("phone", "")

        # Skip if we've seen this place_id or phone
        if place_id and place_id in seen_ids:
            STATS["duplicates_removed"] += 1
            continue
        if phone and phone in seen_phones:
            STATS["duplicates_removed"] += 1
            continue

        # Add to unique list
        unique_businesses.append(business)

        if place_id:
            seen_ids.add(place_id)
        if phone:
            seen_phones.add(phone)

    return unique_businesses

def save_to_csv(businesses: List[Dict], filename: str):
    """
    Save businesses to CSV file

    Args:
        businesses: List of business dictionaries
        filename: Output filename
    """
    import csv

    if not businesses:
        logger.warning("No businesses to save")
        return

    output_path = Path(CONFIG["OUTPUT_DIR"]) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get all keys from first business
    fieldnames = list(businesses[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(businesses)

    logger.info(f"Saved {len(businesses)} businesses to: {output_path}")
    print(f"\nResults saved to: {output_path}")

def print_summary():
    """Print scraping summary"""
    elapsed = time.time() - STATS["start_time"]

    print(f"\n{'='*70}")
    print(f"GOOGLE MAPS HVAC SCRAPING SUMMARY")
    print(f"{'='*70}")
    print(f"Queries processed:     {STATS['queries_processed']}")
    print(f"Total results:         {STATS['total_results']}")
    print(f"Duplicates removed:    {STATS['duplicates_removed']}")
    print(f"Unique businesses:     {STATS['unique_results']}")
    print(f"Time elapsed:          {elapsed/60:.1f} minutes")
    print(f"{'='*70}\n")

def main():
    """Main execution"""
    logger.info("=== GOOGLE MAPS HVAC SCRAPER STARTED ===")

    STATS["start_time"] = time.time()

    # Validate configuration
    validate_config()

    # Collect all businesses
    all_businesses = []

    logger.info(f"Target: {CONFIG['TOTAL_TARGET']} businesses")
    logger.info(f"Queries to process: {len(CONFIG['SEARCH_QUERIES'])}")

    for i, query in enumerate(CONFIG["SEARCH_QUERIES"], 1):
        logger.info(f"\n--- Query {i}/{len(CONFIG['SEARCH_QUERIES'])} ---")

        # Run scraper
        results = run_apify_scraper(query, CONFIG["MAX_RESULTS_PER_QUERY"])

        if results:
            # Normalize data
            normalized = [normalize_business_data(r) for r in results]
            all_businesses.extend(normalized)

            STATS["total_results"] += len(results)
            STATS["queries_processed"] += 1

            logger.info(f"Total collected so far: {len(all_businesses)}")

            # Check if we reached target
            if len(all_businesses) >= CONFIG["TOTAL_TARGET"]:
                logger.info(f"Reached target of {CONFIG['TOTAL_TARGET']} businesses!")
                break
        else:
            logger.warning(f"No results for query: {query}")

        # Small delay between queries
        if i < len(CONFIG["SEARCH_QUERIES"]):
            time.sleep(5)

    # Remove duplicates
    logger.info("\nRemoving duplicates...")
    unique_businesses = remove_duplicates(all_businesses)
    STATS["unique_results"] = len(unique_businesses)

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"hvac_google_maps_{timestamp}.csv"
    save_to_csv(unique_businesses, filename)

    # Print summary
    print_summary()

    logger.info("=== SCRAPING COMPLETED ===")

if __name__ == "__main__":
    main()
