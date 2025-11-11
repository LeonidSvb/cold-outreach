#!/usr/bin/env python3
"""
=== EMAIL ENRICHMENT PIPELINE ===
Version: 1.0.0 | Created: 2025-01-10

PURPOSE:
Complete pipeline for email scraping using existing website_scraper.py
Reads Parquet → CSV → Scraper → Merge → Parquet

USAGE:
# Test on 100 businesses
python run_email_enrichment.py --test 100

# Run on all ready businesses
python run_email_enrichment.py --full
"""

import sys
import logging
import argparse
import pandas as pd
import subprocess
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PARQUET_FILE = Path(__file__).parent.parent / "data" / "raw" / "all_leads.parquet"
ENRICHED_DIR = Path(__file__).parent.parent / "data" / "enriched"
TEMP_DIR = Path(__file__).parent.parent / "data" / "temp"
SCRAPER_SCRIPT = PROJECT_ROOT / "modules" / "scraping" / "scripts" / "website_scraper.py"

def prepare_input_csv(limit=None):
    """Export Parquet to CSV for scraper"""
    logger.info(f"Loading Parquet: {PARQUET_FILE}")

    df = pd.read_parquet(PARQUET_FILE)

    # Filter: only businesses with website (ready for email scraping)
    df_ready = df[df['has_website'] == True].copy()

    logger.info(f"Total businesses: {len(df)}")
    logger.info(f"Ready for scraping (have website): {len(df_ready)}")

    # Limit for testing
    if limit:
        df_ready = df_ready.head(limit)
        logger.info(f"Limited to {limit} for testing")

    # Prepare CSV with required columns
    # Scraper expects 'url' or 'website' column
    df_export = df_ready[['place_id', 'name', 'website', 'city', 'state', 'niche']].copy()
    df_export.rename(columns={'website': 'url'}, inplace=True)

    # Save to temp CSV
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_csv = TEMP_DIR / f"scraper_input_{timestamp}.csv"

    df_export.to_csv(input_csv, index=False)
    logger.info(f"Input CSV created: {input_csv}")

    return input_csv, len(df_export)

def run_scraper(input_csv, output_csv):
    """Run existing website_scraper.py"""
    logger.info("Running website scraper...")
    logger.info(f"Input: {input_csv}")
    logger.info(f"Output: {output_csv}")

    cmd = [
        "py",
        str(SCRAPER_SCRIPT),
        "--input", str(input_csv),
        "--output", str(output_csv),
        "--mode", "standard",  # emails + phones + smart scraping
        "--workers", "25",
        "--timeout", "15"
    ]

    logger.info(f"Command: {' '.join(cmd)}")

    # Run scraper
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Scraper failed with code {result.returncode}")
        logger.error(f"STDERR: {result.stderr}")
        raise Exception("Scraper execution failed")

    logger.info("Scraper completed successfully")
    return output_csv

def merge_results(original_parquet, scraper_output):
    """Merge scraper results back into Parquet"""
    logger.info("Merging results...")

    # Load original data
    df_original = pd.read_parquet(original_parquet)

    # Load scraper results
    df_scraped = pd.read_csv(scraper_output)

    # Rename url back to website for merging
    if 'url' in df_scraped.columns:
        df_scraped.rename(columns={'url': 'website'}, inplace=True)

    # Merge on website (or place_id if available)
    df_merged = df_original.merge(
        df_scraped[['website', 'status', 'emails', 'phones', 'content', 'processing_time']],
        on='website',
        how='left',
        suffixes=('', '_scraped')
    )

    # Rename scraped columns
    if 'emails' in df_merged.columns:
        df_merged.rename(columns={
            'emails': 'email',
            'status': 'scraping_status',
            'content': 'website_content'
        }, inplace=True)

    return df_merged

