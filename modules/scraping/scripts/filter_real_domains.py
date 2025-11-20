#!/usr/bin/env python3
"""
=== FILTER REAL BUSINESS DOMAINS ===
Version: 1.0.0 | Created: 2025-11-19

PURPOSE:
Remove booking platforms and aggregators, keep only real business domains.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_DOMAINS_NO_EMAILS.csv")
OUTPUT_FILE = Path(r"C:\Users\79818\Downloads\Australia_REAL_DOMAINS.csv")

# Booking platforms and aggregators to filter out
BOOKING_PLATFORMS = [
    'traveleto.com',
    'hotelmix.',
    'hotel-mix.',
    'business.site',
    'booking.com',
    'booked.net',
    'airbnb.com',
    'hotels.com',
    'expedia.com',
    'tripadvisor.',
    'wotif.com',
    'stayz.com.au',
    'homeaway.com',
    'vrbo.com',
    'agoda.com',
    'hostelworld.com',
    'hotelscombined.com',
    'trivago.',
    'kayak.com',
    'priceline.com',
    'trip.com',
    'venere.com',
    'hrs.com',
    'lastminute.com'
]


def is_booking_platform(domain: str) -> bool:
    """Check if domain is a booking platform"""
    domain_lower = domain.lower()

    for platform in BOOKING_PLATFORMS:
        if platform in domain_lower:
            return True

    return False


def main():
    logger.info("="*70)
    logger.info("FILTER REAL BUSINESS DOMAINS")
    logger.info("="*70)

    # Load data
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    logger.info(f"Total domains loaded: {len(df)}")

    # Filter out booking platforms
    logger.info("\nFiltering out booking platforms...")

    df_real = df[~df['Domain'].apply(is_booking_platform)].copy()

    removed = len(df) - len(df_real)
    logger.info(f"Removed: {removed} booking platform domains")
    logger.info(f"Remaining: {len(df_real)} real business domains")

    # Show removed examples
    df_removed = df[df['Domain'].apply(is_booking_platform)]
    if len(df_removed) > 0:
        logger.info("\nEXAMPLES OF REMOVED DOMAINS:")
        logger.info("-"*70)
        for _, row in df_removed.head(10).iterrows():
            logger.info(f"  {row['Domain']}")
        logger.info("-"*70)

    # Save
    df_real.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    logger.info("="*70)
    logger.info("COMPLETE")
    logger.info("="*70)
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info(f"Real business domains: {len(df_real)}")
    logger.info("")
    logger.info("Ready for Hunter.io / Anymailfinder!")
    logger.info("="*70)

    # Show sample
    logger.info("\nSAMPLE REAL DOMAINS (first 15):")
    logger.info("-"*70)
    for _, row in df_real.head(15).iterrows():
        logger.info(f"  {row['Company']:<40} | {row['Domain']}")
    logger.info("-"*70)


if __name__ == "__main__":
    main()
