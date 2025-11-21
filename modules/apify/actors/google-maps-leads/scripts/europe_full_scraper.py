#!/usr/bin/env python3
"""
=== FULL EUROPEAN FIELD SERVICES SCRAPER ===
Version: 2.0.0 | Created: 2025-11-11

PURPOSE:
Collect emergency service leads from ALL 13 rich European countries.
Focus on high call volume businesses (perfect for voice agents).

FEATURES:
- 13 European countries coverage
- 9 emergency service categories
- Parquet format (compressed, space-efficient)
- CSV fallback format
- Progress tracking
- Cost monitoring

USAGE:
1. Ensure APIFY_API_KEY in .env
2. Run: python modules/apify/scripts/europe_full_scraper.py
3. Results: modules/apify/results/europe_full_{timestamp}.parquet

FULL PARAMETERS:
- Countries: 13 (GB, IE, CH, NO, SE, DK, NL, FI, BE, DE, FR, IT, ES)
- Categories: 9 (emergency services)
- Expected leads: ~11,000-11,700
- Cost: ~$21-22
- Duration: ~40-50 minutes
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
import pandas as pd

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

# ALL 13 EUROPEAN COUNTRIES - FULL COLLECTION
# Emergency services with HIGH CALL VOLUME (best for voice agents)
CATEGORIES = {
    # TIER 1: English-speaking
    'United Kingdom': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
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
    ],

    # TIER 2: Rich Nordic + Switzerland
    'Switzerland': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
    'Norway': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
    'Sweden': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
    'Denmark': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
    'Netherlands': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
    'Finland': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],

    # TIER 3: Western Europe
    'Belgium': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
    'Germany': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
    'France': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
    'Italy': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
    'Spain': [
        {'category': 'plumber', 'max_results': 100},
        {'category': 'locksmith', 'max_results': 100},
        {'category': 'hvac_contractor', 'max_results': 100},
        {'category': 'electrician', 'max_results': 100},
        {'category': 'towing_service', 'max_results': 100},
        {'category': 'roofing_contractor', 'max_results': 100},
        {'category': 'pest_control_service', 'max_results': 100},
        {'category': 'air_conditioning_contractor', 'max_results': 100},
        {'category': 'garage_builder', 'max_results': 100},
    ],
}

# Country codes for Apify
COUNTRY_CODES = {
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
    'end_time': None,
    'countries_completed': 0,
    'countries_total': len(CATEGORIES)
}

def print_banner():
    """Print script banner"""
    print("=" * 80)
    print(" FULL EUROPEAN FIELD SERVICES SCRAPER")
    print("=" * 80)
    print(f"Target: ~11,000+ leads")
    print(f"Countries: 13 European countries")
    print(f"Categories: 9 emergency services (high call volume)")
    print(f"Actor: {ACTOR_ID}")
    print(f"Timestamp: {TIMESTAMP}")
    print("=" * 80)
    print()
    print("Countries to process:")
    for i, country in enumerate(CATEGORIES.keys(), 1):
        print(f"  {i:2}. {country}")
    print()
    print(f"Total runs: {len(CATEGORIES)} countries x 9 categories = {len(CATEGORIES) * 9} runs")
    print(f"Expected cost: ~${len(CATEGORIES) * 9 * 0.19:.2f}")
    print(f"Expected duration: ~40-50 minutes")
    print()

def run_actor(category, country, max_results):
    """
    Run Apify actor for a specific category and country
    """
    print(f" Running: {category} | {country} | Max: {max_results}")

    actor_input = {
        "category": category,
        "country": COUNTRY_CODES[country],
        "max_results": max_results
    }

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
            return None

        run_id = response.json()['data']['id']
        print(f"   Run ID: {run_id}")

        # Wait for completion
        status_url = f'{BASE_URL}/actor-runs/{run_id}'

        for attempt in range(120):
            time.sleep(5)

            status_response = requests.get(status_url, params=params, timeout=30)
            status_data = status_response.json()['data']
            status = status_data['status']

            if attempt % 6 == 0:
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

        cost = (len(results) / 1000) * 1.90
        STATS['estimated_cost'] += cost
        STATS['total_leads'] += len(results)

        print(f"   Cost: ${cost:.4f}")
        print()

        return results

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return None

def save_results_parquet(all_results):
    """
    Save results in Parquet format (compressed, space-efficient)
    """
    print("\n" + "=" * 80)
    print(" SAVING RESULTS (PARQUET FORMAT)")
    print("=" * 80)

    # Flatten all results
    all_leads = []
    for result in all_results:
        for lead in result['leads']:
            lead['source_country'] = result['country']
            lead['source_category'] = result['category']
            all_leads.append(lead)

    # Convert to DataFrame
    df = pd.DataFrame(all_leads)

    # Save as Parquet (compressed)
    parquet_file = RESULTS_DIR / f'europe_full_{TIMESTAMP}.parquet'
    df.to_parquet(parquet_file, compression='snappy', index=False)

    # Also save as CSV for compatibility
    csv_file = RESULTS_DIR / f'europe_full_{TIMESTAMP}.csv'
    df.to_csv(csv_file, index=False)

    # Calculate file sizes
    parquet_size = parquet_file.stat().st_size / (1024 * 1024)  # MB
    csv_size = csv_file.stat().st_size / (1024 * 1024)  # MB
    compression_ratio = (1 - parquet_size / csv_size) * 100

    print(f"\nSUCCESS: Results saved!")
    print(f"  Parquet: {parquet_file}")
    print(f"  CSV: {csv_file}")
    print()
    print(f"File sizes:")
    print(f"  Parquet: {parquet_size:.2f} MB")
    print(f"  CSV: {csv_size:.2f} MB")
    print(f"  Space saved: {compression_ratio:.1f}%")
    print()
    print(f"Total leads: {len(df)}")
    print(f"Unique fields: {len(df.columns)}")

    return parquet_file

def print_progress():
    """Print current progress"""
    progress = (STATS['countries_completed'] / STATS['countries_total']) * 100
    print(f"\n{'='*80}")
    print(f" PROGRESS: {STATS['countries_completed']}/{STATS['countries_total']} countries ({progress:.1f}%)")
    print(f" Leads collected: {STATS['total_leads']} | Cost so far: ${STATS['estimated_cost']:.2f}")
    print(f"{'='*80}\n")

def print_summary():
    """Print final summary"""
    duration = (STATS['end_time'] - STATS['start_time']).total_seconds() / 60

    print("\n" + "=" * 80)
    print(" FINAL SUMMARY")
    print("=" * 80)
    print(f"Countries processed: {STATS['countries_completed']}/{STATS['countries_total']}")
    print(f"Total runs: {STATS['total_runs']}")
    print(f"Successful: {STATS['successful_runs']}")
    print(f"Failed: {STATS['failed_runs']}")
    print(f"Total leads collected: {STATS['total_leads']}")
    print(f"Estimated cost: ${STATS['estimated_cost']:.2f}")
    print(f"Duration: {duration:.1f} minutes")
    if STATS['total_leads'] > 0:
        print(f"Cost per lead: ${STATS['estimated_cost'] / STATS['total_leads']:.4f}")
    print("=" * 80)

def main():
    """Main execution"""
    print_banner()

    STATS['start_time'] = datetime.now()
    all_results = []

    # Process each country
    for country_idx, (country, categories) in enumerate(CATEGORIES.items(), 1):
        print(f"\n{'='*80}")
        print(f" PROCESSING: {country} ({country_idx}/{len(CATEGORIES)})")
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

            # Delay between runs (avoid rate limiting)
            time.sleep(10)

        STATS['countries_completed'] += 1
        print_progress()

    STATS['end_time'] = datetime.now()

    # Save results
    if all_results:
        parquet_file = save_results_parquet(all_results)

        # Also save detailed JSON
        json_file = RESULTS_DIR / f'europe_full_detailed_{TIMESTAMP}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'timestamp': TIMESTAMP,
                    'total_leads': STATS['total_leads'],
                    'countries': list(CATEGORIES.keys()),
                    'stats': STATS
                },
                'results': all_results
            }, f, indent=2, default=str)

        print(f"\nSUCCESS: Detailed JSON saved to: {json_file}")

    # Print summary
    print_summary()

    print("\n FULL EUROPE COLLECTION COMPLETE!")
    print(f" Output files in: {RESULTS_DIR}")
    print()

if __name__ == "__main__":
    main()
