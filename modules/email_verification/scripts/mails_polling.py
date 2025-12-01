#!/usr/bin/env python3
"""
=== MAILS.SO BATCH POLLING ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Poll Mails.so API for batch validation results

FEATURES:
- Automatic polling with smart intervals
- Progress tracking
- Save results when complete

USAGE:
python modules/email_verification/mails_polling.py --batch-id 0b5206fb-ecb1-4b53-b1bb-6a92ed87c1f1
"""

import requests
import time
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

API_KEY = 'c6c76660-b774-4dcc-be3f-64cdb999e70f'
BASE_URL = 'https://api.mails.so/v1/batch'

def check_batch_status(batch_id: str):
    """Check batch validation status"""
    url = f'{BASE_URL}/{batch_id}'
    headers = {'x-mails-api-key': API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error: {response.status_code} - {response.text}')
            return None

    except Exception as e:
        print(f'Request failed: {e}')
        return None

def poll_until_complete(batch_id: str, max_wait_minutes: int = 30):
    """Poll batch status until complete"""

    print('=' * 80)
    print('MAILS.SO BATCH POLLING')
    print('=' * 80)
    print(f'Batch ID: {batch_id}')
    print(f'Max wait: {max_wait_minutes} minutes')
    print()

    start_time = time.time()
    iteration = 0

    while True:
        iteration += 1
        elapsed = time.time() - start_time
        elapsed_min = int(elapsed / 60)

        print(f'[{datetime.now().strftime("%H:%M:%S")}] Check #{iteration} (elapsed: {elapsed_min}m)...')

        result = check_batch_status(batch_id)

        if not result:
            print('  Failed to get status, retrying in 15s...')
            time.sleep(15)
            continue

        finished_at = result.get('finished_at')
        size = result.get('size', 0)

        if finished_at:
            print()
            print('=' * 80)
            print('BATCH COMPLETE!')
            print('=' * 80)
            print(f'Finished at: {finished_at}')
            print(f'Total emails: {size}')

            # Save results
            save_results(result, batch_id)
            break
        else:
            print(f'  Status: Processing... ({size} emails)')

        # Check timeout
        if elapsed > max_wait_minutes * 60:
            print()
            print('=' * 80)
            print('TIMEOUT REACHED')
            print('=' * 80)
            print(f'Batch still not complete after {max_wait_minutes} minutes')
            print('Run this script again later to check status')
            break

        # Smart polling interval
        if elapsed < 60:
            wait = 10  # First minute: check every 10s
        elif elapsed < 300:
            wait = 30  # 1-5 min: check every 30s
        else:
            wait = 60  # After 5 min: check every 60s

        print(f'  Next check in {wait}s...')
        print()
        time.sleep(wait)

def save_results(result: dict, batch_id: str):
    """Save validation results to CSV"""

    emails_data = result.get('emails', [])

    if not emails_data:
        print('No email results found in response')
        return

    # Convert to DataFrame
    df = pd.DataFrame(emails_data)

    # Save full results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = Path(f'C:/Users/79818/Downloads/mails_validated_{timestamp}.csv')
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    print(f'Full results saved: {output_file}')
    print()

    # Statistics
    total = len(df)
    deliverable = (df['result'] == 'deliverable').sum()
    unknown = (df['result'] == 'unknown').sum()
    risky = (df['result'] == 'risky').sum()
    undeliverable = (df['result'] == 'undeliverable').sum()

    print('VALIDATION RESULTS:')
    print(f'  Total: {total}')
    print(f'  Deliverable: {deliverable} ({deliverable/total*100:.1f}%)')
    print(f'  Unknown: {unknown} ({unknown/total*100:.1f}%)')
    print(f'  Risky: {risky} ({risky/total*100:.1f}%)')
    print(f'  Undeliverable: {undeliverable} ({undeliverable/total*100:.1f}%)')
    print()

    # Save deliverable only
    df_deliverable = df[df['result'] == 'deliverable'].copy()
    if len(df_deliverable) > 0:
        deliverable_file = Path(f'C:/Users/79818/Downloads/mails_DELIVERABLE_{timestamp}.csv')
        df_deliverable.to_csv(deliverable_file, index=False, encoding='utf-8-sig')
        print(f'Deliverable only ({len(df_deliverable)} emails): {deliverable_file}')

    # Save JSON
    json_file = Path(f'C:/Users/79818/Downloads/mails_full_response_{timestamp}.json')
    with open(json_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f'Full JSON response: {json_file}')
    print()

def main():
    parser = argparse.ArgumentParser(description='Poll Mails.so batch validation')
    parser.add_argument('--batch-id', default='0b5206fb-ecb1-4b53-b1bb-6a92ed87c1f1',
                       help='Batch ID to poll')
    parser.add_argument('--max-wait', type=int, default=30,
                       help='Maximum wait time in minutes (default: 30)')

    args = parser.parse_args()

    poll_until_complete(args.batch_id, args.max_wait)

if __name__ == '__main__':
    main()
