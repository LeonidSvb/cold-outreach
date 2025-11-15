#!/usr/bin/env python3
"""
=== RE-SCRAPE SUSPICIOUS EMAILS ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Re-scrape websites with suspicious/invalid emails using FIXED email extraction

FEATURES:
- Filter 100 suspicious/invalid emails from quality analysis
- Match to original CSV to get websites
- Re-scrape with fixed text_utils.py (no AI, just emails)
- Compare old vs new emails
- 30 parallel workers

USAGE:
1. Run: python rescrape_suspicious_emails.py
2. Results: modules/scraping/results/rescrape_comparison_YYYYMMDD_HHMMSS.csv
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import requests
from typing import Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import fixed email extraction
sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.text_utils import extract_emails_from_html

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
QUALITY_ANALYSIS_CSV = Path(__file__).parent.parent.parent / "openai" / "results" / "email_quality_analysis.csv"
SOVIET_BOOTS_CSV = Path(r"C:\Users\79818\Downloads\Soviet Boots - Sheet3.csv")
OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Config
PARALLEL_WORKERS = 30
TEST_LIMIT = 100  # Take 100 suspicious emails
TIMEOUT = 10  # seconds


class EmailRecraper:
    """Re-scrape emails from websites using fixed extraction"""

    def __init__(self):
        self.processed_count = 0
        self.success_count = 0
        self.failed_count = 0
        self._lock = threading.Lock()

    def scrape_emails(self, website: str, old_email: str) -> Dict:
        """Scrape emails from website"""

        if not website or pd.isna(website):
            return {
                'website': website,
                'old_email': old_email,
                'new_emails': '',
                'status': 'no_website',
                'error': 'No website URL'
            }

        # Normalize URL
        if not website.startswith('http'):
            website = f'https://{website}'

        try:
            logger.info(f"Scraping: {website}")

            # Fetch homepage
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(website, headers=headers, timeout=TIMEOUT)

            if response.status_code != 200:
                with self._lock:
                    self.failed_count += 1
                    self.processed_count += 1
                return {
                    'website': website,
                    'old_email': old_email,
                    'new_emails': '',
                    'status': 'http_error',
                    'error': f'HTTP {response.status_code}'
                }

            # Extract emails using FIXED text_utils
            html = response.text
            emails = extract_emails_from_html(html)

            with self._lock:
                if emails:
                    self.success_count += 1
                else:
                    self.failed_count += 1
                self.processed_count += 1

                if self.processed_count % 10 == 0:
                    logger.info(f"Progress: {self.processed_count} | Success: {self.success_count} | Failed: {self.failed_count}")

            return {
                'website': website,
                'old_email': old_email,
                'new_emails': ', '.join(emails),
                'emails_count': len(emails),
                'status': 'success' if emails else 'no_emails_found',
                'error': ''
            }

        except requests.Timeout:
            with self._lock:
                self.failed_count += 1
                self.processed_count += 1
            return {
                'website': website,
                'old_email': old_email,
                'new_emails': '',
                'status': 'timeout',
                'error': 'Request timeout'
            }

        except Exception as e:
            with self._lock:
                self.failed_count += 1
                self.processed_count += 1
            return {
                'website': website,
                'old_email': old_email,
                'new_emails': '',
                'status': 'error',
                'error': str(e)
            }


def main():
    """Main re-scraping pipeline"""
    logger.info("=== RE-SCRAPE SUSPICIOUS EMAILS STARTED ===")

    # Step 1: Load quality analysis
    logger.info(f"Loading quality analysis: {QUALITY_ANALYSIS_CSV}")
    df_quality = pd.read_csv(QUALITY_ANALYSIS_CSV)

    # Step 2: Filter suspicious/invalid emails
    suspicious = df_quality[
        (df_quality['category'] == 'SUSPICIOUS') |
        (df_quality['category'] == 'INVALID')
    ].head(TEST_LIMIT).copy()

    logger.info(f"Found {len(suspicious)} suspicious/invalid emails")
    logger.info(f"Categories: {suspicious['category'].value_counts().to_dict()}")

    # Step 3: Load Soviet Boots CSV to match websites
    logger.info(f"Loading Soviet Boots CSV: {SOVIET_BOOTS_CSV}")
    df_soviet = pd.read_csv(SOVIET_BOOTS_CSV)

    # Step 4: Match emails to websites
    # Expand Soviet Boots CSV to have one row per email
    museums_to_scrape = []

    for _, row in df_soviet.iterrows():
        emails_str = str(row['emails'])
        if pd.isna(row['emails']) or not emails_str.strip():
            continue

        emails = [e.strip() for e in emails_str.split(',') if e.strip()]

        for email in emails:
            # Check if this email is in suspicious list
            if email.lower() in suspicious['email'].str.lower().values:
                museums_to_scrape.append({
                    'name': row['name'],
                    'website': row.get('website', ''),
                    'old_email': email
                })

    logger.info(f"Museums to re-scrape: {len(museums_to_scrape)}")

    if len(museums_to_scrape) == 0:
        logger.error("No museums to scrape! Check email matching logic.")
        return

    # Step 5: Re-scrape with fixed extraction
    logger.info(f"Starting re-scraping with {PARALLEL_WORKERS} workers...")
    scraper = EmailRecraper()
    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        futures = {
            executor.submit(scraper.scrape_emails, museum['website'], museum['old_email']): museum
            for museum in museums_to_scrape
        }

        for future in as_completed(futures):
            result = future.result()
            if result:
                museum = futures[future]
                result['name'] = museum['name']
                results.append(result)

    # Step 6: Create comparison DataFrame
    df_results = pd.DataFrame(results)

    # Add comparison columns
    df_results['fixed'] = df_results.apply(
        lambda row: 'YES' if row['new_emails'] and row['new_emails'] != row['old_email'] else 'NO',
        axis=1
    )

    df_results['same_email'] = df_results.apply(
        lambda row: 'YES' if row['old_email'].lower() in row['new_emails'].lower() else 'NO',
        axis=1
    )

    # Reorder columns
    df_results = df_results[[
        'name', 'website', 'old_email', 'new_emails', 'emails_count',
        'fixed', 'same_email', 'status', 'error'
    ]]

    # Step 7: Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = OUTPUT_DIR / f"rescrape_comparison_{timestamp}.csv"
    df_results.to_csv(output_csv, index=False, encoding='utf-8-sig')

    # Step 8: Print statistics
    elapsed = time.time() - start_time

    logger.info("\n=== RE-SCRAPING COMPLETE ===")
    logger.info(f"Total processed: {scraper.processed_count}")
    logger.info(f"Success (found emails): {scraper.success_count}")
    logger.info(f"Failed (no emails/error): {scraper.failed_count}")
    logger.info(f"Time elapsed: {elapsed:.1f} seconds")
    logger.info(f"Output: {output_csv}")

    # Detailed stats
    logger.info("\n=== COMPARISON STATS ===")
    logger.info(f"Fixed (new email found): {len(df_results[df_results['fixed'] == 'YES'])}")
    logger.info(f"Same email found: {len(df_results[df_results['same_email'] == 'YES'])}")
    logger.info(f"No emails found: {len(df_results[df_results['new_emails'] == ''])}")

    logger.info("\n=== STATUS BREAKDOWN ===")
    logger.info(df_results['status'].value_counts().to_string())

    # Show sample results
    logger.info("\n=== SAMPLE FIXED EMAILS (First 10) ===")
    fixed_samples = df_results[df_results['fixed'] == 'YES'].head(10)
    for _, row in fixed_samples.iterrows():
        logger.info(f"OLD: {row['old_email']}")
        logger.info(f"NEW: {row['new_emails']}")
        logger.info(f"Website: {row['website']}")
        logger.info("---")


if __name__ == "__main__":
    main()
