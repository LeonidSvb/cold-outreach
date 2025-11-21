#!/usr/bin/env python3
"""
=== EUROPEAN FIELD SERVICES SCRAPER (TEST: UK + IRELAND) ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Test European market with UK + Ireland before scaling to all 13 countries.
Focus on emergency services with high call volume (perfect for voice agents).

FEATURES:
- Automatic batch processing via Apify API
- Emergency service categories (24/7 operations)
- UK + Ireland coverage (English-speaking markets)
- Progress tracking
- Auto-aggregation to single CSV
- Cost monitoring

USAGE:
1. Ensure APIFY_API_KEY in .env
2. Run: python modules/apify/scripts/europe_business_scraper.py
3. Results: modules/apify/results/europe_test_{timestamp}.csv

TEST PARAMETERS:
- Countries: 2 (UK + Ireland)
- Categories: 9 (emergency services)
- Leads: 1,800 (900 per country)
- Cost: ~$3.42

SCALE-UP PLAN:
If test successful -> expand to all 13 European countries
Total potential: 11,700 leads across Europe (~$22.23)
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

# TEST CONFIGURATION: UK + Ireland
# Emergency services with HIGH CALL VOLUME (best for voice agents)
CATEGORIES = {
    # United Kingdom (900 leads)
    'United Kingdom': [
        {'category': 'plumber', 'max_results': 100},  # Emergency 24/7
        {'category': 'locksmith', 'max_results': 100},  # Emergency lockouts
        {'category': 'hvac_contractor', 'max_results': 100},  # Heating emergencies
        {'category': 'electrician', 'max_results': 100},  # Power emergencies
        {'category': 'towing_service', 'max_results': 100},  # Roadside assistance
        {'category': 'roofing_contractor', 'max_results': 100},  # Leak repairs
        {'category': 'pest_control_service', 'max_results': 100},  # Urgent infestations
        {'category': 'air_conditioning_contractor', 'max_results': 100},  # Summer emergencies
        {'category': 'garage_builder', 'max_results': 100},  # Garage door emergencies
    ],
    # Ireland (900 leads)
    'Ireland': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ]
}

# Country codes for Apify
COUNTRY_CODES = {
    'United Kingdom': 'GB',
    'Ireland': 'IE'
}

# ALL European countries (for future scale-up)
ALL_EUROPEAN_COUNTRIES = {
    'United Kingdom': 'GB',
    'Ireland': 'IE',
    'Switzerland': 'CH',
    'Norway': 'NO',
    'Sweden': 'SE',
    'Denmark': 'DK',
    'Netherlands': 'NL',
    'Finland': 'FI',
    'Belgium': 'BE',
    'Germany': 'DE',
    'France': 'FR',
    'Italy': 'IT',
    'Spain': 'ES'
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
    print(" EUROPEAN FIELD SERVICES SCRAPER - TEST MODE")
    print("=" * 80)
    print(f"Target: 1,800 leads (TEST)")
    print(f"Countries: UK + Ireland (English-speaking)")
    print(f"Categories: 9 emergency services (high call volume)")
    print(f"Actor: {ACTOR_ID}")
    print(f"Timestamp: {TIMESTAMP}")
    print("=" * 80)
    print()
    print("NOTE: This is a TEST run on 2 countries.")
    print("If successful, scale to all 13 European countries (11,700 leads)")
    print()

def run_actor(category, country, max_results):
    """
    Run Apify actor for a specific category and country

    Args:
        category: Business category (e.g., 'plumber', 'locksmith')
        country: Country name ('United Kingdom' or 'Ireland')
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

        for attempt in range(120):  # Max 10 minutes (5 sec x 120)
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

        print(f"SUCCESS: {len(results)} leads collected")

        # Calculate cost
        cost = (len(results) / 1000) * 1.90
        STATS['estimated_cost'] += cost
        STATS['total_leads'] += len(results)

        print(f"   Cost: ${cost:.4f}")
        print()

        return results

    except Exception as e:
        print(f"ERROR: {str(e)}")
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

    output_file = RESULTS_DIR / f'europe_test_{TIMESTAMP}.csv'

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
    print(" TEST SUMMARY")
    print("=" * 80)
    print(f"Total runs: {STATS['total_runs']}")
    print(f"Successful: {STATS['successful_runs']}")
    print(f"Failed: {STATS['failed_runs']}")
    print(f"Total leads collected: {STATS['total_leads']}")
    print(f"Estimated cost: ${STATS['estimated_cost']:.2f}")
    print(f"Duration: {duration:.1f} minutes")
    if STATS['total_leads'] > 0:
        print(f"Cost per lead: ${STATS['estimated_cost'] / STATS['total_leads']:.4f}")
    print("=" * 80)
    print()
    print("NEXT STEP: If results look good, scale to all 13 European countries")
    print("Expected: 11,700 leads for ~$22.23")

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
        json_file = RESULTS_DIR / f'europe_test_detailed_{TIMESTAMP}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': TIMESTAMP,
                    'total_leads': STATS['total_leads'],
                    'countries': list(CATEGORIES.keys()),
                    'test_mode': True,
                    'next_step': 'Scale to all 13 European countries if successful'
                },
                'results': all_results
            }, f, indent=2, default=str)

        print(f"\nSUCCESS: Detailed JSON saved to: {json_file}")

    # Print summary
    print_summary()

    print("\n TEST COMPLETE!")
    print(f" Output files in: {RESULTS_DIR}")
    print()

if __name__ == "__main__":
    main()
