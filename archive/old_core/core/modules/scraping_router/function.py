#!/usr/bin/env python3
"""
=== SCRAPING ROUTER MODULE ===
Version: 1.0.0 | Created: 2025-09-12

PURPOSE: 
Simple decision logic for HTTP vs Apify scraping

INPUT: 
List of URLs to analyze

OUTPUT: 
{
    "http_urls": ["url1", "url2", ...],
    "apify_urls": ["url3", "url4", ...]
}

LOGIC:
- Test HTTP accessibility
- Detect JavaScript dependency 
- Route to appropriate scraping method
"""

import sys
import os
import json
import time
import requests
from typing import List, Dict, Any
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore")

# Add shared utilities to path
sys.path.append(str(Path(__file__).parent.parent / "_shared"))
from logger import auto_log

# Module statistics
MODULE_STATS = {
    "version": "1.0.0", 
    "total_runs": 0,
    "urls_processed": 0,
    "http_routed": 0,
    "apify_routed": 0,
    "last_run": None,
    "success_rate": 100.0
}

class ScrapingRouter:
    """Simple router for HTTP vs Apify scraping decision"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def _quick_test_http(self, url: str) -> bool:
        """Quick test if URL can be scraped with HTTP"""
        try:
            response = self.session.get(url, timeout=5, allow_redirects=True)
            if response.status_code != 200:
                return False
            
            html = response.text
            if len(html) < 500:  # Too little content
                return False
                
            # Check for JavaScript dependency indicators
            html_lower = html.lower()
            js_indicators = [
                'react', 'angular', 'vue.js', 'loading...', 'javascript required',
                'noscript', 'document.addeventlistener', 'window.onload'
            ]
            
            js_count = sum(1 for indicator in js_indicators if indicator in html_lower)
            if js_count > 2:  # High JavaScript usage
                return False
                
            # Check for bot protection
            protection_signs = ['cloudflare', 'captcha', 'access denied', 'blocked']
            if any(sign in html_lower for sign in protection_signs):
                return False
                
            return True
            
        except Exception:
            return False
    
    def check_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Check URLs and return flags for each"""
        
        results = []
        
        print(f"Checking {len(urls)} URLs...")
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Testing: {url}")
            
            result = {
                "url": url,
                "http_suitable": False,
                "needs_apify": True,
                "error": None
            }
            
            try:
                if self._quick_test_http(url):
                    result["http_suitable"] = True
                    result["needs_apify"] = False
                    print(f"  -> HTTP suitable: YES")
                else:
                    print(f"  -> HTTP suitable: NO")
                    
            except Exception as e:
                result["error"] = str(e)
                print(f"  -> Error: {e}")
                
            results.append(result)
            time.sleep(0.2)  # Be nice to servers
        
        return results

@auto_log("scraping_router")
def check_http_suitability(urls: List[str]) -> List[Dict[str, Any]]:
    """
    Check URLs for HTTP suitability flags
    
    Args:
        urls: List of URLs to check
    
    Returns:
        List of results with flags:
        [
            {
                "url": "https://site.com",
                "http_suitable": True/False,
                "needs_apify": True/False,
                "error": None or error message
            }
        ]
    
    Example:
        urls = ["https://site1.com", "https://site2.com"]
        results = check_http_suitability(urls)
        for result in results:
            print(f"{result['url']}: HTTP suitable = {result['http_suitable']}")
    """
    
    # Update module stats
    MODULE_STATS["total_runs"] += 1
    MODULE_STATS["urls_processed"] += len(urls)
    
    try:
        router = ScrapingRouter()
        results = router.check_urls(urls)
        
        # Update stats
        http_count = sum(1 for r in results if r["http_suitable"])
        apify_count = len(results) - http_count
        
        MODULE_STATS["http_routed"] += http_count
        MODULE_STATS["apify_routed"] += apify_count
        MODULE_STATS["last_run"] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\nCheck complete:")
        print(f"HTTP suitable: {http_count}")
        print(f"Needs Apify: {apify_count}")
        
        return results
        
    except Exception as e:
        print(f"Error checking URLs: {e}")
        # Fallback - mark all as needing Apify
        return [
            {
                "url": url,
                "http_suitable": False,
                "needs_apify": True,
                "error": str(e)
            } for url in urls
        ]

def main():
    """CLI interface for standalone usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Route URLs to optimal scraping method")
    parser.add_argument("urls", nargs='+', help="URLs to route")
    parser.add_argument("--output", help="Output JSON file")
    
    args = parser.parse_args()
    
    print(f"Scraping Router v{MODULE_STATS['version']}")
    print("=" * 50)
    
    # Route URLs
    result = route_scraping_methods(args.urls)
    
    # Save or display results
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))
    
    print(f"\nModule Stats: {MODULE_STATS}")

if __name__ == "__main__":
    main()