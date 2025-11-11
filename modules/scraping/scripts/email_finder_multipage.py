#!/usr/bin/env python3
"""
=== MULTI-PAGE EMAIL FINDER WITH SITEMAP SUPPORT ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Find emails on websites using intelligent multi-page scraping strategy.
Sitemap-first approach with pattern guessing fallback.

STRATEGY:
1. Check homepage (already done - skip if homepage scraped)
2. Try sitemap.xml discovery (70-80% success rate)
3. Scrape contact-related pages from sitemap
4. Fallback to pattern guessing if no sitemap
5. Stop on first email found (efficiency)

USAGE:
python email_finder_multipage.py --input enriched_final_latest.parquet

INPUT:
- Parquet file with columns: place_id, name, website, email
- Only processes leads where email is NULL

OUTPUT:
- Updated parquet with new emails
- CSV report with scraping stats
- Success rate: expected 15-25% additional emails

BENCHMARKS:
- 4,255 leads without email
- Estimated time: 2-3 hours (50 workers)
- Estimated new emails: 600-1,000 (15-25%)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

# Import scraping utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from lib.http_utils import HTTPClient
    from lib.text_utils import extract_emails_from_html
    from lib.sitemap_utils import SitemapParser
except ImportError:
    from modules.scraping.lib.http_utils import HTTPClient
    from modules.scraping.lib.text_utils import extract_emails_from_html
    from modules.scraping.lib.sitemap_utils import SitemapParser


class MultiPageEmailFinder:
    """
    Intelligent multi-page email scraper

    Uses sitemap-first strategy for efficient email discovery
    """

    def __init__(self, workers: int = 50, timeout: int = 10):
        self.http_client = HTTPClient(timeout=timeout)
        self.sitemap_parser = SitemapParser(timeout=timeout)
        self.workers = workers

        # Stats
        self.stats = {
            'total_processed': 0,
            'emails_found': 0,
            'sitemap_success': 0,
            'pattern_fallback': 0,
            'failed': 0
        }

    def find_email(self, website: str, business_name: str) -> Dict:
        """
        Find email using multi-page scraping

        Args:
            website: Website URL
            business_name: Business name (for logging)

        Returns:
            {
                'email': found email or None,
                'strategy': 'sitemap' | 'pattern' | 'none',
                'pages_checked': number of pages scraped,
                'sitemap_found': True/False
            }
        """
        result = {
            'email': None,
            'strategy': 'none',
            'pages_checked': 0,
            'sitemap_found': False
        }

        # Normalize domain
        if not website.startswith('http'):
            website = f'https://{website}'

        try:
            # Get smart pages using sitemap-first
            discovery = self.sitemap_parser.get_smart_pages(website, max_pages=10)

            result['strategy'] = discovery['strategy']
            result['sitemap_found'] = discovery['sitemap_found']

            # Scrape discovered pages
            for page_url in discovery['pages']:
                result['pages_checked'] += 1

                # Fetch page
                page_result = self.http_client.fetch(page_url, check_content_length=False)

                if page_result['status'] == 'success':
                    html_content = page_result['content']

                    # Extract emails
                    emails = extract_emails_from_html(html_content)

                    if emails:
                        # Clean and validate email
                        clean_email = self._clean_email(emails[0])
                        if clean_email:
                            result['email'] = clean_email
                            logger.info(f"✓ Email found for {business_name}: {clean_email}")
                            return result

            # No email found
            if result['pages_checked'] > 0:
                logger.warning(f"✗ No email found for {business_name} ({result['pages_checked']} pages checked)")

        except Exception as e:
            logger.error(f"Error processing {business_name}: {e}")
            result['strategy'] = 'error'

        return result

    def _clean_email(self, email: str) -> Optional[str]:
        """
        Clean and validate email address

        Filters out:
        - Generic/fake emails (example@, test@, noreply@)
        - Invalid formats

        Returns:
            Cleaned email or None if invalid
        """
        if not email:
            return None

        email = email.lower().strip()

        # Filter fake emails
        fake_patterns = [
            'example.com', 'test.com', 'placeholder',
            'noreply@', 'no-reply@', 'donotreply@',
            'webmaster@', 'admin@', 'postmaster@',
            'info@example', 'contact@example'
        ]

        if any(pattern in email for pattern in fake_patterns):
            return None

        # Validate format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return None

        return email

    def process_batch(self, leads_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process batch of leads with parallel workers

        Args:
            leads_df: DataFrame with columns: place_id, name, website

        Returns:
            DataFrame with new columns: new_email, strategy, pages_checked, sitemap_found
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all tasks
            future_to_lead = {
                executor.submit(
                    self.find_email,
                    row['website'],
                    row['name']
                ): row
                for _, row in leads_df.iterrows()
            }

            # Process completed tasks
            for future in as_completed(future_to_lead):
                lead = future_to_lead[future]

                try:
                    result = future.result()

                    # Track stats
                    self.stats['total_processed'] += 1
                    if result['email']:
                        self.stats['emails_found'] += 1
                    if result['sitemap_found']:
                        self.stats['sitemap_success'] += 1
                    if result['strategy'] == 'pattern':
                        self.stats['pattern_fallback'] += 1
                    if result['strategy'] == 'error':
                        self.stats['failed'] += 1

                    # Store result
                    results.append({
                        'place_id': lead['place_id'],
                        'new_email': result['email'],
                        'email_strategy': result['strategy'],
                        'pages_checked': result['pages_checked'],
                        'sitemap_found': result['sitemap_found']
                    })

                    # Progress logging
                    if self.stats['total_processed'] % 50 == 0:
                        logger.info(f"Progress: {self.stats['total_processed']}/{len(leads_df)} | "
                                    f"Emails found: {self.stats['emails_found']}")

                except Exception as e:
                    logger.error(f"Task failed for {lead['name']}: {e}")
                    self.stats['failed'] += 1

        # Convert results to DataFrame
        results_df = pd.DataFrame(results)

        return results_df


def main():
    """Main pipeline"""
    parser = argparse.ArgumentParser(description='Multi-page email finder with sitemap support')
    parser.add_argument('--input', type=str,
                        default='modules/google_maps/data/enriched/enriched_final_latest.parquet',
                        help='Input parquet file')
    parser.add_argument('--workers', type=int, default=50, help='Number of parallel workers')
    parser.add_argument('--timeout', type=int, default=10, help='HTTP timeout (seconds)')
    parser.add_argument('--limit', type=int, default=None, help='Limit processing (for testing)')

    args = parser.parse_args()

    logger.info("=== Multi-Page Email Finder Started ===")

    # Load input
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    logger.info(f"Loading leads from: {input_path}")
    df = pd.read_parquet(input_path)

    # Filter: leads without email but with website
    df_no_email = df[
        (df['email'].isna()) &
        (df['website'].notna()) &
        (df['website'].str.len() > 10)
    ].copy()

    logger.info(f"Total leads: {len(df)}")
    logger.info(f"Leads without email: {len(df_no_email)}")

    # Apply limit if testing
    if args.limit:
        df_no_email = df_no_email.head(args.limit)
        logger.info(f"TESTING MODE: Limited to {args.limit} leads")

    # Initialize finder
    finder = MultiPageEmailFinder(workers=args.workers, timeout=args.timeout)

    # Process leads
    start_time = time.time()
    results_df = finder.process_batch(df_no_email)

    # Merge results back
    df_updated = df_no_email.merge(results_df, on='place_id', how='left')

    # Update email column
    df_updated['email'] = df_updated.apply(
        lambda row: row['new_email'] if pd.notna(row['new_email']) else row['email'],
        axis=1
    )

    # Merge with full dataset
    df_final = df.copy()
    df_final.update(df_updated)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path('modules/scraping/results')
    output_dir.mkdir(parents=True, exist_ok=True)

    output_parquet = output_dir / f"multipage_enriched_{timestamp}.parquet"
    df_final.to_parquet(output_parquet, index=False)

    # Export stats report
    stats_report = output_dir / f"multipage_stats_{timestamp}.csv"
    df_updated[df_updated['new_email'].notna()].to_csv(stats_report, index=False)

    # Final stats
    elapsed = time.time() - start_time
    success_rate = (finder.stats['emails_found'] / finder.stats['total_processed'] * 100) if finder.stats['total_processed'] > 0 else 0

    logger.info("=== Multi-Page Scraping Complete ===")
    logger.info(f"Total processed: {finder.stats['total_processed']}")
    logger.info(f"New emails found: {finder.stats['emails_found']}")
    logger.info(f"Success rate: {success_rate:.1f}%")
    logger.info(f"Sitemap success: {finder.stats['sitemap_success']}")
    logger.info(f"Pattern fallback: {finder.stats['pattern_fallback']}")
    logger.info(f"Failed: {finder.stats['failed']}")
    logger.info(f"Time elapsed: {elapsed/60:.1f} minutes")
    logger.info(f"Output: {output_parquet}")
    logger.info(f"Stats: {stats_report}")


if __name__ == "__main__":
    main()
