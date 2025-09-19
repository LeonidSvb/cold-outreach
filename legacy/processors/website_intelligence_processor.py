#!/usr/bin/env python3
"""
Website Intelligence Processor - Cold Outreach Platform

PURPOSE:
Scrapes all pages from company domains and uses AI to prioritize the most valuable pages 
for B2B outreach intelligence gathering.

FEATURES:
- HTTP-only scraping (no external services)
- Multi-level page discovery with intelligent filtering
- AI-powered page prioritization using OpenAI
- JSON output with all pages and selected priority pages
- Parallel processing for performance
- Self-documenting with embedded analytics

USAGE:
- Input: CSV file with company_domain column
- Output: Adds 'website_intelligence' column with JSON data
- Testing: Use test_website_extraction.py for individual domain testing

REQUIREMENTS:
- OpenAI API key in ../../.env file
- Internet connection for HTTP requests
- Python 3.7+ with built-in libraries only
"""

import os
import sys
import csv
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
import re
from datetime import datetime
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Set, Optional, Tuple

# Script Statistics (Self-Documenting)
SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "total_domains_processed": 0,
    "average_pages_found": 0,
    "average_processing_time": 0,
    "success_rate": 0.0,
    "last_run": None,
    "total_api_cost": 0.0
}

class HTMLLinkExtractor(HTMLParser):
    """Extract all links from HTML content."""
    
    def __init__(self):
        super().__init__()
        self.links = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr_name, attr_value in attrs:
                if attr_name == 'href' and attr_value:
                    self.links.append(attr_value)

