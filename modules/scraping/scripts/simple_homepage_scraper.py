#!/usr/bin/env python3
"""
=== SIMPLE HOMEPAGE SCRAPER ===
Version: 2.0.0 | Updated: 2025-11-18

PURPOSE:
Fast homepage scraping with multi-page fallback - NO AI, just emails + text content
1. Scrape homepage content (clean text)
2. Extract emails from homepage
3. If no emails - try 5 more pages (contact, about, team)
4. Detect site type (static/dynamic)

FEATURES:
- Homepage + multi-page fallback
- Email extraction (all emails)
- Full text content extraction
- Site type detection (static/dynamic)
- Maximum parallel processing (50 workers)
- NO AI analysis (fast & free)
- 4 output files (success, failed_static, failed_dynamic, failed_other)
- Detailed JSON analytics

USAGE:
python simple_homepage_scraper.py --input input.csv --workers 50 --max-pages 5

OUTPUT FILES:
1. success_emails.csv - Found emails
2. failed_static.csv - Static sites, no email
3. failed_dynamic.csv - Dynamic sites, no email
4. failed_other.csv - Errors
5. scraping_analytics.json - Performance metrics

IMPROVEMENTS:
v1.0.0 - Initial simple version (no AI, maximum speed)
v2.0.0 - Added multi-page search, 4 output files, detailed analytics
"""

import sys
import time
import argparse
import pandas as pd
import json
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
    from lib.sitemap_utils import SitemapParser
except ImportError:
    from modules.scraping.lib.http_utils import HTTPClient
    from modules.scraping.lib.text_utils import extract_emails_from_html, clean_html_to_text
    from modules.scraping.lib.sitemap_utils import SitemapParser


