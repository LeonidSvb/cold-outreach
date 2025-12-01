#!/usr/bin/env python3
"""
=== HVAC FULL SCRAPING PIPELINE ===
Version: 1.0.0 | Created: 2025-11-09

PURPOSE:
Complete pipeline for scraping 5000+ HVAC businesses with emails
Stage 1: Google Maps scraping (Apify) -> Company data
Stage 2: Website scraping (HTTP) -> Email extraction

FEATURES:
- Two-stage automated pipeline
- Apify Google Maps for company data
- Parallel HTTP scraping for emails
- Progress tracking and resumable
- Final CSV with all data + emails

USAGE:
1. Ensure APIFY_API_KEY in .env
2. Configure target cities and max results
3. Run: python hvac_full_pipeline.py
4. Results in data/processed/hvac_complete_TIMESTAMP.csv

COST ESTIMATE:
Stage 1 (Apify): ~$3-5 for 5000 businesses
Stage 2 (HTTP): Free, ~2-3 hours processing time

IMPROVEMENTS:
v1.0.0 - Initial integrated pipeline
"""

import os
import sys
import csv
import json
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from modules.shared.logging.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

load_dotenv()

CONFIG = {
    "STAGE_1_ENABLED": True,
    "STAGE_2_ENABLED": True,

    # Stage 1: Google Maps Scraping
    "APIFY_API_KEY": os.getenv("APIFY_API_KEY"),
    "ACTOR_ID": "nwua9Gu5YrADL7ZDj",
    "SEARCH_QUERY_TEMPLATE": "HVAC companies in {city}, {state}",

    # Top 100 US cities for comprehensive coverage
    "TARGET_CITIES": [
        ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
        ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
        ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
        ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
        ("Fort Worth", "TX"), ("Columbus", "OH"), ("Charlotte", "NC"),
        ("San Francisco", "CA"), ("Indianapolis", "IN"), ("Seattle", "WA"),
        ("Denver", "CO"), ("Boston", "MA"), ("Nashville", "TN"),
        ("Oklahoma City", "OK"), ("Las Vegas", "NV"), ("Portland", "OR"),
        ("Memphis", "TN"), ("Louisville", "KY"), ("Baltimore", "MD"),
        ("Milwaukee", "WI"), ("Albuquerque", "NM"), ("Tucson", "AZ"),
        ("Fresno", "CA"), ("Mesa", "AZ"), ("Sacramento", "CA"),
        ("Atlanta", "GA"), ("Kansas City", "MO"), ("Colorado Springs", "CO"),
        ("Miami", "FL"), ("Raleigh", "NC"), ("Omaha", "NE"),
        ("Long Beach", "CA"), ("Virginia Beach", "VA"), ("Oakland", "CA"),
        ("Minneapolis", "MN"), ("Tampa", "FL"), ("Tulsa", "OK"),
        ("Arlington", "TX"), ("New Orleans", "LA"), ("Wichita", "KS"),
        ("Cleveland", "OH"), ("Bakersfield", "CA"),
    ],

    "MAX_RESULTS_PER_CITY": 100,
    "TOTAL_TARGET": 5000,

    # Stage 2: Email Extraction
    "EMAIL_SCRAPER_SCRIPT": "scripts/scraping_parallel_website_email_extractor.py",
    "EMAIL_WORKERS": 25,

    # Output
    "OUTPUT_DIR": "data/processed",
    "TEMP_DIR": "data/temp"
}

PIPELINE_STATS = {
    "stage_1": {
        "cities_processed": 0,
        "total_results": 0,
        "unique_businesses": 0,
        "duplicates_removed": 0,
        "start_time": None,
        "end_time": None
    },
    "stage_2": {
        "websites_checked": 0,
        "emails_found": 0,
        "success_rate": 0.0,
        "start_time": None,
        "end_time": None
    }
}

def validate_config():
    """Validate configuration"""
    if CONFIG["STAGE_1_ENABLED"] and not CONFIG["APIFY_API_KEY"]:
        raise ValueError("APIFY_API_KEY not found in .env")

    if CONFIG["STAGE_2_ENABLED"]:
        email_script = Path(CONFIG["EMAIL_SCRAPER_SCRIPT"])
        if not email_script.exists():
            raise ValueError(f"Email scraper script not found: {email_script}")

    logger.info("Configuration validated")

