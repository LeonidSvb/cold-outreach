#!/usr/bin/env python3
"""
Example usage of HTTP suitability checker
"""

import sys
from pathlib import Path

# Add core modules to path
sys.path.append(str(Path(__file__).parent / "core" / "modules" / "scraping_router"))

from function import check_http_suitability

def main():
    # Test URLs
    test_urls = [
        "https://www.altitudestrategies.ca",
        "https://www.stryvemarketing.com", 
        "https://www.workparty.ca"
    ]
    
    print("=== USAGE EXAMPLE ===")
    
    # Check suitability 
    results = check_http_suitability(test_urls)
    
    # Now you can use results however you want:
    
    # Option 1: Filter by flags
    http_suitable_sites = [r for r in results if r['http_suitable']]
    apify_needed_sites = [r for r in results if r['needs_apify']]
    
    print(f"\nHTTP suitable sites: {len(http_suitable_sites)}")
    for site in http_suitable_sites:
        print(f"  - {site['url']}")
    
    print(f"\nApify needed sites: {len(apify_needed_sites)}")
    for site in apify_needed_sites:
        print(f"  - {site['url']}")
    
    # Option 2: Process each site individually
    print(f"\nIndividual processing:")
    for result in results:
        url = result['url']
        if result['http_suitable']:
            print(f"{url} -> Use simple HTTP scraping")
        elif result['needs_apify']:
            print(f"{url} -> Use Apify or other advanced tools")
        
        if result['error']:
            print(f"{url} -> Error: {result['error']}")
    
    # Option 3: Generate arrays if needed
    http_urls = [r['url'] for r in results if r['http_suitable']]
    complex_urls = [r['url'] for r in results if not r['http_suitable']]
    
    print(f"\nAs arrays:")
    print(f"HTTP array: {http_urls}")
    print(f"Complex array: {complex_urls}")

if __name__ == "__main__":
    main()