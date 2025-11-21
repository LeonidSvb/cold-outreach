#!/usr/bin/env python3
"""
=== TEST HOSPITALITY CATEGORY ===
Quick test to verify categories work before full run

Tests: restaurant category with 10 leads from Australia
Cost: ~$0.02 (practically free)
Time: ~30 seconds

USAGE:
python modules/apify/scripts/test_hospitality_category.py
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

# Test with restaurant (most common category)
TEST_INPUT = {
    "category": "restaurant",
    "country": "AU",
    "max_results": 10
}

print("=" * 70)
print("TESTING HOSPITALITY CATEGORY")
print("=" * 70)
print(f"Category: restaurant")
print(f"Country: Australia (AU)")
print(f"Max results: 10")
print(f"Expected cost: ~$0.02")
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

    print(f"Got {len(results)} restaurant leads")
    print()

    # Show sample
    print("=" * 70)
    print("SAMPLE RESULTS (first 3 restaurants)")
    print("=" * 70)

    for i, lead in enumerate(results[:3], 1):
        print(f"\n{i}. {lead.get('name', 'N/A')}")
        print(f"   Category: {lead.get('google_business_categories', ['N/A'])[0] if lead.get('google_business_categories') else 'N/A'}")
        print(f"   Email: {lead.get('email', 'N/A')}")
        print(f"   Phone: {lead.get('phone', 'N/A')}")
        print(f"   Website: {lead.get('url', lead.get('website', 'N/A'))}")
        print(f"   City: {lead.get('city', 'N/A')}")
        print(f"   Rating: {lead.get('review_score', 'N/A')} ({lead.get('reviews_number', 0)} reviews)")

        # Show all available fields for first lead
        if i == 1:
            print(f"\n   All available fields:")
            for key in sorted(lead.keys()):
                value = str(lead.get(key, ''))
                if len(value) > 50:
                    value = value[:50] + '...'
                print(f"     - {key}: {value}")

    # Statistics
    print("\n" + "=" * 70)
    print("DATA QUALITY STATISTICS")
    print("=" * 70)

    total = len(results)
    has_email = sum(1 for r in results if r.get('email'))
    has_phone = sum(1 for r in results if r.get('phone'))
    has_website = sum(1 for r in results if r.get('url') or r.get('website'))
    has_reviews = sum(1 for r in results if r.get('reviews_number', 0) > 0)

    print(f"Total leads: {total}")
    print(f"Has email: {has_email} ({has_email/total*100:.1f}%)")
    print(f"Has phone: {has_phone} ({has_phone/total*100:.1f}%)")
    print(f"Has website: {has_website} ({has_website/total*100:.1f}%)")
    print(f"Has reviews: {has_reviews} ({has_reviews/total*100:.1f}%)")

    avg_rating = sum(r.get('review_score', 0) for r in results if r.get('review_score')) / has_reviews if has_reviews > 0 else 0
    avg_review_count = sum(r.get('reviews_number', 0) for r in results) / total

    print(f"\nAverage rating: {avg_rating:.1f}/5.0")
    print(f"Average review count: {avg_review_count:.1f}")

    print("\n" + "=" * 70)
    print("TEST SUCCESSFUL!")
    print("=" * 70)
    print("\nData quality looks good! Ready to run full collection:")
    print("python modules/apify/scripts/australia_hospitality_scraper.py")
    print()

    print("Full collection will get:")
    print("- 30 categories (restaurant, cafe, hotel, etc.)")
    print("- Australia + New Zealand")
    print("- ~3,000 total hospitality leads")
    print("- Cost: ~$5.70")
    print("- Time: 2-3 hours")
    print()

except Exception as e:
    print(f"\nERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
