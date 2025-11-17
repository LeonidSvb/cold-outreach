#!/usr/bin/env python3
"""
=== SIMPLE HOMEPAGE SCRAPER ===
Version: 1.0.0 | Created: 2025-01-16

PURPOSE:
Fast homepage scraping - NO AI, just emails + text content
1. Scrape homepage content (clean text)
2. Extract emails from homepage
3. Detect site type (static/dynamic)

FEATURES:
- Homepage-only scraping
- Email extraction
- Full text content extraction
- Site type detection (static/dynamic)
- Maximum parallel processing (50 workers)
- NO AI analysis (fast & free)

USAGE:
python simple_homepage_scraper.py --input input.csv --workers 50

INPUT CSV Required Columns:
- name
- website

OUTPUT CSV Columns:
- name
- website
- email (ONE EMAIL PER ROW - if 3 emails found, 3 rows created)
- homepage_content (full text from homepage)
- site_type (static | dynamic | unknown)
- scrape_status (success | failed)
- error_message

NOTE: Each email gets its own row. If a site has 3 emails, you'll get 3 rows with the same content but different emails.

IMPROVEMENTS:
v1.0.0 - Initial simple version (no AI, maximum speed)
"""

import sys
import time
import argparse
import pandas as pd
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from modules.logging.shared.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Import scraping utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from lib.http_utils import HTTPClient
    from lib.text_utils import extract_emails_from_html, clean_html_to_text
except ImportError:
    from modules.scraping.lib.http_utils import HTTPClient
    from modules.scraping.lib.text_utils import extract_emails_from_html, clean_html_to_text


