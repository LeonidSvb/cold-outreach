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

    def __init__(self, workers: int = 50, max_pages: int = 5,
                 scraping_mode: str = 'deep_search', extract_emails: bool = True,
                 email_format: str = 'separate', save_content: bool = True,
                 save_sitemap: bool = False, save_social_links: bool = False,
                 save_other_links: bool = False, save_deep_content: bool = False):
        # Set attributes first (needed by debug logger)
        self.workers = workers
        self.max_pages = max_pages
        self.scraping_mode = scraping_mode
        self.extract_emails = extract_emails
        self.email_format = email_format
        self.save_content = save_content
        self.save_sitemap = save_sitemap
        self.save_social_links = save_social_links
        self.save_other_links = save_other_links
        self.save_deep_content = save_deep_content

        # Setup debug logger (uses attributes above)
        self.debug_log_path = None
        self.debug_logger = None
        self._setup_debug_logger()

        # Initialize with debug logger
        self.http_client = HTTPClient(timeout=15, retries=3)
        self.sitemap_parser = SitemapParser(timeout=15, debug_logger=self.debug_logger)

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

    def _setup_debug_logger(self):
        """Setup file logger for detailed debugging"""
        import logging

        # Create results directory if not exists
        results_dir = Path(__file__).parent / "results"
        results_dir.mkdir(parents=True, exist_ok=True)

        # Create debug log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.debug_log_path = results_dir / f"debug_logs_{timestamp}.txt"

        # Create dedicated debug logger
        self.debug_logger = logging.getLogger(f'debug_{timestamp}')
        self.debug_logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        self.debug_logger.handlers = []

        # File handler with detailed format
        file_handler = logging.FileHandler(self.debug_log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.debug_logger.addHandler(file_handler)

        # Log initial config
        self.debug_logger.info("="*80)
        self.debug_logger.info("SCRAPER DEBUG LOG STARTED")
        self.debug_logger.info("="*80)
        self.debug_logger.info(f"Config: workers={self.workers}, max_pages={self.max_pages}, mode={self.scraping_mode}")
        self.debug_logger.info(f"Extract emails: {self.extract_emails}, Format: {self.email_format}")
        self.debug_logger.info(f"Save content: {self.save_content}, Save deep content: {self.save_deep_content}")
        self.debug_logger.info("-"*80)

    def scrape_homepage(self, row_data: Dict) -> List[Dict]:
        """
        Scrape homepage and extract emails + content

        Args:
            row_data: Full row data from CSV (preserves all original columns)

        Returns:
            List of dicts - one per email found (or one with empty email if none found)
            All original columns are preserved, new columns are added
        """
        name = row_data.get('name', '')
        website = row_data.get('website', '')

        # Base result preserves ALL original columns
        base_result = row_data.copy()
        base_result.update({
            'email': '',
            'homepage_content': '',
            'site_type': 'unknown',
            'scrape_status': 'failed',
            'error_message': '',
            'email_source': '',
            'sitemap_links': '' if self.save_sitemap else None,
            'social_media_links': '' if self.save_social_links else None,
            'other_links': '' if self.save_other_links else None,
            'deep_pages_content': '' if self.save_deep_content else None
        })

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

                # Extract full text content (conditional)
                clean_text = ''
                if self.save_content:
                    clean_text = clean_html_to_text(html_content, max_length=50000)

                # Detect site type
                site_type = self._detect_site_type(html_content)

                if site_type == 'static':
                    with self._lock:
                        self.stats['static_sites'] += 1
                elif site_type == 'dynamic':
                    with self._lock:
                        self.stats['dynamic_sites'] += 1

                # Extract sitemap links (conditional)
                sitemap_links_str = ''
                if self.save_sitemap:
                    try:
                        sitemap_result = self.sitemap_parser.get_smart_pages(website, max_pages=100)
                        sitemap_links = sitemap_result.get('pages', [])
                        if sitemap_links:
                            sitemap_links_str = ' | '.join(sitemap_links[:50])  # Limit to 50 links
                    except:
                        pass

                # Extract social media links (conditional)
                social_links_str = ''
                if self.save_social_links:
                    social_links = self._extract_social_links(html_content)
                    if social_links:
                        social_links_str = ' | '.join(social_links)

                # Extract other links (conditional)
                other_links_str = ''
                if self.save_other_links:
                    all_links = self._extract_all_links(html_content)
                    # Filter out social media links
                    if self.save_social_links:
                        social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com',
                                        'youtube.com', 'tiktok.com', 'pinterest.com']
                        other_links = [link for link in all_links if not any(domain in link.lower() for domain in social_domains)]
                    else:
                        other_links = all_links
                    if other_links:
                        other_links_str = ' | '.join(other_links[:50])  # Limit to 50 links

                # Update base_result with extracted data
                base_result['homepage_content'] = clean_text
                base_result['site_type'] = site_type
                if self.save_sitemap:
                    base_result['sitemap_links'] = sitemap_links_str
                if self.save_social_links:
                    base_result['social_media_links'] = social_links_str
                if self.save_other_links:
                    base_result['other_links'] = other_links_str

                # Extract emails if enabled
                clean_emails = []
                if self.extract_emails:
                    emails = extract_emails_from_html(html_content)
                    clean_emails = [self._clean_email(e) for e in emails if self._clean_email(e)]

                # Create results based on email format
                results = []

                if self.extract_emails and clean_emails:
                    # Found emails on homepage
                    if self.email_format == 'all':
                        row = base_result.copy()
                        row['email'] = ', '.join(clean_emails)
                        row['scrape_status'] = 'success'
                        row['email_source'] = 'homepage'
                        results.append(row)
                    elif self.email_format == 'primary':
                        row = base_result.copy()
                        row['email'] = clean_emails[0]
                        row['scrape_status'] = 'success'
                        row['email_source'] = 'homepage'
                        results.append(row)
                    else:  # separate
                        for email in clean_emails:
                            row = base_result.copy()
                            row['email'] = email
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

                # No emails on homepage - try deep search if enabled
                deep_emails = []
                deep_pages_content = ''
                if self.extract_emails and not clean_emails and self.scraping_mode == 'deep_search':
                    logger.info(f"⚠ {name}: No emails on homepage, trying deep search...")
                    deep_emails, deep_pages_content = self._deep_email_search(website)

                # Update base_result with deep content if available
                if self.save_deep_content and deep_pages_content:
                    base_result['deep_pages_content'] = deep_pages_content

                if deep_emails:
                    # Handle deep search results based on format
                    if self.email_format == 'all':
                        row = base_result.copy()
                        row['email'] = ', '.join(deep_emails)
                        row['scrape_status'] = 'success'
                        row['email_source'] = 'deep_search'
                        results.append(row)
                    elif self.email_format == 'primary':
                        row = base_result.copy()
                        row['email'] = deep_emails[0]
                        row['scrape_status'] = 'success'
                        row['email_source'] = 'deep_search'
                        results.append(row)
                    else:  # separate
                        for email in deep_emails:
                            row = base_result.copy()
                            row['email'] = email
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

                # No emails found (or email extraction disabled)
                if not self.extract_emails:
                    # Success: content extracted, emails not requested
                    row = base_result.copy()
                    row['scrape_status'] = 'success'
                    row['email_source'] = 'none'
                    results.append(row)

                    with self._lock:
                        self.stats['total_processed'] += 1
                        self.stats['success'] += 1

                    logger.info(f"✓ {name}: Content extracted (no email extraction), {site_type}")
                    return results
                else:
                    # Failed: emails requested but not found
                    failure_type = 'dynamic' if site_type == 'dynamic' else 'static'
                    row = base_result.copy()
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

    def _deep_email_search(self, website: str):
        """
        Deep email search using sitemap + contact pages

        Returns:
            Tuple (List[str] emails, str pages_content)
            - emails: deduplicated list of found emails
            - pages_content: raw content from all pages (if save_deep_content=True)
        """
        all_emails = []
        pages_content_list = []

        # Debug logging
        if self.debug_logger:
            self.debug_logger.info(f"\n{'='*60}")
            self.debug_logger.info(f"DEEP SEARCH: {website}")
            self.debug_logger.info(f"{'='*60}")

        try:
            # Get smart pages (sitemap or pattern-based)
            discovery = self.sitemap_parser.get_smart_pages(website, max_pages=self.max_pages)

            # Debug log discovery results
            if self.debug_logger:
                self.debug_logger.info(f"Strategy: {discovery['strategy']}")
                self.debug_logger.info(f"Sitemap found: {discovery['sitemap_found']}")
                self.debug_logger.info(f"Pages to scrape ({len(discovery['pages'])}): {discovery['pages']}")

            # Scrape discovered pages
            for idx, page_url in enumerate(discovery['pages'], 1):
                try:
                    if self.debug_logger:
                        self.debug_logger.info(f"\n[{idx}/{len(discovery['pages'])}] Scraping: {page_url}")

                    response = self.http_client.fetch(page_url, check_content_length=False)

                    if response['status'] == 'success':
                        html_content = response['content']

                        # Extract emails
                        emails = extract_emails_from_html(html_content)
                        clean_emails = [self._clean_email(e) for e in emails if self._clean_email(e)]
                        all_emails.extend(clean_emails)

                        if self.debug_logger:
                            self.debug_logger.info(f"  Status: SUCCESS | Emails found: {len(clean_emails)} | {clean_emails if clean_emails else 'none'}")

                        # Save content if requested
                        if self.save_deep_content:
                            page_text = clean_html_to_text(html_content, max_length=10000)
                            if page_text:
                                pages_content_list.append(f"=== {page_url} ===\n{page_text}\n")
                    else:
                        if self.debug_logger:
                            self.debug_logger.info(f"  Status: FAILED | Reason: {response.get('error', 'unknown')}")

                except Exception as e:
                    if self.debug_logger:
                        self.debug_logger.info(f"  Status: ERROR | {str(e)}")
                    continue

        except Exception as e:
            if self.debug_logger:
                self.debug_logger.error(f"Deep search error: {str(e)}")
            pass

        # Deduplicate and limit to reasonable number
        unique_emails = list(set(all_emails))

        # Filter out if too many emails (likely scraped wrong content)
        if len(unique_emails) > 20:
            logger.warning(f"Too many emails found ({len(unique_emails)}), likely scraped wrong content - ignoring")
            if self.debug_logger:
                self.debug_logger.warning(f"TOO MANY EMAILS ({len(unique_emails)}) - Filtering out as likely scraped wrong content")
            unique_emails = []

        # Combine pages content
        combined_content = '\n\n'.join(pages_content_list) if pages_content_list else ''

        # Final debug summary
        if self.debug_logger:
            self.debug_logger.info(f"\nDEEP SEARCH RESULT:")
            self.debug_logger.info(f"  Total emails found: {len(all_emails)} (before dedup)")
            self.debug_logger.info(f"  Unique emails: {len(unique_emails)}")
            self.debug_logger.info(f"  Final emails: {unique_emails if unique_emails else 'none'}")
            self.debug_logger.info(f"{'='*60}\n")

        return unique_emails, combined_content

    def _fill_links_fields(self, row: Dict, sitemap_links_str: str, social_links_str: str, other_links_str: str) -> Dict:
        """Fill links fields in row dict"""
        if self.save_sitemap:
            row['sitemap_links'] = sitemap_links_str
        if self.save_social_links:
            row['social_media_links'] = social_links_str
        if self.save_other_links:
            row['other_links'] = other_links_str
        return row

    def _extract_social_links(self, html_content: str) -> List[str]:
        """Extract social media links from HTML"""
        import re
        social_patterns = [
            r'https?://(?:www\.)?facebook\.com/[^\s"\'>]+',
            r'https?://(?:www\.)?twitter\.com/[^\s"\'>]+',
            r'https?://(?:www\.)?linkedin\.com/[^\s"\'>]+',
            r'https?://(?:www\.)?instagram\.com/[^\s"\'>]+',
            r'https?://(?:www\.)?youtube\.com/[^\s"\'>]+',
            r'https?://(?:www\.)?tiktok\.com/[^\s"\'>]+',
            r'https?://(?:www\.)?pinterest\.com/[^\s"\'>]+',
        ]

        social_links = []
        for pattern in social_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            social_links.extend(matches)

        return list(set(social_links))  # Deduplicate

    def _extract_all_links(self, html_content: str) -> List[str]:
        """Extract all links from HTML"""
        import re
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if href and not href.startswith(('#', 'javascript:', 'mailto:')):
                    links.append(href)
            return list(set(links))  # Deduplicate
        except:
            return []

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
                    row.to_dict()
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


