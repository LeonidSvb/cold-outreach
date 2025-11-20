#!/usr/bin/env python3
"""
=== EXTRACT DOMAINS WITHOUT EMAILS ===
Version: 1.0.0 | Created: 2025-11-19

PURPOSE:
Extract website domains for companies where NO email was found.
Output clean CSV for Hunter.io / Anymailfinder processing.
"""

import sys
from pathlib import Path
import pandas as pd
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
RESULTS_DIR = Path(r"C:\Users\79818\Desktop\Outreach - new\modules\scraping\results\scraped_20251119_211718")
OUTPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_DOMAINS_NO_EMAILS.csv")


def clean_domain(url: str) -> str:
    """Extract clean domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path

        # Remove www.
        if domain.startswith('www.'):
            domain = domain[4:]

        return domain.lower().strip()
    except:
        return url


def main():
    logger.info("="*70)
    logger.info("EXTRACT DOMAINS WITHOUT EMAILS")
    logger.info("="*70)

    # Load failed files
    failed_files = [
        RESULTS_DIR / "failed_static.csv",
        RESULTS_DIR / "failed_dynamic.csv",
        RESULTS_DIR / "failed_other.csv"
    ]

    all_failed = []

    for file in failed_files:
        if file.exists():
            logger.info(f"Loading: {file.name}")
            df = pd.read_csv(file, encoding='utf-8-sig')
            all_failed.append(df)
            logger.info(f"  Rows: {len(df)}")

    # Combine
    df_failed = pd.concat(all_failed, ignore_index=True)
    logger.info(f"\nTotal companies without emails: {len(df_failed)}")

    # Extract domains
    df_failed['domain'] = df_failed['website'].apply(clean_domain)

    # Remove duplicates
    df_failed = df_failed.drop_duplicates(subset=['domain'])
    logger.info(f"Unique domains: {len(df_failed)}")

    # Prepare output
    df_output = df_failed[['company_name_short', 'domain', 'website']].copy()
    df_output.columns = ['Company', 'Domain', 'Website']

    # Sort by company name
    df_output = df_output.sort_values('Company')

    # Save
    df_output.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    logger.info("="*70)
    logger.info("COMPLETE")
    logger.info("="*70)
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info(f"Total domains: {len(df_output)}")
    logger.info("")
    logger.info("Ready for Hunter.io / Anymailfinder processing!")
    logger.info("="*70)

    # Show sample
    logger.info("\nSAMPLE (first 10):")
    logger.info("-"*70)
    for _, row in df_output.head(10).iterrows():
        logger.info(f"  {row['Company']:<40} | {row['Domain']}")
    logger.info("-"*70)


if __name__ == "__main__":
    main()