class SimpleHomepageScraper:
    """
    Simple homepage scraper - emails + content only
    """

    def __init__(self, workers: int = 50):
        self.http_client = HTTPClient(timeout=15, retries=3)
        self.workers = workers

        # Thread-safe stats
        self._lock = threading.Lock()
        self.stats = {
            "total_processed": 0,
            "success": 0,
            "failed": 0,
            "emails_found": 0,
            "no_emails": 0,
            "static_sites": 0,
            "dynamic_sites": 0,
        }

    def scrape_homepage(self, name: str, website: str) -> List[Dict]:
        """
        Scrape homepage and extract emails + content

        Returns:
            List of dicts - one per email found (or one with empty email if none found)
            [
                {
                    'name': business name,
                    'website': website URL,
                    'email': email found,
                    'homepage_content': full text content,
                    'site_type': 'static' | 'dynamic' | 'unknown',
                    'scrape_status': 'success' | 'failed',
                    'error_message': error if failed
                }
            ]
        """
        base_result = {
            'name': name,
            'website': website,
            'email': '',
            'homepage_content': '',
            'site_type': 'unknown',
            'scrape_status': 'failed',
            'error_message': ''
        }

        if not website or pd.isna(website):
            base_result['error_message'] = 'No website provided'
            with self._lock:
                self.stats['total_processed'] += 1
                self.stats['failed'] += 1
            return [base_result]

        # Normalize URL
        if not website.startswith('http'):
            website = f'https://{website}'

        try:
            # Fetch homepage
            response = self.http_client.fetch(website, check_content_length=False)

            if response['status'] == 'success':
                html_content = response['content']

                # Extract emails
                emails = extract_emails_from_html(html_content)
                clean_emails = [self._clean_email(e) for e in emails if self._clean_email(e)]

                # Extract full text content
                clean_text = clean_html_to_text(html_content, max_length=50000)

                # Detect site type
                site_type = self._detect_site_type(html_content)

                if site_type == 'static':
                    with self._lock:
                        self.stats['static_sites'] += 1
                elif site_type == 'dynamic':
                    with self._lock:
                        self.stats['dynamic_sites'] += 1

                # Create one row per email
                results = []
                if clean_emails:
                    for email in clean_emails:
                        row = base_result.copy()
                        row['email'] = email
                        row['homepage_content'] = clean_text
                        row['site_type'] = site_type
                        row['scrape_status'] = 'success'
                        results.append(row)

                    with self._lock:
                        self.stats['emails_found'] += len(clean_emails)
                else:
                    # No emails found - create one row with empty email
                    row = base_result.copy()
                    row['homepage_content'] = clean_text
                    row['site_type'] = site_type
                    row['scrape_status'] = 'success'
                    results.append(row)

                    with self._lock:
                        self.stats['no_emails'] += 1

                with self._lock:
                    self.stats['total_processed'] += 1
                    self.stats['success'] += 1

                logger.info(f"✓ {name}: {len(clean_emails)} emails, {len(clean_text)} chars, {site_type}")

                return results

            else:
                base_result['error_message'] = response.get('error', 'Unknown error')
                with self._lock:
                    self.stats['total_processed'] += 1
                    self.stats['failed'] += 1

                logger.warning(f"✗ {name}: {base_result['error_message']}")
                return [base_result]

        except Exception as e:
            base_result['error_message'] = str(e)
            with self._lock:
                self.stats['total_processed'] += 1
                self.stats['failed'] += 1

            logger.error(f"✗ {name}: {e}")
            return [base_result]

    def _clean_email(self, email: str) -> Optional[str]:
        """Clean and validate email"""
        if not email:
            return None

        email = email.strip().lower()

        # Remove common junk
        if any(x in email for x in ['example.com', 'domain.com', 'yoursite.com', 'test.com']):
            return None

        # Basic validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            return None

        # Length check
        if len(email) < 5 or len(email) > 100:
            return None

        return email

    def _detect_site_type(self, html_content: str) -> str:
        """
        Detect if site is static or dynamic (React/Vue/Angular/etc)

        Returns:
            'static' | 'dynamic' | 'unknown'
        """
        html_lower = html_content.lower()

        # Check for SPA frameworks
        dynamic_indicators = [
            'react', 'vue', 'angular', 'next.js', 'nuxt',
            'app.js', 'bundle.js', 'main.js',
            '<div id="root"', '<div id="app"',
            'ng-app', 'v-app', 'data-react',
        ]

        for indicator in dynamic_indicators:
            if indicator in html_lower:
                return 'dynamic'

        # Static site indicators
        static_indicators = [
            '<html', '<body', '<p>', '<div>',
        ]

        # If has basic HTML structure but no SPA frameworks
        if any(indicator in html_lower for indicator in static_indicators):
            return 'static'

        return 'unknown'

    def process_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process batch of leads with parallel scraping

        Args:
            df: DataFrame with 'name' and 'website' columns

        Returns:
            DataFrame with scraping results (one row per email)
        """
        logger.info("="*70)
        logger.info("SIMPLE HOMEPAGE SCRAPER STARTED")
        logger.info("="*70)
        logger.info(f"Total leads: {len(df)}")
        logger.info(f"Workers: {self.workers}")
        logger.info("="*70)

        start_time = time.time()
        all_rows = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    self.scrape_homepage,
                    row['name'],
                    row['website']
                ): idx for idx, row in df.iterrows()
            }

            # Collect results
            processed_count = 0
            for future in as_completed(futures):
                try:
                    # Each result is a list of dicts (one per email)
                    result_rows = future.result()
                    all_rows.extend(result_rows)

                    processed_count += 1

                    # Progress update every 50 leads
                    if processed_count % 50 == 0:
                        logger.info(f"Progress: {processed_count}/{len(df)} leads processed...")

                except Exception as e:
                    logger.error(f"Task failed: {e}")

        # Create results DataFrame
        df_results = pd.DataFrame(all_rows)

        # Print summary
        duration = time.time() - start_time

        logger.info("="*70)
        logger.info("SCRAPING COMPLETE")
        logger.info("="*70)
        logger.info(f"Total leads processed: {self.stats['total_processed']}")
        logger.info(f"Total rows in output: {len(df_results)}")
        logger.info(f"Success: {self.stats['success']} ({self.stats['success']/self.stats['total_processed']*100:.1f}%)")
        logger.info(f"Failed: {self.stats['failed']} ({self.stats['failed']/self.stats['total_processed']*100:.1f}%)")
        logger.info(f"Total emails found: {self.stats['emails_found']}")
        logger.info(f"Leads with emails: {self.stats['success'] - self.stats['no_emails']}")
        logger.info(f"Leads without emails: {self.stats['no_emails']}")
        logger.info(f"Static sites: {self.stats['static_sites']}")
        logger.info(f"Dynamic sites: {self.stats['dynamic_sites']}")
        logger.info(f"Duration: {duration:.2f}s ({duration/60:.1f} min)")
        logger.info(f"Speed: {len(df)/duration:.2f} leads/sec")
        logger.info("="*70)

        return df_results


def main():
    parser = argparse.ArgumentParser(description='Simple Homepage Scraper - Emails + Content')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', help='Output CSV file path (optional, auto-generated if not provided)')
    parser.add_argument('--workers', type=int, default=50, help='Number of parallel workers (default: 50)')
    parser.add_argument('--limit', type=int, help='Limit number of leads to process (for testing)')

    args = parser.parse_args()

    # Read input CSV
    logger.info(f"Reading input file: {args.input}")
    df = pd.read_csv(args.input, encoding='utf-8-sig')

    # Validate columns
    required_cols = ['name', 'website']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)

    # Apply limit if specified
    if args.limit:
        df = df.head(args.limit)
        logger.info(f"Limited to first {args.limit} leads")

    # Create scraper
    scraper = SimpleHomepageScraper(workers=args.workers)

    # Process batch
    df_results = scraper.process_batch(df)

    # Generate output filename
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent.parent / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"reenactors_scraped_{timestamp}.csv"

    # Save results
    df_results.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"Results saved to: {output_path}")
    logger.info(f"Total rows: {len(df_results)}")


if __name__ == "__main__":
    main()