def validate_url(url: str) -> bool:
    """Check if string looks like a valid URL"""
    if not url or pd.isna(url):
        return False
    url_str = str(url).strip().lower()
    if not url_str:
        return False
    # Check for valid URL patterns
    has_domain = ('.' in url_str and len(url_str) > 4)
    has_protocol = url_str.startswith(('http://', 'https://'))
    looks_like_url = any(x in url_str for x in ['www.', '.com', '.org', '.net', '.io', '.co'])
    return has_domain and (has_protocol or looks_like_url)


def main():
    parser = argparse.ArgumentParser(description='Simple Homepage Scraper - Emails + Content')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', help='Output directory (optional, auto-generated if not provided)')
    parser.add_argument('--workers', type=int, default=50, help='Number of parallel workers (default: 50)')
    parser.add_argument('--max-pages', type=int, default=5, help='Max pages to search per site (default: 5)')
    parser.add_argument('--scraping-mode', choices=['homepage_only', 'deep_search'], default='deep_search',
                        help='Scraping mode: homepage_only or deep_search (default: deep_search)')
    parser.add_argument('--no-emails', action='store_true', help='Disable email extraction (only get content)')
    parser.add_argument('--email-format', choices=['all', 'primary', 'separate'], default='separate',
                        help='Email output format: all (comma-separated), primary (first only), separate (one row per email)')
    parser.add_argument('--website-column', default='website', help='Column name containing website URLs (default: website)')
    parser.add_argument('--name-column', default='name', help='Column name containing company names (default: name)')
    parser.add_argument('--limit', type=int, help='Limit number of leads to process (for testing)')
    parser.add_argument('--no-content', action='store_true', help='Do not save homepage content (save space)')
    parser.add_argument('--save-sitemap', action='store_true', help='Save sitemap links')
    parser.add_argument('--save-social', action='store_true', help='Save social media links')
    parser.add_argument('--save-links', action='store_true', help='Save other links from homepage')
    parser.add_argument('--save-deep-content', action='store_true', help='Save raw content from all deep search pages')

    args = parser.parse_args()

    # Read input CSV
    logger.info(f"Reading input file: {args.input}")
    df = pd.read_csv(args.input, encoding='utf-8-sig')

    total_loaded = len(df)
    logger.info(f"Loaded {total_loaded} rows from CSV")

    # Validate website column exists
    if args.website_column not in df.columns:
        logger.error(f"Missing required column: '{args.website_column}'")
        sys.exit(1)

    # Validate URLs and filter out invalid ones
    logger.info(f"Validating URLs in column '{args.website_column}'...")
    df['_url_valid'] = df[args.website_column].apply(validate_url)
    valid_count = df['_url_valid'].sum()
    invalid_count = total_loaded - valid_count

    logger.info(f"URL Validation Results:")
    logger.info(f"  Valid URLs: {valid_count}")
    logger.info(f"  Invalid URLs: {invalid_count}")

    # Filter to only valid URLs
    df_valid = df[df['_url_valid']].copy()
    df_valid = df_valid.drop(columns=['_url_valid'])

    if len(df_valid) == 0:
        logger.error("No valid URLs found in CSV!")
        sys.exit(1)

    # Rename columns for processing
    rename_map = {args.website_column: 'website'}
    if args.name_column in df_valid.columns:
        rename_map[args.name_column] = 'name'
    else:
        logger.info(f"'{args.name_column}' column not found, will use website URLs as identifiers")
        df_valid['name'] = df_valid[args.website_column]  # Use website as identifier

    df_valid = df_valid.rename(columns=rename_map)

    # Apply limit if specified
    if args.limit:
        df_valid = df_valid.head(args.limit)
        logger.info(f"Limited to first {args.limit} leads")

    logger.info(f"Processing {len(df_valid)} valid websites")

    # Create scraper
    scraper = SimpleHomepageScraper(
        workers=args.workers,
        max_pages=args.max_pages,
        scraping_mode=args.scraping_mode,
        extract_emails=not args.no_emails,
        email_format=args.email_format,
        save_content=not args.no_content,
        save_sitemap=args.save_sitemap,
        save_social_links=args.save_social,
        save_other_links=args.save_links,
        save_deep_content=args.save_deep_content
    )

    # Process batch
    df_results = scraper.process_batch(df_valid)

    # Generate output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.output:
        output_dir = Path(args.output)
    else:
        # Save in homepage_email_scraper/results/ (not parent.parent)
        output_dir = Path(__file__).parent / "results" / f"scraped_{timestamp}"

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    # Split results into 3 universal files
    logger.info("="*70)
    logger.info("SAVING RESULTS (UNIFIED FORMAT)")
    logger.info("="*70)

    # 1. SUCCESS - achieved goal (email OR content)
    success_df = df_results[df_results['scrape_status'] == 'success'].copy()

    # Deduplicate by email if emails were extracted
    if not args.no_emails and 'email' in success_df.columns:
        rows_before = len(success_df)
        success_df = success_df.drop_duplicates(subset=['email'], keep='first')
        rows_after = len(success_df)
        duplicates_removed = rows_before - rows_after
    else:
        rows_after = len(success_df)
        duplicates_removed = 0

    # Save SUCCESS in multiple formats
    success_path_csv = output_dir / "success.csv"
    success_path_json = output_dir / "success.json"
    success_path_excel = output_dir / "success.xlsx"

    success_df.to_csv(success_path_csv, index=False, encoding='utf-8-sig')
    success_df.to_json(success_path_json, orient='records', force_ascii=False, indent=2)
    try:
        success_df.to_excel(success_path_excel, index=False, engine='openpyxl')
    except ImportError:
        logger.warning("openpyxl not installed, skipping Excel export")

    logger.info(f"1. SUCCESS: {rows_after} rows ({duplicates_removed} duplicates removed)")
    logger.info(f"   - {success_path_csv.name}")
    logger.info(f"   - {success_path_json.name}")
    if success_path_excel.exists():
        logger.info(f"   - {success_path_excel.name}")

    # 2. FAILED - did not achieve goal
    failed_df = df_results[df_results['scrape_status'] == 'failed'].copy()

    # Add failure_reason column for clarity
    def categorize_failure(row):
        error_msg = str(row.get('error_message', ''))
        if 'no_email_found_static' in error_msg:
            return 'no_email_found_static'
        elif 'no_email_found_dynamic' in error_msg:
            return 'no_email_found_dynamic'
        elif 'timeout' in error_msg.lower():
            return 'connection_timeout'
        elif '404' in error_msg or 'not found' in error_msg.lower():
            return 'page_not_found'
        elif error_msg:
            return error_msg
        else:
            return 'unknown_error'

    failed_df['failure_reason'] = failed_df.apply(categorize_failure, axis=1)

    # Save FAILED in multiple formats
    failed_path_csv = output_dir / "failed.csv"
    failed_path_json = output_dir / "failed.json"
    failed_path_excel = output_dir / "failed.xlsx"

    failed_df.to_csv(failed_path_csv, index=False, encoding='utf-8-sig')
    failed_df.to_json(failed_path_json, orient='records', force_ascii=False, indent=2)
    try:
        failed_df.to_excel(failed_path_excel, index=False, engine='openpyxl')
    except ImportError:
        pass

    logger.info(f"2. FAILED: {len(failed_df)} rows")
    logger.info(f"   - {failed_path_csv.name}")
    logger.info(f"   - {failed_path_json.name}")
    if failed_path_excel.exists():
        logger.info(f"   - {failed_path_excel.name}")

    # Breakdown by failure reason
    failure_counts = failed_df['failure_reason'].value_counts()
    for reason, count in failure_counts.items():
        logger.info(f"     - {reason}: {count}")

    # 3. ALL COMBINED - everything together
    combined_df = df_results.copy()
    if not args.no_emails and 'email' in combined_df.columns:
        combined_df = combined_df.drop_duplicates(subset=['email', 'scrape_status'], keep='first')

    # Add failure_reason to combined as well
    combined_df['failure_reason'] = combined_df.apply(
        lambda row: categorize_failure(row) if row['scrape_status'] == 'failed' else '',
        axis=1
    )

    # Save COMBINED in multiple formats
    combined_path_csv = output_dir / "all_combined.csv"
    combined_path_json = output_dir / "all_combined.json"
    combined_path_excel = output_dir / "all_combined.xlsx"

    combined_df.to_csv(combined_path_csv, index=False, encoding='utf-8-sig')
    combined_df.to_json(combined_path_json, orient='records', force_ascii=False, indent=2)
    try:
        combined_df.to_excel(combined_path_excel, index=False, engine='openpyxl')
    except ImportError:
        pass

    logger.info(f"3. ALL COMBINED: {len(combined_df)} rows")
    logger.info(f"   - {combined_path_csv.name}")
    logger.info(f"   - {combined_path_json.name}")
    if combined_path_excel.exists():
        logger.info(f"   - {combined_path_excel.name}")

    # 4. Save JSON analytics
    analytics = scraper.get_analytics()
    analytics_path = output_dir / "scraping_analytics.json"
    with open(analytics_path, 'w', encoding='utf-8') as f:
        json.dump(analytics, f, indent=2, ensure_ascii=False)
    logger.info(f"\n4. Analytics: {analytics_path.name}")

    logger.info("\n" + "="*70)
    logger.info("ALL FILES SAVED")
    logger.info("="*70)
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"\nSummary:")
    logger.info(f"  Success: {rows_after} rows")
    logger.info(f"  Failed: {len(failed_df)} rows")
    logger.info(f"  Combined: {len(combined_df)} rows")
    if not args.no_emails:
        logger.info(f"  Unique emails: {rows_after}")
        logger.info(f"  Duplicates removed: {duplicates_removed}")
    if 'name' in success_df.columns:
        logger.info(f"  Unique companies: {success_df['name'].nunique()}")
    logger.info(f"\nFormats: CSV + JSON + Excel (if openpyxl installed)")
    logger.info("="*70)


if __name__ == "__main__":
    main()
