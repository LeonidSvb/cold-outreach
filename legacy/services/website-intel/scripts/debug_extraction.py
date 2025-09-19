#!/usr/bin/env python3
"""
Debug extraction process to see where page discovery fails
"""

import os
from domain_intelligence_extractor import WebsiteIntelligenceExtractor

class DebugExtractor(WebsiteIntelligenceExtractor):
    """Debug version of extractor with detailed logging"""
    
    def discover_pages(self, domain: str):
        """Debug version of discover_pages"""
        print(f"\n=== DEBUG DISCOVER_PAGES ===")
        pages = set()
        base_url = self.normalize_url(domain)
        print(f"Base URL: {base_url}")
        
        # Add base domain
        pages.add(base_url)
        print(f"Added base URL to pages: {len(pages)} pages")
        
        # Try to get sitemap first
        sitemap_urls = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemaps.xml"
        ]
        
        sitemap_found = False
        for sitemap_url in sitemap_urls:
            print(f"Trying sitemap: {sitemap_url}")
            sitemap_pages = self.parse_sitemap(sitemap_url)
            if sitemap_pages:
                pages.update(sitemap_pages[:50])
                print(f"Found {len(sitemap_pages)} pages in sitemap")
                print(f"Total pages now: {len(pages)}")
                sitemap_found = True
                break
        
        if not sitemap_found:
            print("No sitemap found")
        
        # Multi-level crawling for better page discovery
        print(f"\n--- STARTING MULTI-LEVEL CRAWLING ---")
        discovered_urls = set([base_url])
        urls_to_process = set([base_url])
        processed_urls = set()
        
        # Crawl up to 2 levels deep
        for depth in range(2):
            print(f"\n=== DEPTH {depth + 1} ===")
            current_batch = urls_to_process - processed_urls
            
            print(f"URLs to process at this depth: {len(current_batch)}")
            for url in list(current_batch)[:3]:  # Show first 3
                print(f"  - {url}")
            
            if not current_batch:
                print("No URLs to process, breaking")
                break
                
            new_urls = set()
            
            # Process up to 5 URLs per depth level
            for url in list(current_batch)[:5]:
                if url in processed_urls:
                    continue
                    
                print(f"\nProcessing: {url}")
                links = self.extract_internal_links(url, domain)
                print(f"Found {len(links)} internal links")
                
                # Show first 5 links found
                for link in links[:5]:
                    print(f"  Link: {link}")
                
                new_links = set(links) - discovered_urls
                print(f"New links (not already discovered): {len(new_links)}")
                
                new_urls.update(new_links)
                discovered_urls.update(new_links)
                processed_urls.add(url)
                
                print(f"Total discovered URLs: {len(discovered_urls)}")
                
                # Add small delay to be respectful
                import time
                time.sleep(0.5)
            
            urls_to_process.update(new_urls)
            print(f"URLs for next depth level: {len(urls_to_process - processed_urls)}")
        
        # Combine sitemap and crawled pages
        pages.update(discovered_urls)
        
        print(f"\n=== FINAL RESULTS ===")
        print(f"Total pages discovered: {len(pages)}")
        print("All discovered pages:")
        for i, page in enumerate(sorted(pages), 1):
            print(f"  {i}. {page}")
        
        return pages

def main():
    """Test with debug extractor"""
    
    # Load API key from environment
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    openai_api_key = None
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    openai_api_key = line.split('=', 1)[1].strip()
                    break
    
    if not openai_api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return
    
    # Initialize debug extractor
    extractor = DebugExtractor(openai_api_key)
    
    # Test page discovery only
    print("=" * 60)
    print("DEBUG: Testing page discovery for stryvemarketing.com")
    print("=" * 60)
    
    pages = extractor.discover_pages('stryvemarketing.com')
    
    print(f"\n🎯 Final result: {len(pages)} pages discovered")

if __name__ == "__main__":
    main()