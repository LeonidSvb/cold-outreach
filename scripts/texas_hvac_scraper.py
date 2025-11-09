#!/usr/bin/env python3
"""
=== TEXAS HVAC EMAIL SCRAPER ===
Version: 1.0.0 | Created: 2025-11-09

Optimized for Texas HVAC companies with cost-effective filters

USAGE:
  Test:   python texas_hvac_scraper.py --mode test
  Medium: python texas_hvac_scraper.py --mode medium
  Full:   python texas_hvac_scraper.py --mode full

FEATURES:
- Texas-specific city targeting
- Quality filters (only with website, min reviews)
- Deduplication by place_id + phone + website
- Cost optimization

PRICING:
- Test:   300 companies → 200 emails → $1.80
- Medium: 2000 companies → 1340 emails → $12
- Full:   6000 companies → 3600 emails (deduped) → $36
"""

import os
import sys
import csv
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Tuple
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

# Texas city configurations
TEXAS_CITIES = {
    "test": [
        ("Houston", "TX"),
        ("Dallas", "TX"),
        ("Austin", "TX")
    ],
    "expansion": [
        ("San Antonio", "TX"),      # Major metro, not yet scraped
        ("Fort Worth", "TX"),        # DFW west side
        ("El Paso", "TX"),          # West Texas, different market
        ("Plano", "TX"),            # North Dallas, affluent suburb
        ("Corpus Christi", "TX"),   # Gulf Coast
        ("Laredo", "TX"),           # South Texas border
        ("Lubbock", "TX"),          # West Texas tech hub
        ("Arlington", "TX")         # Between Dallas-Fort Worth
    ],
    "medium": [
        ("Houston", "TX"),
        ("Dallas", "TX"),
        ("Austin", "TX"),
        ("San Antonio", "TX"),
        ("Fort Worth", "TX")
    ],
    "full": [
        ("Houston", "TX"),
        ("Dallas", "TX"),
        ("Austin", "TX"),
        ("San Antonio", "TX"),
        ("Fort Worth", "TX"),
        ("El Paso", "TX"),
        ("Arlington", "TX"),
        ("Corpus Christi", "TX"),
        ("Plano", "TX"),
        ("Laredo", "TX")
    ]
}

MODES = {
    "test": {
        "per_city": 100,
        "batch_size": 3,
        "expected_total": 300,
        "expected_emails": 200,
        "cost": 1.80
    },
    "expansion": {
        "per_city": 150,
        "batch_size": 4,
        "expected_total": 1200,
        "expected_emails": 589,
        "expected_deduped": 571,
        "cost": 7.20
    },
    "medium": {
        "per_city": 400,
        "batch_size": 5,
        "expected_total": 2000,
        "expected_emails": 1340,
        "cost": 12.00
    },
    "full": {
        "per_city": 600,
        "batch_size": 10,
        "expected_total": 6000,
        "expected_emails": 4020,
        "expected_deduped": 3600,
        "cost": 36.00
    }
}

CONFIG = {
    "APIFY_API_KEY": os.getenv("APIFY_API_KEY"),
    "ACTOR_ID": "lukaskrivka/google-maps-with-contact-details",
    "SEARCH_TEMPLATE": "HVAC contractors {city}, {state}",
    "OUTPUT_DIR": "data/processed"
}

STATS = {
    "total_scraped": 0,
    "total_emails": 0,
    "duplicates_removed": 0,
    "unique_companies": 0,
    "start_time": None
}

def run_batch(search_queries: List[str], max_per_query: int) -> List[Dict]:
    """Run Apify actor for batch of queries"""
    logger.info(f"Starting batch: {len(search_queries)} queries")

    # Actor input - minimal config (actor extracts emails by default)
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
        logger.error(f"Failed: {response.status_code} - {response.text}")
        return []

    run_id = response.json()["data"]["id"]
    logger.info(f"Run ID: {run_id}")

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
        logger.error(f"Failed: {status}")
        return []

    # Get results
    dataset_id = status_data["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"

    results_response = requests.get(dataset_url, params=params)
    results = results_response.json()

    logger.info(f"Retrieved: {len(results)} results")

    return results

def filter_quality(results: List[Dict]) -> List[Dict]:
    """Filter results for quality (website, reviews)"""
    # UPDATED: Removed strict filters - let actor handle enrichment
    # Actor will try to get emails from websites when available
    # Companies without websites will naturally have no emails

    logger.info(f"Processing {len(results)} results (no quality filtering)")

    return results

def process_result(r: Dict) -> Dict:
    """Normalize result"""
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
        "place_id": r.get("placeId", ""),
        "phone_unformatted": r.get("phoneUnformatted", "")
    }