class WebsiteIntelligenceProcessor:
    """Main processor for website intelligence gathering."""
    
    def __init__(self):
        self.api_key = self._load_api_key()
        self.session_stats = {
            "domains_processed": 0,
            "total_pages_found": 0,
            "successful_prioritizations": 0,
            "total_api_calls": 0,
            "total_cost": 0.0,
            "start_time": time.time()
        }
        
    def _load_api_key(self) -> str:
        """Load OpenAI API key from environment."""
        env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        if not os.path.exists(env_path):
            raise FileNotFoundError("No .env file found. Please create one with OPENAI_API_KEY.")
            
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    return line.split('=', 1)[1].strip()
        
        raise ValueError("OPENAI_API_KEY not found in .env file")
    
    def _make_http_request(self, url: str, timeout: int = 10) -> Optional[str]:
        """Make HTTP request with proper error handling."""
        try:
            # Create SSL context that handles certificate issues
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            # Create request with headers
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            
            # Make request
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
                if response.status == 200:
                    content = response.read()
                    # Try to decode as UTF-8, fallback to latin-1
                    try:
                        return content.decode('utf-8')
                    except UnicodeDecodeError:
                        return content.decode('latin-1', errors='ignore')
                        
        except Exception as e:
            print(f"ERROR fetching {url}: {str(e)}")
            return None
    
    def _extract_links(self, html_content: str, base_url: str) -> Set[str]:
        """Extract and normalize all links from HTML content."""
        parser = HTMLLinkExtractor()
        try:
            parser.feed(html_content)
        except:
            return set()
            
        links = set()
        base_domain = urllib.parse.urlparse(base_url).netloc.lower()
        
        for link in parser.links:
            try:
                # Skip non-content links
                if any(x in link.lower() for x in ['.css', '.js', '.jpg', '.png', '.gif', '.pdf', 
                                                   '.doc', '.zip', 'mailto:', 'tel:', '#']):
                    continue
                    
                # Resolve relative URLs
                full_url = urllib.parse.urljoin(base_url, link)
                parsed = urllib.parse.urlparse(full_url)
                
                # Only internal links
                if parsed.netloc.lower() == base_domain or not parsed.netloc:
                    # Clean URL
                    clean_url = f"{parsed.scheme}://{base_domain}{parsed.path}"
                    if clean_url.endswith('/'):
                        clean_url = clean_url[:-1]
                    links.add(clean_url)
                    
            except:
                continue
                
        return links
    
    def _discover_pages(self, domain: str, max_pages: int = 50) -> List[str]:
        """Discover all pages on a website."""
        if not domain.startswith(('http://', 'https://')):
            base_url = f"https://{domain}"
        else:
            base_url = domain
            
        discovered = set()
        to_crawl = {base_url}
        crawled = set()
        
        print(f"DISCOVERING pages on {domain}...")
        
        while to_crawl and len(discovered) < max_pages:
            current_batch = list(to_crawl)[:5]  # Process 5 at a time
            to_crawl -= set(current_batch)
            
            for url in current_batch:
                if url in crawled:
                    continue
                    
                crawled.add(url)
                html_content = self._make_http_request(url)
                
                if html_content:
                    discovered.add(url)
                    new_links = self._extract_links(html_content, base_url)
                    
                    # Add new links to crawl queue
                    for link in new_links:
                        if link not in crawled and link not in discovered:
                            to_crawl.add(link)
                            
                    print(f"  Found {len(new_links)} links on {url}")
                    
                if len(discovered) >= max_pages:
                    break
                    
        result = list(discovered)
        print(f"SUCCESS: Discovered {len(result)} pages on {domain}")
        return result
    
    def _prioritize_pages_with_ai(self, pages: List[str], domain: str) -> Dict:
        """Use OpenAI to prioritize pages for outreach intelligence."""
        # Load prompt
        prompt_path = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'page_prioritizer.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()
        
        # Parse prompt into messages
        sections = prompt_content.split('USER:')
        system_msg = sections[0].replace('SYSTEM:', '').strip()
        user_msgs = []
        
        for i in range(1, len(sections)):
            if 'A:' in sections[i]:
                user_part, assistant_part = sections[i].split('A:', 1)
                user_msgs.append(user_part.strip())
                if i == 1:  # Only add assistant response for first example
                    user_msgs.append(assistant_part.strip())
        
        # Build messages array
        messages = [{"role": "system", "content": system_msg}]
        
        # Add conversation history
        for i, msg in enumerate(user_msgs[:-1]):
            role = "user" if i % 2 == 0 else "assistant"
            messages.append({"role": role, "content": msg})
        
        # Add current request
        current_request = f"Here are all the pages found on {domain}:\n\n" + "\n".join(pages)
        messages.append({"role": "user", "content": current_request})
        
        # Make API call
        try:
            print(f"AI: Analyzing {len(pages)} pages for {domain}...")
            
            api_data = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(api_data).encode('utf-8'),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            # Extract and parse response
            content = result['choices'][0]['message']['content'].strip()
            
            # Calculate cost (approximate)
            usage = result.get('usage', {})
            cost = (usage.get('prompt_tokens', 0) * 0.0015 + usage.get('completion_tokens', 0) * 0.002) / 1000
            self.session_stats["total_cost"] += cost
            self.session_stats["total_api_calls"] += 1
            
            # Try to extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                parsed_response = json.loads(json_str)
                
                # Ensure required fields
                result_data = {
                    "all_pages": pages,
                    "selected_pages": parsed_response.get("selected_pages", pages[:3]),
                    "prompt_used": "page_prioritizer.txt",
                    "selection_reasoning": parsed_response.get("selection_reasoning", "AI analysis completed"),
                    "analysis_cost": round(cost, 6),
                    "analysis_date": datetime.now().isoformat()
                }
                
                print(f"SUCCESS: AI selected {len(result_data['selected_pages'])} priority pages (cost: ${cost:.4f})")
                self.session_stats["successful_prioritizations"] += 1
                return result_data
                
        except Exception as e:
            print(f"ERROR: AI prioritization failed for {domain}: {str(e)}")
        
        # Fallback: simple heuristic selection
        priority_keywords = ['about', 'services', 'solutions', 'case-studies', 'portfolio', 'blog', 'news']
        selected = []
        
        for keyword in priority_keywords:
            matching = [p for p in pages if keyword in p.lower()]
            selected.extend(matching[:1])  # Take first match per keyword
            if len(selected) >= 4:
                break
                
        if len(selected) < 2:
            selected = pages[:3]  # Fallback to first 3 pages
            
        return {
            "all_pages": pages,
            "selected_pages": selected[:4],
            "prompt_used": "page_prioritizer.txt (fallback)",
            "selection_reasoning": "Heuristic fallback due to AI error",
            "analysis_cost": 0.0,
            "analysis_date": datetime.now().isoformat()
        }
    
    def process_domain(self, domain: str) -> Optional[Dict]:
        """Process a single domain - discover pages and prioritize."""
        try:
            print(f"\nPROCESSING: {domain}")
            start_time = time.time()
            
            # Discover all pages
            all_pages = self._discover_pages(domain)
            
            if not all_pages:
                print(f"ERROR: No pages found for {domain}")
                return None
                
            self.session_stats["total_pages_found"] += len(all_pages)
            
            # AI prioritization
            intelligence_data = self._prioritize_pages_with_ai(all_pages, domain)
            
            # Add processing metadata
            intelligence_data["processing_time"] = round(time.time() - start_time, 2)
            intelligence_data["total_pages_found"] = len(all_pages)
            
            self.session_stats["domains_processed"] += 1
            
            print(f"SUCCESS: Completed {domain} in {intelligence_data['processing_time']}s")
            return intelligence_data
            
        except Exception as e:
            print(f"ERROR: Failed to process {domain}: {str(e)}")
            return None
    
    def process_csv_file(self, input_file: str, test_limit: int = None) -> str:
        """Process CSV file and add website intelligence column."""
        print(f"PROCESSING CSV file: {input_file}")
        
        # Read input file
        rows = []
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            rows = list(reader)
        
        if 'company_domain' not in headers:
            raise ValueError("CSV must have 'company_domain' column")
        
        # Add new column if not exists
        if 'website_intelligence' not in headers:
            headers = list(headers) + ['website_intelligence']
        
        # Process domains (with test limit)
        domains_to_process = []
        for i, row in enumerate(rows):
            if test_limit and i >= test_limit:
                break
            domain = row.get('company_domain', '').strip()
            if domain and not row.get('website_intelligence'):  # Skip if already processed
                domains_to_process.append((i, domain))
        
        print(f"PROCESSING {len(domains_to_process)} domains...")
        
        # Process with thread pool
        def process_domain_wrapper(domain_info):
            idx, domain = domain_info
            return idx, self.process_domain(domain)
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(process_domain_wrapper, domains_to_process))
        
        # Update rows with results
        for idx, intelligence_data in results:
            if intelligence_data:
                rows[idx]['website_intelligence'] = json.dumps(intelligence_data, ensure_ascii=False)
            else:
                rows[idx]['website_intelligence'] = json.dumps({
                    "error": "Failed to process domain",
                    "analysis_date": datetime.now().isoformat()
                }, ensure_ascii=False)
        
        # Write output file
        output_file = input_file.replace('.csv', '_with_intelligence.csv')
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        
        # Update script stats
        global SCRIPT_STATS
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["total_domains_processed"] += self.session_stats["domains_processed"]
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()
        SCRIPT_STATS["total_api_cost"] += self.session_stats["total_cost"]
        
        if self.session_stats["domains_processed"] > 0:
            SCRIPT_STATS["average_pages_found"] = self.session_stats["total_pages_found"] / self.session_stats["domains_processed"]
            SCRIPT_STATS["average_processing_time"] = (time.time() - self.session_stats["start_time"]) / self.session_stats["domains_processed"]
            SCRIPT_STATS["success_rate"] = self.session_stats["successful_prioritizations"] / self.session_stats["domains_processed"]
        
        return output_file
    
    def get_session_report(self) -> Dict:
        """Generate session performance report."""
        runtime = time.time() - self.session_stats["start_time"]
        return {
            "session_summary": {
                "domains_processed": self.session_stats["domains_processed"],
                "total_pages_found": self.session_stats["total_pages_found"],
                "successful_ai_prioritizations": self.session_stats["successful_prioritizations"],
                "total_api_calls": self.session_stats["total_api_calls"],
                "total_cost": round(self.session_stats["total_cost"], 4),
                "average_pages_per_domain": round(self.session_stats["total_pages_found"] / max(self.session_stats["domains_processed"], 1), 1),
                "success_rate": round(self.session_stats["successful_prioritizations"] / max(self.session_stats["domains_processed"], 1) * 100, 1),
                "total_runtime": round(runtime, 2),
                "average_time_per_domain": round(runtime / max(self.session_stats["domains_processed"], 1), 2)
            },
            "script_stats": SCRIPT_STATS
        }

if __name__ == "__main__":
    processor = WebsiteIntelligenceProcessor()
    
    # Test with 10 domains from the CSV
    input_file = "../../leads/1-raw/Lumid - verification - Canada_cleaned.csv"
    
    try:
        output_file = processor.process_csv_file(input_file, test_limit=10)
        report = processor.get_session_report()
        
        print("\n" + "="*80)
        print("PROCESSING REPORT")
        print("="*80)
        
        session = report["session_summary"]
        print(f"Domains processed: {session['domains_processed']}")
        print(f"Total pages found: {session['total_pages_found']}")
        print(f"Average pages per domain: {session['average_pages_per_domain']}")
        print(f"AI prioritizations successful: {session['successful_ai_prioritizations']}")
        print(f"Success rate: {session['success_rate']}%")
        print(f"Total API cost: ${session['total_cost']}")
        print(f"Total runtime: {session['total_runtime']}s")
        print(f"Average time per domain: {session['average_time_per_domain']}s")
        print(f"Output file: {output_file}")
        
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()