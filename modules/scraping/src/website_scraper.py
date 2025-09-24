#!/usr/bin/env python3
"""
=== WEBSITE SCRAPER ===
Version: 2.0.0 | Created: 2025-09-25

PURPOSE:
Ultra-parallel website scraping with intelligent page discovery and content extraction.
Optimized for B2B cold outreach intelligence gathering with maximum performance.

FEATURES:
- Ultra-parallel scraping: 50+ concurrent HTTP requests
- Multi-level page discovery with intelligent filtering
- Priority page identification (/about, /team, /contact, /services)
- Content cleaning and text-only extraction
- Smart batching following massive processing principles
- Real-time progress tracking with performance metrics
- Cost-efficient processing optimized for 2000+ domains
- Windows encoding compliance (no emojis)

USAGE:
1. Configure target domains in CONFIG section below
2. Set processing parameters and output settings
3. Run: python website_scraper.py
4. Results automatically saved to results/ with timestamp

IMPROVEMENTS:
v2.0.0 - Complete rewrite with ultra-parallel architecture, intelligent page discovery
v1.0.0 - Basic content extraction functionality
"""

import asyncio
import aiohttp
import json
import time
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Set
import warnings
warnings.filterwarnings("ignore")

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from shared.logger import auto_log

# ============================================================================
# CONFIG SECTION - EDIT HERE
# ============================================================================

CONFIG = {
    # SCRAPING PERFORMANCE SETTINGS
    "SCRAPING": {
        "CONCURRENT_REQUESTS": 50,
        "TIMEOUT_SECONDS": 8,
        "MAX_REDIRECTS": 3,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "DELAY_BETWEEN_BATCHES": 0.1,
        "MAX_RETRIES": 2
    },

    # CONTENT EXTRACTION SETTINGS
    "EXTRACTION": {
        "MAX_PAGES_PER_DOMAIN": 15,
        "MIN_CONTENT_LENGTH": 500,
        "MAX_CONTENT_LENGTH": 50000,
        "TEXT_ONLY_MODE": True,
        "CLEAN_HTML": True,
        "EXTRACT_METADATA": True
    },

    # PRIORITY PAGE DISCOVERY
    "DISCOVERY": {
        "PRIORITY_PAGES": [
            "/about", "/about-us", "/about/", "/team", "/team/", "/leadership",
            "/contact", "/contact-us", "/contact/", "/careers", "/jobs",
            "/services", "/services/", "/solutions", "/products", "/case-studies"
        ],
        "MAX_DISCOVERY_DEPTH": 2,
        "FOLLOW_INTERNAL_LINKS": True,
        "IGNORE_PATTERNS": [
            "login", "register", "cart", "checkout", "admin", "wp-admin",
            ".pdf", ".doc", ".jpg", ".png", ".gif", ".css", ".js",
            "privacy", "terms", "cookie", "sitemap"
        ]
    },

    # BATCH PROCESSING
    "PROCESSING": {
        "DOMAIN_BATCH_SIZE": 20,
        "ENABLE_PROGRESS_TRACKING": True,
        "SAVE_INTERMEDIATE_RESULTS": True,
        "MEMORY_OPTIMIZATION": True
    },

    # OUTPUT SETTINGS
    "OUTPUT": {
        "SAVE_JSON": True,
        "SAVE_RAW_TEXT": True,
        "RESULTS_DIR": "../results",
        "INCLUDE_PAGE_METADATA": True,
        "COMPRESS_OUTPUT": False
    }
}

# ============================================================================
# SCRIPT STATISTICS - AUTO-UPDATED
# ============================================================================

