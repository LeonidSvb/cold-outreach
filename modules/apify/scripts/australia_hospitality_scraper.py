#!/usr/bin/env python3
"""
=== AUSTRALIA + NEW ZEALAND HOSPITALITY LEADS SCRAPER ===
Version: 1.0.0 | Created: 2025-11-21

PURPOSE:
Scrape restaurants, cafes, hotels, accommodation businesses from AU + NZ
Optimized for FREE TIER: 100 leads per category limit

STRATEGY:
- Focus on TOP 30 high-value hospitality categories
- 100 leads per category (free tier limit)
- AU + NZ split: 50 leads each country per category
- Total: ~3,000 quality hospitality leads

COST:
~$5.70 for 3,000 leads ($1.90 per 1,000)
OR use free $5 credit from Apify

USAGE:
1. Ensure APIFY_API_KEY in .env
2. Run: python modules/apify/scripts/australia_hospitality_scraper.py
3. Results: modules/apify/results/hospitality_au_nz_{timestamp}.csv
"""

import os
import sys
import time
import json
import csv
from pathlib import Path
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()

APIFY_API_KEY = os.getenv('APIFY_API_KEY')
if not APIFY_API_KEY:
    raise ValueError("APIFY_API_KEY environment variable is required")

ACTOR_ID = 'xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps'
BASE_URL = 'https://api.apify.com/v2'

RESULTS_DIR = Path(__file__).parent.parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# TOP 30 HIGH-VALUE HOSPITALITY CATEGORIES
# Prioritized by business volume and cold outreach potential
CATEGORIES = {
    'Australia': [
        # Tier 1: Core Restaurant & Cafe (10 categories)
        {'category': 'restaurant', 'max_results': 50},
        {'category': 'cafe', 'max_results': 50},
        {'category': 'coffee_shop', 'max_results': 50},
        {'category': 'bar', 'max_results': 50},
        {'category': 'pub', 'max_results': 50},
        {'category': 'fast_food_restaurant', 'max_results': 50},
        {'category': 'pizzeria', 'max_results': 50},
        {'category': 'bakery', 'max_results': 50},
        {'category': 'breakfast_restaurant', 'max_results': 50},
        {'category': 'italian_restaurant', 'max_results': 50},

        # Tier 2: Accommodation (5 categories)
        {'category': 'hotel', 'max_results': 50},
        {'category': 'motel', 'max_results': 50},
        {'category': 'bed_and_breakfast', 'max_results': 50},
        {'category': 'hostel', 'max_results': 50},
        {'category': 'resort_hotel', 'max_results': 50},

        # Tier 3: Specialty Dining (10 categories)
        {'category': 'chinese_restaurant', 'max_results': 50},
        {'category': 'thai_restaurant', 'max_results': 50},
        {'category': 'indian_restaurant', 'max_results': 50},
        {'category': 'japanese_restaurant', 'max_results': 50},
        {'category': 'sushi_restaurant', 'max_results': 50},
        {'category': 'seafood_restaurant', 'max_results': 50},
        {'category': 'steak_house', 'max_results': 50},
        {'category': 'mexican_restaurant', 'max_results': 50},
        {'category': 'french_restaurant', 'max_results': 50},
        {'category': 'vietnamese_restaurant', 'max_results': 50},

        # Tier 4: Quick Service & Specialty (5 categories)
        {'category': 'sandwich_shop', 'max_results': 50},
        {'category': 'hamburger_restaurant', 'max_results': 50},
        {'category': 'ice_cream_shop', 'max_results': 50},
        {'category': 'wine_bar', 'max_results': 50},
        {'category': 'bistro', 'max_results': 50},
    ],

    'New Zealand': [
        # Same 30 categories for NZ
        {'category': 'restaurant', 'max_results': 50},
        {'category': 'cafe', 'max_results': 50},
        {'category': 'coffee_shop', 'max_results': 50},
        {'category': 'bar', 'max_results': 50},
        {'category': 'pub', 'max_results': 50},
        {'category': 'fast_food_restaurant', 'max_results': 50},
        {'category': 'pizzeria', 'max_results': 50},
        {'category': 'bakery', 'max_results': 50},
        {'category': 'breakfast_restaurant', 'max_results': 50},
        {'category': 'italian_restaurant', 'max_results': 50},
        {'category': 'hotel', 'max_results': 50},
        {'category': 'motel', 'max_results': 50},
        {'category': 'bed_and_breakfast', 'max_results': 50},
        {'category': 'hostel', 'max_results': 50},
        {'category': 'resort_hotel', 'max_results': 50},
        {'category': 'chinese_restaurant', 'max_results': 50},
        {'category': 'thai_restaurant', 'max_results': 50},
        {'category': 'indian_restaurant', 'max_results': 50},
        {'category': 'japanese_restaurant', 'max_results': 50},
        {'category': 'sushi_restaurant', 'max_results': 50},
        {'category': 'seafood_restaurant', 'max_results': 50},
        {'category': 'steak_house', 'max_results': 50},
        {'category': 'mexican_restaurant', 'max_results': 50},
        {'category': 'french_restaurant', 'max_results': 50},
        {'category': 'vietnamese_restaurant', 'max_results': 50},
        {'category': 'sandwich_shop', 'max_results': 50},
        {'category': 'hamburger_restaurant', 'max_results': 50},
        {'category': 'ice_cream_shop', 'max_results': 50},
        {'category': 'wine_bar', 'max_results': 50},
        {'category': 'bistro', 'max_results': 50},
    ]
}

COUNTRY_CODES = {
    'Australia': 'AU',
    'New Zealand': 'NZ'
}

