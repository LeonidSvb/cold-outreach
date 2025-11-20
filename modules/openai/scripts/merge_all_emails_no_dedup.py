#!/usr/bin/env python3
"""
=== MERGE ALL EMAILS (NO DEDUPLICATION) ===
Version: 1.0.0 | Created: 2025-11-19

PURPOSE:
Merge ALL scraped emails with validation results.
NO deduplication - keep all emails even if multiple per company.
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
ORIGINAL_FILE = Path(r"C:\Users\79818\Downloads\Australia_WITH_Website.csv")
OUTPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_FINAL_WITH_VALIDATION.csv")


def main():
    logger.info("="*70)
    logger.info("MERGE ALL EMAILS (NO DEDUPLICATION)")
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

    # Normalize emails for merge
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

    # Load original data for phone/city
    logger.info("\nAdding phone and city from original data...")
    df_original = pd.read_csv(ORIGINAL_FILE, encoding='utf-8-sig')
    df_original['website_lower'] = df_original['Website'].str.lower().str.strip().str.rstrip('/')
    df_merged['website_lower'] = df_merged['website'].str.lower().str.strip().str.rstrip('/')

    df_merged = df_merged.merge(
        df_original[['website_lower', 'Phone Number', 'Company City']].rename(
            columns={'Phone Number': 'phone_original', 'Company City': 'city_original'}
        ),
        on='website_lower',
        how='left'
    )

    logger.info(f"  Total rows: {len(df_merged)}")

    # Show final validation breakdown
    logger.info("\nFINAL VALIDATION BREAKDOWN:")
    for status in ['deliverable', 'unknown', 'risky', 'undeliverable']:
        count = (df_merged['Result'] == status).sum()
        if count > 0:
            percentage = count / len(df_merged) * 100
            logger.info(f"  {status}: {count} ({percentage:.1f}%)")

    # Prepare output columns
    df_output = df_merged[[
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

    # Save
    df_output.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    logger.info("="*70)
    logger.info("MERGE COMPLETE")
    logger.info("="*70)
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info(f"Total emails: {len(df_output)}")
    logger.info("")
    logger.info("USABLE EMAILS (Deliverable + Unknown + Risky):")
    usable = ((df_output['Result'] == 'deliverable') |
              (df_output['Result'] == 'unknown') |
              (df_output['Result'] == 'risky')).sum()
    logger.info(f"  {usable} emails ready for campaigns")
    logger.info("="*70)


if __name__ == "__main__":
    main()