class SimpleHomepageScraper:
    """
    Simple homepage scraper with multi-page fallback
    """

    def __init__(self, workers: int = 50, max_pages: int = 5):
        self.http_client = HTTPClient(timeout=15, retries=3)
        self.sitemap_parser = SitemapParser(timeout=15)
        self.workers = workers
        self.max_pages = max_pages

        # Thread-safe stats
        self._lock = threading.Lock()
        self.stats = {
            "total_processed": 0,
            "success": 0,
            "failed": 0,
            "emails_found": 0,
            "emails_from_homepage": 0,
            "emails_from_deep": 0,
            "no_emails": 0,
            "static_sites": 0,
            "dynamic_sites": 0,
            "failed_static": 0,
            "failed_dynamic": 0,
            "failed_other": 0,
        }
        self.start_time = time.time()

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
                        row['email_source'] = 'homepage'
                        results.append(row)

                    with self._lock:
                        self.stats['emails_found'] += len(clean_emails)
                        self.stats['emails_from_homepage'] += len(clean_emails)
                        self.stats['total_processed'] += 1
                        self.stats['success'] += 1

                    logger.info(f"✓ {name}: {len(clean_emails)} emails (homepage), {site_type}")
                    return results

                # No emails on homepage - try deep search
                logger.info(f"⚠ {name}: No emails on homepage, trying deep search...")
                deep_emails = self._deep_email_search(website)

                if deep_emails:
                    for email in deep_emails:
                        row = base_result.copy()
                        row['email'] = email
                        row['homepage_content'] = clean_text
                        row['site_type'] = site_type
                        row['scrape_status'] = 'success'
                        row['email_source'] = 'deep_search'
                        results.append(row)

                    with self._lock:
                        self.stats['emails_found'] += len(deep_emails)
                        self.stats['emails_from_deep'] += len(deep_emails)
                        self.stats['total_processed'] += 1
                        self.stats['success'] += 1

                    logger.info(f"✓ {name}: {len(deep_emails)} emails (deep search), {site_type}")
                    return results

                # No emails found anywhere
                failure_type = 'dynamic' if site_type == 'dynamic' else 'static'
                row = base_result.copy()
                row['homepage_content'] = clean_text
                row['site_type'] = site_type
                row['scrape_status'] = 'failed'
                row['error_message'] = f'no_email_found_{failure_type}'
                row['email_source'] = 'none'
                results.append(row)

                with self._lock:
                    self.stats['total_processed'] += 1
                    self.stats['no_emails'] += 1
                    if failure_type == 'dynamic':
                        self.stats['failed_dynamic'] += 1
                    else:
                        self.stats['failed_static'] += 1

                logger.warning(f"✗ {name}: No emails found, {site_type}")
                return results

            else:
                base_result['error_message'] = response.get('error', 'Unknown error')
                base_result['email_source'] = 'none'
                with self._lock:
                    self.stats['total_processed'] += 1
                    self.stats['failed'] += 1
                    self.stats['failed_other'] += 1

                logger.warning(f"✗ {name}: {base_result['error_message']}")
                return [base_result]

        except Exception as e:
            base_result['error_message'] = str(e)
            base_result['email_source'] = 'none'
            with self._lock:
                self.stats['total_processed'] += 1
                self.stats['failed'] += 1
                self.stats['failed_other'] += 1

            logger.error(f"✗ {name}: {e}")
            return [base_result]

    def _deep_email_search(self, website: str) -> List[str]:
        """
        Deep email search using sitemap + contact pages

        Returns:
            List of found emails (deduplicated)
        """
        all_emails = []

        try:
            # Get smart pages (sitemap or pattern-based)
            discovery = self.sitemap_parser.get_smart_pages(website, max_pages=self.max_pages)

            # Scrape discovered pages
            for page_url in discovery['pages']:
                try:
                    response = self.http_client.fetch(page_url, check_content_length=False)

                    if response['status'] == 'success':
                        emails = extract_emails_from_html(response['content'])
                        clean_emails = [self._clean_email(e) for e in emails if self._clean_email(e)]
                        all_emails.extend(clean_emails)

                except Exception:
                    continue

        except Exception:
            pass

        # Deduplicate and limit to reasonable number
        unique_emails = list(set(all_emails))

        # Filter out if too many emails (likely scraped wrong content)
        if len(unique_emails) > 20:
            logger.warning(f"Too many emails found ({len(unique_emails)}), likely scraped wrong content - ignoring")
            return []

        return unique_emails

    def _clean_email(self, email: str) -> Optional[str]:
        """Clean and validate email"""
        if not email:
            return None

        email = email.strip().lower()

        # Fix truncated emails (.co -> .com)
        if email.endswith('.co') and not email.endswith('.co.uk'):
            email = email + 'm'

        # Remove common junk and useless emails
        fake_patterns = [
            'example.com', 'domain.com', 'yoursite.com', 'test.com',
            'filler@godaddy', 'noreply@', 'no-reply@', 'donotreply@',
            'webmaster@', 'postmaster@', 'mailer-daemon@',
            'privacy@', 'abuse@', 'hostmaster@'
        ]

        if any(pattern in email for pattern in fake_patterns):
            return None

        # Remove NPS generic emails
        nps_generic = ['abli_education@nps.gov', 'abli_interpretation@nps.gov', 'abli_administration@nps.gov']
        if email in nps_generic:
            return None

        # Basic validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            return None

        # Length check
        if len(email) < 5 or len(email) > 100:
            return None

        return email

    def get_analytics(self) -> Dict:
        """
        Get comprehensive analytics in JSON format

        Returns:
            Dict with detailed metrics
        """
        elapsed = time.time() - self.start_time

        return {
            "summary": {
                "total_sites": self.stats['total_processed'],
                "success_rate": f"{(self.stats['success'] / self.stats['total_processed'] * 100):.2f}%" if self.stats['total_processed'] > 0 else "0%",
                "duration_seconds": round(elapsed, 2),
                "duration_minutes": round(elapsed / 60, 2),
                "sites_per_second": round(self.stats['total_processed'] / elapsed, 2) if elapsed > 0 else 0
            },
            "results": {
                "success": {
                    "count": self.stats['success'],
                    "percentage": f"{(self.stats['success'] / self.stats['total_processed'] * 100):.2f}%" if self.stats['total_processed'] > 0 else "0%",
                    "total_emails": self.stats['emails_found'],
                    "from_homepage": self.stats['emails_from_homepage'],
                    "from_deep_search": self.stats['emails_from_deep']
                },
                "failed": {
                    "total": self.stats['failed'],
                    "static_no_email": {
                        "count": self.stats['failed_static'],
                        "percentage": f"{(self.stats['failed_static'] / self.stats['total_processed'] * 100):.2f}%" if self.stats['total_processed'] > 0 else "0%"
                    },
                    "dynamic_no_email": {
                        "count": self.stats['failed_dynamic'],
                        "percentage": f"{(self.stats['failed_dynamic'] / self.stats['total_processed'] * 100):.2f}%" if self.stats['total_processed'] > 0 else "0%"
                    },
                    "other_errors": {
                        "count": self.stats['failed_other'],
                        "percentage": f"{(self.stats['failed_other'] / self.stats['total_processed'] * 100):.2f}%" if self.stats['total_processed'] > 0 else "0%"
                    }
                }
            },
            "site_types": {
                "static": self.stats['static_sites'],
                "dynamic": self.stats['dynamic_sites']
            }
        }

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
    parser.add_argument('--output', help='Output directory (optional, auto-generated if not provided)')
    parser.add_argument('--workers', type=int, default=50, help='Number of parallel workers (default: 50)')
    parser.add_argument('--max-pages', type=int, default=5, help='Max pages to search per site (default: 5)')
    parser.add_argument('--limit', type=int, help='Limit number of leads to process (for testing)')

    args = parser.parse_args()

    # Read input CSV
    logger.info(f"Reading input file: {args.input}")
    df = pd.read_csv(args.input, encoding='utf-8-sig')

    # Validate only website column is required
    if 'website' not in df.columns:
        logger.error("Missing required column: 'website'")
        sys.exit(1)

    # Auto-generate name from domain if not present
    if 'name' not in df.columns:
        logger.info("'name' column not found, generating from website domains")
        df['name'] = df['website'].apply(
            lambda x: x.split('//')[-1].split('/')[0] if isinstance(x, str) and x else 'Unknown'
        )

    # Apply limit if specified
    if args.limit:
        df = df.head(args.limit)
        logger.info(f"Limited to first {args.limit} leads")

    # Create scraper
    scraper = SimpleHomepageScraper(workers=args.workers, max_pages=args.max_pages)

    # Process batch
    df_results = scraper.process_batch(df)

    # Generate output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(__file__).parent.parent / "results" / f"scraped_{timestamp}"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Split results into 4 files
    logger.info("="*70)
    logger.info("SPLITTING RESULTS INTO 4 FILES")
    logger.info("="*70)

    # 1. Success - found emails
    success_df = df_results[df_results['scrape_status'] == 'success'].copy()

    # Deduplicate by email (keep first occurrence)
    rows_before = len(success_df)
    success_df = success_df.drop_duplicates(subset=['email'], keep='first')
    rows_after = len(success_df)
    duplicates_removed = rows_before - rows_after

    success_path = output_dir / "success_emails.csv"
    success_df.to_csv(success_path, index=False, encoding='utf-8-sig')
    logger.info(f"1. Success emails: {rows_after} unique emails ({duplicates_removed} duplicates removed) -> {success_path.name}")

    # 2. Failed - static sites, no email
    failed_static_df = df_results[
        (df_results['scrape_status'] == 'failed') &
        (df_results['error_message'].str.contains('no_email_found_static', na=False))
    ].copy()
    failed_static_path = output_dir / "failed_static.csv"
    failed_static_df.to_csv(failed_static_path, index=False, encoding='utf-8-sig')
    logger.info(f"2. Failed static: {len(failed_static_df)} rows -> {failed_static_path.name}")

    # 3. Failed - dynamic sites, no email
    failed_dynamic_df = df_results[
        (df_results['scrape_status'] == 'failed') &
        (df_results['error_message'].str.contains('no_email_found_dynamic', na=False))
    ].copy()
    failed_dynamic_path = output_dir / "failed_dynamic.csv"
    failed_dynamic_df.to_csv(failed_dynamic_path, index=False, encoding='utf-8-sig')
    logger.info(f"3. Failed dynamic: {len(failed_dynamic_df)} rows -> {failed_dynamic_path.name}")

    # 4. Failed - other errors (connection errors, etc)
    failed_other_df = df_results[
        (df_results['scrape_status'] == 'failed') &
        (~df_results['error_message'].str.contains('no_email_found', na=False))
    ].copy()
    failed_other_path = output_dir / "failed_other.csv"
    failed_other_df.to_csv(failed_other_path, index=False, encoding='utf-8-sig')
    logger.info(f"4. Failed other: {len(failed_other_df)} rows -> {failed_other_path.name}")

    # 5. Save JSON analytics
    analytics = scraper.get_analytics()
    analytics_path = output_dir / "scraping_analytics.json"
    with open(analytics_path, 'w', encoding='utf-8') as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
    logger.info(f"5. Analytics: {analytics_path.name}")

    logger.info("="*70)
    logger.info("ALL FILES SAVED")
    logger.info("="*70)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Unique emails: {rows_after}")
    logger.info(f"Unique companies: {success_df['name'].nunique()}")
    logger.info(f"Duplicates removed: {duplicates_removed}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
