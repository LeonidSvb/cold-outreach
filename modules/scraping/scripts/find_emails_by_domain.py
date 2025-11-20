#!/usr/bin/env python3
"""
=== FIND EMAILS BY DOMAIN VIA MAILS.SO API ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Search for emails using domain via mails.so API.
Process domains from Australia_REAL_DOMAINS.csv in batches of 50.
"""

import sys
from pathlib import Path
import pandas as pd
import requests
import time
from typing import Dict, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
INPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_REAL_DOMAINS.csv")
OUTPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_EMAILS_FOUND_BY_DOMAIN.csv")
API_KEY = 'c6c76660-b774-4dcc-be3f-64cdb999e70f'
BATCH_SIZE = 50
DELAY_BETWEEN_BATCHES = 2  # seconds


def find_emails_by_domain(domain: str) -> Optional[List[str]]:
    """
    Find emails for domain via mails.so API

    Returns:
        List of email addresses found or None if error
    """
    try:
        # Check if mails.so has domain search endpoint
        # If not, we'll use email pattern guessing

        # Common email patterns to try
        patterns = [
            f'info@{domain}',
            f'contact@{domain}',
            f'hello@{domain}',
            f'sales@{domain}',
            f'admin@{domain}'
        ]

        found_emails = []

        for email in patterns:
            url = f'https://api.mails.so/v1/validate?email={email}'
            headers = {'x-mails-api-key': API_KEY}

            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # If email is valid, add it
                if data.get('is_valid', False):
                    found_emails.append(email)

            time.sleep(0.3)  # Rate limiting

        return found_emails if found_emails else None

    except Exception as e:
        logger.error(f"Error searching domain {domain}: {e}")
        return None


def process_batch(domains_df: pd.DataFrame, batch_num: int, total_batches: int) -> List[Dict]:
    """
    Process batch of domains

    Args:
        domains_df: DataFrame with domains
        batch_num: Current batch number
        total_batches: Total number of batches

    Returns:
        List of results
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"BATCH {batch_num}/{total_batches} - Processing {len(domains_df)} domains")
    logger.info(f"{'='*70}")

    results = []

    for idx, row in domains_df.iterrows():
        company = row['Company']
        domain = row['Domain']
        website = row['Website']

        logger.info(f"  [{idx+1}/{len(domains_df)}] Searching: {domain}")

        emails = find_emails_by_domain(domain)

        if emails:
            logger.info(f"      -> FOUND {len(emails)} emails: {', '.join(emails)}")

            for email in emails:
                results.append({
                    'Company': company,
                    'Domain': domain,
                    'Website': website,
                    'Email': email,
                    'Source': 'mails.so_pattern_match'
                })
        else:
            logger.info(f"      -> No emails found")
            results.append({
                'Company': company,
                'Domain': domain,
                'Website': website,
                'Email': '',
                'Source': 'not_found'
            })

    return results


def main():
    logger.info("="*70)
    logger.info("FIND EMAILS BY DOMAIN VIA MAILS.SO API")
    logger.info("="*70)

    # Load domains
    logger.info(f"Loading domains from: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')

    total_domains = len(df)
    logger.info(f"Total domains: {total_domains}")

    # Calculate batches
    total_batches = (total_domains + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(f"Batches to process: {total_batches} (batch size: {BATCH_SIZE})")

    # Process in batches
    all_results = []

    for i in range(0, total_domains, BATCH_SIZE):
        batch_num = (i // BATCH_SIZE) + 1
        batch_df = df.iloc[i:i+BATCH_SIZE]

        batch_results = process_batch(batch_df, batch_num, total_batches)
        all_results.extend(batch_results)

        # Delay between batches
        if batch_num < total_batches:
            logger.info(f"\nWaiting {DELAY_BETWEEN_BATCHES}s before next batch...")
            time.sleep(DELAY_BETWEEN_BATCHES)

    # Create results DataFrame
    df_results = pd.DataFrame(all_results)

    # Filter only found emails
    df_found = df_results[df_results['Email'] != ''].copy()

    # Save results
    df_found.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    # Statistics
    logger.info("\n" + "="*70)
    logger.info("SEARCH COMPLETE")
    logger.info("="*70)
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info(f"Total domains searched: {total_domains}")
    logger.info(f"Domains with emails found: {len(df_found)}")
    logger.info(f"Total emails found: {len(df_found)}")
    logger.info(f"Success rate: {len(df_found)/total_domains*100:.1f}%")
    logger.info("="*70)

    # Show sample
    if len(df_found) > 0:
        logger.info("\nSAMPLE RESULTS:")
        logger.info("-"*70)
        for _, row in df_found.head(10).iterrows():
            logger.info(f"  {row['Company']:<40} | {row['Email']}")
        logger.info("-"*70)


if __name__ == "__main__":
    main()
