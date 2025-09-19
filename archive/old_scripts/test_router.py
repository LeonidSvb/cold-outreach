#!/usr/bin/env python3
"""
Test scraping router on real URLs
"""

import sys
from pathlib import Path

# Add core modules to path
sys.path.append(str(Path(__file__).parent / "core" / "modules" / "scraping_router"))

from function import route_scraping_methods

def main():
    # Test URLs from our previous analysis
    test_urls = [
        "http://www.altitudestrategies.ca",
        "http://www.stryvemarketing.com", 
        "http://www.workparty.ca",
        "http://www.kiplingmedia.com",
        "http://www.theog.co",
        "http://www.polkarsenal.com"
    ]
    
    print("=== SCRAPING ROUTER TEST ===")
    print(f"Testing {len(test_urls)} URLs")
    print("-" * 40)
    
    result = route_scraping_methods(test_urls)
    
    print("\n" + "="*40)
    print("ROUTING RESULTS:")
    print("="*40)
    
    print(f"\nHTTP SUITABLE ({len(result['http_urls'])}):")
    for url in result['http_urls']:
        print(f"  - {url}")
    
    print(f"\nAPIFY NEEDED ({len(result['apify_urls'])}):")
    for url in result['apify_urls']:
        print(f"  - {url}")
    
    # Simple cost calculation
    http_cost = len(result['http_urls']) * 0.0001
    apify_cost = len(result['apify_urls']) * 0.002
    total_cost = http_cost + apify_cost
    
    print(f"\nCOST ESTIMATE:")
    print(f"HTTP cost: ${http_cost:.4f}")
    print(f"Apify cost: ${apify_cost:.4f}")
    print(f"Total: ${total_cost:.4f}")

if __name__ == "__main__":
    main()