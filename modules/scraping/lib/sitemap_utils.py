#!/usr/bin/env python3
"""
Sitemap Utilities for Smart Multi-Page Scraping

Extracts URLs from sitemap.xml and robots.txt for intelligent page discovery.
Provides sitemap-first strategy with pattern guessing fallback.
"""

import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from typing import List, Optional, Dict
import re


class SitemapParser:
    """Parse sitemaps and extract relevant URLs for email scraping"""

    def __init__(self, timeout: int = 10, debug_logger=None):
        self.timeout = timeout
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        self.debug_logger = debug_logger

    def get_sitemap_from_robots(self, domain: str) -> Optional[str]:
        """
        Extract sitemap URL from robots.txt

        Args:
            domain: Base domain (e.g., https://example.com)

        Returns:
            Sitemap URL or None
        """
        robots_url = urljoin(domain, '/robots.txt')

        try:
            response = requests.get(
                robots_url,
                headers={'User-Agent': self.user_agent},
                timeout=self.timeout
            )

            if response.status_code == 200:
                # Find "Sitemap:" directive
                for line in response.text.split('\n'):
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        return sitemap_url

        except Exception:
            pass

        return None

    def fetch_sitemap(self, domain: str) -> Optional[str]:
        """
        Fetch sitemap.xml from common locations

        Tries multiple locations:
        1. robots.txt (most reliable)
        2. /sitemap.xml
        3. /sitemap_index.xml
        4. /sitemap-misc.xml

        Returns:
            Sitemap XML content or None
        """
        # Try robots.txt first
        sitemap_url = self.get_sitemap_from_robots(domain)
        if sitemap_url:
            try:
                response = requests.get(
                    sitemap_url,
                    headers={'User-Agent': self.user_agent},
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return response.text
            except Exception:
                pass

        # Fallback: Try common sitemap locations
        common_paths = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemap-misc.xml',
            '/sitemap-pages.xml'
        ]

        for path in common_paths:
            try:
                sitemap_url = urljoin(domain, path)
                response = requests.get(
                    sitemap_url,
                    headers={'User-Agent': self.user_agent},
                    timeout=self.timeout
                )

                if response.status_code == 200 and 'xml' in response.headers.get('Content-Type', ''):
                    return response.text

            except Exception:
                continue

        return None

    def parse_sitemap_xml(self, xml_content: str) -> List[str]:
        """
        Parse sitemap XML and extract all URLs

        Handles both regular sitemaps and sitemap indexes.

        Returns:
            List of URLs
        """
        urls = []

        try:
            root = ET.fromstring(xml_content)

            # Handle XML namespaces
            namespaces = {
                'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
                'xhtml': 'http://www.w3.org/1999/xhtml'
            }

            # Check if this is a sitemap index (contains <sitemap> elements)
            sitemap_elements = root.findall('.//sm:sitemap/sm:loc', namespaces)
            if sitemap_elements:
                # This is a sitemap index - return child sitemap URLs
                return [elem.text for elem in sitemap_elements if elem.text]

            # Regular sitemap - extract <url><loc> elements
            url_elements = root.findall('.//sm:url/sm:loc', namespaces)
            urls = [elem.text for elem in url_elements if elem.text]

            # Fallback: try without namespace
            if not urls:
                url_elements = root.findall('.//url/loc')
                urls = [elem.text for elem in url_elements if elem.text]

        except ET.ParseError:
            pass

        return urls

    def filter_contact_pages(self, urls: List[str], keywords: List[str] = None) -> List[str]:
        """
        Filter URLs to find contact-related pages

        Args:
            urls: List of all URLs from sitemap
            keywords: Keywords to match (default: comprehensive industry-standard list)

        Returns:
            Filtered list of URLs likely to contain contact info
        """
        if keywords is None:
            # Comprehensive industry-standard keywords dictionary
            keywords = [
                # Contact pages (primary)
                'contact', 'contactus', 'contact-us', 'kontakt', 'contacto', 'contatto',
                'get-in-touch', 'reach-us', 'reach-out', 'connect',

                # Information & policies (often contain contact)
                'contact-information', 'contact-info', 'info', 'information',
                'policies', 'policy', 'privacy', 'terms', 'legal',

                # About & team pages
                'about', 'aboutus', 'about-us', 'our-story', 'who-we-are',
                'team', 'staff', 'leadership', 'management', 'people',

                # Support & help
                'support', 'help', 'customer-service', 'customer-support',
                'service', 'services', 'faq', 'helpdesk',

                # Sales & quotes
                'quote', 'quotes', 'request-quote', 'get-quote', 'pricing',
                'request', 'inquiry', 'enquiry', 'estimate',

                # Location & directions
                'location', 'locations', 'find-us', 'directions', 'map',
                'visit', 'address', 'office', 'offices', 'branch',

                # Appointment & scheduling
                'schedule', 'appointment', 'booking', 'book', 'reservation',
                'consultation', 'meeting',

                # Communication channels
                'call', 'phone', 'email', 'mail', 'message', 'feedback',
                'inquiry-form', 'contact-form', 'write-us',

                # Business-specific
                'corporate', 'business', 'enterprise', 'partner', 'vendor',
                'wholesale', 'b2b', 'press', 'media', 'careers', 'jobs'
            ]

        filtered = []
        rejected = []

        for url in urls:
            url_lower = url.lower()

            # Check if any keyword appears ANYWHERE in URL path (not just at start)
            matched_keywords = [kw for kw in keywords if kw in url_lower]
            if matched_keywords:
                filtered.append(url)
                if self.debug_logger:
                    self.debug_logger.debug(f"  ✓ MATCH: {url} (keywords: {', '.join(matched_keywords)})")
            else:
                rejected.append(url)
                if self.debug_logger:
                    self.debug_logger.debug(f"  ✗ SKIP: {url}")

        # Summary log
        if self.debug_logger:
            self.debug_logger.info(f"Filtering results: {len(filtered)} matched, {len(rejected)} rejected")

        return filtered

    def get_smart_pages(self, domain: str, max_pages: int = 10) -> Dict:
        """
        Intelligent page discovery using sitemap-first strategy

        Args:
            domain: Base domain URL
            max_pages: Maximum pages to return (cost optimization)

        Returns:
            {
                'strategy': 'sitemap' | 'pattern',
                'pages': [list of URLs to scrape],
                'sitemap_found': True/False
            }
        """
        if self.debug_logger:
            self.debug_logger.info(f"\n--- PAGE DISCOVERY START ---")
            self.debug_logger.info(f"Attempting sitemap fetch for: {domain}")

        result = {
            'strategy': 'pattern',
            'pages': [],
            'sitemap_found': False
        }

        # Try sitemap first
        sitemap_content = self.fetch_sitemap(domain)

        if sitemap_content:
            if self.debug_logger:
                self.debug_logger.info("✓ Sitemap found!")

            all_urls = self.parse_sitemap_xml(sitemap_content)
            if self.debug_logger:
                self.debug_logger.info(f"Parsed {len(all_urls)} URLs from sitemap")

            # Handle sitemap index (recursive fetch)
            if all_urls and 'sitemap' in all_urls[0].lower():
                if self.debug_logger:
                    self.debug_logger.info(f"Detected sitemap index, fetching child sitemap: {all_urls[0]}")
                # This was a sitemap index, fetch first child sitemap
                try:
                    child_response = requests.get(all_urls[0], timeout=self.timeout)
                    if child_response.status_code == 200:
                        all_urls = self.parse_sitemap_xml(child_response.text)
                        if self.debug_logger:
                            self.debug_logger.info(f"Child sitemap parsed: {len(all_urls)} URLs")
                except Exception as e:
                    if self.debug_logger:
                        self.debug_logger.warning(f"Failed to fetch child sitemap: {str(e)}")
                    pass

            if all_urls:
                if self.debug_logger:
                    self.debug_logger.info(f"\nFiltering {len(all_urls)} URLs by keywords...")

                contact_pages = self.filter_contact_pages(all_urls)

                result['strategy'] = 'sitemap'
                result['sitemap_found'] = True
                result['pages'] = contact_pages[:max_pages]

                if self.debug_logger:
                    self.debug_logger.info(f"\nFinal selection (limited to {max_pages}): {len(result['pages'])} pages")
                    for idx, page in enumerate(result['pages'], 1):
                        self.debug_logger.info(f"  {idx}. {page}")

                return result
        else:
            if self.debug_logger:
                self.debug_logger.info("✗ No sitemap found")

        # Fallback: Pattern guessing
        if self.debug_logger:
            self.debug_logger.info("\nFalling back to pattern-based guessing...")

        result['strategy'] = 'pattern'
        result['pages'] = self._get_pattern_pages(domain)

        if self.debug_logger:
            self.debug_logger.info(f"Generated {len(result['pages'])} pattern-based URLs:")
            for idx, page in enumerate(result['pages'], 1):
                self.debug_logger.info(f"  {idx}. {page}")
            self.debug_logger.info("--- PAGE DISCOVERY END ---\n")

        return result

    def _get_pattern_pages(self, domain: str) -> List[str]:
        """
        Generate URLs using common patterns

        Returns:
            List of URLs to try
        """
        patterns = [
            '/contact',
            '/contact-us',
            '/contactus',
            '/get-in-touch',
            '/about',
            '/about-us',
            '/our-story',
            '/get-quote',
            '/request-quote',
            '/schedule',
            '/reach-us'
        ]

        return [urljoin(domain, path) for path in patterns]


def get_sitemap_pages(domain: str, max_pages: int = 10) -> Dict:
    """
    Convenience function for sitemap-based page discovery

    Args:
        domain: Base domain URL
        max_pages: Max pages to return

    Returns:
        Result dict with strategy and pages
    """
    parser = SitemapParser()
    return parser.get_smart_pages(domain, max_pages)
