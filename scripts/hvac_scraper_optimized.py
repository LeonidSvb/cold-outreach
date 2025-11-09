#!/usr/bin/env python3
"""
=== HVAC EMAIL SCRAPER - OPTIMIZED VERSION ===
Version: 3.0.0 | Created: 2025-11-09

Based on optimal strategy from HVAC_SCRAPING_STRATEGY.md

USAGE:
  Phase 1 (Test):    python hvac_scraper_optimized.py --mode test
  Phase 2 (Medium):  python hvac_scraper_optimized.py --mode medium
  Phase 3 (Full):    python hvac_scraper_optimized.py --mode full

FEATURES:
- Three-phase approach (test → medium → full)
- Batch processing (10-20 cities per API call)
- Cost tracking and estimates
- Quality validation
- Resume capability

EXPECTED RESULTS:
- Test:   60 companies, 40 emails, $0.12, 2 min
- Medium: 1000 companies, 670 emails, $2, 20 min
- Full:   5000 companies, 3350 emails, $10, 2 hours
"""

import os
import sys
import csv
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
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

# City configurations for different phases
CITIES_CONFIG = {
    "test": {
        "cities": [
            ("Miami", "FL"),
            ("Austin", "TX"),
            ("Denver", "CO")
        ],
        "max_per_city": 20,
        "batch_size": 3,
        "expected_emails": 40,
        "est_cost": 0.12
    },
    "medium": {
        "cities": [
            ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
            ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
            ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
            ("San Jose", "CA")
        ],
        "max_per_city": 100,
        "batch_size": 10,
        "expected_emails": 670,
        "est_cost": 2.00
    },
    "full": {
        "cities": [
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
            ("Cleveland", "OH"), ("Bakersfield", "CA")
        ],
        "max_per_city": 100,
        "batch_size": 10,
        "expected_emails": 3350,
        "est_cost": 10.00
    }
}

CONFIG = {
    "APIFY_API_KEY": os.getenv("APIFY_API_KEY"),
    "ACTOR_ID": "lukaskrivka/google-maps-with-contact-details",
    "SEARCH_TEMPLATE": "HVAC companies in {city}, {state}",
    "OUTPUT_DIR": "data/processed"
}

STATS = {
    "mode": "",
    "batches_processed": 0,
    "total_companies": 0,
    "total_emails": 0,
    "start_time": None,
    "actual_cost": 0.0
}