def deduplicate(results: List[Dict]) -> List[Dict]:
    """Remove duplicates by place_id, phone, website"""
    seen_ids: Set[str] = set()
    seen_phones: Set[str] = set()
    seen_domains: Set[str] = set()
    unique = []

    for r in results:
        place_id = r.get("place_id", "")
        phone = r.get("phone_unformatted", "")
        website = r.get("website", "")

        # Extract domain from website
        domain = ""
        if website:
            try:
                from urllib.parse import urlparse
                domain = urlparse(website).netloc.replace('www.', '')
            except:
                domain = website

        # Check duplicates
        is_duplicate = False

        if place_id and place_id in seen_ids:
            is_duplicate = True
        elif phone and phone in seen_phones:
            is_duplicate = True
        elif domain and domain in seen_domains:
            is_duplicate = True

        if is_duplicate:
            STATS["duplicates_removed"] += 1
            continue

        # Add to unique
        unique.append(r)

        if place_id:
            seen_ids.add(place_id)
        if phone:
            seen_phones.add(phone)
        if domain:
            seen_domains.add(domain)

    logger.info(f"Deduplication: {len(results)} → {len(unique)} (removed {len(results) - len(unique)})")

    return unique

def save_results(results: List[Dict], mode: str) -> str:
    """Save to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(CONFIG["OUTPUT_DIR"])
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"texas_hvac_{mode}_{timestamp}.csv"

    if results:
        fieldnames = list(results[0].keys())

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"Saved: {output_file}")

    return str(output_file)

def print_summary(mode: str, output_file: str, config: Dict):
    """Print summary"""
    elapsed = (time.time() - STATS["start_time"]) / 60
    email_rate = (STATS["total_emails"] / max(STATS["unique_companies"], 1)) * 100

    print(f"\n{'='*70}")
    print(f"TEXAS HVAC SCRAPING - {mode.upper()} MODE")
    print(f"{'='*70}")
    print(f"Total scraped:         {STATS['total_scraped']}")
    print(f"Duplicates removed:    {STATS['duplicates_removed']}")
    print(f"Unique companies:      {STATS['unique_companies']}")
    print(f"With emails:           {STATS['total_emails']} ({email_rate:.1f}%)")
    print(f"Expected emails:       {config['expected_emails']}")
    print(f"Estimated cost:        ${config['cost']:.2f}")
    print(f"Time elapsed:          {elapsed:.1f} min")
    print(f"Output file:           {output_file}")
    print(f"{'='*70}\n")

    # Quality check
    if email_rate >= 60:
        print(f"[EXCELLENT] {email_rate:.0f}% email rate (target: 67%)")
    elif email_rate >= 50:
        print(f"[GOOD] {email_rate:.0f}% email rate (acceptable)")
    else:
        print(f"[LOW] {email_rate:.0f}% email rate (check quality)")

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Texas HVAC Email Scraper")
    parser.add_argument("--mode", type=str, choices=["test", "expansion", "medium", "full"],
                       required=True, help="Scraping mode")
    parser.add_argument("--yes", action="store_true",
                       help="Auto-confirm without prompt")
    args = parser.parse_args()

    mode = args.mode
    config = MODES[mode]
    cities = TEXAS_CITIES[mode]

    logger.info(f"=== TEXAS HVAC SCRAPER - {mode.upper()} ===")

    if not CONFIG["APIFY_API_KEY"]:
        logger.error("APIFY_API_KEY not found")
        return

    # Pre-flight info
    print(f"\n{'='*70}")
    print(f"TEXAS HVAC - {mode.upper()} MODE")
    print(f"{'='*70}")
    print(f"Cities:                {len(cities)}")
    print(f"Per city:              {config['per_city']}")
    print(f"Expected total:        {config['expected_total']}")
    print(f"Expected emails:       {config['expected_emails']}")
    if mode in ["expansion", "full"] and "expected_deduped" in config:
        print(f"After deduplication:   ~{config['expected_deduped']}")
    print(f"Estimated cost:        ${config['cost']:.2f}")
    print(f"Estimated time:        {len(cities) / config['batch_size'] * 2:.0f} min")
    print(f"{'='*70}\n")

    if not args.yes:
        confirmation = input("Continue? (yes/no): ")
        if confirmation.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
    else:
        logger.info("Auto-confirmed with --yes flag")

    STATS["start_time"] = time.time()

    all_results = []
    batch_size = config["batch_size"]

    # Process in batches
    for i in range(0, len(cities), batch_size):
        batch_cities = cities[i:i+batch_size]

        logger.info(f"\n--- Batch {i//batch_size + 1} ---")

        # Create queries
        queries = [
            CONFIG["SEARCH_TEMPLATE"].format(city=city, state=state)
            for city, state in batch_cities
        ]

        # Run batch
        results = run_batch(queries, config["per_city"])

        if results:
            # Filter quality
            filtered = filter_quality(results)

            # Process
            processed = [process_result(r) for r in filtered]
            all_results.extend(processed)

            STATS["total_scraped"] += len(results)

            logger.info(f"Batch complete: {len(processed)} quality results")

        # Delay between batches
        if i + batch_size < len(cities):
            time.sleep(3)

    # Deduplicate
    logger.info("\nDeduplicating...")
    unique_results = deduplicate(all_results)

    STATS["unique_companies"] = len(unique_results)
    STATS["total_emails"] = sum(1 for r in unique_results if r["emails_count"] > 0)

    # Save
    output_file = save_results(unique_results, mode)

    # Summary
    print_summary(mode, output_file, config)

    logger.info("=== COMPLETED ===")

if __name__ == "__main__":
    main()
