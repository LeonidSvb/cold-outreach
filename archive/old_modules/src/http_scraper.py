#!/usr/bin/env python3
"""
=== HTTP SCRAPER ===
Version: 1.0.0 | Created: 2025-09-21

PURPOSE:
Ultra-fast HTTP scraping with parallel processing for simple websites.
Extracts only clean text content and relevant links for optimal performance.

FEATURES:
- 50+ concurrent HTTP workers
- Text-only extraction (no HTML processing)
- Smart link discovery and prioritization
- 100+ domains/minute processing speed
- Minimal memory footprint

USAGE:
from http_scraper import HTTPScraper
scraper = HTTPScraper()
results = await scraper.scrape_domains_parallel(["example.com"])

IMPROVEMENTS:
v1.0.0 - Initial implementation based on legacy text_only_scraper
"""

import asyncio
import aiohttp
import time
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser
from typing import Dict, List, Any, Optional, Set
import ssl
import warnings
warnings.filterwarnings("ignore")

class TextOnlyParser(HTMLParser):
    """Fast HTML parser for extracting only text and links"""

    def __init__(self, base_domain: str = ""):
        super().__init__()
        self.text_content = []
        self.links = []
        self.current_tag = None
        self.base_domain = base_domain
        self.ignore_tags = {'script', 'style', 'nav', 'footer', 'header', 'aside', 'meta', 'link'}

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag == 'a':
            for attr in attrs:
                if attr[0] == 'href' and attr[1]:
                    href = attr[1].strip()
                    if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                        self.links.append(href)

    def handle_endtag(self, tag):
        self.current_tag = None

    def handle_data(self, data):
        # Extract only useful text
        if self.current_tag not in self.ignore_tags:
            text = data.strip()
            if len(text) > 10:  # Ignore short strings
                self.text_content.append(text)

    def get_clean_data(self, max_text_length: int = 3000) -> Dict[str, Any]:
        """Get cleaned text and links"""

        # Combine and clean text
        full_text = ' '.join(self.text_content)

        # Remove extra whitespace and clean special characters
        clean_text = re.sub(r'\s+', ' ', full_text)
        clean_text = re.sub(r'[^\w\s\.\,\!\?\-\(\)\'\":;]', ' ', clean_text)

        # Remove duplicate links and normalize
        unique_links = list(set(self.links))

        return {
            "text": clean_text[:max_text_length],
            "text_length": len(clean_text),
            "links": unique_links[:50],  # Maximum 50 links
            "link_count": len(unique_links)
        }

