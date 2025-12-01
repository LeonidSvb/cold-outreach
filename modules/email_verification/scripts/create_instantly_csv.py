#!/usr/bin/env python3
"""
Create Instantly-ready CSV with verification status column
Combines all verification batches and applies filtering logic
"""

import sys
import glob
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.shared.logging.universal_logger import get_logger

logger = get_logger(__name__)


def determine_campaign_status(row):
    """
    Determine campaign status based on verification results

    Strategy (Option 2 - Medium):
    - SEND: deliverable
    - TEST: risky with score >= 60
    - SKIP: everything else
    """
    result = row['result']
    score = row['score']

    if result == 'deliverable':
        return 'SEND'
    elif result == 'risky' and score >= 60:
        return 'TEST'
    else:
        return 'SKIP'


def main():
    logger.info("="*60)
    logger.info("CREATING INSTANTLY-READY CSV")
    logger.info("="*60)

    # Find all verification result files
    results_dir = Path(__file__).parent.parent / "results"
    verification_files = sorted(glob.glob(str(results_dir / "verified_emails_*.csv")))

    # Exclude combined files
    verification_files = [f for f in verification_files if 'COMBINED' not in f and 'FINAL' not in f]

    logger.info(f"Found {len(verification_files)} verification files")

    # Load and combine all batches
    all_batches = []
    for file in verification_files:
        df = pd.read_csv(file, encoding='utf-8')
        logger.info(f"Loaded: {Path(file).name} ({len(df)} emails)")
        all_batches.append(df)

    # Combine
    combined = pd.concat(all_batches, ignore_index=True)
    logger.info(f"Total verified emails: {len(combined)}")

    # Add campaign status column
    combined['campaign_status'] = combined.apply(determine_campaign_status, axis=1)

    # Add verification timestamp
    combined['verified_date'] = datetime.now().strftime('%Y-%m-%d')

    # Statistics
    status_counts = combined['campaign_status'].value_counts()
    logger.info("\nCampaign Status Distribution:")
    for status, count in status_counts.items():
        pct = count / len(combined) * 100
        logger.info(f"  {status}: {count} ({pct:.1f}%)")

    # Reorder columns for Instantly
    # Put important columns first
    important_cols = ['campaign_status', 'email', 'name', 'website', 'result', 'score']
    other_cols = [c for c in combined.columns if c not in important_cols]
    column_order = important_cols + other_cols
    combined = combined[column_order]

    # Save full enriched file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_file = results_dir / f"museum_emails_VERIFIED_FULL_{timestamp}.csv"
    combined.to_csv(full_file, index=False, encoding='utf-8')
    logger.info(f"\nFull enriched CSV saved: {full_file}")

    # Create Instantly-ready file (SEND + TEST only)
    instantly_ready = combined[combined['campaign_status'].isin(['SEND', 'TEST'])].copy()
    instantly_file = results_dir / f"museum_emails_INSTANTLY_READY_{timestamp}.csv"
    instantly_ready.to_csv(instantly_file, index=False, encoding='utf-8')
    logger.info(f"Instantly-ready CSV saved: {instantly_file}")
    logger.info(f"  Contains {len(instantly_ready)} emails (SEND + TEST)")

    # Create SEND-only file (safest option)
    send_only = combined[combined['campaign_status'] == 'SEND'].copy()
    send_file = results_dir / f"museum_emails_SEND_ONLY_{timestamp}.csv"
    send_only.to_csv(send_file, index=False, encoding='utf-8')
    logger.info(f"SEND-only CSV saved: {send_file}")
    logger.info(f"  Contains {len(send_only)} emails (safest)")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nTotal verified:     {len(combined)}")
    print(f"SEND (deliverable): {len(send_only)} ({len(send_only)/len(combined)*100:.1f}%)")
    print(f"TEST (risky 60+):   {len(instantly_ready) - len(send_only)} ({(len(instantly_ready)-len(send_only))/len(combined)*100:.1f}%)")
    print(f"SKIP (problematic): {len(combined) - len(instantly_ready)} ({(len(combined)-len(instantly_ready))/len(combined)*100:.1f}%)")
    print()
    print("FILES CREATED:")
    print(f"1. Full enriched:    {full_file.name}")
    print(f"2. Instantly ready:  {instantly_file.name}")
    print(f"3. SEND only:        {send_file.name}")
    print()
    print("RECOMMENDATION:")
    print("- Use SEND_ONLY for safest campaign (<5% bounce)")
    print("- Use INSTANTLY_READY for moderate risk (~10-15% bounce)")
    print("- Use FULL for filtering in spreadsheet software")
    print("="*60)


if __name__ == "__main__":
    main()
