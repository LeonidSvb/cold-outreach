#!/usr/bin/env python3
"""
=== PRODUCTION EMAIL ENRICHMENT PIPELINE ===
Version: 2.0.0 | Created: 2025-01-10

PURPOSE:
Industry-standard incremental scraping with intelligent fallback.
Minimizes HTTP requests, maximizes email extraction rate.

STRATEGY (Best Practice):
1. Homepage scraping (all businesses) - fast, gets 35-40% emails
2. Multi-page fallback (no email found) - slower, gets +15-20% emails
3. Pattern guessing (still no email) - instant, gets +10-15% emails

TOTAL EXPECTED: ~60-70% email coverage

USAGE:
python run_email_enrichment_production.py
"""

import sys
import logging
import pandas as pd
import subprocess
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PARQUET_FILE = Path(__file__).parent.parent / "data" / "raw" / "all_leads.parquet"
ENRICHED_DIR = Path(__file__).parent.parent / "data" / "enriched"
TEMP_DIR = Path(__file__).parent.parent / "data" / "temp"
SCRAPER_SCRIPT = PROJECT_ROOT / "modules" / "scraping" / "scripts" / "website_scraper.py"

# Common email patterns (for pattern guessing)
EMAIL_PATTERNS = ['info', 'contact', 'hello', 'sales', 'support', 'office']

def prepare_input_csv(df, filename):
    """Generic CSV preparation"""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_csv = TEMP_DIR / f"{filename}_{timestamp}.csv"

    df_export = df[['place_id', 'name', 'website', 'city', 'state', 'niche']].copy()
    df_export.rename(columns={'website': 'url'}, inplace=True)
    df_export.to_csv(input_csv, index=False)

    return input_csv, timestamp