STATS = {
    'total_runs': 0,
    'successful_runs': 0,
    'failed_runs': 0,
    'total_leads': 0,
    'total_cost_usd': 0.0
}

ALL_RESULTS = []

def run_actor(country, category, max_results):
    """Start and wait for actor run to complete"""

    country_code = COUNTRY_CODES[country]

    actor_input = {
        'category': category,
        'country': country_code,
        'max_results': max_results
    }

    print(f"\nStarting: {country} - {category} ({max_results} leads)")
    print(f"Input: {json.dumps(actor_input)}")

    # Start run
    api_url = f'{BASE_URL}/acts/{ACTOR_ID.replace("/", "~")}/runs'
    params = {'token': APIFY_API_KEY}

    try:
        response = requests.post(
            api_url,
            json=actor_input,
            headers={'Content-Type': 'application/json'},
            params=params,
            timeout=30
        )

        if response.status_code != 201:
            print(f"ERROR: Failed to start run: {response.status_code}")
            print(f"Response: {response.text}")
            return None

        run_id = response.json()['data']['id']
        print(f"Run ID: {run_id}")

        # Wait for completion
        status_url = f'{BASE_URL}/actor-runs/{run_id}'

        for i in range(120):  # 10 minutes max
            time.sleep(5)

            status_response = requests.get(status_url, params=params, timeout=30)
            status_data = status_response.json()['data']
            status = status_data['status']

            if i % 6 == 0:  # Print every 30 seconds
                print(f"  [{i*5}s] Status: {status}")

            if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
                break

        if status != 'SUCCEEDED':
            print(f"ERROR: Run failed with status: {status}")
            return None

        # Get results
        dataset_id = status_data['defaultDatasetId']
        dataset_url = f'{BASE_URL}/datasets/{dataset_id}/items'

        results_response = requests.get(dataset_url, params=params, timeout=60)
        results = results_response.json()

        # Add metadata
        for result in results:
            result['source_country'] = country
            result['source_category'] = category

        print(f"SUCCESS: Got {len(results)} leads")

        # Calculate cost
        cost = len(results) * 0.0019
        STATS['total_cost_usd'] += cost
        print(f"Cost: ${cost:.4f}")

        return results

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None

def save_results():
    """Save all results to CSV"""

    if not ALL_RESULTS:
        print("\nNo results to save!")
        return

    output_file = RESULTS_DIR / f'hospitality_au_nz_{TIMESTAMP}.csv'

    # Get all unique field names
    fieldnames = set()
    for result in ALL_RESULTS:
        fieldnames.update(result.keys())

    fieldnames = sorted(fieldnames)

    # Ensure key fields are first
    priority_fields = ['name', 'email', 'phone', 'website', 'url', 'address',
                       'city', 'country', 'source_country', 'source_category']

    ordered_fields = []
    for field in priority_fields:
        if field in fieldnames:
            ordered_fields.append(field)
            fieldnames.remove(field)

    ordered_fields.extend(sorted(fieldnames))

    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=ordered_fields)
        writer.writeheader()
        writer.writerows(ALL_RESULTS)

    print(f"\n{'='*70}")
    print(f"RESULTS SAVED")
    print(f"{'='*70}")
    print(f"File: {output_file}")
    print(f"Total leads: {len(ALL_RESULTS)}")
    print(f"File size: {output_file.stat().st_size / 1024:.2f} KB")

def print_summary():
    """Print final summary"""

    print(f"\n{'='*70}")
    print(f"COLLECTION COMPLETE")
    print(f"{'='*70}")
    print(f"Total runs: {STATS['total_runs']}")
    print(f"Successful: {STATS['successful_runs']}")
    print(f"Failed: {STATS['failed_runs']}")
    print(f"Total leads: {STATS['total_leads']}")
    print(f"Total cost: ${STATS['total_cost_usd']:.2f}")
    print(f"Cost per lead: ${STATS['total_cost_usd']/STATS['total_leads']:.4f}")
    print(f"{'='*70}\n")

def main():
    print("="*70)
    print("AUSTRALIA + NEW ZEALAND HOSPITALITY LEADS SCRAPER")
    print("="*70)
    print(f"Target: 30 categories × 2 countries × 50 leads")
    print(f"Expected: ~3,000 hospitality leads")
    print(f"Estimated cost: ~$5.70")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

    # Process each country
    for country, categories in CATEGORIES.items():
        print(f"\n{'='*70}")
        print(f"PROCESSING: {country.upper()}")
        print(f"{'='*70}")
        print(f"Categories: {len(categories)}")

        for i, cat_config in enumerate(categories, 1):
            category = cat_config['category']
            max_results = cat_config['max_results']

            print(f"\n[{i}/{len(categories)}] {category}")

            STATS['total_runs'] += 1

            results = run_actor(country, category, max_results)

            if results:
                STATS['successful_runs'] += 1
                STATS['total_leads'] += len(results)
                ALL_RESULTS.extend(results)
            else:
                STATS['failed_runs'] += 1

            # Rate limiting
            if i < len(categories):
                print("Waiting 10 seconds before next run...")
                time.sleep(10)

    # Save and summarize
    save_results()
    print_summary()

    print("\nNext steps:")
    print("1. Check CSV file in modules/apify/results/")
    print("2. Validate data quality")
    print("3. Import to CRM or outreach tool")
    print("4. Start cold outreach campaigns!")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        if ALL_RESULTS:
            print("Saving partial results...")
            save_results()
            print_summary()
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        if ALL_RESULTS:
            print("\nSaving partial results...")
            save_results()
