#!/usr/bin/env python3
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
sys.path.insert(0, 'modules/email_verification')
from validator import MailsValidator

BATCH_ID = 'c6c76660-b774-4dcc-be3f-64cdb999e70f'
API_KEY = input("API key: ").strip()

validator = MailsValidator(API_KEY)
print(f"Fetching batch {BATCH_ID}...")

result = validator.check_status(BATCH_ID)
if not result:
    print("Error: Could not get batch")
    sys.exit(1)

if not result.get('finished_at'):
    print("Waiting for completion...")
    result = validator.poll_results(BATCH_ID, max_wait_minutes=10, callback=lambda i, e: print(f"#{i} ({e}s)"))
    if not result:
        print("Timeout!")
        sys.exit(1)

print("Processing...")
results_df = validator.process_results(result)

# Load original
orig_file = Path('modules/scraping/homepage_email_scraper/results/scraped_20251120_235438/success.csv')
if orig_file.exists():
    orig_df = pd.read_csv(orig_file)
    merged = results_df.merge(orig_df, on='email', how='left')
else:
    merged = results_df

# Stats
stats = validator.get_statistics(results_df)
print(f"\nTotal: {stats['total']}")
print(f"Deliverable: {stats['deliverable']} ({stats['deliverable_pct']:.1f}%)")
print(f"Unknown: {stats['unknown']} ({stats['unknown_pct']:.1f}%)")
print(f"Undeliverable: {stats['undeliverable']} ({stats['undeliverable_pct']:.1f}%)")

# Save
downloads = Path.home() / 'Downloads'
ts = datetime.now().strftime('%Y%m%d_%H%M%S')

# All
all_f = downloads / f'validated_all_{ts}.csv'
merged.to_csv(all_f, index=False, encoding='utf-8-sig')
print(f"\nSaved: {all_f.name}")

# Deliverable
deliv = validator.filter_by_result(merged, 'deliverable')
deliv_f = downloads / f'validated_deliverable_{ts}.csv'
deliv.to_csv(deliv_f, index=False, encoding='utf-8-sig')
print(f"Saved: {deliv_f.name} ({len(deliv)} rows)")

# Corporate
if 'is_free' in deliv.columns:
    corp = validator.filter_corporate_only(deliv)
    corp_f = downloads / f'validated_corporate_{ts}.csv'
    corp.to_csv(corp_f, index=False, encoding='utf-8-sig')
    print(f"Saved: {corp_f.name} ({len(corp)} rows)")

print("\nDone!")