def run_scraper(input_csv, output_csv, mode='single', workers=50):
    """
    Run website_scraper.py with specified mode

    Args:
        mode: 'single' (homepage only) or 'smart' (multi-page)
    """
    cmd = [
        "py",
        str(SCRAPER_SCRIPT),
        "--input", str(input_csv),
        "--output", str(output_csv),
        "--extract-emails",
        "--extract-phones",
        "--scrape-mode", mode,
        "--workers", str(workers),
        "--timeout", "10"
    ]

    logger.info(f"Running scraper: mode={mode}, workers={workers}")
    logger.info(f"Input: {input_csv}")
    logger.info(f"Output: {output_csv}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"Scraper failed with code {result.returncode}")
        logger.error(f"STDERR: {result.stderr}")
        raise Exception("Scraper execution failed")

    logger.info("Scraper completed successfully")
    return output_csv

def extract_domain(url):
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www.
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return None

def generate_pattern_emails(df):
    """
    Generate common email patterns for businesses without email
    Industry standard: info@, contact@, hello@, etc.
    """
    logger.info("Generating pattern-based emails...")

    results = []

    for _, row in df.iterrows():
        domain = extract_domain(row['website'])

        if not domain:
            continue

        # Generate common patterns
        pattern_emails = [f"{pattern}@{domain}" for pattern in EMAIL_PATTERNS]

        results.append({
            'place_id': row['place_id'],
            'website': row['website'],
            'pattern_emails': ', '.join(pattern_emails),
            'method': 'pattern_guess'
        })

    logger.info(f"Generated pattern emails for {len(results)} businesses")
    return pd.DataFrame(results)

def merge_enrichment_results(original_parquet, homepage_output, multipage_output=None, pattern_df=None):
    """
    Merge all enrichment stages into final dataset
    Priority: homepage > multipage > pattern guess
    """
    logger.info("Merging enrichment results...")

    # Load original
    df_original = pd.read_parquet(original_parquet)

    # Load homepage results
    df_homepage = pd.read_csv(homepage_output)
    if 'url' in df_homepage.columns:
        df_homepage.rename(columns={'url': 'website'}, inplace=True)

    # Start merge with homepage
    df_merged = df_original.merge(
        df_homepage[['website', 'status', 'emails', 'phones', 'content', 'content_length']],
        on='website',
        how='left',
        suffixes=('', '_homepage')
    )

    # Merge multi-page results (if available)
    if multipage_output and Path(multipage_output).exists():
        df_multipage = pd.read_csv(multipage_output)
        if 'url' in df_multipage.columns:
            df_multipage.rename(columns={'url': 'website'}, inplace=True)

        # Update emails from multi-page where homepage didn't find
        df_merged = df_merged.merge(
            df_multipage[['website', 'emails', 'content']],
            on='website',
            how='left',
            suffixes=('', '_multipage')
        )

        # Use multipage email if homepage didn't find
        df_merged['emails'] = df_merged['emails'].fillna(df_merged['emails_multipage'])
        df_merged['content'] = df_merged['content'].fillna(df_merged['content_multipage'])

        # Cleanup
        df_merged.drop(columns=['emails_multipage', 'content_multipage'], inplace=True, errors='ignore')

    # Add pattern emails (as backup)
    if pattern_df is not None and len(pattern_df) > 0:
        df_merged = df_merged.merge(
            pattern_df[['website', 'pattern_emails']],
            on='website',
            how='left'
        )

    # Rename for clarity
    df_merged.rename(columns={
        'emails': 'email',
        'status': 'scraping_status',
        'content': 'website_content'
    }, inplace=True)

    return df_merged

def save_enriched_parquet(df, stage_name='final'):
    """Save enriched Parquet with timestamp"""
    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enriched_{stage_name}_{timestamp}.parquet"

    output_file = ENRICHED_DIR / filename
    df.to_parquet(output_file, index=False)

    # Also save as latest
    latest_file = ENRICHED_DIR / f"enriched_{stage_name}_latest.parquet"
    df.to_parquet(latest_file, index=False)

    logger.info(f"Saved: {output_file}")
    logger.info(f"Latest: {latest_file}")

    return output_file

def print_stage_summary(df, stage_name):
    """Print summary for each stage"""
    print(f"\n{'='*80}")
    print(f"{stage_name.upper()} SUMMARY")
    print(f"{'='*80}")

    total = len(df)
    has_email = (df['email'].notna()) & (df['email'].str.len() > 0)
    email_count = has_email.sum()

    print(f"Total businesses: {total:,}")
    print(f"Emails found:     {email_count:,} ({email_count/total*100:.1f}%)")

    if 'website_content' in df.columns:
        has_content = (df['website_content'].notna()) & (df['website_content'].str.len() > 100)
        content_count = has_content.sum()
        print(f"Content scraped:  {content_count:,} ({content_count/total*100:.1f}%)")

    print(f"{'='*80}\n")

    return email_count, total

def main():
    """
    PRODUCTION PIPELINE - Industry Standard Incremental Scraping
    """
    try:
        print("\n" + "="*80)
        print("PRODUCTION EMAIL ENRICHMENT PIPELINE v2.0")
        print("="*80)
        print("Strategy: Incremental scraping with intelligent fallback")
        print("="*80 + "\n")

        # Load original data
        logger.info(f"Loading: {PARQUET_FILE}")
        df_original = pd.read_parquet(PARQUET_FILE)
        df_ready = df_original[df_original['has_website'] == True].copy()

        logger.info(f"Total businesses with website: {len(df_ready):,}")

        # ================================================================
        # STAGE 1: HOMEPAGE SCRAPING (all businesses)
        # ================================================================
        print("\n[STAGE 1] HOMEPAGE SCRAPING")
        print("-" * 80)
        print(f"Businesses: {len(df_ready):,}")
        print(f"Mode: Single page (homepage only)")
        print(f"Workers: 50")
        print(f"Estimated time: ~{len(df_ready) * 0.5 / 60:.1f} minutes")
        print()

        stage1_input, timestamp = prepare_input_csv(df_ready, "stage1_homepage")
        stage1_output = TEMP_DIR / f"stage1_homepage_{timestamp}.csv"

        run_scraper(stage1_input, stage1_output, mode='single', workers=50)

        # Analyze Stage 1 results
        df_stage1 = pd.read_csv(stage1_output)
        if 'url' in df_stage1.columns:
            df_stage1.rename(columns={'url': 'website'}, inplace=True)

        has_email_stage1 = (df_stage1['emails'].notna()) & (df_stage1['emails'].str.len() > 0)
        stage1_emails = has_email_stage1.sum()

        print(f"\n[STAGE 1 RESULTS]")
        print(f"  Emails found: {stage1_emails:,} ({stage1_emails/len(df_stage1)*100:.1f}%)")
        print(f"  No email:     {len(df_stage1) - stage1_emails:,}")

        # Save Stage 1 results
        df_after_stage1 = merge_enrichment_results(PARQUET_FILE, stage1_output)
        save_enriched_parquet(df_after_stage1, 'stage1_homepage')

        # ================================================================
        # STAGE 2: MULTI-PAGE FALLBACK (only businesses without email)
        # ================================================================
        df_no_email = df_stage1[~has_email_stage1 & (df_stage1['status'] == 'success')].copy()

        if len(df_no_email) > 0:
            print(f"\n[STAGE 2] MULTI-PAGE FALLBACK (contact/about pages)")
            print("-" * 80)
            print(f"Businesses: {len(df_no_email):,} (no email on homepage)")
            print(f"Mode: Smart (contact + about + team pages)")
            print(f"Workers: 50")
            print(f"Estimated time: ~{len(df_no_email) * 1.5 / 60:.1f} minutes")
            print()

            # Prepare input
            df_no_email_input = df_ready[df_ready['website'].isin(df_no_email['website'])].copy()
            stage2_input, timestamp2 = prepare_input_csv(df_no_email_input, "stage2_multipage")
            stage2_output = TEMP_DIR / f"stage2_multipage_{timestamp2}.csv"

            run_scraper(stage2_input, stage2_output, mode='smart', workers=50)

            # Analyze Stage 2 results
            df_stage2 = pd.read_csv(stage2_output)
            if 'url' in df_stage2.columns:
                df_stage2.rename(columns={'url': 'website'}, inplace=True)

            has_email_stage2 = (df_stage2['emails'].notna()) & (df_stage2['emails'].str.len() > 0)
            stage2_emails = has_email_stage2.sum()

            print(f"\n[STAGE 2 RESULTS]")
            print(f"  Additional emails: {stage2_emails:,} ({stage2_emails/len(df_stage2)*100:.1f}%)")
            print(f"  Total emails: {stage1_emails + stage2_emails:,}")
        else:
            stage2_output = None
            stage2_emails = 0
            logger.info("Stage 2 skipped - all businesses have email from Stage 1")

        # ================================================================
        # STAGE 3: PATTERN GUESSING (still no email)
        # ================================================================
        if stage2_output:
            df_stage2_loaded = pd.read_csv(stage2_output)
            if 'url' in df_stage2_loaded.columns:
                df_stage2_loaded.rename(columns={'url': 'website'}, inplace=True)

            still_no_email = df_stage2_loaded[
                (~((df_stage2_loaded['emails'].notna()) & (df_stage2_loaded['emails'].str.len() > 0)))
            ].copy()

            if len(still_no_email) > 0:
                print(f"\n[STAGE 3] PATTERN GUESSING (info@, contact@, etc.)")
                print("-" * 80)
                print(f"Businesses: {len(still_no_email):,} (still no email)")
                print(f"Method: Generate common email patterns")
                print()

                pattern_df = generate_pattern_emails(still_no_email)

                print(f"[STAGE 3 RESULTS]")
                print(f"  Pattern emails generated: {len(pattern_df):,}")
                print(f"  (Note: Pattern emails need verification)")
            else:
                pattern_df = None
        else:
            pattern_df = None

        # ================================================================
        # FINAL MERGE
        # ================================================================
        print(f"\n[FINAL MERGE]")
        print("-" * 80)

        df_final = merge_enrichment_results(
            PARQUET_FILE,
            stage1_output,
            stage2_output,
            pattern_df
        )

        # Save final
        output_file = save_enriched_parquet(df_final, 'final')

        # Print final stats
        email_count, total = print_stage_summary(df_final, "FINAL RESULTS")

        # Breakdown by method
        print("\nEMAIL EXTRACTION BY METHOD:")
        print(f"  Homepage (Stage 1):  {stage1_emails:,} ({stage1_emails/total*100:.1f}%)")
        print(f"  Multi-page (Stage 2): {stage2_emails:,} ({stage2_emails/total*100:.1f}%)")
        if pattern_df is not None:
            print(f"  Pattern guess:        {len(pattern_df):,} (needs verification)")

        # Save failed list
        no_email_final = df_final[
            ~((df_final['email'].notna()) & (df_final['email'].str.len() > 0))
        ]

        if len(no_email_final) > 0:
            failed_csv = ENRICHED_DIR / f"no_email_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            no_email_final[['place_id', 'name', 'website', 'city', 'state', 'niche', 'pattern_emails']].to_csv(
                failed_csv, index=False
            )
            print(f"\nBusinesses without email: {failed_csv}")

        print("\n" + "="*80)
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*80)
        print(f"Final enriched data: {output_file}")
        print(f"\nNEXT STEPS:")
        print(f"  1. Review enriched data: {output_file}")
        print(f"  2. Verify pattern emails (optional)")
        print(f"  3. Run AI enrichment on {email_count:,} businesses with emails")
        print("="*80 + "\n")

        logger.info("Production pipeline completed successfully!")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
