#!/usr/bin/env python3
"""
Debug internal links extraction
"""

import re
import urllib.request
import ssl

def debug_link_extraction():
    """Debug what's happening in link extraction"""
    
    # Setup
    url = "https://stryvemarketing.com"
    domain = "stryvemarketing.com"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    print(f"Fetching: {url}")
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=ssl_context) as response:
            content = response.read().decode('utf-8')
        
        print(f"Content length: {len(content)} chars")
        print(f"First 500 chars:\n{content[:500]}")
        
        # Extract all hrefs
        href_pattern = r'href=["\']([^"\']+)["\']'
        all_links = re.findall(href_pattern, content, re.IGNORECASE)
        
        print(f"\nFound {len(all_links)} href attributes total")
        
        # Show first 10 raw hrefs
        print("\nFirst 10 raw hrefs:")
        for i, link in enumerate(all_links[:10], 1):
            print(f"  {i}. {link}")
        
        # Filter process step by step
        base_domain = domain.lower().replace('www.', '')
        base_url_clean = url.rstrip('/')
        internal_links = []
        
        print(f"\nBase domain: {base_domain}")
        print(f"Base URL clean: {base_url_clean}")
        
        skip_counts = {
            'anchors_etc': 0,
            'external': 0,
            'processed': 0,
            'not_internal': 0,
            'extensions': 0,
            'final': 0
        }
        
        for i, link in enumerate(all_links):
            if i >= 20:  # Only debug first 20 links
                break
                
            print(f"\n--- Link {i+1}: '{link}' ---")
            
            # Skip non-relevant links
            if any(link.startswith(prefix) for prefix in ['#', 'mailto:', 'tel:', 'javascript:', 'data:', 'ftp:']):
                print(f"  SKIP: anchor/mailto/etc")
                skip_counts['anchors_etc'] += 1
                continue
            
            # Skip external domains early (before processing)  
            if link.startswith(('http://', 'https://')) and base_domain not in link.lower():
                print(f"  SKIP: external domain")
                skip_counts['external'] += 1
                continue
            
            # Process relative URLs
            if link.startswith('/'):
                clean_link = base_url_clean + link
                print(f"  PROCESSED: relative -> {clean_link}")
            elif link.startswith(('http://', 'https://')):
                clean_link = link
                print(f"  PROCESSED: absolute -> {clean_link}")
            else:
                # Relative path - skip complex ones for now
                if any(char in link for char in ['?', '#', 'javascript']):
                    print(f"  SKIP: complex relative")
                    continue
                if not any(char in link for char in ['.', '/']):
                    print(f"  SKIP: simple text")
                    continue
                clean_link = base_url_clean + '/' + link.lstrip('/')
                print(f"  PROCESSED: relative path -> {clean_link}")
            
            skip_counts['processed'] += 1
            
            # Final validation
            if base_domain not in clean_link.lower():
                print(f"  REJECT: not internal domain")
                skip_counts['not_internal'] += 1
                continue
            
            # Clean up the URL
            clean_link = clean_link.split('#')[0]  # Remove anchors
            clean_link = clean_link.split('?')[0]  # Remove query params
            clean_link = clean_link.rstrip('/')    # Remove trailing slash
            
            print(f"  CLEANED: -> {clean_link}")
            
            # Skip obvious non-content URLs
            if any(ext in clean_link.lower() for ext in ['.css', '.js', '.png', '.jpg', '.gif', '.ico', '.svg', '.pdf', '.xml']):
                print(f"  REJECT: file extension")
                skip_counts['extensions'] += 1
                continue
            
            # Normalize www vs non-www
            clean_link = clean_link.replace('://www.', '://').replace(f'://{base_domain}', f'://www.{base_domain}')
            print(f"  FINAL: -> {clean_link}")
            
            internal_links.append(clean_link)
            skip_counts['final'] += 1
        
        print(f"\n=== SUMMARY ===")
        print(f"Total hrefs found: {len(all_links)}")
        print(f"Skipped anchors/mailto/etc: {skip_counts['anchors_etc']}")
        print(f"Skipped external: {skip_counts['external']}")
        print(f"Processed: {skip_counts['processed']}")
        print(f"Rejected not internal: {skip_counts['not_internal']}")
        print(f"Rejected extensions: {skip_counts['extensions']}")
        print(f"Final internal links: {skip_counts['final']}")
        
        print(f"\nFinal unique internal links ({len(set(internal_links))}):")
        for link in sorted(set(internal_links)):
            print(f"  - {link}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_link_extraction()