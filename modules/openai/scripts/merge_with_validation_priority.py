#!/usr/bin/env python3
"""
=== MERGE EMAILS WITH VALIDATION (VALIDATION PRIORITY) ===
Version: 1.1.0 | Created: 2025-11-19

PURPOSE:
Merge scraped emails with validation results, prioritizing by validation status FIRST,
then by email prefix quality.

PRIORITY:
1. Validation status: deliverable > unknown > risky > undeliverable
2. Email prefix: info@ > contact@ > sales@ > bookings@ > admin@

This ensures we select the BEST validated email per company.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths
SCRAPED_FILE = Path(r"C:\Users\79818\Desktop\Outreach - new\modules\scraping\results\scraped_20251119_211718\success_emails.csv")
VALIDATION_FILE = Path(r"C:\Users\79818\Downloads\batch_ab7f227a-14ce-4b79-93a0-d4c00c1f8a49_all.csv")
OUTPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_FINAL_WITH_VALIDATION.csv")

# Validation status priority (higher = better)
VALIDATION_PRIORITY = {
    'deliverable': 4,
    'unknown': 3,
    'risky': 2,
    'undeliverable': 1
}

# Email prefix priority (higher = better)
EMAIL_PREFIX_PRIORITY = {
    'info': 100,
    'contact': 90,
    'hello': 85,
    'sales': 80,
    'bookings': 75,
    'reservations': 70,
    'events': 60,
    'functions': 55,
    'reception': 50,
    'admin': 45,
    'enquiries': 40,
    'enquiry': 38,
    'accounts': 35,
    'office': 30
}


def get_email_prefix(email: str) -> str:
    """Extract prefix from email (before @)"""
    return email.split('@')[0].lower()


def get_email_priority(email: str) -> int:
    """Get priority score for email prefix"""
    prefix = get_email_prefix(email)

    # Check known prefixes
    for known_prefix, score in EMAIL_PREFIX_PRIORITY.items():
        if prefix.startswith(known_prefix):
            return score

    return 0  # Unknown prefix


def get_validation_priority(result: str) -> int:
    """Get priority score for validation result"""
    return VALIDATION_PRIORITY.get(result.lower(), 0)


def main():
    logger.info("="*70)
    logger.info("MERGE EMAILS WITH VALIDATION (VALIDATION PRIORITY)")
    logger.info("="*70)

    # Load scraped emails
    logger.info(f"Loading scraped emails: {SCRAPED_FILE}")
    df_scraped = pd.read_csv(SCRAPED_FILE, encoding='utf-8-sig')
    logger.info(f"  Total emails scraped: {len(df_scraped)}")

    # Load validation results
    logger.info(f"Loading validation results: {VALIDATION_FILE}")
    df_validation = pd.read_csv(VALIDATION_FILE, encoding='utf-8-sig')
    logger.info(f"  Total emails validated: {len(df_validation)}")

    # Show validation stats
    logger.info("\nVALIDATION STATS:")
    for status, count in df_validation['Result'].value_counts().items():
        percentage = count / len(df_validation) * 100
        logger.info(f"  {status}: {count} ({percentage:.1f}%)")

    # Normalize email columns for merge
    df_scraped['email_lower'] = df_scraped['email'].str.lower().str.strip()
    df_validation['email_lower'] = df_validation['Email'].str.lower().str.strip()

    # Merge on email
    logger.info("\nMerging by email address...")
    df_merged = df_scraped.merge(
        df_validation[['email_lower', 'Result', 'Reason', 'Score', 'Provider']],
        on='email_lower',
        how='left'
    )

    matched = df_merged['Result'].notna().sum()
    logger.info(f"  Matched emails: {matched}/{len(df_scraped)}")

    # Add priority scores
    logger.info("\nCalculating priority scores...")
    df_merged['validation_priority'] = df_merged['Result'].fillna('undeliverable').apply(get_validation_priority)
    df_merged['email_priority'] = df_merged['email'].apply(get_email_priority)
    df_merged['total_priority'] = df_merged['validation_priority'] * 1000 + df_merged['email_priority']

    # Keep best email per company
    logger.info("Selecting best email per company (validation status first)...")
    df_merged = df_merged.sort_values('total_priority', ascending=False)
    df_best = df_merged.groupby('company_name_short').first().reset_index()

    # Load original data for phone/city
    logger.info("\nAdding phone and city from original data...")
    original_file = Path(r"C:\Users\79818\Downloads\Australia_WITH_Website.csv")
    df_original = pd.read_csv(original_file, encoding='utf-8-sig')
    df_original['website_lower'] = df_original['Website'].str.lower().str.strip().str.rstrip('/')
    df_best['website_lower'] = df_best['website'].str.lower().str.strip().str.rstrip('/')

    df_best = df_best.merge(
        df_original[['website_lower', 'Phone Number', 'Company City']].rename(
            columns={'Phone Number': 'phone_original', 'Company City': 'city_original'}
        ),
        on='website_lower',
        how='left'
    )

    logger.info(f"  Unique companies: {len(df_best)}")

    # Show final validation breakdown
    logger.info("\nFINAL VALIDATION BREAKDOWN:")
    for status in ['deliverable', 'unknown', 'risky', 'undeliverable']:
        count = (df_best['Result'] == status).sum()
        percentage = count / len(df_best) * 100
        logger.info(f"  {status}: {count} ({percentage:.1f}%)")

    # Prepare output columns
    df_output = df_best[[
        'company_name_short',
        'email',
        'website',
        'phone_original',
        'city_original',
        'Result',
        'Reason',
        'Score',
        'Provider'
    ]].copy()

    df_output.columns = ['Company', 'Email', 'Website', 'Phone', 'City',
                         'Result', 'Reason', 'Score', 'Provider']

    # Fill empty Phone/City with empty string
    df_output['Phone'] = df_output['Phone'].fillna('')
    df_output['City'] = df_output['City'].fillna('')

    # Add Company_Casual column (keep existing if present)
    logger.info("\nAdding casual company names...")

    # Check if old file exists with Company_Casual
    if OUTPUT_FILE.exists():
        df_old = pd.read_csv(OUTPUT_FILE, encoding='utf-8-sig')
        if 'Company_Casual' in df_old.columns:
            logger.info("  Using existing Company_Casual from previous file")
            df_output = df_output.merge(
                df_old[['Company', 'Company_Casual']],
                on='Company',
                how='left'
            )
            # Fill missing with Company name
            df_output['Company_Casual'] = df_output['Company_Casual'].fillna(df_output['Company'])

    if 'Company_Casual' not in df_output.columns:
        logger.info("  No existing casual names, using Company name")
        df_output['Company_Casual'] = df_output['Company']

    # Save
    df_output.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    logger.info("="*70)
    logger.info("MERGE COMPLETE")
    logger.info("="*70)
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info(f"Total companies: {len(df_output)}")
    logger.info("")
    logger.info("USABLE EMAILS (Deliverable + Unknown + Risky):")
    usable = ((df_output['Result'] == 'deliverable') |
              (df_output['Result'] == 'unknown') |
              (df_output['Result'] == 'risky')).sum()
    logger.info(f"  {usable} emails ready for campaigns")
    logger.info("="*70)


if __name__ == "__main__":
    main()