def save_enriched_parquet(df, test=False):
    """Save enriched data to Parquet"""
    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if test:
        filename = f"test_with_emails_{timestamp}.parquet"
    else:
        filename = f"with_emails_{timestamp}.parquet"
        # Also save as latest
        latest_file = ENRICHED_DIR / "with_emails_latest.parquet"
        df.to_parquet(latest_file, index=False)
        logger.info(f"Saved as latest: {latest_file}")

    output_file = ENRICHED_DIR / filename
    df.to_parquet(output_file, index=False)

    logger.info(f"Enriched Parquet saved: {output_file}")
    return output_file

def analyze_results(df):
    """Analyze scraping results"""
    print("\n" + "="*80)
    print("EMAIL SCRAPING RESULTS")
    print("="*80)

    total = len(df)

    # Overall stats
    if 'scraping_status' in df.columns:
        success = (df['scraping_status'] == 'success').sum()
        success_rate = success / total * 100

        print(f"\nOVERALL:")
        print(f"  Total processed:    {total:>5}")
        print(f"  Successful scrapes: {success:>5} ({success_rate:.1f}%)")

        # Status breakdown
        print(f"\nSTATUS BREAKDOWN:")
        status_counts = df['scraping_status'].value_counts()
        for status, count in status_counts.items():
            pct = count / total * 100
            print(f"  {status:20} {count:>5} ({pct:>5.1f}%)")

    # Email extraction stats
    if 'email' in df.columns:
        has_email = df['email'].notna() & (df['email'] != '')
        email_count = has_email.sum()
        email_rate = email_count / total * 100

        print(f"\nEMAIL EXTRACTION:")
        print(f"  Emails found:       {email_count:>5} ({email_rate:.1f}%)")
        print(f"  No email found:     {total - email_count:>5} ({100-email_rate:.1f}%)")

        # Show sample emails
        sample_emails = df[has_email][['name', 'city', 'niche', 'email']].head(5)
        print(f"\nSAMPLE EMAILS:")
        for idx, row in sample_emails.iterrows():
            print(f"  {row['name']:40} | {row['email']}")

    # Failed scraping
    if 'scraping_status' in df.columns:
        failed = df[df['scraping_status'] != 'success']
        if len(failed) > 0:
            print(f"\nFAILED BUSINESSES:")
            print(f"  Total failed: {len(failed)}")
            failed_csv = ENRICHED_DIR / f"failed_scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            failed[['place_id', 'name', 'website', 'scraping_status']].to_csv(failed_csv, index=False)
            print(f"  Saved to: {failed_csv}")

    print("\n" + "="*80 + "\n")

def main():
    parser = argparse.ArgumentParser(description='Email Enrichment Pipeline')
    parser.add_argument('--test', type=int, metavar='N',
                       help='Test mode: scrape only N businesses')
    parser.add_argument('--full', action='store_true',
                       help='Full mode: scrape all ready businesses')

    args = parser.parse_args()

    if not args.test and not args.full:
        parser.error("Must specify --test N or --full")

    try:
        # Step 1: Prepare input CSV
        limit = args.test if args.test else None
        input_csv, count = prepare_input_csv(limit=limit)

        # Estimate time
        estimated_seconds = count * 0.5  # 0.5 sec per business (standard mode)
        estimated_minutes = estimated_seconds / 60

        print(f"\n{'='*80}")
        print(f"EMAIL ENRICHMENT PIPELINE")
        print(f"{'='*80}")
        print(f"Mode:               {'TEST' if args.test else 'FULL'}")
        print(f"Businesses:         {count:,}")
        print(f"Estimated time:     ~{estimated_minutes:.1f} minutes")
        print(f"{'='*80}\n")

        # Step 2: Run scraper
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_csv = TEMP_DIR / f"scraper_output_{timestamp}.csv"

        run_scraper(input_csv, output_csv)

        # Step 3: Merge results
        df_enriched = merge_results(PARQUET_FILE, output_csv)

        # Step 4: Save enriched Parquet
        output_file = save_enriched_parquet(df_enriched, test=bool(args.test))

        # Step 5: Analyze results
        analyze_results(df_enriched)

        logger.info("Pipeline completed successfully!")
        logger.info(f"Enriched data saved to: {output_file}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
