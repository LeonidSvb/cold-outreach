#!/usr/bin/env python3
"""
=== CONTENT SCRAPER MODULE ===
Version: 1.0.0 | Created: 2025-01-15

PURPOSE: 
Scrape multiple URLs and convert to clean JSON format without CSS/JS/HTML

INPUT: 
- urls (List[str]): List of URLs to scrape
- include_metadata (bool): Include metadata like title, description (default: True)
- clean_level (str): Cleaning level - 'basic', 'aggressive' (default: 'basic')

OUTPUT: 
Dict[str, Dict]: Mapping of URL to clean content data in JSON format

FEATURES:
- HTML parsing with CSS/JS removal
- Text extraction and cleaning
- Metadata extraction (title, description, keywords)
- Error handling for failed URLs
- Parallel processing support
- JSON structured output
"""

import sys
import os
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

# Add shared utilities to path
sys.path.append(str(Path(__file__).parent.parent / "_shared"))
from logger import auto_log

# Module statistics (auto-updated by logger)
MODULE_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "urls_processed": 0,
    "successful_scrapes": 0,
    "failed_scrapes": 0,
    "avg_content_size": 0,
    "last_run": None,
    "success_rate": 100.0
}

class ContentScraper:
    """Scrapes URLs and converts to clean JSON"""
    
    def __init__(self, clean_level: str = 'basic', include_metadata: bool = True):
        self.clean_level = clean_level
        self.include_metadata = include_metadata
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        
        # Basic cleaning
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'\n+', '\n', text)  # Multiple newlines to single
        text = text.strip()
        
        if self.clean_level == 'aggressive':
            # More aggressive cleaning
            text = re.sub(r'[^\w\s\-\.\,\!\?\:\;\(\)]', '', text)
            text = re.sub(r'\b(cookie|gdpr|privacy|terms|legal)\b', '', text, flags=re.IGNORECASE)
        
        return text
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, str]:
        """Extract page metadata"""
        metadata = {}
        
        # Title
        title_tag = soup.find('title')
        metadata['title'] = self._clean_text(title_tag.text) if title_tag else ''
        
        # Meta description
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and desc_tag.get('content'):
            metadata['description'] = self._clean_text(desc_tag.get('content'))
        else:
            metadata['description'] = ''
        
        # Meta keywords
        keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag and keywords_tag.get('content'):
            metadata['keywords'] = self._clean_text(keywords_tag.get('content'))
        else:
            metadata['keywords'] = ''
        
        # URL info
        parsed = urlparse(url)
        metadata['domain'] = parsed.netloc
        metadata['path'] = parsed.path
        
        return metadata
    
    def _extract_main_content(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract main content sections"""
        content = {}
        
        # Remove unwanted elements
        unwanted_tags = ['script', 'style', 'nav', 'header', 'footer', 'aside', 
                        'advertisement', 'cookie', 'popup', 'modal']
        
        for tag_name in unwanted_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Remove elements with certain classes/ids
        unwanted_selectors = [
            '[class*="cookie"]', '[class*="gdpr"]', '[class*="popup"]',
            '[class*="modal"]', '[class*="advertisement"]', '[class*="ad-"]',
            '[id*="cookie"]', '[id*="popup"]', '[id*="modal"]'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Extract different content sections
        
        # Main content (try various selectors)
        main_selectors = ['main', '.main-content', '.content', '#content', 'article', '.article']
        main_content = ''
        
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                main_content = self._clean_text(main_element.get_text())
                break
        
        if not main_content:
            # Fallback to body content
            body = soup.find('body')
            if body:
                main_content = self._clean_text(body.get_text())
        
        content['main_content'] = main_content
        
        # Extract headings structure
        headings = []
        for level in range(1, 7):  # h1 to h6
            for heading in soup.find_all(f'h{level}'):
                heading_text = self._clean_text(heading.get_text())
                if heading_text:
                    headings.append({
                        'level': level,
                        'text': heading_text
                    })
        
        content['headings'] = headings
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            link_text = self._clean_text(link.get_text())
            if link_text and len(link_text) > 3:  # Skip empty or very short links
                links.append({
                    'text': link_text,
                    'href': link['href']
                })
        
        content['links'] = links[:20]  # Limit to first 20 links
        
        return content
    
    def _scrape_single_url(self, url: str) -> Dict[str, Any]:
        """Scrape single URL and return clean content"""
        try:
            print(f"Scraping: {url}")
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            result = {
                'url': url,
                'success': True,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status_code': response.status_code,
                'content_length': len(response.content)
            }
            
            if self.include_metadata:
                result['metadata'] = self._extract_metadata(soup, url)
            
            result['content'] = self._extract_main_content(soup)
            
            return result
            
        except Exception as e:
            return {
                'url': url,
                'success': False,
                'error': str(e),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def scrape_urls(self, urls: List[str], max_workers: int = 3) -> Dict[str, Dict[str, Any]]:
        """Scrape multiple URLs in parallel"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self._scrape_single_url, url): url for url in urls}
            
            for future in as_completed(future_to_url):
                result = future.result()
                results[result['url']] = result
        
        return results

@auto_log("content_scraper")
def scrape_urls_to_clean_json(urls: List[str], include_metadata: bool = True, 
                             clean_level: str = 'basic', max_workers: int = 3) -> Dict[str, Dict[str, Any]]:
    """
    Scrape multiple URLs and convert to clean JSON format
    
    Args:
        urls: List of URLs to scrape
        include_metadata: Include metadata like title, description (default: True)
        clean_level: Cleaning level - 'basic', 'aggressive' (default: 'basic')
        max_workers: Number of parallel workers (default: 3)
    
    Returns:
        Dict[str, Dict]: Mapping of URL to clean content data
    
    Example:
        urls = ["https://example.com/about", "https://example.com/services"]
        content = scrape_urls_to_clean_json(urls)
        for url, data in content.items():
            if data['success']:
                print(f"Title: {data['metadata']['title']}")
                print(f"Content: {data['content']['main_content'][:200]}...")
    """
    
    # Update module stats
    MODULE_STATS["total_runs"] += 1
    MODULE_STATS["urls_processed"] += len(urls)
    
    try:
        scraper = ContentScraper(clean_level=clean_level, include_metadata=include_metadata)
        results = scraper.scrape_urls(urls, max_workers=max_workers)
        
        # Update stats
        successful = sum(1 for r in results.values() if r['success'])
        failed = len(results) - successful
        
        MODULE_STATS["successful_scrapes"] += successful
        MODULE_STATS["failed_scrapes"] += failed
        
        # Calculate average content size
        content_sizes = [len(r.get('content', {}).get('main_content', '')) 
                        for r in results.values() if r['success']]
        if content_sizes:
            avg_size = sum(content_sizes) / len(content_sizes)
            MODULE_STATS["avg_content_size"] = (
                (MODULE_STATS["avg_content_size"] * (MODULE_STATS["total_runs"] - 1) + avg_size) 
                / MODULE_STATS["total_runs"]
            )
        
        MODULE_STATS["success_rate"] = (
            (MODULE_STATS["successful_scrapes"] / (MODULE_STATS["successful_scrapes"] + MODULE_STATS["failed_scrapes"]) * 100)
            if (MODULE_STATS["successful_scrapes"] + MODULE_STATS["failed_scrapes"]) > 0 else 100
        )
        
        MODULE_STATS["last_run"] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Scraping complete! {successful}/{len(urls)} successful")
        return results
        
    except Exception as e:
        print(f"Error scraping URLs: {e}")
        raise

def main():
    """CLI interface for standalone usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape URLs to clean JSON format")
    parser.add_argument("input", help="Input file with URLs (one per line) or JSON file")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument("--clean-level", choices=['basic', 'aggressive'], default='basic', 
                       help="Content cleaning level")
    parser.add_argument("--no-metadata", action='store_true', help="Don't include metadata")
    parser.add_argument("--workers", type=int, default=3, help="Number of parallel workers")
    
    args = parser.parse_args()
    
    print(f"Content Scraper v{MODULE_STATS['version']}")
    print("=" * 50)
    
    # Read input URLs
    input_path = Path(args.input)
    if input_path.suffix.lower() == '.json':
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            urls = data.get('filtered_links', data.get('links', []))
    else:
        with open(input_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(urls)} URLs from {input_path}")
    
    # Scrape content
    results = scrape_urls_to_clean_json(
        urls, 
        include_metadata=not args.no_metadata,
        clean_level=args.clean_level,
        max_workers=args.workers
    )
    
    # Save results
    output_path = Path(args.output) if args.output else input_path.with_suffix('.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to {output_path}")
    print(f"Module Stats: {MODULE_STATS}")

if __name__ == "__main__":
    main()