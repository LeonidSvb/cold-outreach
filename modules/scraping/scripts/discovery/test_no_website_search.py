#!/usr/bin/env python3
"""
=== TEST: NO WEBSITE SEARCH ===
Version: 1.0.0 | Created: 2025-11-19

PURPOSE:
Test search strategy for companies without website
Uses DuckDuckGo search to find company website/email

STRATEGY:
1. Search: "{company_name} {city} Australia contact"
2. Extract potential websites from search results
3. Try scraping emails from found websites
4. Fallback: search for email directly in results

TEST:
50 companies without website from Australia list

OUTPUT:
- test_no_website_results.csv
"""

import sys
import time
import pandas as pd
import re
import requests
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from modules.logging.shared.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


class NoWebsiteSearcher:
    """
    Search for company websites and emails when no website provided
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_company(self, company_name: str, city: str) -> Dict:
        """
        Search for company website using DuckDuckGo

        Args:
            company_name: Company name
            city: City name

        Returns:
            Dict with results: {
                'found_website': str or None,
                'found_email': str or None,
                'search_status': 'success' | 'failed',
                'error_message': str
            }
        """
        result = {
            'found_website': None,
            'found_email': None,
            'search_status': 'failed',
            'error_message': ''
        }

        try:
            # Build search query
            query = f"{company_name} {city} Australia contact"
            encoded_query = quote_plus(query)

            # DuckDuckGo HTML search (no API key needed)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                html = response.text

                # Extract URLs from search results
                urls = self._extract_urls(html)

                # Look for company website
                potential_website = self._find_company_website(urls, company_name)

                if potential_website:
                    result['found_website'] = potential_website
                    result['search_status'] = 'success'
                    logger.info(f"✓ {company_name}: Found website {potential_website}")
                else:
                    result['error_message'] = 'No website found in search results'
                    logger.warning(f"✗ {company_name}: No website found")

                # Also try to find email directly in HTML
                emails = self._extract_emails(html)
                if emails:
                    result['found_email'] = emails[0]
                    logger.info(f"✓ {company_name}: Found email {emails[0]}")

            else:
                result['error_message'] = f"HTTP {response.status_code}"
                logger.warning(f"✗ {company_name}: HTTP {response.status_code}")

        except Exception as e:
            result['error_message'] = str(e)
            logger.error(f"✗ {company_name}: {e}")

        return result

    def _extract_urls(self, html: str) -> list:
        """Extract URLs from HTML"""
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_pattern, html)

        # Clean URLs
        cleaned_urls = []
        for url in urls:
            # Remove trailing punctuation
            url = url.rstrip('.,;)')

            # Skip common non-company domains
            skip_domains = [
                'duckduckgo.com', 'google.com', 'facebook.com',
                'youtube.com', 'wikipedia.org', 'twitter.com',
                'instagram.com', 'linkedin.com', 'pinterest.com'
            ]

            if not any(skip in url.lower() for skip in skip_domains):
                cleaned_urls.append(url)

        return cleaned_urls[:10]  # Limit to first 10

    def _find_company_website(self, urls: list, company_name: str) -> Optional[str]:
        """Find most likely company website from list"""
        if not urls:
            return None

        # Normalize company name for matching
        normalized_name = re.sub(r'[^a-z0-9]+', '', company_name.lower())

        for url in urls:
            domain = url.split('/')[2] if '//' in url else url.split('/')[0]
            domain_normalized = re.sub(r'[^a-z0-9]+', '', domain.lower())

            # Check if company name appears in domain
            if normalized_name[:10] in domain_normalized or domain_normalized in normalized_name:
                return url

        # If no match, return first URL
        return urls[0] if urls else None

    def _extract_emails(self, text: str) -> list:
        """Extract emails from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)

        # Filter fake emails
        fake_patterns = [
            'example.com', 'domain.com', 'test.com',
            'noreply@', 'no-reply@'
        ]

        clean_emails = []
        for email in emails:
            email = email.lower()
            if not any(pattern in email for pattern in fake_patterns):
                clean_emails.append(email)

        return list(set(clean_emails))[:3]  # Limit to 3 unique


def main():
    """Test on 50 companies without website"""

    # Load data
    input_file = r"C:\Users\79818\Downloads\All Australia Accommodation - No Email Full List for Upwork.csv"
    logger.info(f"Loading data from: {input_file}")

    df = pd.read_csv(input_file, encoding='utf-8-sig')

    # Filter: no website
    df_no_website = df[df['Website'].isna() | (df['Website'] == '')].copy()

    logger.info(f"Total companies: {len(df)}")
    logger.info(f"Companies without website: {len(df_no_website)}")

    # Take first 50 for testing
    df_test = df_no_website.head(50).copy()

    logger.info("="*70)
    logger.info("TESTING SEARCH FOR 50 COMPANIES WITHOUT WEBSITE")
    logger.info("="*70)

    # Initialize searcher
    searcher = NoWebsiteSearcher()

    results = []

    for idx, row in df_test.iterrows():
        company_name = row['Business Name']
        city = row['Company City']

        logger.info(f"[{idx+1}/50] Searching: {company_name}, {city}")

        # Search
        search_result = searcher.search_company(company_name, city)

        results.append({
            'original_name': company_name,
            'city': city,
            'phone': row.get('Phone Number', ''),
            'found_website': search_result['found_website'],
            'found_email': search_result['found_email'],
            'search_status': search_result['search_status'],
            'error_message': search_result['error_message']
        })

        # Rate limiting (be nice to DuckDuckGo)
        time.sleep(2)

    # Save results
    df_results = pd.DataFrame(results)

    output_dir = Path(__file__).parent.parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "test_no_website_results.csv"
    df_results.to_csv(output_file, index=False, encoding='utf-8-sig')

    # Stats
    websites_found = df_results['found_website'].notna().sum()
    emails_found = df_results['found_email'].notna().sum()

    logger.info("="*70)
    logger.info("TEST COMPLETE")
    logger.info("="*70)
    logger.info(f"Total tested: 50")
    logger.info(f"Websites found: {websites_found} ({websites_found/50*100:.1f}%)")
    logger.info(f"Emails found: {emails_found} ({emails_found/50*100:.1f}%)")
    logger.info(f"Output: {output_file}")
    logger.info("="*70)


if __name__ == "__main__":
    main()
