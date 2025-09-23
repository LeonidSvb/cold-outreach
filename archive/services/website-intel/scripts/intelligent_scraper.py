#!/usr/bin/env python3
"""
=== INTELLIGENT WEBSITE SCRAPER ===
Version: 1.0.0 | Created: 2025-09-08

PURPOSE: 
Complete intelligent scraping pipeline: Discovery → AI Prioritization → Selective Content Extraction

IMPROVEMENTS:
- 2025-09-08: Combined page discovery + AI prioritization ✅
- 2025-09-08: Selective scraping based on AI classification ✅
- 2025-09-08: Full automation with dialogue-style prompting ✅

WHAT THIS DOES:
1. Discovers all pages from domain (using content_extractor)
2. Uses AI to prioritize pages for outreach intelligence
3. Scrapes only high/medium priority pages
4. Saves both prioritization results and extracted content

USAGE:
python intelligent_scraper.py stryvemarketing.com       # Single domain
python intelligent_scraper.py domains.csv 5            # Batch from CSV
"""

import json
import os
import sys
import time
from datetime import datetime
from content_extractor import ContentExtractor, load_domains_from_csv
from page_prioritizer import PagePrioritizer, load_api_key

# Self-documenting statistics
SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "domains_processed": 0,
    "pages_discovered": 0,
    "pages_prioritized": 0,
    "pages_scraped": 0,
    "success_rate": 0,
    "last_updated": "2025-09-08",
    "last_run": None
}

