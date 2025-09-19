#!/usr/bin/env python3
"""
=== WEBSITE CONTENT EXTRACTOR ===
Version: 1.0.0 | Created: 2025-09-08

PURPOSE: 
Extract raw content from company websites for cold outreach personalization

RECENT CHANGES:
- 2025-09-08: Initial version with multi-level page discovery ✅
- 2025-09-08: Self-documenting architecture implemented ✅
- 2025-09-08: Separating content extraction from AI analysis ✅

CURRENT STATS:
- Total runs: 0
- Success rate: 0%
- Average pages per domain: 0
- Average processing time: 0 seconds

KNOWN LIMITATIONS:
- Some WordPress sites may block automated requests
- JavaScript-heavy sites may miss content
- Large sites (1000+ pages) may timeout

WHAT THIS SCRIPT DOES:
1. Takes domain from CSV or single domain
2. Discovers internal pages (about, services, etc.)
3. Extracts clean text content from priority pages
4. Saves raw content to JSON (NO AI analysis)
5. Updates its own stats and documentation

USAGE:
python content_extractor.py                    # Process 5 test domains
python content_extractor.py domain.com         # Single domain
python content_extractor.py --csv file.csv     # Full CSV file

OUTPUT:
- Raw content JSON files in outputs/raw/
- Updated stats in this script file
"""

import csv
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from typing import Dict, List, Set

# === SCRIPT STATS (AUTO-UPDATED) ===
SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "total_domains_processed": 0,
    "successful_extractions": 0,
    "failed_extractions": 0,
    "total_pages_found": 0,
    "total_pages_processed": 0,
    "last_run": None,
    "average_pages_per_domain": 0.0,
    "success_rate": 0.0,
    "last_updated": "2025-09-08"
}

# === RUN HISTORY ===
RUN_HISTORY = []

class HTMLContentExtractor(HTMLParser):
    """Extract clean text content from HTML"""
    
    def __init__(self):
        super().__init__()
        self.text_content = []
        self.ignore_tags = {'script', 'style', 'meta', 'link', 'noscript', 'nav', 'footer', 'header'}
        self.ignore_content = False
        
    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.ignore_tags:
            self.ignore_content = True
    
    def handle_endtag(self, tag):
        if tag.lower() in self.ignore_tags:
            self.ignore_content = False
    
    def handle_data(self, data):
        if not self.ignore_content and data.strip():
            cleaned = ' '.join(data.split())
            if cleaned:
                self.text_content.append(cleaned)
    
    def get_text(self) -> str:
        return ' '.join(self.text_content)

