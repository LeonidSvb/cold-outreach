#!/usr/bin/env python3
"""
PREMIUM HOSPITALITY LEADS - TOP 50% BY REVENUE
15 highest-value categories only
Target: 1,500 leads ($2.85)
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
    raise ValueError("APIFY_API_KEY not found in .env")

ACTOR_ID = 'xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps'
BASE_URL = 'https://api.apify.com/v2'

RESULTS_DIR = Path(__file__).parent.parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# TOP 15 PREMIUM CATEGORIES (50% highest revenue potential)
CATEGORIES = {
    'Australia': [
        # Accommodation (5) - Highest budgets
        {'category': 'hotel', 'max_results': 50},
        {'category': 'resort_hotel', 'max_results': 50},
        {'category': 'motel', 'max_results': 50},
        {'category': 'bed_and_breakfast', 'max_results': 50},
        {'category': 'hostel', 'max_results': 50},

        # Premium Dining (7) - High ticket
        {'category': 'restaurant', 'max_results': 50},
        {'category': 'steak_house', 'max_results': 50},
        {'category': 'seafood_restaurant', 'max_results': 50},
        {'category': 'french_restaurant', 'max_results': 50},
        {'category': 'japanese_restaurant', 'max_results': 50},
        {'category': 'sushi_restaurant', 'max_results': 50},
        {'category': 'italian_restaurant', 'max_results': 50},

        # Specialty Venues (3) - High margins
        {'category': 'wine_bar', 'max_results': 50},
        {'category': 'bistro', 'max_results': 50},
        {'category': 'cafe', 'max_results': 50},
    ],
    'New Zealand': [
        {'category': 'hotel', 'max_results': 50},
        {'category': 'resort_hotel', 'max_results': 50},
        {'category': 'motel', 'max_results': 50},
        {'category': 'bed_and_breakfast', 'max_results': 50},
        {'category': 'hostel', 'max_results': 50},
        {'category': 'restaurant', 'max_results': 50},
        {'category': 'steak_house', 'max_results': 50},
        {'category': 'seafood_restaurant', 'max_results': 50},
        {'category': 'french_restaurant', 'max_results': 50},
        {'category': 'japanese_restaurant', 'max_results': 50},
        {'category': 'sushi_restaurant', 'max_results': 50},
        {'category': 'italian_restaurant', 'max_results': 50},
        {'category': 'wine_bar', 'max_results': 50},
        {'category': 'bistro', 'max_results': 50},
        {'category': 'cafe', 'max_results': 50},
    ]
}

COUNTRY_CODES = {'Australia': 'AU', 'New Zealand': 'NZ'}
STATS = {'total_runs': 0, 'successful_runs': 0, 'failed_runs': 0, 'total_leads': 0, 'total_cost_usd': 0.0}
ALL_RESULTS = []

def run_actor(country, category, max_results):
    country_code = COUNTRY_CODES[country]
    actor_input = {'category': category, 'country': country_code, 'max_results': max_results}

    print(f"\nStarting: {country} - {category} ({max_results} leads)")

    api_url = f'{BASE_URL}/acts/{ACTOR_ID.replace("/", "~")}/runs'
    params = {'token': APIFY_API_KEY}

    try:
        response = requests.post(api_url, json=actor_input, headers={'Content-Type': 'application/json'}, params=params, timeout=30)

        if response.status_code != 201:
            print(f"ERROR: {response.status_code} - {response.text}")
            return None

        run_id = response.json()['data']['id']
        print(f"Run ID: {run_id}")

        status_url = f'{BASE_URL}/actor-runs/{run_id}'

        for i in range(120):
            time.sleep(5)
            status_response = requests.get(status_url, params=params, timeout=30)
            status_data = status_response.json()['data']
            status = status_data['status']

            if i % 6 == 0:
                print(f"  [{i*5}s] {status}")

            if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
                break

        if status != 'SUCCEEDED':
            print(f"ERROR: Run failed - {status}")
            return None

        dataset_id = status_data['defaultDatasetId']
        dataset_url = f'{BASE_URL}/datasets/{dataset_id}/items'
        results_response = requests.get(dataset_url, params=params, timeout=60)
        results = results_response.json()

        for result in results:
            result['source_country'] = country
            result['source_category'] = category

        print(f"SUCCESS: {len(results)} leads")

        cost = len(results) * 0.0019
        STATS['total_cost_usd'] += cost
        print(f"Cost: ${cost:.4f}")

        return results

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None

def save_results():
    if not ALL_RESULTS:
        print("\nNo results!")
        return

    output_file = RESULTS_DIR / f'premium_hospitality_{TIMESTAMP}.csv'

    fieldnames = set()
    for result in ALL_RESULTS:
        fieldnames.update(result.keys())

    priority = ['name', 'email', 'phone', 'website', 'url', 'address', 'city', 'country', 'source_country', 'source_category']
    ordered = [f for f in priority if f in fieldnames]
    ordered.extend(sorted(fieldnames - set(priority)))

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=ordered)
        writer.writeheader()
        writer.writerows(ALL_RESULTS)

    print(f"\n{'='*70}")
    print(f"SAVED: {output_file}")
    print(f"Total leads: {len(ALL_RESULTS)}")
    print(f"Size: {output_file.stat().st_size / 1024:.2f} KB")
    print(f"{'='*70}")

def main():
    print("="*70)
    print("PREMIUM HOSPITALITY LEADS SCRAPER")
    print("="*70)
    print("Top 15 highest-value categories")
    print("Target: 1,500 premium leads")
    print("Cost: ~$2.85")
    print("="*70)

    for country, categories in CATEGORIES.items():
        print(f"\n{'='*70}")
        print(f"COUNTRY: {country.upper()}")
        print(f"{'='*70}")

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

            if i < len(categories):
                print("Waiting 10s...")
                time.sleep(10)

    save_results()

    print(f"\n{'='*70}")
    print(f"FINAL STATS")
    print(f"{'='*70}")
    print(f"Runs: {STATS['total_runs']} ({STATS['successful_runs']} OK, {STATS['failed_runs']} failed)")
    print(f"Total leads: {STATS['total_leads']}")
    print(f"Total cost: ${STATS['total_cost_usd']:.2f}")
    print(f"Cost/lead: ${STATS['total_cost_usd']/STATS['total_leads']:.4f}" if STATS['total_leads'] > 0 else "N/A")
    print(f"{'='*70}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted!")
        if ALL_RESULTS:
            save_results()
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
