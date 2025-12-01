#!/usr/bin/env python3
"""
=== TEST HVAC SCRAPER ===
Quick test of Apify Google Maps scraping for 1-2 cities

USAGE:
python test_hvac_scraper.py
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
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
    "APIFY_API_KEY": os.getenv("APIFY_API_KEY"),
    "ACTOR_ID": "nwua9Gu5YrADL7ZDj",
    "TEST_CITIES": [
        ("Miami", "FL"),
        ("Austin", "TX")
    ],
    "MAX_RESULTS": 20
}

def run_test_search(city: str, state: str):
    """Test Apify search for one city"""
    search_query = f"HVAC companies in {city}, {state}"

    print(f"\n{'='*60}")
    print(f"Testing: {search_query}")
    print(f"{'='*60}")

    actor_input = {
        "searchStringsArray": [search_query],
        "maxCrawledPlacesPerSearch": CONFIG["MAX_RESULTS"],
        "language": "en",
        "exportPlaceUrls": False,
        "maxImages": 0,
        "maxReviews": 0
    }

    # Start run
    api_url = f"https://api.apify.com/v2/acts/{CONFIG['ACTOR_ID']}/runs"
    params = {"token": CONFIG["APIFY_API_KEY"]}

    print(f"Starting Apify run...")
    response = requests.post(
        api_url,
        json=actor_input,
        headers={"Content-Type": "application/json"},
        params=params
    )

    if response.status_code != 201:
        print(f"ERROR: Failed to start run: {response.status_code}")
        print(response.text)
        return []

    run_id = response.json()["data"]["id"]
    print(f"Run ID: {run_id}")
    print(f"Waiting for completion...")

    # Poll for completion
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"

    while True:
        time.sleep(5)
        status_response = requests.get(status_url, params=params)
        status = status_response.json()["data"]["status"]
        print(f"  Status: {status}")

        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break

    if status != "SUCCEEDED":
        print(f"ERROR: Run failed with status: {status}")
        return []

    # Get results
    dataset_id = status_response.json()["data"]["defaultDatasetId"]
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"

    print(f"Downloading results...")
    results_response = requests.get(dataset_url, params=params)
    results = results_response.json()

    print(f"\nSUCCESS: Got {len(results)} results!")

    # Show sample
    if results:
        print(f"\nSample result:")
        sample = results[0]
        print(f"  Name: {sample.get('title', 'N/A')}")
        print(f"  Address: {sample.get('address', 'N/A')}")
        print(f"  Phone: {sample.get('phone', 'N/A')}")
        print(f"  Website: {sample.get('website', 'N/A')}")
        print(f"  Rating: {sample.get('totalScore', 'N/A')}")

    return results

def main():
    """Run test"""
    print(f"\n{'='*60}")
    print(f"APIFY GOOGLE MAPS TEST")
    print(f"{'='*60}")

    if not CONFIG["APIFY_API_KEY"]:
        print("ERROR: APIFY_API_KEY not found in .env")
        return

    print(f"API Key: {CONFIG['APIFY_API_KEY'][:20]}...")
    print(f"Actor: {CONFIG['ACTOR_ID']}")
    print(f"Test cities: {len(CONFIG['TEST_CITIES'])}")

    all_results = []

    for city, state in CONFIG["TEST_CITIES"]:
        results = run_test_search(city, state)
        all_results.extend(results)
        time.sleep(3)

    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total results: {len(all_results)}")
    print(f"Test PASSED!" if all_results else "Test FAILED!")
    print(f"{'='*60}\n")

    # Save test results
    if all_results:
        output_file = f"data/temp/test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2)

        print(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