class HTTPScraper:
    """Ultra-fast HTTP scraper with parallel processing"""

    def __init__(self):
        self.config = {
            "max_workers": 50,
            "timeout_seconds": 10,
            "max_pages_per_domain": 15,
            "max_text_per_page": 3000,
            "retry_attempts": 2,
            "delay_between_requests": 0.1,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        self.priority_paths = [
            "/about", "/about-us", "/team", "/leadership",
            "/contact", "/contact-us", "/careers", "/jobs",
            "/services", "/products", "/solutions", "/pricing"
        ]

        self.session_stats = {
            "domains_processed": 0,
            "pages_scraped": 0,
            "total_text_extracted": 0,
            "errors": 0,
            "start_time": time.time()
        }

    async def scrape_domains_parallel(self, domains: List[str], max_workers: int = None) -> Dict[str, Any]:
        """
        Scrape multiple domains in parallel

        Args:
            domains: List of domain URLs to scrape
            max_workers: Maximum concurrent workers (overrides config)

        Returns:
            Dict mapping domains to scraping results
        """

        max_workers = max_workers or self.config["max_workers"]
        print(f"Starting parallel HTTP scraping: {len(domains)} domains, {max_workers} workers")

        self.session_stats["start_time"] = time.time()

        # Create SSL context that doesn't verify certificates (for speed)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Configure connector with optimal settings
        connector = aiohttp.TCPConnector(
            limit=max_workers * 2,
            limit_per_host=20,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=ssl_context
        )

        timeout = aiohttp.ClientTimeout(total=self.config["timeout_seconds"])

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(max_workers)

            # Process domains with semaphore control
            tasks = [
                self._scrape_single_domain_with_semaphore(session, semaphore, domain)
                for domain in domains
            ]

            # Execute all tasks and collect results
            results = {}
            completed = 0

            for coro in asyncio.as_completed(tasks):
                try:
                    domain, result = await coro
                    results[domain] = result
                    completed += 1

                    # Progress reporting
                    if completed % 10 == 0 or completed == len(domains):
                        elapsed = time.time() - self.session_stats["start_time"]
                        rate = completed / elapsed if elapsed > 0 else 0
                        print(f"Progress: {completed}/{len(domains)} ({completed/len(domains)*100:.1f}%) - {rate:.1f} domains/sec")

                except Exception as e:
                    print(f"Task failed: {e}")
                    self.session_stats["errors"] += 1

        self._print_session_summary(results)
        return results

    async def _scrape_single_domain_with_semaphore(self, session: aiohttp.ClientSession, semaphore: asyncio.Semaphore, domain: str) -> tuple:
        """Scrape single domain with semaphore control"""

        async with semaphore:
            result = await self._scrape_single_domain(session, domain)
            return domain, result

    async def _scrape_single_domain(self, session: aiohttp.ClientSession, domain: str) -> Dict[str, Any]:
        """Scrape a single domain comprehensively"""

        start_time = time.time()
        result = {
            "domain": domain,
            "success": False,
            "pages": [],
            "total_text_length": 0,
            "total_links": 0,
            "processing_time": 0,
            "error": None
        }

        try:
            # Normalize domain URL
            if not domain.startswith(('http://', 'https://')):
                domain = 'https://' + domain

            # Get main page
            main_page = await self._fetch_page_content(session, domain)
            if not main_page:
                result["error"] = "Failed to fetch main page"
                return result

            result["pages"].append(main_page)
            result["total_text_length"] += main_page.get("text_length", 0)
            result["total_links"] += main_page.get("link_count", 0)

            # Get priority pages
            priority_urls = self._extract_priority_urls(domain, main_page.get("links", []))

            # Limit pages per domain
            pages_to_fetch = priority_urls[:self.config["max_pages_per_domain"] - 1]

            # Fetch additional pages
            if pages_to_fetch:
                additional_pages = await self._fetch_multiple_pages(session, pages_to_fetch)
                for page in additional_pages:
                    if page:
                        result["pages"].append(page)
                        result["total_text_length"] += page.get("text_length", 0)
                        result["total_links"] += page.get("link_count", 0)

            result["success"] = True
            result["processing_time"] = time.time() - start_time

            # Update session stats
            self.session_stats["domains_processed"] += 1
            self.session_stats["pages_scraped"] += len(result["pages"])
            self.session_stats["total_text_extracted"] += result["total_text_length"]

        except Exception as e:
            result["error"] = str(e)
            result["processing_time"] = time.time() - start_time
            self.session_stats["errors"] += 1

        return result

    async def _fetch_page_content(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse content from a single page"""

        headers = {
            "User-Agent": self.config["user_agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }

        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()

                    # Parse HTML with our custom parser
                    parser = TextOnlyParser(url)
                    parser.feed(html)
                    content_data = parser.get_clean_data(self.config["max_text_per_page"])

                    return {
                        "url": url,
                        "status_code": response.status,
                        "text": content_data["text"],
                        "text_length": content_data["text_length"],
                        "links": content_data["links"],
                        "link_count": content_data["link_count"],
                        "fetch_time": time.time()
                    }

        except Exception as e:
            # Silent failure for individual pages
            pass

        return None

    async def _fetch_multiple_pages(self, session: aiohttp.ClientSession, urls: List[str]) -> List[Optional[Dict[str, Any]]]:
        """Fetch multiple pages concurrently"""

        # Limit concurrent page fetches per domain
        semaphore = asyncio.Semaphore(5)

        async def fetch_with_delay(url):
            async with semaphore:
                # Small delay to be polite
                await asyncio.sleep(self.config["delay_between_requests"])
                return await self._fetch_page_content(session, url)

        tasks = [fetch_with_delay(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return valid results
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            elif result is not None:
                # Log exception if needed
                pass

        return valid_results

    def _extract_priority_urls(self, base_domain: str, links: List[str]) -> List[str]:
        """Extract priority URLs from links list"""

        priority_urls = []
        base_parsed = urlparse(base_domain)

        for link in links:
            if not link:
                continue

            try:
                # Convert relative URLs to absolute
                if link.startswith('/'):
                    full_url = f"{base_parsed.scheme}://{base_parsed.netloc}{link}"
                elif link.startswith(('http://', 'https://')):
                    # Check if it's the same domain
                    link_parsed = urlparse(link)
                    if link_parsed.netloc != base_parsed.netloc:
                        continue
                    full_url = link
                else:
                    # Skip relative paths without leading slash
                    continue

                # Check if it's a priority page
                link_lower = link.lower()
                for priority_path in self.priority_paths:
                    if priority_path in link_lower:
                        if full_url not in priority_urls:
                            priority_urls.append(full_url)
                            break

            except Exception:
                continue

        return priority_urls

    def _print_session_summary(self, results: Dict[str, Any]):
        """Print session processing summary"""

        total_time = time.time() - self.session_stats["start_time"]
        successful = sum(1 for r in results.values() if r.get("success", False))
        failed = len(results) - successful

        print(f"\n=== HTTP SCRAPING SESSION COMPLETE ===")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Domains: {len(results)} (Success: {successful}, Failed: {failed})")
        print(f"Pages Scraped: {self.session_stats['pages_scraped']}")
        print(f"Text Extracted: {self.session_stats['total_text_extracted']:,} characters")
        print(f"Processing Rate: {len(results)/total_time:.1f} domains/sec")
        print(f"Success Rate: {successful/len(results)*100:.1f}%")

    async def scrape_single_domain(self, domain: str) -> Dict[str, Any]:
        """Scrape a single domain (convenience method)"""

        results = await self.scrape_domains_parallel([domain])
        return results.get(domain, {})

# ============================================================================
# STANDALONE EXECUTION
# ============================================================================

async def main():
    """Test the HTTP scraper"""

    test_domains = [
        "example.com",
        "github.com",
        "stackoverflow.com"
    ]

    scraper = HTTPScraper()

    print("Testing HTTP Scraper...")
    print("=" * 50)

    results = await scraper.scrape_domains_parallel(test_domains)

    for domain, result in results.items():
        print(f"\nDomain: {domain}")
        print(f"Success: {result.get('success', False)}")
        print(f"Pages: {len(result.get('pages', []))}")
        print(f"Text Length: {result.get('total_text_length', 0):,}")
        print(f"Processing Time: {result.get('processing_time', 0):.2f}s")

        if result.get('error'):
            print(f"Error: {result['error']}")

        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(main())