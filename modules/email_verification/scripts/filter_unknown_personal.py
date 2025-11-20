#!/usr/bin/env python3
"""
=== FILTER UNKNOWN PERSONAL DOMAINS ===
Version: 1.0.0 | Created: 2025-01-20

PURPOSE:
Remove Unknown emails on personal domains (gmail, yahoo, etc).
Keep Unknown emails on corporate domains.

LOGIC:
- Unknown + Personal Domain (IsFree=true or common ISPs) -> EXCLUDE
- Unknown + Corporate Domain -> KEEP
- All other statuses (deliverable, risky, undeliverable) -> KEEP

USAGE:
python filter_unknown_personal.py
"""

import pandas as pd
from datetime import datetime
from pathlib import Path

CONFIG = {
    "INPUT_CSV": r"C:\Users\79818\Downloads\batch_76caaf24-a326-4772-ab1e-daf320068609_all.csv",
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",

    "PERSONAL_DOMAINS": [
        # Free email providers
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'mail.ru', 'yandex.ru', 'icloud.com', 'aol.com',
        'proton.me', 'protonmail.com', 'gmx.com', 'zoho.com',
        'mail.com', 'inbox.com', 'live.com', 'msn.com',

        # ISP providers
        'comcast.net', 'verizon.net', 'att.net', 'cox.net',
        'charter.net', 'sbcglobal.net', 'bellsouth.net'
    ]
}

def is_personal_domain(domain, is_free):
    """Check if domain is personal (free or ISP)"""
    if pd.isna(domain):
        return False

    domain_lower = str(domain).lower().strip()

    # Check IsFree flag from validation service
    if is_free == True or str(is_free).lower() == 'true':
        return True

    # Check against known personal domains
    return domain_lower in CONFIG['PERSONAL_DOMAINS']


def filter_unknown_personal(df):
    """
    Filter out Unknown emails on personal domains.
    Keep everything else.
    """
    print("Starting Unknown personal domain filtering...")

    initial_count = len(df)

    # Create mask for rows to EXCLUDE
    exclude_mask = (
        (df['Result'].str.lower() == 'unknown') &
        (df.apply(lambda row: is_personal_domain(row['Domain'], row['IsFree']), axis=1))
    )

    excluded_count = exclude_mask.sum()

    # Keep rows that are NOT excluded
    filtered_df = df[~exclude_mask].copy()

    final_count = len(filtered_df)

    # Log statistics
    print(f"Initial rows: {initial_count}")
    print(f"Excluded Unknown on personal domains: {excluded_count}")
    print(f"Final rows: {final_count}")
    print(f"Retention rate: {final_count/initial_count*100:.1f}%")

    # Breakdown by Result status
    if 'Result' in filtered_df.columns:
        status_counts = filtered_df['Result'].value_counts()
        print("\nFinal breakdown by status:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")

    return filtered_df


def main():
    print("\n=== Filter Unknown Personal Domains ===\n")

    # Read CSV
    print(f"Reading CSV: {CONFIG['INPUT_CSV']}")
    df = pd.read_csv(CONFIG['INPUT_CSV'], encoding='utf-8-sig')

    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # Show initial status distribution
    if 'Result' in df.columns:
        print("\nInitial status distribution:")
        for status, count in df['Result'].value_counts().items():
            print(f"  {status}: {count}")

    print()
    # Filter
    filtered_df = filter_unknown_personal(df)

    # Save results
    CONFIG['OUTPUT_DIR'].mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"filtered_unknown_{timestamp}.csv"
    output_path = CONFIG['OUTPUT_DIR'] / output_filename

    filtered_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\nSaved filtered results: {output_path}")

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print(f"Original: {len(df)} emails")
    print(f"Filtered: {len(filtered_df)} emails")
    print(f"Removed: {len(df) - len(filtered_df)} Unknown on personal domains")
    print("=" * 50 + "\n")

    return filtered_df


if __name__ == "__main__":
    main()
