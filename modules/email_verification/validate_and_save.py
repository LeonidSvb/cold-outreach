#!/usr/bin/env python3
"""
Quick validation script for scraped emails
Validates and saves to Downloads folder
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import os

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from validator import MailsValidator

# Get API key
API_KEY = input("Enter Mails.so API key: ").strip()

if not API_KEY:
    print("Error: API key required")
    sys.exit(1)

# Load success CSV
success_file = Path('modules/scraping/homepage_email_scraper/results/scraped_20251120_235438/success.csv')
df = pd.read_csv(success_file)

# Get unique emails
emails = df['email'].dropna().unique().tolist()

print(f"\n{'='*80}")
print(f"STARTING VALIDATION")
print(f"{'='*80}")
print(f"Total unique emails: {len(emails)}")
print(f"First 5: {emails[:5]}")
print()

# Initialize validator
validator = MailsValidator(API_KEY)

# Submit batch
print("Submitting batch to Mails.so...")
result = validator.submit_batch(emails, name="AU_Client_Scraping")

if not result['success']:
    print(f"Error: {result.get('error')}")
    sys.exit(1)

batch_id = result['batch_id']
print(f"Batch submitted! ID: {batch_id}")
print(f"Size: {result['size']} emails")
print()

# Poll for results
print("Waiting for validation (max 10 minutes)...")
def progress_callback(iteration, elapsed):
    print(f"Check #{iteration} (elapsed: {elapsed}s)")

validation_results = validator.poll_results(
    batch_id,
    max_wait_minutes=10,
    callback=progress_callback
)

if not validation_results:
    print("Validation timed out!")
    sys.exit(1)

print("\nValidation complete!")

# Process results
results_df = validator.process_results(validation_results)

# Merge with original data
merged_df = results_df.merge(df, on='email', how='left')

# Get statistics
stats = validator.get_statistics(results_df)

print(f"\n{'='*80}")
print("VALIDATION RESULTS")
print(f"{'='*80}")
print(f"Total: {stats['total']}")
print(f"Deliverable: {stats['deliverable']} ({stats['deliverable_pct']:.1f}%)")
print(f"Unknown: {stats['unknown']} ({stats['unknown_pct']:.1f}%)")
print(f"Risky: {stats['risky']} ({stats['risky_pct']:.1f}%)")
print(f"Undeliverable: {stats['undeliverable']} ({stats['undeliverable_pct']:.1f}%)")
print()

# Save to Downloads
downloads_folder = Path.home() / 'Downloads'
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# All results
all_file = downloads_folder / f'validated_all_{timestamp}.csv'
merged_df.to_csv(all_file, index=False, encoding='utf-8-sig')
print(f"Saved all results: {all_file.name}")

# Deliverable only
deliverable_df = validator.filter_by_result(merged_df, 'deliverable')
deliverable_file = downloads_folder / f'validated_deliverable_{timestamp}.csv'
deliverable_df.to_csv(deliverable_file, index=False, encoding='utf-8-sig')
print(f"Saved deliverable only: {deliverable_file.name} ({len(deliverable_df)} rows)")

# Corporate only
corporate_df = validator.filter_corporate_only(deliverable_df)
corporate_file = downloads_folder / f'validated_corporate_{timestamp}.csv'
corporate_df.to_csv(corporate_file, index=False, encoding='utf-8-sig')
print(f"Saved corporate only: {corporate_file.name} ({len(corporate_df)} rows)")

print(f"\n{'='*80}")
print("ALL FILES SAVED TO DOWNLOADS FOLDER")
print(f"{'='*80}")