class IntelligentScraper:
    """Complete intelligent scraping pipeline"""
    
    def __init__(self, openai_api_key):
        self.content_extractor = ContentExtractor()
        self.page_prioritizer = PagePrioritizer(openai_api_key)
        
    def extract_page_titles(self, domain, discovered_pages):
        """Extract titles from discovered pages for AI prioritization"""
        print(f"  Extracting titles from {len(discovered_pages)} pages...")
        
        pages_with_titles = []
        processed = 0
        
        for url in list(discovered_pages)[:20]:  # Limit to first 20 for title extraction
            try:
                # Use content extractor's make_request method to get HTML
                html_content = self.content_extractor.make_request(url)
                if html_content:
                    # Extract title from HTML
                    title_start = html_content.lower().find('<title>')
                    title_end = html_content.lower().find('</title>')
                    if title_start != -1 and title_end != -1:
                        title = html_content[title_start + 7:title_end].strip()
                        title = ' '.join(title.split())  # Clean whitespace
                    else:
                        title = "No title"
                    
                    pages_with_titles.append({
                        "url": url,
                        "title": title
                    })
                    processed += 1
                    
                    if processed % 5 == 0:
                        print(f"    Extracted {processed} titles...")
                        
            except Exception as e:
                # Add without title if extraction fails
                pages_with_titles.append({
                    "url": url,
                    "title": "No title"
                })
                
        print(f"  Extracted {len(pages_with_titles)} page titles")
        return pages_with_titles
    
    def process_domain(self, domain_info):
        """Complete intelligent processing for single domain"""
        domain = domain_info['domain'] if isinstance(domain_info, dict) else domain_info
        company_name = domain_info.get('company_name', domain) if isinstance(domain_info, dict) else domain
        
        print(f"\n=== PROCESSING: {domain} ===")
        
        start_time = time.time()
        
        try:
            # Step 1: Discover pages
            print("STEP 1: Discovering pages...")
            discovered_pages = self.content_extractor.discover_pages(domain)
            
            if not discovered_pages:
                return {
                    'domain': domain,
                    'success': False,
                    'error': 'No pages discovered',
                    'pages_discovered': 0,
                    'pages_prioritized': 0,
                    'pages_scraped': 0
                }
            
            print(f"  Found {len(discovered_pages)} pages")
            
            # Step 2: Extract titles for AI prioritization  
            print("STEP 2: Extracting page titles...")
            pages_with_titles = self.extract_page_titles(domain, discovered_pages)
            
            # Step 3: AI Prioritization
            print("STEP 3: AI prioritization...")
            prioritization = self.page_prioritizer.classify_pages(pages_with_titles)
            
            if not prioritization:
                return {
                    'domain': domain,
                    'success': False,
                    'error': 'AI prioritization failed',
                    'pages_discovered': len(discovered_pages),
                    'pages_prioritized': 0,
                    'pages_scraped': 0
                }
            
            # Step 4: Selective content extraction
            print("STEP 4: Extracting content from priority pages...")
            
            # Combine high and medium priority pages
            priority_pages = prioritization['high_priority'] + prioritization['medium_priority']
            
            print(f"  Scraping {len(priority_pages)} priority pages...")
            
            extracted_content = {}
            scraped_count = 0
            
            for url in priority_pages[:10]:  # Limit to 10 pages max
                try:
                    # Extract content using content extractor
                    content = self.content_extractor.extract_page_content(url)
                    if content:
                        # Extract title as well
                        html_content = self.content_extractor.make_request(url)
                        title = "No title"
                        if html_content:
                            title_start = html_content.lower().find('<title>')
                            title_end = html_content.lower().find('</title>')
                            if title_start != -1 and title_end != -1:
                                title = html_content[title_start + 7:title_end].strip()
                                title = ' '.join(title.split())
                        
                        extracted_content[url] = {
                            'title': title,
                            'content': content,
                            'word_count': len(content.split()) if content else 0,
                            'fetched_at': datetime.now().isoformat(),
                        }
                        scraped_count += 1
                        print(f"    Scraped: {url}")
                        
                except Exception as e:
                    print(f"    Error scraping {url}: {e}")
                    
            processing_time = time.time() - start_time
            
            # Build final result
            result = {
                'domain': domain,
                'company_name': company_name,
                'success': True,
                'processed_at': datetime.now().isoformat(),
                'processing_time': round(processing_time, 1),
                'pages_discovered': len(discovered_pages),
                'pages_prioritized': len(pages_with_titles),
                'pages_scraped': scraped_count,
                'prioritization': prioritization,
                'content': extracted_content,
                'stats': {
                    'high_priority': len(prioritization['high_priority']),
                    'medium_priority': len(prioritization['medium_priority']),
                    'low_priority': len(prioritization['low_priority']),
                    'skipped': len(prioritization['skip'])
                }
            }
            
            # Update global stats
            global SCRIPT_STATS
            SCRIPT_STATS["domains_processed"] += 1
            SCRIPT_STATS["pages_discovered"] += len(discovered_pages)
            SCRIPT_STATS["pages_prioritized"] += len(pages_with_titles)
            SCRIPT_STATS["pages_scraped"] += scraped_count
            
            return result
            
        except Exception as e:
            return {
                'domain': domain,
                'success': False,
                'error': str(e),
                'pages_discovered': 0,
                'pages_prioritized': 0,
                'pages_scraped': 0
            }
    
    def save_results(self, results, filename_suffix="intelligent"):
        """Save intelligent scraping results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"intelligent_{filename_suffix}_{timestamp}.json"
        
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'intelligent')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, filename)
        
        # Calculate success rate
        if SCRIPT_STATS["domains_processed"] > 0:
            successful = len([r for r in results if r['success']])
            SCRIPT_STATS["success_rate"] = round((successful / len(results)) * 100, 1)
        
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()
        
        # Include stats in output
        full_results = {
            "results": results,
            "script_stats": SCRIPT_STATS,
            "summary": {
                "total_domains": len(results),
                "successful": len([r for r in results if r['success']]),
                "failed": len([r for r in results if not r['success']]),
                "total_pages_discovered": sum(r.get('pages_discovered', 0) for r in results),
                "total_pages_scraped": sum(r.get('pages_scraped', 0) for r in results),
                "avg_pages_per_domain": round(sum(r.get('pages_discovered', 0) for r in results) / len(results), 1) if results else 0
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(full_results, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved: {filename}")
        return output_path

def main():
    """Main execution function"""
    
    print("=== INTELLIGENT WEBSITE SCRAPER ===")
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return
    
    # Initialize intelligent scraper
    try:
        scraper = IntelligentScraper(api_key)
    except Exception as e:
        print(f"Error initializing scraper: {e}")
        return
    
    # Determine input
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python intelligent_scraper.py domain.com")
        print("  python intelligent_scraper.py domains.csv 5")
        return
    
    input_arg = sys.argv[1]
    
    if input_arg.endswith('.csv'):
        # Batch processing from CSV
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        print(f"Processing {batch_size} domains from CSV...")
        
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'leads', input_arg)
        domains = load_domains_from_csv(csv_path, limit=batch_size)
        
        if not domains:
            print(f"No domains found in {input_arg}")
            return
            
    else:
        # Single domain processing
        domain = input_arg.replace('https://', '').replace('http://', '').replace('www.', '')
        domains = [{'domain': domain, 'company_name': domain}]
        print(f"Processing single domain: {domain}")
    
    # Process domains
    results = []
    total_start_time = time.time()
    
    for i, domain_info in enumerate(domains, 1):
        print(f"\n[{i}/{len(domains)}] Starting domain: {domain_info['domain']}")
        result = scraper.process_domain(domain_info)
        results.append(result)
        
        # Show progress
        if result['success']:
            print(f"  [SUCCESS] {result['pages_scraped']}/{result['pages_discovered']} pages scraped in {result['processing_time']}s")
        else:
            print(f"  [FAILED] {result.get('error', 'Unknown error')}")
    
    total_time = time.time() - total_start_time
    
    # Save results
    scraper.save_results(results, f"{len(domains)}_domains")
    
    # Print summary
    successful = len([r for r in results if r['success']])
    failed = len(results) - successful
    total_discovered = sum(r.get('pages_discovered', 0) for r in results)
    total_scraped = sum(r.get('pages_scraped', 0) for r in results)
    
    print(f"\n=== INTELLIGENT SCRAPING SUMMARY ===")
    print(f"Domains processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total pages discovered: {total_discovered}")
    print(f"Total pages scraped: {total_scraped}")
    print(f"Processing time: {total_time:.1f}s")
    print(f"Average per domain: {total_time/len(results):.1f}s")
    
    if successful > 0:
        print(f"\n[SUCCESS] Intelligent scraping completed!")
    else:
        print(f"\n[FAILED] No domains processed successfully")

if __name__ == "__main__":
    main()