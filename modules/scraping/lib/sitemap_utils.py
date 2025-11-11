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

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

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
            keywords: Keywords to match (default: contact, about, quote, etc.)

        Returns:
            Filtered list of URLs likely to contain contact info
        """
        if keywords is None:
            keywords = [
                'contact', 'about', 'quote', 'reach', 'call', 'email',
                'get-in-touch', 'reach-us', 'request-quote', 'schedule',
                'appointment', 'service-request'
            ]

        filtered = []

        for url in urls:
            url_lower = url.lower()

            # Check if any keyword appears in URL path
            if any(keyword in url_lower for keyword in keywords):
                filtered.append(url)

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
        result = {
            'strategy': 'pattern',
            'pages': [],
            'sitemap_found': False
        }

        # Try sitemap first
        sitemap_content = self.fetch_sitemap(domain)

        if sitemap_content:
            all_urls = self.parse_sitemap_xml(sitemap_content)

            # Handle sitemap index (recursive fetch)
            if all_urls and 'sitemap' in all_urls[0].lower():
                # This was a sitemap index, fetch first child sitemap
                try:
                    child_response = requests.get(all_urls[0], timeout=self.timeout)
                    if child_response.status_code == 200:
                        all_urls = self.parse_sitemap_xml(child_response.text)
                except Exception:
                    pass

            if all_urls:
                contact_pages = self.filter_contact_pages(all_urls)

                result['strategy'] = 'sitemap'
                result['sitemap_found'] = True
                result['pages'] = contact_pages[:max_pages]

                return result

        # Fallback: Pattern guessing
        result['strategy'] = 'pattern'
        result['pages'] = self._get_pattern_pages(domain)

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
