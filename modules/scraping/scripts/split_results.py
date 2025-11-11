#!/usr/bin/env python3
"""
=== SPLIT ENRICHMENT RESULTS ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Split enriched results into 3 separate files:
1. WITH_EMAILS.csv - Successfully scraped + has emails
2. WITH_PHONES_ONLY.csv - Successfully scraped + no emails but has phone
3. FAILED_SCRAPING.csv - Failed to scrape (for other services)

USAGE:
python split_results.py --input enriched_results.csv

OUTPUT:
- {input_stem}_WITH_EMAILS.csv
- {input_stem}_WITH_PHONES_ONLY.csv
- {input_stem}_FAILED_SCRAPING.csv
"""

import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime

def split_enrichment_results(input_file: Path):
    """Split enrichment results into 3 files"""

    print("=" * 80)
    print("SPLITTING ENRICHMENT RESULTS")
    print("=" * 80)
    print(f"Input file: {input_file}")
    print()

    # Load data
    df = pd.read_csv(input_file)
    total = len(df)

    print(f"Total leads: {total}")
    print()

    # 1. WITH EMAILS - successfully scraped + has emails
    with_emails = df[
        (df['processing_status'] == 'success') &
        (df['emails'].notna()) &
        (df['emails'] != '')
    ].copy()

    # 2. WITH PHONES ONLY - successfully scraped + no emails but has phone
    with_phones_only = df[
        (df['processing_status'] == 'success') &
        ((df['emails'].isna()) | (df['emails'] == '')) &
        (df['phone'].notna()) &
        (df['phone'] != '')
    ].copy()

    # 3. FAILED SCRAPING - failed to scrape (for other services)
    failed_scraping = df[
        df['processing_status'].isin(['scraping_failed', 'no_website'])
    ].copy()

    # Stats
    print("=" * 80)
    print("SPLIT STATISTICS")
    print("=" * 80)
    print(f"WITH EMAILS:        {len(with_emails):>5} ({len(with_emails)/total*100:>5.1f}%)")
    print(f"WITH PHONES ONLY:   {len(with_phones_only):>5} ({len(with_phones_only)/total*100:>5.1f}%)")
    print(f"FAILED SCRAPING:    {len(failed_scraping):>5} ({len(failed_scraping)/total*100:>5.1f}%)")
    print(f"{'':->80}")
    print(f"TOTAL:              {total:>5}")
    print()

    # Prepare output paths
    output_dir = input_file.parent
    input_stem = input_file.stem

    file_with_emails = output_dir / f"{input_stem}_WITH_EMAILS.csv"
    file_with_phones = output_dir / f"{input_stem}_WITH_PHONES_ONLY.csv"
    file_failed = output_dir / f"{input_stem}_FAILED_SCRAPING.csv"

    # Save files
    print("=" * 80)
    print("SAVING FILES")
    print("=" * 80)

    # 1. WITH EMAILS - all columns
    with_emails.to_csv(file_with_emails, index=False, encoding='utf-8')
    print(f"✓ WITH EMAILS:      {file_with_emails.name}")
    print(f"  Total: {len(with_emails)} leads")

    # 2. WITH PHONES ONLY - all columns
    with_phones_only.to_csv(file_with_phones, index=False, encoding='utf-8')
    print(f"✓ WITH PHONES ONLY: {file_with_phones.name}")
    print(f"  Total: {len(with_phones_only)} leads")

    # 3. FAILED SCRAPING - only essential columns (place_id, name, website, phone, address)
    failed_columns = ['place_id', 'name', 'website', 'phone', 'address', 'processing_status']
    failed_scraping_subset = failed_scraping[failed_columns].copy()
    failed_scraping_subset.to_csv(file_failed, index=False, encoding='utf-8')
    print(f"✓ FAILED SCRAPING:  {file_failed.name}")
    print(f"  Total: {len(failed_scraping)} leads")

    print()
    print("=" * 80)
    print("SPLIT COMPLETED")
    print("=" * 80)

    # Summary by relevance for WITH_EMAILS
    if 'relevance_score' in with_emails.columns:
        print()
        print("WITH_EMAILS - RELEVANCE BREAKDOWN:")
        high_rel = len(with_emails[with_emails['relevance_score'] >= 7])
        med_rel = len(with_emails[(with_emails['relevance_score'] >= 4) & (with_emails['relevance_score'] < 7)])
        low_rel = len(with_emails[with_emails['relevance_score'] < 4])

        print(f"  High relevance (7+):   {high_rel:>4} ({high_rel/len(with_emails)*100:>5.1f}%)")
        print(f"  Medium relevance (4-6): {med_rel:>4} ({med_rel/len(with_emails)*100:>5.1f}%)")
        print(f"  Low relevance (0-3):    {low_rel:>4} ({low_rel/len(with_emails)*100:>5.1f}%)")

    print()


def main():
    parser = argparse.ArgumentParser(description='Split enrichment results into 3 files')
    parser.add_argument('--input', type=str, required=True, help='Input enriched CSV file')

    args = parser.parse_args()

    input_file = Path(args.input)

    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        return

    split_enrichment_results(input_file)


if __name__ == "__main__":
    main()
