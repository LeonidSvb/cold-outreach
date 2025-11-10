#!/usr/bin/env python3
"""
=== 2-STAGE EMAIL + CONTENT ENRICHMENT ===
Version: 1.0.0 | Created: 2025-01-10

PURPOSE:
Smart 2-stage pipeline for maximum speed:
1. Quick email extraction (all businesses)
2. Content scraping (only where email found)

STRATEGY:
Stage 1: 3,736 businesses × 0.5 sec = ~31 min
Stage 2: ~1,718 (46%) × 0.5 sec = ~14 min
TOTAL: ~45 minutes (vs 15 hours!)

USAGE:
python run_email_enrichment_fast.py
"""

import sys
import logging
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

def prepare_stage1_input():
    """Prepare CSV for Stage 1: Email extraction"""
    logger.info(f"Loading Parquet: {PARQUET_FILE}")

    df = pd.read_parquet(PARQUET_FILE)
    df_ready = df[df['has_website'] == True].copy()

    logger.info(f"Total businesses with website: {len(df_ready)}")

    # Prepare CSV
    df_export = df_ready[['place_id', 'name', 'website', 'city', 'state', 'niche']].copy()
    df_export.rename(columns={'website': 'url'}, inplace=True)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_csv = TEMP_DIR / f"stage1_input_{timestamp}.csv"

    df_export.to_csv(input_csv, index=False)
    logger.info(f"Stage 1 input created: {input_csv}")

    return input_csv, len(df_export), timestamp

