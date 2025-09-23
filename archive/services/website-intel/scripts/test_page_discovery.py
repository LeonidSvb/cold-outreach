#!/usr/bin/env python3
"""
Test Page Discovery Script
Debug and test page discovery functionality for specific domains
"""

import re
import urllib.parse
import urllib.request
import ssl
from typing import Set, List

class PageDiscoveryTester:
    """Test page discovery functionality"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL"""
        if not url:
            return ""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def make_request(self, url: str, timeout: int = 10) -> str:
        """Make HTTP request"""
        try:
            normalized_url = self.normalize_url(url)
            print(f"  Making request to: {normalized_url}")
            
            req = urllib.request.Request(normalized_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=timeout, context=self.ssl_context) as response:
                content = response.read()
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    content = content.decode('utf-8', errors='ignore')
                
                print(f"  Response status: {response.status}")
                print(f"  Content length: {len(content)} chars")
                return content
        
        except Exception as e:
            print(f"  ERROR: {e}")
            return ""
    
    def test_sitemap_discovery(self, domain: str) -> List[str]:
        """Test sitemap discovery"""
        print(f"\n=== TESTING SITEMAP DISCOVERY ===")
        
        base_url = self.normalize_url(domain)
        sitemap_urls = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml", 
            f"{base_url}/sitemaps.xml",
            f"{base_url}/robots.txt"  # Check robots.txt for sitemap
        ]
        
        found_urls = []
        
        for sitemap_url in sitemap_urls:
            print(f"\nTrying: {sitemap_url}")
            content = self.make_request(sitemap_url)
            
            if content:
                if 'robots.txt' in sitemap_url:
                    # Extract sitemap URLs from robots.txt
                    sitemap_matches = re.findall(r'Sitemap:\s*(https?://[^\s]+)', content, re.IGNORECASE)
                    print(f"  Found sitemaps in robots.txt: {sitemap_matches}")
                    
                    for sitemap_match in sitemap_matches:
                        print(f"\nFetching sitemap from robots.txt: {sitemap_match}")
                        sitemap_content = self.make_request(sitemap_match)
                        if sitemap_content:
                            urls = self.parse_sitemap_content(sitemap_content)
                            found_urls.extend(urls)
                            print(f"  Found {len(urls)} URLs in sitemap")
                else:
                    # Parse XML sitemap
                    urls = self.parse_sitemap_content(content)
                    found_urls.extend(urls)
                    print(f"  Found {len(urls)} URLs in sitemap")
                    
                if found_urls:
                    break
        
        return found_urls
    
    def parse_sitemap_content(self, content: str) -> List[str]:
        """Parse sitemap content"""
        # Extract URLs from sitemap
        url_pattern = r'<loc>(.*?)</loc>'
        urls = re.findall(url_pattern, content, re.IGNORECASE | re.DOTALL)
        
        # Filter HTML pages only
        html_urls = []
        for url in urls:
            url = url.strip()
            # Skip non-HTML files
            if not any(ext in url.lower() for ext in ['.xml', '.pdf', '.jpg', '.png', '.gif', '.css', '.js', '.ico']):
                html_urls.append(url)
        
        return html_urls
    
    def test_internal_link_extraction(self, domain: str, max_depth: int = 2) -> Set[str]:
        """Test internal link extraction with multiple depth levels"""
        print(f"\n=== TESTING INTERNAL LINK EXTRACTION ===")
        
        base_url = self.normalize_url(domain)
        base_domain = domain.lower().replace('www.', '').replace('https://', '').replace('http://', '').strip('/')
        
        discovered_urls = set()
        urls_to_process = {base_url}
        processed_urls = set()
        
        for depth in range(max_depth):
            print(f"\n--- DEPTH {depth + 1} ---")
            current_batch = urls_to_process - processed_urls
            
            if not current_batch:
                print("  No new URLs to process at this depth")
                break
                
            print(f"  Processing {len(current_batch)} URLs")
            
            new_urls = set()
            
            for url in list(current_batch)[:5]:  # Limit to 5 URLs per depth for testing
                if url in processed_urls:
                    continue
                    
                print(f"\n  Processing: {url}")
                content = self.make_request(url)
                processed_urls.add(url)
                
                if content:
                    links = self.extract_links_from_content(content, base_domain, base_url)
                    new_links = links - discovered_urls
                    print(f"    Found {len(new_links)} new internal links")
                    
                    for link in list(new_links)[:10]:  # Show first 10
                        print(f"      - {link}")
                    
                    new_urls.update(new_links)
                    discovered_urls.update(new_links)
            
            urls_to_process.update(new_urls)
        
        print(f"\n  TOTAL DISCOVERED: {len(discovered_urls)} URLs")
        return discovered_urls
    
    def extract_links_from_content(self, content: str, base_domain: str, base_url: str) -> Set[str]:
        """Extract internal links from content with improved parsing"""
        # Clean href pattern - only standard quoted hrefs
        href_pattern = r'href=["\']([^"\']+)["\']'
        links = re.findall(href_pattern, content, re.IGNORECASE)
        
        internal_links = set()
        base_url_clean = base_url.rstrip('/')
        
        for link in links:
            # Skip non-relevant links
            if any(link.startswith(prefix) for prefix in ['#', 'mailto:', 'tel:', 'javascript:', 'data:', 'ftp:']):
                continue
            
            # Skip external domains early (before processing)  
            if link.startswith(('http://', 'https://')) and base_domain not in link.lower():
                continue
            
            # Process relative URLs
            if link.startswith('/'):
                # Absolute path relative to domain
                clean_link = base_url_clean + link
            elif link.startswith(('http://', 'https://')):
                # Full URL - just clean it
                clean_link = link
            else:
                # Relative path - skip complex ones for now
                if any(char in link for char in ['?', '#', 'javascript']):
                    continue
                if not any(char in link for char in ['.', '/']):
                    continue
                clean_link = base_url_clean + '/' + link.lstrip('/')
            
            # Final validation
            if base_domain in clean_link.lower():
                # Clean up the URL
                clean_link = clean_link.split('#')[0]  # Remove anchors
                clean_link = clean_link.split('?')[0]  # Remove query params
                clean_link = clean_link.rstrip('/')    # Remove trailing slash
                
                # Skip obvious non-content URLs
                if any(ext in clean_link.lower() for ext in ['.css', '.js', '.png', '.jpg', '.gif', '.ico', '.svg', '.pdf', '.xml']):
                    continue
                
                # Normalize www vs non-www
                clean_link = clean_link.replace('://www.', '://').replace(f'://{base_domain}', f'://www.{base_domain}')
                
                internal_links.add(clean_link)
        
        return internal_links
    
    def prioritize_discovered_pages(self, urls: Set[str]) -> List[str]:
        """Prioritize pages for content extraction"""
        print(f"\n=== PRIORITIZING PAGES ===")
        
        priority_keywords = [
            # Highest priority
            ['about-us', 'about_us', 'aboutus', 'about'],
            ['about-me', 'about_me', 'aboutme'],  
            ['about-company', 'about-the-company', 'company-info', 'company'],
            ['our-story', 'our_story', 'story'],
            ['team', 'leadership', 'founders'],
            ['approach', 'methodology', 'process'],
            ['mission', 'values', 'culture'],
            ['history', 'background'],
            # Medium priority  
            ['services', 'what-we-do', 'what_we_do'],
            ['portfolio', 'work', 'case-studies'],
            # Lower priority
            ['home', 'homepage', 'index'],
        ]
        
        prioritized_pages = []
        used_pages = set()
        
        print(f"Analyzing {len(urls)} URLs:")
        for url in sorted(urls):
            print(f"  {url}")
        
        # Sort by priority keywords
        for i, keyword_group in enumerate(priority_keywords):
            print(f"\nPriority level {i+1}: {keyword_group}")
            
            for url in urls:
                if url in used_pages:
                    continue
                    
                url_path = urllib.parse.urlparse(url).path.lower()
                
                for keyword in keyword_group:
                    if keyword in url_path:
                        prioritized_pages.append(url)
                        used_pages.add(url)
                        print(f"  MATCHED: {url} (keyword: {keyword})")
                        break
                        
                if len(prioritized_pages) >= 10:  # Limit to top pages
                    break
            
            if len(prioritized_pages) >= 10:
                break
        
        # Add homepage if not included
        base_urls = [url for url in urls if urllib.parse.urlparse(url).path in ['/', '']]
        for base_url in base_urls:
            if base_url not in used_pages and len(prioritized_pages) < 10:
                prioritized_pages.insert(0, base_url)
                print(f"  ADDED HOMEPAGE: {base_url}")
        
        print(f"\nFINAL PRIORITIZED LIST ({len(prioritized_pages)} pages):")
        for i, url in enumerate(prioritized_pages[:8], 1):
            print(f"  {i}. {url}")
        
        return prioritized_pages[:8]
    
    def test_domain(self, domain: str):
        """Test complete page discovery for domain"""
        print(f"\n{'='*60}")
        print(f"TESTING DOMAIN: {domain}")
        print(f"{'='*60}")
        
        all_discovered_urls = set()
        
        # Test sitemap discovery
        sitemap_urls = self.test_sitemap_discovery(domain)
        if sitemap_urls:
            all_discovered_urls.update(sitemap_urls)
            print(f"\nSitemap discovery found: {len(sitemap_urls)} URLs")
        
        # Test internal link extraction
        crawled_urls = self.test_internal_link_extraction(domain, max_depth=2)
        if crawled_urls:
            all_discovered_urls.update(crawled_urls)
            print(f"\nInternal crawling found: {len(crawled_urls)} URLs")
        
        print(f"\nTOTAL UNIQUE URLS DISCOVERED: {len(all_discovered_urls)}")
        
        if all_discovered_urls:
            # Prioritize pages
            prioritized = self.prioritize_discovered_pages(all_discovered_urls)
            
            print(f"\n{'='*40}")
            print(f"FINAL RECOMMENDATION:")
            print(f"Process these {len(prioritized)} pages for content extraction")
            print(f"{'='*40}")

def main():
    """Test with stryvemarketing.com"""
    tester = PageDiscoveryTester()
    
    # Test the problematic domain
    tester.test_domain("stryvemarketing.com")

if __name__ == "__main__":
    main()