class ContentExtractor:
    """Main content extraction class"""
    
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
        """Normalize URL to ensure proper format"""
        if not url:
            return ""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def make_request(self, url: str, timeout: int = 10) -> str:
        """Make HTTP request with error handling"""
        try:
            normalized_url = self.normalize_url(url)
            req = urllib.request.Request(normalized_url, headers=self.headers)
            
            with urllib.request.urlopen(req, timeout=timeout, context=self.ssl_context) as response:
                content = response.read()
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    content = content.decode('utf-8', errors='ignore')
                return content
        except Exception as e:
            print(f"  Request failed: {e}")
            return ""
    
    def extract_internal_links(self, url: str, domain: str) -> List[str]:
        """Extract internal links from a page"""
        content = self.make_request(url)
        if not content:
            return []
        
        href_pattern = r'href=["\']([^"\']+)["\']'
        all_links = re.findall(href_pattern, content, re.IGNORECASE)
        
        internal_links = []
        base_domain = domain.lower().replace('www.', '')
        base_url_clean = self.normalize_url(domain).rstrip('/')
        
        for link in all_links:
            # Skip non-relevant links
            if any(link.startswith(prefix) for prefix in ['#', 'mailto:', 'tel:', 'javascript:', 'data:', 'ftp:']):
                continue
            
            # Skip external domains
            if link.startswith(('http://', 'https://')) and base_domain not in link.lower():
                continue
            
            # Process relative URLs
            if link.startswith('//'):
                if base_domain not in link.lower():
                    continue
                clean_link = 'https:' + link
            elif link.startswith('/'):
                clean_link = base_url_clean + link
            elif link.startswith(('http://', 'https://')):
                clean_link = link
            else:
                if any(char in link for char in ['?', '#', 'javascript']):
                    continue
                if not any(char in link for char in ['.', '/']):
                    continue
                clean_link = base_url_clean + '/' + link.lstrip('/')
            
            # Final validation and cleaning
            if base_domain in clean_link.lower():
                clean_link = clean_link.split('#')[0].split('?')[0].rstrip('/')
                
                # Skip non-content URLs
                if any(ext in clean_link.lower() for ext in ['.css', '.js', '.png', '.jpg', '.gif', '.ico', '.svg', '.pdf', '.xml']):
                    continue
                if any(path in clean_link.lower() for path in ['wp-json', 'xmlrpc', 'platform-api']):
                    continue
                
                # Normalize www
                if '//www.' not in clean_link:
                    clean_link = clean_link.replace(f'://{base_domain}', f'://www.{base_domain}')
                
                internal_links.append(clean_link)
        
        return list(set(internal_links))
    
    def discover_pages(self, domain: str) -> Set[str]:
        """Discover pages through multi-level crawling"""
        base_url = self.normalize_url(domain)
        discovered_urls = set([base_url])
        urls_to_process = set([base_url])
        processed_urls = set()
        
        # Crawl up to 2 levels deep
        for depth in range(2):
            current_batch = urls_to_process - processed_urls
            if not current_batch:
                break
                
            new_urls = set()
            for url in list(current_batch)[:5]:  # Process max 5 URLs per depth
                if url in processed_urls:
                    continue
                    
                links = self.extract_internal_links(url, domain)
                new_links = set(links) - discovered_urls
                
                new_urls.update(new_links)
                discovered_urls.update(new_links)
                processed_urls.add(url)
                
                time.sleep(0.5)  # Be respectful
            
            urls_to_process.update(new_urls)
        
        return discovered_urls
    
    def prioritize_pages(self, pages: Set[str]) -> List[str]:
        """Prioritize pages for content extraction"""
        priority_keywords = [
            ['about-us', 'about_us', 'aboutus', 'about'],
            ['about-me', 'about_me', 'aboutme'],  
            ['approach', 'methodology', 'process'],
            ['our-story', 'our_story', 'story'],
            ['team', 'leadership', 'founders'],
            ['company', 'company-info'],
            ['services', 'what-we-do'],
            ['mission', 'values', 'culture'],
            ['careers', 'jobs', 'work-with-us']
        ]
        
        prioritized_pages = []
        used_pages = set()
        
        for keyword_group in priority_keywords:
            for page in pages:
                if page in used_pages:
                    continue
                    
                page_path = urllib.parse.urlparse(page).path.lower()
                for keyword in keyword_group:
                    if keyword in page_path:
                        prioritized_pages.append(page)
                        used_pages.add(page)
                        break
                        
                if len(prioritized_pages) >= 8:
                    break
        
        # Add homepage if not included
        for page in pages:
            if urllib.parse.urlparse(page).path in ['/', ''] and page not in used_pages:
                prioritized_pages.insert(0, page)
                break
        
        return prioritized_pages[:5]  # Return top 5
    
    def extract_page_content(self, url: str) -> str:
        """Extract clean text content from a page"""
        content = self.make_request(url)
        if not content:
            return ""
        
        parser = HTMLContentExtractor()
        parser.feed(content)
        text_content = parser.get_text()
        
        # Additional cleaning
        text_content = ' '.join(text_content.split())
        return text_content.strip()
    
    def process_domain(self, domain: str, company_name: str = "") -> Dict:
        """Process a single domain"""
        print(f"Processing: {domain}")
        start_time = time.time()
        
        result = {
            'domain': domain,
            'company_name': company_name,
            'processed_at': datetime.now().isoformat(),
            'success': False,
            'pages_found': 0,
            'pages_processed': 0,
            'content': {},
            'errors': []
        }
        
        try:
            # Step 1: Discover pages
            print(f"  Discovering pages...")
            pages = self.discover_pages(domain)
            result['pages_found'] = len(pages)
            print(f"  Found {len(pages)} pages")
            
            if not pages:
                result['errors'].append("No pages discovered")
                return result
            
            # Step 2: Prioritize pages
            priority_pages = self.prioritize_pages(pages)
            print(f"  Processing {len(priority_pages)} priority pages:")
            for page in priority_pages:
                print(f"    - {page}")
            
            # Step 3: Extract content from priority pages
            for page in priority_pages:
                print(f"    Extracting: {page}")
                content = self.extract_page_content(page)
                if content:
                    result['content'][page] = content
                    result['pages_processed'] += 1
                time.sleep(1)  # Be respectful
            
            if result['pages_processed'] > 0:
                result['success'] = True
                processing_time = time.time() - start_time
                print(f"  SUCCESS: {result['pages_processed']} pages processed in {processing_time:.1f}s")
            else:
                result['errors'].append("No content extracted")
                print(f"  FAILED: No content extracted")
            
        except Exception as e:
            error_msg = f"Processing failed: {e}"
            result['errors'].append(error_msg)
            print(f"  ERROR: {error_msg}")
        
        return result
    
    def save_raw_content(self, result: Dict):
        """Save raw content to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain_safe = result['domain'].replace('/', '_').replace(':', '_')
        filename = f"raw_content_{domain_safe}_{timestamp}.json"
        
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'raw')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved: {output_path}")
        return output_path

def load_domains_from_csv(csv_path: str, limit: int = None) -> List[Dict]:
    """Load domains from CSV file"""
    domains = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader):
                if limit and i >= limit:
                    break
                
                domain = row.get('company_domain', '').strip()
                if domain and domain != '':
                    domains.append({
                        'domain': domain,
                        'company_name': row.get('company_name', '').strip()
                    })
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return domains

def update_script_stats(results: List[Dict]):
    """Update script statistics after each run"""
    global SCRIPT_STATS, RUN_HISTORY
    
    # Update counters
    SCRIPT_STATS["total_runs"] += 1
    SCRIPT_STATS["total_domains_processed"] += len(results)
    SCRIPT_STATS["last_run"] = datetime.now().isoformat()
    SCRIPT_STATS["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    
    # Count successes and failures
    successful = len([r for r in results if r['success']])
    failed = len([r for r in results if not r['success']])
    
    SCRIPT_STATS["successful_extractions"] += successful
    SCRIPT_STATS["failed_extractions"] += failed
    
    # Count pages
    total_pages_found = sum(r['pages_found'] for r in results)
    total_pages_processed = sum(r['pages_processed'] for r in results)
    
    SCRIPT_STATS["total_pages_found"] += total_pages_found
    SCRIPT_STATS["total_pages_processed"] += total_pages_processed
    
    # Calculate rates
    if SCRIPT_STATS["total_domains_processed"] > 0:
        SCRIPT_STATS["success_rate"] = round(
            (SCRIPT_STATS["successful_extractions"] / SCRIPT_STATS["total_domains_processed"]) * 100, 1
        )
        SCRIPT_STATS["average_pages_per_domain"] = round(
            SCRIPT_STATS["total_pages_found"] / SCRIPT_STATS["total_domains_processed"], 1
        )
    
    # Add to run history
    run_summary = {
        "timestamp": datetime.now().isoformat(),
        "domains_processed": len(results),
        "successful": successful,
        "failed": failed,
        "total_pages_found": total_pages_found,
        "total_pages_processed": total_pages_processed
    }
    RUN_HISTORY.append(run_summary)
    
    # Keep only last 10 runs
    if len(RUN_HISTORY) > 10:
        RUN_HISTORY = RUN_HISTORY[-10:]
    
    print(f"\n=== SCRIPT STATS UPDATED ===")
    print(f"Total runs: {SCRIPT_STATS['total_runs']}")
    print(f"Success rate: {SCRIPT_STATS['success_rate']}%")
    print(f"Average pages per domain: {SCRIPT_STATS['average_pages_per_domain']}")

def main():
    """Main execution function"""
    extractor = ContentExtractor()
    
    # Determine what to process
    if len(sys.argv) > 1:
        if sys.argv[1] == "--csv" and len(sys.argv) > 2:
            # Process full CSV
            csv_path = sys.argv[2]
            domains = load_domains_from_csv(csv_path)
            print(f"Processing {len(domains)} domains from CSV...")
        elif sys.argv[1].endswith('.csv'):
            # Process CSV with default limit of 10
            domains = load_domains_from_csv(sys.argv[1], limit=10)
            print(f"Processing first {len(domains)} domains from CSV...")
        else:
            # Single domain
            domains = [{'domain': sys.argv[1], 'company_name': ''}]
            print(f"Processing single domain: {sys.argv[1]}")
    else:
        # Default: process first 5 domains from test CSV
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'leads', 'Lumid - verification - Canada.csv')
        domains = load_domains_from_csv(csv_path, limit=5)
        print(f"Processing first 5 test domains from CSV...")
    
    if not domains:
        print("No domains to process!")
        return
    
    # Process domains
    results = []
    for i, domain_info in enumerate(domains, 1):
        print(f"\n--- Processing {i}/{len(domains)} ---")
        result = extractor.process_domain(domain_info['domain'], domain_info['company_name'])
        results.append(result)
        
        # Save raw content
        if result['success']:
            extractor.save_raw_content(result)
    
    # Update script stats
    update_script_stats(results)
    
    # Print summary
    print(f"\n=== SUMMARY ===")
    successful = len([r for r in results if r['success']])
    print(f"Processed: {len(results)} domains")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    print(f"Total pages found: {sum(r['pages_found'] for r in results)}")
    print(f"Total pages processed: {sum(r['pages_processed'] for r in results)}")

if __name__ == "__main__":
    main()

# === AUTO-UPDATED STATS SECTION ===
# This section is automatically updated by the script
# Last updated: 2025-09-08
# 
# PERFORMANCE METRICS:
# - Script has been run 0 times
# - Total domains processed: 0
# - Success rate: 0%
# - Average pages per domain: 0
#
# RECENT PERFORMANCE:
# (No runs yet)