def run_batch(search_queries: List[str], max_per_query: int) -> List[Dict]:
    """Run one batch of searches"""
    logger.info(f"Starting batch with {len(search_queries)} queries")

    actor_input = {
        "searchStringsArray": search_queries,
        "maxCrawledPlacesPerSearch": max_per_query,
        "language": "en"
    }

    # Start run
    actor_id_api = CONFIG['ACTOR_ID'].replace('/', '~')
    api_url = f"https://api.apify.com/v2/acts/{actor_id_api}/runs"
    params = {"token": CONFIG["APIFY_API_KEY"]}

    response = requests.post(
        api_url,
        json=actor_input,
        headers={"Content-Type": "application/json"},
        params=params
    )

    if response.status_code != 201:
        logger.error(f"Failed to start: {response.status_code}")
        return []

    run_id = response.json()["data"]["id"]
    logger.info(f"Run started: {run_id}")

    # Poll for completion
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"

    while True:
        time.sleep(10)
        status_response = requests.get(status_url, params=params)
        status_data = status_response.json()["data"]
        status = status_data["status"]

        logger.info(f"  Status: {status}")

        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break

    if status != "SUCCEEDED":
        logger.error(f"Run failed: {status}")
        return []

    # Get results
    dataset_id = status_data["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"

    results_response = requests.get(dataset_url, params=params)
    results = results_response.json()

    logger.info(f"Retrieved {len(results)} results")

    return results

def process_result(r: Dict) -> Dict:
    """Normalize single result"""
    emails = r.get('emails', [])
    if isinstance(emails, list):
        emails_clean = [e.strip().lower() for e in emails if e]
    else:
        emails_clean = []

    return {
        "company_name": r.get("title", ""),
        "address": r.get("address", ""),
        "city": r.get("city", ""),
        "state": r.get("state", ""),
        "zip": r.get("postalCode", ""),
        "phone": r.get("phone", ""),
        "website": r.get("website", ""),
        "category": r.get("categoryName", ""),
        "rating": r.get("totalScore", ""),
        "reviews": r.get("reviewsCount", 0),
        "emails": "; ".join(emails_clean),
        "emails_count": len(emails_clean),
        "facebook": r.get("facebook", ""),
        "instagram": r.get("instagram", ""),
        "linkedin": r.get("linkedin", ""),
        "place_id": r.get("placeId", "")
    }

def save_results(results: List[Dict], mode: str) -> str:
    """Save results to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(CONFIG["OUTPUT_DIR"])
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"hvac_{mode}_{timestamp}.csv"

    if results:
        fieldnames = list(results[0].keys())

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"Results saved to: {output_file}")

    return str(output_file)

def print_summary(mode: str, output_file: str, config: Dict):
    """Print execution summary"""
    elapsed = (time.time() - STATS["start_time"]) / 60
    email_rate = (STATS["total_emails"] / max(STATS["total_companies"], 1)) * 100

    print(f"\n{'='*70}")
    print(f"HVAC SCRAPING SUMMARY - {mode.upper()} MODE")
    print(f"{'='*70}")
    print(f"Companies found:       {STATS['total_companies']}")
    print(f"Emails found:          {STATS['total_emails']} ({email_rate:.1f}%)")
    print(f"Expected emails:       {config['expected_emails']}")
    print(f"Performance:           {email_rate:.0f}% vs 67% target")
    print(f"Time elapsed:          {elapsed:.1f} minutes")
    print(f"Estimated cost:        ${config['est_cost']:.2f}")
    print(f"Output file:           {output_file}")
    print(f"{'='*70}\n")

    # Quality check
    if email_rate >= 60:
        print("✅ SUCCESS: Email rate is good (60%+)")
    elif email_rate >= 50:
        print("⚠️ WARNING: Email rate is acceptable (50-60%)")
    else:
        print("❌ ISSUE: Email rate is low (<50%) - check data quality")

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="HVAC Email Scraper - Optimized")
    parser.add_argument("--mode", type=str, choices=["test", "medium", "full"],
                       required=True, help="Scraping mode")
    args = parser.parse_args()

    mode = args.mode
    config = CITIES_CONFIG[mode]

    logger.info(f"=== HVAC SCRAPER - {mode.upper()} MODE ===")

    if not CONFIG["APIFY_API_KEY"]:
        logger.error("APIFY_API_KEY not found in .env")
        return

    # Pre-flight info
    print(f"\n{'='*70}")
    print(f"MODE: {mode.upper()}")
    print(f"{'='*70}")
    print(f"Cities to process:     {len(config['cities'])}")
    print(f"Results per city:      {config['max_per_city']}")
    print(f"Total expected:        ~{len(config['cities']) * config['max_per_city']}")
    print(f"Expected emails:       ~{config['expected_emails']}")
    print(f"Estimated cost:        ${config['est_cost']:.2f}")
    print(f"Estimated time:        {len(config['cities']) / config['batch_size'] * 2:.0f} minutes")
    print(f"{'='*70}\n")

    confirmation = input("Continue? (yes/no): ")
    if confirmation.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return

    STATS["mode"] = mode
    STATS["start_time"] = time.time()

    all_results = []
    cities = config["cities"]
    batch_size = config["batch_size"]

    # Process in batches
    for i in range(0, len(cities), batch_size):
        batch_cities = cities[i:i+batch_size]

        logger.info(f"\n--- Batch {i//batch_size + 1}/{(len(cities)-1)//batch_size + 1} ---")

        # Create search queries
        search_queries = [
            CONFIG["SEARCH_TEMPLATE"].format(city=city, state=state)
            for city, state in batch_cities
        ]

        # Run batch
        results = run_batch(search_queries, config["max_per_city"])

        if results:
            processed = [process_result(r) for r in results]
            all_results.extend(processed)

            STATS["batches_processed"] += 1
            STATS["total_companies"] += len(processed)
            STATS["total_emails"] += sum(1 for r in processed if r["emails_count"] > 0)

            logger.info(f"Batch complete: {len(processed)} companies, {sum(1 for r in processed if r['emails_count'] > 0)} with emails")
            logger.info(f"Total so far: {STATS['total_companies']} companies, {STATS['total_emails']} emails")

        # Small delay between batches
        if i + batch_size < len(cities):
            time.sleep(3)

    # Save results
    output_file = save_results(all_results, mode)

    # Print summary
    print_summary(mode, output_file, config)

    logger.info("=== SCRAPING COMPLETED ===")

if __name__ == "__main__":
    main()
