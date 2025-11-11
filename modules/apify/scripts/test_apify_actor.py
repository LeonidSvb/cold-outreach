#!/usr/bin/env python3
"""
=== TEST APIFY ACTOR ===
Quick test script to verify actor works before full run

USAGE:
python modules/apify/scripts/test_apify_actor.py
"""

import os
import sys
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

APIFY_API_KEY = os.getenv('APIFY_API_KEY')
if not APIFY_API_KEY:
    raise ValueError("APIFY_API_KEY environment variable is required")
ACTOR_ID = 'xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps'
BASE_URL = 'https://api.apify.com/v2'

# Test with small dataset
TEST_INPUT = {
    "category": "plumber",
    "country": "AU",
    "max_results": 10  # Small test
}

print("=" * 70)
print("TESTING APIFY ACTOR")
print("=" * 70)
print(f"Actor: {ACTOR_ID}")
print(f"Test input: {json.dumps(TEST_INPUT, indent=2)}")
print("=" * 70)
print()

# Start run
api_url = f'{BASE_URL}/acts/{ACTOR_ID.replace("/", "~")}/runs'
params = {'token': APIFY_API_KEY}

print("Starting actor run...")

try:
    response = requests.post(
        api_url,
        json=TEST_INPUT,
        headers={'Content-Type': 'application/json'},
        params=params,
        timeout=30
    )

    if response.status_code != 201:
        print(f"ERROR: Failed to start run: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)

    run_id = response.json()['data']['id']
    print(f"Run started: {run_id}")
    print()

    # Wait for completion
    print("Waiting for completion...")
    status_url = f'{BASE_URL}/actor-runs/{run_id}'

    for i in range(60):
        time.sleep(5)

        status_response = requests.get(status_url, params=params, timeout=30)
        status_data = status_response.json()['data']
        status = status_data['status']

        print(f"   [{i*5}s] Status: {status}")

        if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
            break

    if status != 'SUCCEEDED':
        print(f"\nERROR: Run failed: {status}")
        sys.exit(1)

    print(f"\nRun succeeded!")
    print()

    # Get results
    dataset_id = status_data['defaultDatasetId']
    dataset_url = f'{BASE_URL}/datasets/{dataset_id}/items'

    print("Fetching results...")
    results_response = requests.get(dataset_url, params=params, timeout=60)
    results = results_response.json()

    print(f"Got {len(results)} leads")
    print()

    # Show sample
    print("=" * 70)
    print("SAMPLE RESULTS (first 3 leads)")
    print("=" * 70)

    for i, lead in enumerate(results[:3], 1):
        print(f"\n{i}. {lead.get('name', 'N/A')}")
        print(f"   Country: {lead.get('country', 'N/A')}")
        print(f"   Email: {lead.get('email', 'N/A')}")
        print(f"   Phone: {lead.get('phone', 'N/A')}")
        print(f"   Website: {lead.get('url', lead.get('website', 'N/A'))}")

        # Show all available fields for first lead
        if i == 1:
            print(f"\n   Available fields:")
            for key in sorted(lead.keys()):
                print(f"     - {key}")

    print("\n" + "=" * 70)
    print("TEST SUCCESSFUL!")
    print("=" * 70)
    print("\nYou can now run the full scraper:")
    print("python modules/apify/scripts/australia_business_scraper.py")
    print()

except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