SCRIPT_STATS = {
    "version": "2.0.0",
    "total_runs": 0,
    "total_domains_processed": 0,
    "total_pages_scraped": 0,
    "avg_pages_per_domain": 0.0,
    "success_rate": 0.0,
    "avg_processing_time": 0.0,
    "last_run": None
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class WebsiteScraper:
    """Ultra-parallel website scraper with intelligent page discovery"""

    def __init__(self):
        self.config = CONFIG
        self.results_dir = Path(__file__).parent.parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.session = None
        self.stats = {
            "start_time": time.time(),
            "domains_processed": 0,
            "pages_scraped": 0,
            "successful_domains": 0,
            "failed_domains": 0,
            "total_content_chars": 0
        }

    @auto_log("website_scraper")
    async def scrape_websites(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Main function to scrape multiple websites with ultra-parallel processing"""

        print(f"Starting Website Scraper v{SCRIPT_STATS['version']}")
        print(f"Target domains: {len(domains):,}")
        print(f"Concurrent requests: {self.config['SCRAPING']['CONCURRENT_REQUESTS']}")
        print(f"Max pages per domain: {self.config['EXTRACTION']['MAX_PAGES_PER_DOMAIN']}")
        print(f"Processing mode: {'Text-only' if self.config['EXTRACTION']['TEXT_ONLY_MODE'] else 'Full HTML'}")
        print("=" * 60)

        start_time = time.time()

        # Initialize session with optimized settings
        timeout = aiohttp.ClientTimeout(total=self.config["SCRAPING"]["TIMEOUT_SECONDS"])
        connector = aiohttp.TCPConnector(
            limit=self.config["SCRAPING"]["CONCURRENT_REQUESTS"] * 2,
            limit_per_host=10,
            keepalive_timeout=30
        )

        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            self.session = session

            # Process domains in optimized batches
            results = await self._process_domains_in_batches(domains)

        # Calculate final statistics
        processing_time = time.time() - start_time
        await self._calculate_final_stats(results, processing_time)

        # Save results
        await self._save_results(results, processing_time)

        # Print summary
        self._print_summary(results, processing_time)

        return results

    async def _process_domains_in_batches(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Process domains in optimized batches for maximum performance"""

        batch_size = self.config["PROCESSING"]["DOMAIN_BATCH_SIZE"]
        all_results = []

        print(f"Processing {len(domains)} domains in batches of {batch_size}...")

        for i in range(0, len(domains), batch_size):
            batch = domains[i:i + batch_size]
            batch_number = (i // batch_size) + 1
            total_batches = (len(domains) + batch_size - 1) // batch_size

            print(f"\nBatch {batch_number}/{total_batches}: Processing {len(batch)} domains")

            # Process batch in parallel
            batch_results = await self._process_single_batch(batch)
            all_results.extend([r for r in batch_results if r is not None])

            # Progress update
            completed = min(i + batch_size, len(domains))
            progress = (completed / len(domains)) * 100
            print(f"Overall progress: {progress:.1f}% ({completed}/{len(domains)} domains)")

            # Small delay between batches to be polite
            if i + batch_size < len(domains):
                await asyncio.sleep(self.config["SCRAPING"]["DELAY_BETWEEN_BATCHES"])

        return all_results

    async def _process_single_batch(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Process a single batch of domains with controlled concurrency"""

        semaphore = asyncio.Semaphore(self.config["SCRAPING"]["CONCURRENT_REQUESTS"])

        async def scrape_with_semaphore(domain):
            async with semaphore:
                return await self._scrape_single_domain(domain)

        # Create tasks for batch
        tasks = [scrape_with_semaphore(domain) for domain in domains]

        # Execute with progress tracking
        results = []
        completed = 0

        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            completed += 1

            if self.config["PROCESSING"]["ENABLE_PROGRESS_TRACKING"] and completed % 5 == 0:
                print(f"  Batch progress: {completed}/{len(domains)} domains completed")

        return results

    async def _scrape_single_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Comprehensive scraping of a single domain with page discovery"""

        try:
            # Normalize domain
            if not domain.startswith(('http://', 'https://')):
                domain = 'https://' + domain

            # Initialize domain result
            domain_result = {
                "domain": domain,
                "scraped_at": datetime.now().isoformat(),
                "pages": [],
                "discovery": {
                    "total_links_found": 0,
                    "priority_pages_found": 0,
                    "pages_successfully_scraped": 0
                },
                "metadata": {
                    "total_content_length": 0,
                    "processing_time": 0,
                    "scraping_method": "HTTP"
                }
            }

            domain_start_time = time.time()

            # Step 1: Scrape main page
            main_page = await self._scrape_single_page(domain, is_main_page=True)
            if not main_page:
                domain_result["error"] = "Failed to scrape main page"
                return domain_result

            domain_result["pages"].append(main_page)

            # Step 2: Discover additional pages
            if self.config["DISCOVERY"]["FOLLOW_INTERNAL_LINKS"]:
                additional_urls = self._discover_priority_pages(domain, main_page.get("links", []))
                domain_result["discovery"]["total_links_found"] = len(main_page.get("links", []))
                domain_result["discovery"]["priority_pages_found"] = len(additional_urls)

                # Step 3: Scrape additional priority pages
                max_additional = self.config["EXTRACTION"]["MAX_PAGES_PER_DOMAIN"] - 1
                for url in additional_urls[:max_additional]:
                    page_data = await self._scrape_single_page(url)
                    if page_data:
                        domain_result["pages"].append(page_data)

            # Step 4: Calculate final domain statistics
            domain_result["discovery"]["pages_successfully_scraped"] = len(domain_result["pages"])
            domain_result["metadata"]["total_content_length"] = sum(
                page.get("content_length", 0) for page in domain_result["pages"]
            )
            domain_result["metadata"]["processing_time"] = time.time() - domain_start_time

            # Update global stats
            self.stats["domains_processed"] += 1
            self.stats["pages_scraped"] += len(domain_result["pages"])
            self.stats["successful_domains"] += 1
            self.stats["total_content_chars"] += domain_result["metadata"]["total_content_length"]

            return domain_result

        except Exception as e:
            self.stats["failed_domains"] += 1
            print(f"Error scraping domain {domain}: {e}")
            return {
                "domain": domain,
                "scraped_at": datetime.now().isoformat(),
                "error": str(e),
                "pages": [],
                "metadata": {"processing_time": 0}
            }

    async def _scrape_single_page(self, url: str, is_main_page: bool = False) -> Optional[Dict[str, Any]]:
        """Scrape a single page with intelligent content extraction"""

        try:
            headers = {
                "User-Agent": self.config["SCRAPING"]["USER_AGENT"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive"
            }

            page_start_time = time.time()

            async with self.session.get(url, headers=headers) as response:
                if response.status != 200:
                    return None

                html_content = await response.text()

                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')

                # Extract page data
                page_data = {
                    "url": url,
                    "status_code": response.status,
                    "scraped_at": datetime.now().isoformat(),
                    "processing_time": time.time() - page_start_time
                }

                # Extract metadata
                if self.config["OUTPUT"]["INCLUDE_PAGE_METADATA"]:
                    page_data.update(self._extract_page_metadata(soup))

                # Extract and clean content
                if self.config["EXTRACTION"]["TEXT_ONLY_MODE"]:
                    # Text-only extraction for maximum performance
                    cleaned_content = self._extract_clean_text(soup)
                    page_data["content"] = cleaned_content
                    page_data["content_length"] = len(cleaned_content)
                else:
                    # Full HTML preservation
                    if self.config["EXTRACTION"]["CLEAN_HTML"]:
                        cleaned_html = self._clean_html_content(soup)
                        page_data["html"] = cleaned_html
                    else:
                        page_data["html"] = html_content

                # Extract links for page discovery (only for main pages)
                if is_main_page and self.config["DISCOVERY"]["FOLLOW_INTERNAL_LINKS"]:
                    page_data["links"] = self._extract_internal_links(soup, url)

                # Content length validation
                content_length = page_data.get("content_length", 0)
                if content_length < self.config["EXTRACTION"]["MIN_CONTENT_LENGTH"]:
                    page_data["warning"] = f"Low content length: {content_length} chars"

                return page_data

        except asyncio.TimeoutError:
            return None
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "scraped_at": datetime.now().isoformat()
            }

    def _extract_page_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract page metadata (title, description, headings)"""

        metadata = {
            "title": "",
            "meta_description": "",
            "headings": [],
            "page_type": "unknown"
        }

        # Extract title
        if soup.title:
            metadata["title"] = soup.title.string.strip() if soup.title.string else ""

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            metadata["meta_description"] = meta_desc["content"].strip()

        # Extract headings
        headings = []
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            heading_text = heading.get_text().strip()
            if heading_text and len(heading_text) < 200:  # Reasonable heading length
                headings.append({
                    "level": heading.name,
                    "text": heading_text
                })
        metadata["headings"] = headings[:10]  # Limit to first 10 headings

        # Determine page type
        metadata["page_type"] = self._classify_page_type(metadata["title"], soup.get_text())

        return metadata

    def _extract_clean_text(self, soup: BeautifulSoup) -> str:
        """Extract and clean text content from HTML"""

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()

        # Get text content
        text = soup.get_text(separator=' ', strip=True)

        # Clean whitespace
        text = ' '.join(text.split())

        # Truncate if too long
        max_length = self.config["EXTRACTION"]["MAX_CONTENT_LENGTH"]
        if len(text) > max_length:
            text = text[:max_length] + "... [truncated]"

        return text

    def _clean_html_content(self, soup: BeautifulSoup) -> str:
        """Clean HTML content while preserving structure"""

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer']):
            element.decompose()

        # Return cleaned HTML
        return str(soup)

    def _extract_internal_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract internal links for page discovery"""

        base_domain = urlparse(base_url).netloc
        internal_links = []

        for link in soup.find_all('a', href=True):
            href = link['href']

            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            parsed_url = urlparse(absolute_url)

            # Filter internal links only
            if parsed_url.netloc == base_domain:
                # Remove fragments and query parameters for cleaner URLs
                clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

                # Check if URL should be ignored
                should_ignore = any(pattern in clean_url.lower() for pattern in self.config["DISCOVERY"]["IGNORE_PATTERNS"])

                if not should_ignore and clean_url not in internal_links:
                    internal_links.append(clean_url)

        return internal_links

    def _discover_priority_pages(self, base_url: str, all_links: List[str]) -> List[str]:
        """Discover priority pages based on URL patterns"""

        priority_urls = []

        for link in all_links:
            # Check if link matches priority patterns
            for priority_pattern in self.config["DISCOVERY"]["PRIORITY_PAGES"]:
                if priority_pattern in link.lower():
                    if link not in priority_urls:
                        priority_urls.append(link)

        return priority_urls

    def _classify_page_type(self, title: str, content: str) -> str:
        """Classify page type based on title and content"""

        title_lower = title.lower()
        content_lower = content.lower()

        # Page type classification
        if any(word in title_lower for word in ['about', 'who we are', 'our story']):
            return 'about'
        elif any(word in title_lower for word in ['team', 'staff', 'people', 'leadership']):
            return 'team'
        elif any(word in title_lower for word in ['contact', 'reach us', 'get in touch']):
            return 'contact'
        elif any(word in title_lower for word in ['services', 'what we do', 'offerings']):
            return 'services'
        elif any(word in title_lower for word in ['products', 'solutions']):
            return 'products'
        elif any(word in title_lower for word in ['case studies', 'portfolio', 'work']):
            return 'case_studies'
        elif any(word in title_lower for word in ['careers', 'jobs', 'opportunities']):
            return 'careers'
        elif any(word in title_lower for word in ['news', 'blog', 'articles']):
            return 'news'
        else:
            return 'general'

    async def _calculate_final_stats(self, results: List[Dict[str, Any]], processing_time: float):
        """Calculate and update final processing statistics"""

        # Basic statistics
        total_domains = len(results)
        successful_domains = len([r for r in results if "error" not in r])
        total_pages = sum(len(r.get("pages", [])) for r in results)

        # Update global script stats
        global SCRIPT_STATS
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["total_domains_processed"] += total_domains
        SCRIPT_STATS["total_pages_scraped"] += total_pages
        SCRIPT_STATS["success_rate"] = (successful_domains / total_domains * 100) if total_domains > 0 else 0
        SCRIPT_STATS["avg_pages_per_domain"] = total_pages / successful_domains if successful_domains > 0 else 0
        SCRIPT_STATS["avg_processing_time"] = processing_time
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()

    async def _save_results(self, results: List[Dict[str, Any]], processing_time: float):
        """Save scraping results with comprehensive metadata"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Prepare comprehensive results data
        results_data = {
            "metadata": {
                "timestamp": timestamp,
                "script_version": SCRIPT_STATS["version"],
                "processing_summary": {
                    "total_domains": len(results),
                    "successful_domains": self.stats["successful_domains"],
                    "failed_domains": self.stats["failed_domains"],
                    "total_pages_scraped": self.stats["pages_scraped"],
                    "avg_pages_per_domain": self.stats["pages_scraped"] / max(1, self.stats["successful_domains"]),
                    "total_processing_time": processing_time,
                    "avg_time_per_domain": processing_time / len(results) if results else 0,
                    "total_content_characters": self.stats["total_content_chars"],
                    "avg_content_per_page": self.stats["total_content_chars"] / max(1, self.stats["pages_scraped"])
                },
                "configuration": self.config,
                "performance_metrics": {
                    "domains_per_second": len(results) / processing_time if processing_time > 0 else 0,
                    "pages_per_second": self.stats["pages_scraped"] / processing_time if processing_time > 0 else 0,
                    "success_rate": (self.stats["successful_domains"] / len(results) * 100) if results else 0
                }
            },
            "results": results
        }

        # Save main JSON results
        if self.config["OUTPUT"]["SAVE_JSON"]:
            json_filename = f"website_scraping_{timestamp}.json"
            json_filepath = self.results_dir / json_filename

            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)

            print(f"JSON results saved: {json_filename}")

        # Save raw text data if requested
        if self.config["OUTPUT"]["SAVE_RAW_TEXT"]:
            text_filename = f"raw_text_content_{timestamp}.json"
            text_filepath = self.results_dir / text_filename

            # Extract only text content for separate file
            text_data = {
                "metadata": {
                    "timestamp": timestamp,
                    "total_domains": len(results),
                    "extraction_mode": "text_only" if self.config["EXTRACTION"]["TEXT_ONLY_MODE"] else "html"
                },
                "content": {}
            }

            for result in results:
                if "error" not in result and result.get("pages"):
                    domain = result["domain"]
                    text_data["content"][domain] = []

                    for page in result["pages"]:
                        if "content" in page:
                            text_data["content"][domain].append({
                                "url": page["url"],
                                "title": page.get("title", ""),
                                "content": page["content"],
                                "content_length": page.get("content_length", 0)
                            })

            with open(text_filepath, 'w', encoding='utf-8') as f:
                json.dump(text_data, f, indent=2, ensure_ascii=False)

            print(f"Raw text data saved: {text_filename}")

    def _print_summary(self, results: List[Dict[str, Any]], processing_time: float):
        """Print comprehensive scraping summary"""

        print("\n" + "=" * 60)
        print("WEBSITE SCRAPING SUMMARY")
        print("=" * 60)

        # Basic statistics
        total_domains = len(results)
        successful_domains = len([r for r in results if "error" not in r])
        failed_domains = total_domains - successful_domains
        total_pages = sum(len(r.get("pages", [])) for r in results)

        print(f"Domains processed: {total_domains:,}")
        print(f"Successful: {successful_domains:,} ({successful_domains/total_domains*100:.1f}%)")
        print(f"Failed: {failed_domains:,} ({failed_domains/total_domains*100:.1f}%)")
        print(f"Total pages scraped: {total_pages:,}")
        print(f"Avg pages per domain: {total_pages/successful_domains:.1f}" if successful_domains > 0 else "N/A")

        # Performance metrics
        print(f"\nPERFORMANCE:")
        print(f"Total processing time: {processing_time:.2f}s")
        print(f"Average time per domain: {processing_time/total_domains:.2f}s" if total_domains > 0 else "N/A")
        print(f"Domains per second: {total_domains/processing_time:.2f}" if processing_time > 0 else "N/A")
        print(f"Pages per second: {total_pages/processing_time:.2f}" if processing_time > 0 else "N/A")

        # Content statistics
        total_chars = sum(
            sum(page.get("content_length", 0) for page in result.get("pages", []))
            for result in results
        )
        print(f"\nCONTENT STATISTICS:")
        print(f"Total content extracted: {total_chars:,} characters")
        print(f"Average content per page: {total_chars/total_pages:,.0f} chars" if total_pages > 0 else "N/A")
        print(f"Average content per domain: {total_chars/successful_domains:,.0f} chars" if successful_domains > 0 else "N/A")

        # Error summary
        if failed_domains > 0:
            print(f"\nERRORS: {failed_domains} domains failed")
            error_results = [r for r in results if "error" in r]
            for i, error_result in enumerate(error_results[:3]):  # Show first 3 errors
                print(f"  {i+1}. {error_result['domain']}: {error_result['error']}")
            if len(error_results) > 3:
                print(f"  ... and {len(error_results) - 3} more errors")

        print("=" * 60)

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function for testing"""

    print("=" * 60)
    print(f"WEBSITE SCRAPER v{SCRIPT_STATS['version']}")
    print("=" * 60)

    # Sample domains for testing
    test_domains = [
        "https://www.altitudestrategies.ca",
        "https://www.stryvemarketing.com",
        "http://www.bigfishcreative.ca",
        "http://www.workparty.ca",
        "http://www.theog.co"
    ]

    scraper = WebsiteScraper()
    results = await scraper.scrape_websites(test_domains)

    print(f"\nScraping completed: {len(results)} results generated")

    return results

if __name__ == "__main__":
    asyncio.run(main())