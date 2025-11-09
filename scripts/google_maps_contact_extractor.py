#!/usr/bin/env python3
"""
=== GOOGLE MAPS CONTACT INFO EXTRACTOR ===
Version: 1.0.0 | Created: 2025-11-09

PURPOSE:
Re-scrape specific Google Maps places with contact info extraction enabled
Use this to get emails from places where HTTP scraping failed

FEATURES:
- Uses place IDs for accurate targeting
- Extracts emails and social media from Google Maps listings
- Compares with previous HTTP scraping results

USAGE:
python google_maps_contact_extractor.py
"""

import os
import sys
import csv
import json
import time
import requests
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
    "APIFY_API_KEY": os.getenv("APIFY_API_KEY"),
    "ACTOR_ID": "nwua9Gu5YrADL7ZDj",
    "INPUT_CSV": "data/temp/problem_sites_placeids.csv",
    "OUTPUT_DIR": "data/temp"
}

STATS = {
    "total_sites": 0,
    "successful": 0,
    "with_contacts": 0,
    "emails_found": 0
}

def run_google_maps_scraper(place_ids: List[str]) -> List[Dict]:
    """
    Run Google Maps Scraper for specific place IDs with contact extraction

    Args:
        place_ids: List of Google Maps place IDs

    Returns:
        List of enriched business data
    """
    logger.info(f"Starting Google Maps Scraper for {len(place_ids)} places")

    # Build place URLs from IDs
    start_urls = [f"https://www.google.com/maps/search/?api=1&query=Google&query_place_id={pid}"
                  for pid in place_ids]

    actor_input = {
        "startUrls": start_urls,
        "maxCrawledPlacesPerSearch": 1,
        "language": "en",
        "exportPlaceUrls": False,
        "maxImages": 0,
        "maxReviews": 0,
        "maxQuestions": 0,

        # CRITICAL: Enable contact info extraction
        "scrapeCompanyContactsInfo": True,

        "onlyDataFromSearchPage": False
    }

    # Start run
    api_url = f"https://api.apify.com/v2/acts/{CONFIG['ACTOR_ID']}/runs"
    params = {"token": CONFIG["APIFY_API_KEY"]}

    logger.info("Sending request to Apify...")
    response = requests.post(
        api_url,
        json=actor_input,
        headers={"Content-Type": "application/json"},
        params=params
    )

    if response.status_code != 201:
        logger.error(f"Failed to start: {response.status_code}")
        logger.error(response.text)
        return []

    run_id = response.json()["data"]["id"]
    logger.info(f"Run started: {run_id}")

    # Poll for completion
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"

    while True:
        time.sleep(10)
        status_response = requests.get(status_url, params=params)
        status = status_response.json()["data"]["status"]
        logger.info(f"  Status: {status}")

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

    logger.info(f"Got {len(results)} results")

    return results

def process_csv() -> List[Dict]:
    """Process CSV with problem sites"""
    logger.info(f"Reading: {CONFIG['INPUT_CSV']}")

    with open(CONFIG['INPUT_CSV'], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        sites = list(reader)

    STATS["total_sites"] = len(sites)
    logger.info(f"Found {len(sites)} sites to re-scrape")

    # Extract place IDs
    place_ids = [s['placeId'] for s in sites if s.get('placeId')]

    logger.info(f"Running Google Maps Scraper for {len(place_ids)} places...")

    # Run scraper
    results = run_google_maps_scraper(place_ids)

    # Process results
    enriched = []

    for result in results:
        # Extract contact info
        website = result.get('website', '')
        email = result.get('email', '')  # From Google Maps
        phone = result.get('phone', '')

        # Check for additional contact fields
        company_contacts = result.get('companyContactsInfo', {})
        emails_list = company_contacts.get('emails', []) if company_contacts else []
        social_media = company_contacts.get('socialMedia', {}) if company_contacts else {}

        # Combine all emails
        all_emails = []
        if email:
            all_emails.append(email)
        if emails_list:
            all_emails.extend(emails_list)

        # Remove duplicates
        all_emails = list(set([e.lower() for e in all_emails if e]))

        # Update stats
        STATS["successful"] += 1
        if all_emails or social_media:
            STATS["with_contacts"] += 1
            STATS["emails_found"] += len(all_emails)

        enriched_result = {
            "title": result.get('title', ''),
            "website": website,
            "phone": phone,
            "placeId": result.get('placeId', ''),
            "emails_from_google_maps": "; ".join(all_emails),
            "emails_count": len(all_emails),
            "facebook": social_media.get('facebook', '') if social_media else '',
            "instagram": social_media.get('instagram', '') if social_media else '',
            "twitter": social_media.get('twitter', '') if social_media else '',
            "linkedin": social_media.get('linkedin', '') if social_media else '',
            "has_contacts": "Yes" if (all_emails or social_media) else "No"
        }

        enriched.append(enriched_result)

        # Log result
        if all_emails:
            logger.info(f"✅ {enriched_result['title']}")
            logger.info(f"   Emails: {', '.join(all_emails)}")
        else:
            logger.info(f"❌ {enriched_result['title']} - No contacts")

    return enriched

def save_results(results: List[Dict]) -> str:
    """Save results to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Path(CONFIG["OUTPUT_DIR"]) / f"google_maps_contacts_{timestamp}.csv"

    if not results:
        logger.warning("No results to save")
        return ""

    fieldnames = list(results[0].keys())

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Results saved to: {output_file}")
    return str(output_file)

def print_summary():
    """Print summary"""
    print(f"\n{'='*70}")
    print(f"GOOGLE MAPS CONTACT EXTRACTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total sites processed:     {STATS['total_sites']}")
    print(f"Successful scrapes:        {STATS['successful']}")
    print(f"With contact info:         {STATS['with_contacts']}")
    print(f"Total emails found:        {STATS['emails_found']}")

    if STATS['successful'] > 0:
        print(f"Success rate:              {STATS['with_contacts']/STATS['successful']*100:.1f}%")

    print(f"{'='*70}\n")

def main():
    """Main execution"""
    logger.info("=== GOOGLE MAPS CONTACT EXTRACTOR STARTED ===")

    if not CONFIG["APIFY_API_KEY"]:
        logger.error("APIFY_API_KEY not found in .env")
        return

    start_time = time.time()

    # Process sites
    results = process_csv()

    # Save results
    output_file = save_results(results)

    # Print summary
    print_summary()

    elapsed = time.time() - start_time
    logger.info(f"Completed in {elapsed:.1f} seconds")
    logger.info(f"Results: {output_file}")

if __name__ == "__main__":
    main()
