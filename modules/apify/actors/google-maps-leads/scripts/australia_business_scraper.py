#!/usr/bin/env python3
"""
=== AUSTRALIA + NEW ZEALAND BUSINESS LEADS SCRAPER ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Automatically scrape 1,500+ business leads from Australia and New Zealand
using Apify actor "9+ Million Business Leads With Emails"

FEATURES:
- Automatic batch processing via Apify API
- Multiple categories (field services)
- AU + NZ coverage
- Progress tracking
- Auto-aggregation to single CSV
- Cost monitoring

USAGE:
1. Ensure APIFY_API_KEY in .env
2. Run: python modules/apify/scripts/australia_business_scraper.py
3. Results: modules/apify/results/australia_nz_combined_{timestamp}.csv

COST:
~$2.85 for 1,500 leads ($1.90 per 1,000)
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

# Load environment
load_dotenv()

# Configuration
APIFY_API_KEY = os.getenv('APIFY_API_KEY')
if not APIFY_API_KEY:
    raise ValueError("APIFY_API_KEY environment variable is required")
ACTOR_ID = 'xmiso_scrapers/millions-us-businesses-leads-with-emails-from-google-maps'
BASE_URL = 'https://api.apify.com/v2'

# Output directory
RESULTS_DIR = Path(__file__).parent.parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

# Timestamp for this run
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Categories configuration for 1,500 leads
# Based on field service niches (voice agents for local businesses)
# CORRECTED category names from Apify allowed values list
CATEGORIES = {
    # Australia (1,050 leads = 70%)
    'Australia': [
        {'category': 'hvac_contractor', 'max_results': 150},
        {'category': 'air_conditioning_contractor', 'max_results': 120},
        {'category': 'electrician', 'max_results': 120},
        {'category': 'plumber', 'max_results': 120},
        {'category': 'landscaper', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 90},
        {'category': 'roofing_contractor', 'max_results': 80},
        {'category': 'locksmith', 'max_results': 70},
        {'category': 'garage_builder', 'max_results': 60},
        {'category': 'tree_service', 'max_results': 60},
        {'category': 'pool_cleaning_service', 'max_results': 50},
        {'category': 'towing_service', 'max_results': 30},
    ],
    # New Zealand (450 leads = 30%)
    'New Zealand': [
        {'category': 'hvac_contractor', 'max_results': 60},
        {'category': 'electrician', 'max_results': 60},
        {'category': 'plumber', 'max_results': 60},
        {'category': 'air_conditioning_contractor', 'max_results': 50},
        {'category': 'landscaper', 'max_results': 45},
        {'category': 'roofing_contractor', 'max_results': 40},
        {'category': 'locksmith', 'max_results': 35},
        {'category': 'pest_control_service', 'max_results': 30},
        {'category': 'tree_service', 'max_results': 30},
        {'category': 'garage_builder', 'max_results': 25},
        {'category': 'towing_service', 'max_results': 15},
    ]
}

# Country codes for Apify
COUNTRY_CODES = {
    'Australia': 'AU',
    'New Zealand': 'NZ'
}

# Tracking
STATS = {
    'total_runs': 0,
    'successful_runs': 0,
    'failed_runs': 0,
    'total_leads': 0,
    'estimated_cost': 0.0,
    'start_time': None,
    'end_time': None
}

def print_banner():
    """Print script banner"""
    print("=" * 80)
    print(" AUSTRALIA + NEW ZEALAND BUSINESS LEADS SCRAPER")
    print("=" * 80)
    print(f"Target: 1,500 leads")
    print(f"Countries: Australia (70%), New Zealand (30%)")
    print(f"Actor: {ACTOR_ID}")
    print(f"Timestamp: {TIMESTAMP}")
    print("=" * 80)
    print()

def run_actor(category, country, max_results):
    """
    Run Apify actor for a specific category and country

    Args:
        category: Business category (e.g., 'hvac', 'electrician')
        country: Country name ('Australia' or 'New Zealand')
        max_results: Maximum number of results to fetch

    Returns:
        List of business leads or None if failed
    """
    print(f" Running: {category} | {country} | Max: {max_results}")

    # Prepare actor input
    actor_input = {
        "category": category,
        "country": COUNTRY_CODES[country],
        "max_results": max_results
    }

    # Start actor run
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
            print(f"   Response: {response.text[:200]}")
            return None

        run_id = response.json()['data']['id']
        print(f"   Run ID: {run_id}")

        # Wait for completion
        status_url = f'{BASE_URL}/actor-runs/{run_id}'

        for attempt in range(120):  # Max 10 minutes (5 sec × 120)
            time.sleep(5)

            status_response = requests.get(status_url, params=params, timeout=30)
            status_data = status_response.json()['data']
            status = status_data['status']

            if attempt % 6 == 0:  # Print every 30 seconds
                print(f"   Status: {status} ({attempt * 5}s)")

            if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
                break

        if status != 'SUCCEEDED':
            print(f"ERROR: Run failed: {status}")
            return None

        # Get results
        dataset_id = status_data['defaultDatasetId']
        dataset_url = f'{BASE_URL}/datasets/{dataset_id}/items'

        results_response = requests.get(dataset_url, params=params, timeout=60)
        results = results_response.json()

        print(f"SUCCESS: Success: {len(results)} leads collected")

        # Calculate cost
        cost = (len(results) / 1000) * 1.90
        STATS['estimated_cost'] += cost
        STATS['total_leads'] += len(results)

        print(f"   Cost: ${cost:.4f}")
        print()

        return results

    except Exception as e:
        print(f"ERROR: Error: {str(e)}")
        return None

def aggregate_results(all_results):
    """
    Aggregate all results into single CSV file

    Args:
        all_results: List of dicts containing country, category, and leads data

    Returns:
        Path to output CSV file
    """
    print("\n" + "=" * 80)
    print(" AGGREGATING RESULTS")
    print("=" * 80)

    output_file = RESULTS_DIR / f'australia_nz_combined_{TIMESTAMP}.csv'

    # Collect all unique field names
    all_fields = set()
    for result in all_results:
        for lead in result['leads']:
            all_fields.update(lead.keys())

    # Add metadata fields
    all_fields.update(['source_country', 'source_category'])

    # Sort fields for consistent column order
    fieldnames = sorted(list(all_fields))

    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in all_results:
            for lead in result['leads']:
                # Add metadata
                lead['source_country'] = result['country']
                lead['source_category'] = result['category']
                writer.writerow(lead)

    print(f"\nSUCCESS: Results saved to: {output_file}")
    print(f"   Total leads: {STATS['total_leads']}")
    print(f"   Unique fields: {len(fieldnames)}")

    return output_file

def print_summary():
    """Print final summary"""
    duration = (STATS['end_time'] - STATS['start_time']).total_seconds() / 60

    print("\n" + "=" * 80)
    print(" FINAL SUMMARY")
    print("=" * 80)
    print(f"Total runs: {STATS['total_runs']}")
    print(f"Successful: {STATS['successful_runs']}")
    print(f"Failed: {STATS['failed_runs']}")
    print(f"Total leads collected: {STATS['total_leads']}")
    print(f"Estimated cost: ${STATS['estimated_cost']:.2f}")
    print(f"Duration: {duration:.1f} minutes")
    print(f"Cost per lead: ${STATS['estimated_cost'] / STATS['total_leads']:.4f}")
    print("=" * 80)

def main():
    """Main execution"""
    print_banner()

    STATS['start_time'] = datetime.now()
    all_results = []

    # Process each country
    for country, categories in CATEGORIES.items():
        print(f"\n{'='*80}")
        print(f" PROCESSING: {country}")
        print(f"{'='*80}\n")

        for cat_config in categories:
            category = cat_config['category']
            max_results = cat_config['max_results']

            STATS['total_runs'] += 1

            # Run actor
            leads = run_actor(category, country, max_results)

            if leads:
                STATS['successful_runs'] += 1
                all_results.append({
                    'country': country,
                    'category': category,
                    'leads': leads
                })
            else:
                STATS['failed_runs'] += 1

            # Small delay between runs
            time.sleep(2)

    STATS['end_time'] = datetime.now()

    # Aggregate all results
    if all_results:
        output_file = aggregate_results(all_results)

        # Also save detailed JSON
        json_file = RESULTS_DIR / f'australia_nz_detailed_{TIMESTAMP}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': TIMESTAMP,
                    'total_leads': STATS['total_leads'],
                    'countries': list(CATEGORIES.keys()),
                    'stats': STATS
                },
                'results': all_results
            }, f, indent=2)

        print(f"\nSUCCESS: Detailed JSON saved to: {json_file}")

    # Print summary
    print_summary()

    print("\n SCRAPING COMPLETE!")
    print(f" Output files in: {RESULTS_DIR}")
    print()

if __name__ == "__main__":
    main()