def run_stage1_emails(input_csv, output_csv):
    """Stage 1: Quick email extraction (single page, fast)"""
    logger.info("="*80)
    logger.info("STAGE 1: QUICK EMAIL EXTRACTION")
    logger.info("="*80)

    cmd = [
        "py",
        str(SCRAPER_SCRIPT),
        "--input", str(input_csv),
        "--output", str(output_csv),
        "--extract-emails",        # Only emails
        "--scrape-mode", "single", # Only homepage (FAST!)
        "--workers", "50",         # More workers
        "--timeout", "10"          # Lower timeout
    ]

    logger.info(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Stage 1 failed with code {result.returncode}")
        logger.error(f"STDERR: {result.stderr}")
        raise Exception("Stage 1 execution failed")

    logger.info("Stage 1 completed successfully")
    return output_csv

def prepare_stage2_input(stage1_output):
    """Prepare CSV for Stage 2: Only businesses with emails"""
    logger.info("Analyzing Stage 1 results...")

    df = pd.read_csv(stage1_output)

    # Filter: only businesses where email was found
    has_email = (df['emails'].notna()) & (df['emails'].str.len() > 0)
    df_with_email = df[has_email].copy()

    logger.info(f"Stage 1 results:")
    logger.info(f"  Total processed: {len(df)}")
    logger.info(f"  Emails found: {len(df_with_email)} ({len(df_with_email)/len(df)*100:.1f}%)")

    if len(df_with_email) == 0:
        logger.warning("No emails found in Stage 1!")
        return None, 0

    # Prepare Stage 2 input
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_csv = TEMP_DIR / f"stage2_input_{timestamp}.csv"

    df_with_email.to_csv(input_csv, index=False)
    logger.info(f"Stage 2 input created: {input_csv}")

    return input_csv, len(df_with_email)

def run_stage2_content(input_csv, output_csv):
    """Stage 2: Content scraping for businesses with emails"""
    logger.info("="*80)
    logger.info("STAGE 2: CONTENT SCRAPING (emails found only)")
    logger.info("="*80)

    cmd = [
        "py",
        str(SCRAPER_SCRIPT),
        "--input", str(input_csv),
        "--output", str(output_csv),
        "--extract-emails",        # Re-extract (for consistency)
        "--extract-phones",        # Also get phones
        "--scrape-mode", "single", # Single page (homepage)
        "--workers", "50",
        "--timeout", "10"
    ]

    logger.info(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Stage 2 failed with code {result.returncode}")
        logger.error(f"STDERR: {result.stderr}")
        raise Exception("Stage 2 execution failed")

    logger.info("Stage 2 completed successfully")
    return output_csv

def merge_stages(original_parquet, stage1_output, stage2_output):
    """Merge both stages into final enriched dataset"""
    logger.info("Merging Stage 1 + Stage 2 results...")

    # Load original data
    df_original = pd.read_parquet(original_parquet)

    # Load Stage 1 (emails only)
    df_stage1 = pd.read_csv(stage1_output)
    if 'url' in df_stage1.columns:
        df_stage1.rename(columns={'url': 'website'}, inplace=True)

    # Load Stage 2 (content for emails found)
    df_stage2 = pd.read_csv(stage2_output)
    if 'url' in df_stage2.columns:
        df_stage2.rename(columns={'url': 'website'}, inplace=True)

    # Merge Stage 1 emails
    df_merged = df_original.merge(
        df_stage1[['website', 'status', 'emails']],
        on='website',
        how='left',
        suffixes=('', '_stage1')
    )

    # Merge Stage 2 content (for those with emails)
    df_merged = df_merged.merge(
        df_stage2[['website', 'content', 'phones', 'processing_time']],
        on='website',
        how='left',
        suffixes=('', '_stage2')
    )

    # Rename columns
    df_merged.rename(columns={
        'emails': 'email',
        'status': 'scraping_status',
        'content': 'website_content'
    }, inplace=True)

    return df_merged

def save_enriched_parquet(df):
    """Save final enriched data"""
    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"with_emails_{timestamp}.parquet"

    output_file = ENRICHED_DIR / filename
    df.to_parquet(output_file, index=False)

    # Also save as latest
    latest_file = ENRICHED_DIR / "with_emails_latest.parquet"
    df.to_parquet(latest_file, index=False)

    logger.info(f"Enriched Parquet saved: {output_file}")
    logger.info(f"Latest version: {latest_file}")

    return output_file

def print_final_stats(df):
    """Print comprehensive final statistics"""
    print("\n" + "="*80)
    print("FINAL ENRICHMENT RESULTS")
    print("="*80)

    total = len(df)

    # Email stats
    has_email = (df['email'].notna()) & (df['email'].str.len() > 0)
    email_count = has_email.sum()

    print(f"\nEMAIL EXTRACTION:")
    print(f"  Total businesses:   {total:>5}")
    print(f"  Emails found:       {email_count:>5} ({email_count/total*100:.1f}%)")
    print(f"  No email:           {total-email_count:>5} ({(total-email_count)/total*100:.1f}%)")

    # Content stats
    has_content = (df['website_content'].notna()) & (df['website_content'].str.len() > 100)
    content_count = has_content.sum()

    print(f"\nCONTENT EXTRACTION:")
    print(f"  With content:       {content_count:>5} ({content_count/total*100:.1f}%)")
    print(f"  Without content:    {total-content_count:>5}")

    # Ready for AI
    ready_for_ai = has_email & has_content
    ai_ready_count = ready_for_ai.sum()

    print(f"\nREADY FOR AI ANALYSIS:")
    print(f"  Email + Content:    {ai_ready_count:>5} ({ai_ready_count/total*100:.1f}%)")

    # Sample
    print(f"\nSAMPLE ENRICHED BUSINESSES:")
    sample = df[ready_for_ai][['name', 'city', 'niche', 'email']].head(10)
    for idx, row in sample.iterrows():
        print(f"  {row['name']:45} | {row['city']:20} | {row['email']}")

    # Save failed
    failed = df[~has_email & df['scraping_status'].notna()]
    if len(failed) > 0:
        failed_csv = ENRICHED_DIR / f"no_email_found_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        failed[['place_id', 'name', 'website', 'city', 'state', 'niche']].to_csv(failed_csv, index=False)
        print(f"\nBusinesses without email saved to: {failed_csv}")

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("  1. AI analysis on enriched data")
    print("  2. Icebreaker generation")
    print("  3. Export to Instantly")
    print("="*80 + "\n")

def main():
    """Main 2-stage execution"""
    try:
        print("\n" + "="*80)
        print("2-STAGE EMAIL + CONTENT ENRICHMENT PIPELINE")
        print("="*80)
        print("Strategy: Quick emails first, then content for successes")
        print("="*80 + "\n")

        # Stage 1: Email extraction
        stage1_input, total_count, timestamp = prepare_stage1_input()

        estimated_stage1 = total_count * 0.5 / 60  # 0.5 sec per business
        print(f"STAGE 1: Email extraction")
        print(f"  Businesses: {total_count:,}")
        print(f"  Estimated time: ~{estimated_stage1:.1f} minutes")
        print()

        stage1_output = TEMP_DIR / f"stage1_output_{timestamp}.csv"
        run_stage1_emails(stage1_input, stage1_output)

        # Stage 2: Content scraping for emails found
        stage2_input, stage2_count = prepare_stage2_input(stage1_output)

        if stage2_input is None:
            logger.error("No emails found in Stage 1. Stopping.")
            return

        estimated_stage2 = stage2_count * 0.5 / 60
        print(f"\nSTAGE 2: Content scraping")
        print(f"  Businesses: {stage2_count:,}")
        print(f"  Estimated time: ~{estimated_stage2:.1f} minutes")
        print()

        stage2_output = TEMP_DIR / f"stage2_output_{timestamp}.csv"
        run_stage2_content(stage2_input, stage2_output)

        # Merge results
        df_final = merge_stages(PARQUET_FILE, stage1_output, stage2_output)

        # Save
        output_file = save_enriched_parquet(df_final)

        # Stats
        print_final_stats(df_final)

        logger.info("2-Stage pipeline completed successfully!")
        logger.info(f"Final enriched data: {output_file}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
