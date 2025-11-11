#!/usr/bin/env python3
"""
Download results from manual Apify runs
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime
from apify_client import ApifyClient

# Configuration
APIFY_API_KEY = os.getenv('APIFY_API_KEY')
if not APIFY_API_KEY:
    raise ValueError("APIFY_API_KEY environment variable is required")
MANUAL_RUN_IDS = ['f5hcgdr4Pr14BUpaP']  # Your manual run

# Output directory
RESULTS_DIR = Path(__file__).parent.parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

client = ApifyClient(APIFY_API_KEY)

print("=" * 70)
print("DOWNLOADING MANUAL RUN RESULTS")
print("=" * 70)
print()

all_manual_leads = []

for run_id in MANUAL_RUN_IDS:
    print(f"Processing run: {run_id}")

    try:
        # Get run details
        run = client.run(run_id).get()
        dataset_id = run.get('defaultDatasetId')

        if not dataset_id:
            print(f"  No dataset found")
            continue

        # Get items
        items = client.dataset(dataset_id).list_items().items

        print(f"  Downloaded: {len(items)} leads")

        # Add metadata
        for item in items:
            item['source_type'] = 'manual_run'
            item['source_run_id'] = run_id

        all_manual_leads.extend(items)

    except Exception as e:
        print(f"  ERROR: {e}")

print()
print(f"Total manual leads: {len(all_manual_leads)}")

# Save to CSV
if all_manual_leads:
    output_file = RESULTS_DIR / f'manual_runs_{TIMESTAMP}.csv'

    # Get all field names
    fieldnames = set()
    for lead in all_manual_leads:
        fieldnames.update(lead.keys())

    fieldnames = sorted(list(fieldnames))

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_manual_leads)

    print(f"\nSaved to: {output_file}")
    print(f"Fields: {len(fieldnames)}")

    # Also save JSON
    json_file = RESULTS_DIR / f'manual_runs_{TIMESTAMP}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(all_manual_leads, f, indent=2)

    print(f"JSON backup: {json_file}")

print("\nDone!")