def run_apify_search(city: str, state: str, max_results: int = 100) -> List[Dict]:
    """
    Run Apify Google Maps scraper for a specific city

    Args:
        city: City name
        state: State abbreviation
        max_results: Max results to retrieve

    Returns:
        List of business dictionaries
    """
    search_query = CONFIG["SEARCH_QUERY_TEMPLATE"].format(city=city, state=state)
    logger.info(f"Searching: {search_query}")

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
        "onlyDataFromSearchPage": False
    }

    # Start run
    api_url = f"https://api.apify.com/v2/acts/{CONFIG['ACTOR_ID']}/runs"
    params = {"token": CONFIG["APIFY_API_KEY"]}

    response = requests.post(api_url, json=actor_input, headers={"Content-Type": "application/json"}, params=params)

    if response.status_code != 201:
        logger.error(f"Failed to start run: {response.status_code}")
        return []

    run_id = response.json()["data"]["id"]
    logger.info(f"Run started: {run_id}, waiting for completion...")

    # Poll for completion
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"

    while True:
        time.sleep(10)
        status_response = requests.get(status_url, params=params)
        status = status_response.json()["data"]["status"]

        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break

    if status != "SUCCEEDED":
        logger.error(f"Run failed: {status}")
        return []

    # Get results
    dataset_id = status_response.json()["data"]["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"

    results_response = requests.get(dataset_url, params=params)
    results = results_response.json()

    logger.info(f"Got {len(results)} results from {city}, {state}")

    return results

def normalize_business(raw: Dict) -> Dict:
    """Normalize Apify result to standard format"""
    return {
        "company_name": raw.get("title", ""),
        "address": raw.get("address", ""),
        "city": raw.get("city", ""),
        "state": raw.get("state", ""),
        "zip": raw.get("postalCode", ""),
        "country": "USA",
        "phone": raw.get("phoneUnformatted", "") or raw.get("phone", ""),
        "website": raw.get("website", ""),
        "category": raw.get("categoryName", ""),
        "rating": raw.get("totalScore", ""),
        "reviews_count": raw.get("reviewsCount", 0),
        "google_maps_url": raw.get("url", ""),
        "place_id": raw.get("placeId", ""),
        "latitude": raw.get("location", {}).get("lat", ""),
        "longitude": raw.get("location", {}).get("lng", "")
    }

def remove_duplicates(businesses: List[Dict]) -> List[Dict]:
    """Remove duplicates based on place_id and phone"""
    seen_ids = set()
    seen_phones = set()
    unique = []

    for biz in businesses:
        place_id = biz.get("place_id", "")
        phone = biz.get("phone", "")

        if (place_id and place_id in seen_ids) or (phone and phone in seen_phones):
            PIPELINE_STATS["stage_1"]["duplicates_removed"] += 1
            continue

        unique.append(biz)
        if place_id:
            seen_ids.add(place_id)
        if phone:
            seen_phones.add(phone)

    return unique

def stage_1_google_maps_scraping() -> str:
    """
    Stage 1: Scrape business data from Google Maps

    Returns:
        Path to temporary CSV with business data
    """
    logger.info("\n" + "="*70)
    logger.info("STAGE 1: GOOGLE MAPS SCRAPING")
    logger.info("="*70)

    PIPELINE_STATS["stage_1"]["start_time"] = time.time()

    all_businesses = []

    for i, (city, state) in enumerate(CONFIG["TARGET_CITIES"], 1):
        logger.info(f"\n--- City {i}/{len(CONFIG['TARGET_CITIES'])}: {city}, {state} ---")

        results = run_apify_search(city, state, CONFIG["MAX_RESULTS_PER_CITY"])

        if results:
            normalized = [normalize_business(r) for r in results]
            all_businesses.extend(normalized)

            PIPELINE_STATS["stage_1"]["total_results"] += len(results)
            PIPELINE_STATS["stage_1"]["cities_processed"] += 1

            logger.info(f"Total collected: {len(all_businesses)}")

            # Check target
            if len(all_businesses) >= CONFIG["TOTAL_TARGET"]:
                logger.info(f"Reached target of {CONFIG['TOTAL_TARGET']}!")
                break

        # Delay between cities
        if i < len(CONFIG["TARGET_CITIES"]):
            time.sleep(5)

    # Remove duplicates
    logger.info("\nRemoving duplicates...")
    unique_businesses = remove_duplicates(all_businesses)
    PIPELINE_STATS["stage_1"]["unique_businesses"] = len(unique_businesses)

    # Save temporary CSV
    temp_dir = Path(CONFIG["TEMP_DIR"])
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_file = temp_dir / f"stage1_businesses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    fieldnames = list(unique_businesses[0].keys())
    with open(temp_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_businesses)

    PIPELINE_STATS["stage_1"]["end_time"] = time.time()

    logger.info(f"\nStage 1 completed: {len(unique_businesses)} unique businesses")
    logger.info(f"Temporary file: {temp_file}")

    return str(temp_file)

def stage_2_email_extraction(input_csv: str) -> str:
    """
    Stage 2: Extract emails from websites

    Args:
        input_csv: Path to CSV from Stage 1

    Returns:
        Path to final CSV with emails
    """
    logger.info("\n" + "="*70)
    logger.info("STAGE 2: EMAIL EXTRACTION FROM WEBSITES")
    logger.info("="*70)

    PIPELINE_STATS["stage_2"]["start_time"] = time.time()

    # Prepare output path
    output_file = Path(CONFIG["OUTPUT_DIR"]) / f"hvac_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Run email extraction script
    cmd = [
        "python",
        CONFIG["EMAIL_SCRAPER_SCRIPT"],
        "--input", input_csv,
        "--output", str(output_file),
        "--workers", str(CONFIG["EMAIL_WORKERS"])
    ]

    logger.info(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Email extraction failed: {result.stderr}")
        raise RuntimeError("Stage 2 failed")

    logger.info("Email extraction completed")

    # Parse stats from output
    PIPELINE_STATS["stage_2"]["end_time"] = time.time()

    return str(output_file)

def print_final_summary(final_csv: str):
    """Print comprehensive pipeline summary"""
    s1 = PIPELINE_STATS["stage_1"]
    s2 = PIPELINE_STATS["stage_2"]

    stage1_time = (s1["end_time"] - s1["start_time"]) / 60 if s1["end_time"] else 0
    stage2_time = (s2["end_time"] - s2["start_time"]) / 60 if s2["end_time"] else 0
    total_time = stage1_time + stage2_time

    print(f"\n{'='*70}")
    print(f"HVAC FULL PIPELINE SUMMARY")
    print(f"{'='*70}")
    print(f"\nSTAGE 1: Google Maps Scraping")
    print(f"  Cities processed:      {s1['cities_processed']}")
    print(f"  Total results:         {s1['total_results']}")
    print(f"  Duplicates removed:    {s1['duplicates_removed']}")
    print(f"  Unique businesses:     {s1['unique_businesses']}")
    print(f"  Time:                  {stage1_time:.1f} minutes")

    print(f"\nSTAGE 2: Email Extraction")
    print(f"  (See detailed stats above)")
    print(f"  Time:                  {stage2_time:.1f} minutes")

    print(f"\nTOTAL")
    print(f"  Total time:            {total_time:.1f} minutes")
    print(f"  Final CSV:             {final_csv}")
    print(f"{'='*70}\n")

def main():
    """Main pipeline execution"""
    logger.info("=== HVAC FULL PIPELINE STARTED ===")

    validate_config()

    temp_csv = None
    final_csv = None

    try:
        # Stage 1: Google Maps Scraping
        if CONFIG["STAGE_1_ENABLED"]:
            temp_csv = stage_1_google_maps_scraping()
        else:
            logger.info("Stage 1 skipped (disabled in config)")
            # Use existing temp file
            temp_files = list(Path(CONFIG["TEMP_DIR"]).glob("stage1_businesses_*.csv"))
            if not temp_files:
                raise ValueError("No temp CSV found and Stage 1 disabled")
            temp_csv = str(sorted(temp_files)[-1])
            logger.info(f"Using existing temp file: {temp_csv}")

        # Stage 2: Email Extraction
        if CONFIG["STAGE_2_ENABLED"]:
            final_csv = stage_2_email_extraction(temp_csv)
        else:
            logger.info("Stage 2 skipped (disabled in config)")
            final_csv = temp_csv

        # Print summary
        print_final_summary(final_csv)

        logger.info("=== PIPELINE COMPLETED SUCCESSFULLY ===")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
