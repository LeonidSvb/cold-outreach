#!/usr/bin/env python3
"""
=== EMAIL VALIDATION VIA MAILS.SO API ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Validate emails using mails.so API in batches of 50.
Process all emails from Australia_FINAL_WITH_VALIDATION.csv
"""

import sys
from pathlib import Path
import pandas as pd
import requests
import time
from typing import Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
INPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_FINAL_WITH_VALIDATION.csv")
OUTPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_VALIDATED_MAILSSO.csv")
API_KEY = 'c6c76660-b774-4dcc-be3f-64cdb999e70f'
BATCH_SIZE = 50
DELAY_BETWEEN_BATCHES = 2  # seconds


def validate_email(email: str) -> Optional[Dict]:
    """
    Validate single email via mails.so API

    Returns:
        Dict with validation results or None if error
    """
    try:
        url = f'https://api.mails.so/v1/validate?email={email}'
        headers = {'x-mails-api-key': API_KEY}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            logger.warning(f"API error for {email}: HTTP {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Error validating {email}: {e}")
        return None


def process_batch(emails: list, batch_num: int, total_batches: int) -> list:
    """
    Process batch of emails

    Args:
        emails: List of email addresses
        batch_num: Current batch number
        total_batches: Total number of batches

    Returns:
        List of validation results
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"BATCH {batch_num}/{total_batches} - Processing {len(emails)} emails")
    logger.info(f"{'='*70}")

    results = []

    for idx, email in enumerate(emails, 1):
        logger.info(f"  [{idx}/{len(emails)}] Validating: {email}")

        result = validate_email(email)

        if result:
            results.append({
                'email': email,
                'is_valid': result.get('is_valid', False),
                'is_disposable': result.get('is_disposable', False),
                'is_role': result.get('is_role', False),
                'is_free': result.get('is_free', False),
                'score': result.get('score', 0),
                'reason': result.get('reason', ''),
                'domain': result.get('domain', ''),
                'provider': result.get('provider', ''),
                'mx_records': result.get('mx_records', False),
                'smtp_check': result.get('smtp_check', False)
            })

            status = "VALID" if result.get('is_valid') else "INVALID"
            score = result.get('score', 0)
            logger.info(f"      → {status} (score: {score})")
        else:
            # API error - mark as unknown
            results.append({
                'email': email,
                'is_valid': False,
                'is_disposable': False,
                'is_role': False,
                'is_free': False,
                'score': 0,
                'reason': 'api_error',
                'domain': '',
                'provider': '',
                'mx_records': False,
                'smtp_check': False
            })
            logger.warning(f"      → API ERROR")

        # Small delay between requests
        time.sleep(0.2)

    return results


def main():
    logger.info("="*70)
    logger.info("EMAIL VALIDATION VIA MAILS.SO API")
    logger.info("="*70)

    # Load data
    logger.info(f"Loading emails from: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')

    total_emails = len(df)
    logger.info(f"Total emails to validate: {total_emails}")

    # Get unique emails
    emails = df['Email'].unique().tolist()
    unique_count = len(emails)
    logger.info(f"Unique emails: {unique_count}")

    # Calculate batches
    total_batches = (unique_count + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(f"Batches to process: {total_batches} (batch size: {BATCH_SIZE})")

    # Process in batches
    all_results = []

    for i in range(0, unique_count, BATCH_SIZE):
        batch_num = (i // BATCH_SIZE) + 1
        batch_emails = emails[i:i+BATCH_SIZE]

        batch_results = process_batch(batch_emails, batch_num, total_batches)
        all_results.extend(batch_results)

        # Delay between batches
        if batch_num < total_batches:
            logger.info(f"\nWaiting {DELAY_BETWEEN_BATCHES}s before next batch...")
            time.sleep(DELAY_BETWEEN_BATCHES)

    # Create results DataFrame
    df_results = pd.DataFrame(all_results)

    # Merge with original data
    logger.info("\nMerging validation results with original data...")
    df_merged = df.merge(
        df_results.add_suffix('_mailsso'),
        left_on='Email',
        right_on='email_mailsso',
        how='left'
    )

    # Drop duplicate email column
    if 'email_mailsso' in df_merged.columns:
        df_merged = df_merged.drop(columns=['email_mailsso'])

    # Save results
    df_merged.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    # Statistics
    logger.info("\n" + "="*70)
    logger.info("VALIDATION COMPLETE")
    logger.info("="*70)
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info(f"Total emails processed: {len(all_results)}")

    valid_count = df_results['is_valid'].sum()
    invalid_count = len(df_results) - valid_count

    logger.info(f"\nResults:")
    logger.info(f"  Valid emails: {valid_count} ({valid_count/len(df_results)*100:.1f}%)")
    logger.info(f"  Invalid emails: {invalid_count} ({invalid_count/len(df_results)*100:.1f}%)")

    if 'is_disposable' in df_results.columns:
        disposable = df_results['is_disposable'].sum()
        logger.info(f"  Disposable: {disposable}")

    if 'is_role' in df_results.columns:
        role = df_results['is_role'].sum()
        logger.info(f"  Role emails: {role}")

    if 'is_free' in df_results.columns:
        free = df_results['is_free'].sum()
        logger.info(f"  Free providers: {free}")

    logger.info("="*70)

    # Show sample
    logger.info("\nSAMPLE RESULTS:")
    logger.info("-"*70)
    sample = df_results[['email', 'is_valid', 'score', 'reason']].head(10)
    for _, row in sample.iterrows():
        status = "VALID" if row['is_valid'] else "INVALID"
        logger.info(f"  {row['email']:<40} | {status:8} | Score: {row['score']:3} | {row['reason']}")
    logger.info("-"*70)


if __name__ == "__main__":
    main()
