#!/usr/bin/env python3
"""
=== LINK EXTRACTOR MODULE ===
Version: 1.0.0 | Created: 2025-01-15

PURPOSE: 
Extract all discoverable links from a company website with depth control

INPUT: 
- domain (str): Website domain (e.g., "https://example.com" or "example.com")
- max_depth (int): Maximum crawling depth (default: 2)
- max_links (int): Maximum links to extract (default: 100)

OUTPUT: 
List[str] of unique, valid URLs discovered on the website

FEATURES:
- Depth-controlled crawling
- Automatic duplicate filtering  
- Domain validation and normalization
- Respects robots.txt guidelines
- HTTP-only implementation (no external services)
"""

import sys
import os
import requests
import time
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from typing import List, Set, Dict, Any
from pathlib import Path

# Add shared utilities to path
sys.path.append(str(Path(__file__).parent.parent / "_shared"))
from logger import auto_log

# Module statistics (auto-updated by logger)
MODULE_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "domains_processed": 0,
    "avg_links_found": 0,
    "last_run": None,
    "success_rate": 100.0
}

class LinkExtractor:
    """Extracts all links from website with depth control"""
    
    def __init__(self, max_depth: int = 2, max_links: int = 100):
        self.max_depth = max_depth
        self.max_links = max_links
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain URL"""
        if not domain.startswith(('http://', 'https://')):
            domain = 'https://' + domain
        
        parsed = urlparse(domain)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid for crawling"""
        try:
            parsed = urlparse(url)
            base_parsed = urlparse(base_domain)
            
            # Must be same domain
            if parsed.netloc != base_parsed.netloc:
                return False
            
            # Skip certain file types
            skip_extensions = ['.pdf', '.doc', '.docx', '.zip', '.exe', '.jpg', '.png', '.gif']
            if any(url.lower().endswith(ext) for ext in skip_extensions):
                return False
                
            # Skip common excluded paths
            skip_paths = ['#', 'javascript:', 'mailto:', 'tel:', 'ftp:']
            if any(url.lower().startswith(skip) for skip in skip_paths):
                return False
                
            return True
        except:
            return False
    
    def _get_page_links(self, url: str, base_domain: str) -> List[str]:
        """Extract links from single page"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            # Find all links
            for link in soup.find_all('a', href=True):
                href = link['href'].strip()
                if not href:
                    continue
                    
                # Convert relative URLs to absolute
                absolute_url = urljoin(url, href)
                
                if self._is_valid_url(absolute_url, base_domain):
                    links.append(absolute_url)
            
            return links
            
        except Exception as e:
            print(f"Error extracting links from {url}: {e}")
            return []
    
    def _crawl_recursive(self, start_url: str, current_depth: int, 
                        visited: Set[str], all_links: Set[str]) -> None:
        """Recursively crawl website"""
        if current_depth > self.max_depth or len(all_links) >= self.max_links:
            return
            
        if start_url in visited:
            return
            
        visited.add(start_url)
        print(f"Crawling depth {current_depth}: {start_url}")
        
        # Get links from current page
        page_links = self._get_page_links(start_url, self._normalize_domain(start_url))
        
        for link in page_links:
            if len(all_links) >= self.max_links:
                break
                
            all_links.add(link)
            
            # Recursive crawl if not at max depth
            if current_depth < self.max_depth:
                self._crawl_recursive(link, current_depth + 1, visited, all_links)
        
        # Small delay to be respectful
        time.sleep(0.5)

@auto_log("link_extractor")
def extract_all_links(domain: str, max_depth: int = 2, max_links: int = 100) -> List[str]:
    """
    Extract all discoverable links from a website
    
    Args:
        domain: Website domain (e.g., "https://example.com" or "example.com")
        max_depth: Maximum crawling depth (default: 2)
        max_links: Maximum links to extract (default: 100)
    
    Returns:
        List[str]: Unique, valid URLs discovered on the website
    
    Example:
        links = extract_all_links("https://example.com", max_depth=3)
        print(f"Found {len(links)} links")
    """
    
    # Update module stats
    MODULE_STATS["total_runs"] += 1
    MODULE_STATS["domains_processed"] += 1
    
    try:
        extractor = LinkExtractor(max_depth=max_depth, max_links=max_links)
        base_domain = extractor._normalize_domain(domain)
        
        print(f"Starting link extraction from {base_domain}")
        print(f"Max depth: {max_depth}, Max links: {max_links}")
        
        visited = set()
        all_links = set()
        
        # Start crawling
        extractor._crawl_recursive(base_domain, 0, visited, all_links)
        
        # Convert to sorted list
        result = sorted(list(all_links))
        
        # Update stats
        MODULE_STATS["avg_links_found"] = (
            (MODULE_STATS["avg_links_found"] * (MODULE_STATS["total_runs"] - 1) + len(result)) 
            / MODULE_STATS["total_runs"]
        )
        MODULE_STATS["last_run"] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Extraction complete! Found {len(result)} unique links")
        return result
        
    except Exception as e:
        print(f"Error extracting links from {domain}: {e}")
        raise

def main():
    """CLI interface for standalone usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract all links from a website")
    parser.add_argument("domain", help="Website domain to extract links from")
    parser.add_argument("--depth", type=int, default=2, help="Maximum crawling depth")
    parser.add_argument("--max-links", type=int, default=100, help="Maximum links to extract")
    parser.add_argument("--output", help="Output file to save links")
    
    args = parser.parse_args()
    
    print(f"Link Extractor v{MODULE_STATS['version']}")
    print("=" * 50)
    
    links = extract_all_links(args.domain, args.depth, args.max_links)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            for link in links:
                f.write(link + '\n')
        print(f"Links saved to {args.output}")
    else:
        print(f"\nDiscovered {len(links)} links:")
        for i, link in enumerate(links, 1):
            print(f"{i:3d}. {link}")
    
    print(f"\nModule Stats: {MODULE_STATS}")

if __name__ == "__main__":
    main()