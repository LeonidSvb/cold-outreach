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
        Filter URLs to find contact-related pages with priority scoring

        Args:
            urls: List of all URLs from sitemap
            keywords: Keywords to match (default: comprehensive industry-standard list)

        Returns:
            Filtered list of URLs sorted by relevance (highest priority first)
        """
        # Priority keywords (higher score = more relevant)
        priority_keywords = {
            # Priority 1 (100 points): Exact contact pages
            'contact': 100, 'contactus': 100, 'contact-us': 100, 'kontakt': 100,
            'contacto': 100, 'contatto': 100, 'get-in-touch': 100, 'reach-us': 100,
            'contact-information': 100, 'contact-info': 100,

            # Priority 2 (80 points): About & info pages
            'about': 80, 'aboutus': 80, 'about-us': 80, 'our-story': 80,
            'policies': 80, 'policy': 80, 'info': 80, 'information': 80,

            # Priority 3 (60 points): Team & support
            'team': 60, 'staff': 60, 'leadership': 60, 'management': 60,
            'support': 60, 'help': 60, 'customer-service': 60, 'customer-support': 60,

            # Priority 4 (40 points): Business pages
            'quote': 40, 'quotes': 40, 'request-quote': 40, 'get-quote': 40,
            'location': 40, 'locations': 40, 'find-us': 40, 'directions': 40,
            'schedule': 40, 'appointment': 40, 'inquiry': 40, 'enquiry': 40,

            # Priority 5 (20 points): Generic business terms
            'office': 20, 'offices': 20, 'branch': 20, 'call': 20, 'phone': 20,
            'email': 20, 'mail': 20, 'message': 20, 'feedback': 20,
            'corporate': 20, 'business': 20, 'partner': 20, 'press': 20, 'media': 20,

            # Low priority (10 points): Weak signals
            'services': 10, 'faq': 10, 'helpdesk': 10, 'book': 10, 'reservation': 10
        }

        scored_urls = []
        rejected = []

        for url in urls:
            url_lower = url.lower()

            # Skip product pages (very low priority for contact info)
            if '/products/' in url_lower or '/collections/' in url_lower:
                if self.debug_logger:
                    self.debug_logger.debug(f"  ✗ SKIP: {url} (product/collection page)")
                rejected.append(url)
                continue

            # Calculate priority score
            score = 0
            matched_keywords = []

            for keyword, priority in priority_keywords.items():
                if keyword in url_lower:
                    score += priority
                    matched_keywords.append(keyword)

            # Bonus: /pages/ or /policies/ paths are more likely to have contact info
            # (only if at least one keyword matched)
            if score > 0 and ('/pages/' in url_lower or '/policies/' in url_lower):
                score += 50

            if score > 0:
                scored_urls.append((url, score, matched_keywords))
                if self.debug_logger:
                    self.debug_logger.debug(f"  ✓ MATCH: {url} (score: {score}, keywords: {', '.join(matched_keywords)})")
            else:
                rejected.append(url)
                if self.debug_logger:
                    self.debug_logger.debug(f"  ✗ SKIP: {url}")

        # Sort by score (highest first)
        scored_urls.sort(key=lambda x: x[1], reverse=True)
        filtered = [url for url, score, keywords in scored_urls]

        # Summary log
        if self.debug_logger:
            self.debug_logger.info(f"Filtering results: {len(filtered)} matched (sorted by relevance), {len(rejected)} rejected")
            if filtered and len(filtered) <= 10:
                self.debug_logger.info("Top matches:")
                for idx, (url, score, kw) in enumerate(scored_urls[:10], 1):
                    self.debug_logger.info(f"  {idx}. [Score: {score}] {url}")

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

            # Check if this is a sitemap index (contains child sitemaps)
            # Handle URLs with query parameters (e.g., sitemap_products_1.xml?from=123&to=456)
            child_sitemaps = [url for url in all_urls if 'sitemap' in url.lower() and '.xml' in url]

            if child_sitemaps:
                # This is a sitemap index - fetch ALL child sitemaps
                if self.debug_logger:
                    self.debug_logger.info(f"Detected sitemap index with {len(child_sitemaps)} child sitemaps")

                all_urls = []
                for idx, child_sitemap_url in enumerate(child_sitemaps[:10], 1):  # Limit to 10 child sitemaps
                    try:
                        if self.debug_logger:
                            self.debug_logger.info(f"  [{idx}/{min(len(child_sitemaps), 10)}] Fetching: {child_sitemap_url}")

                        child_response = requests.get(child_sitemap_url, timeout=self.timeout)
                        if child_response.status_code == 200:
                            child_urls = self.parse_sitemap_xml(child_response.text)
                            all_urls.extend(child_urls)

                            if self.debug_logger:
                                self.debug_logger.info(f"      Parsed {len(child_urls)} URLs")
                    except Exception as e:
                        if self.debug_logger:
                            self.debug_logger.warning(f"      Failed to fetch: {str(e)}")
                        continue

                if self.debug_logger:
                    self.debug_logger.info(f"\nTotal URLs from all child sitemaps: {len(all_urls)}")

            if all_urls:
                if self.debug_logger:
                    self.debug_logger.info(f"\nFiltering {len(all_urls)} URLs by keywords...")

                contact_pages = self.filter_contact_pages(all_urls)

                # If not enough contact pages found, add pattern-based URLs as fallback
                if len(contact_pages) < max_pages:
                    if self.debug_logger:
                        self.debug_logger.info(f"\nOnly {len(contact_pages)} contact pages found in sitemap")
                        self.debug_logger.info("Adding pattern-based URLs as supplement...")

                    pattern_urls = self._get_pattern_pages(domain)
                    # Add pattern URLs that aren't already in contact_pages
                    for url in pattern_urls:
                        if url not in contact_pages and len(contact_pages) < max_pages:
                            contact_pages.append(url)
                            if self.debug_logger:
                                self.debug_logger.info(f"  + Added pattern URL: {url}")

                result['strategy'] = 'sitemap+pattern' if len(contact_pages) > len(self.filter_contact_pages(all_urls)) else 'sitemap'
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
            # Primary contact pages
            '/contact',
            '/contact-us',
            '/contactus',
            '/get-in-touch',
            '/reach-us',

            # Policies & info (often have contact info)
            '/policies/contact-information',
            '/pages/contact',
            '/pages/contact-us',
            '/pages/about',

            # About pages
            '/about',
            '/about-us',
            '/our-story',
            '/team',

            # Sales & support
            '/get-quote',
            '/request-quote',
            '/schedule',
            '/support',
            '/customer-service',

            # Location
            '/locations',
            '/find-us',
            '/visit-us'
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
