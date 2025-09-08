#!/usr/bin/env python3
"""
Website Intelligence Extractor
Extracts personalization data from company websites for cold outreach campaigns
"""

import csv
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from html.parser import HTMLParser
import ssl

class HTMLContentExtractor(HTMLParser):
    """Extract clean text content from HTML"""
    
    def __init__(self):
        super().__init__()
        self.text_content = []
        self.current_tag = None
        # Tags that should be ignored completely
        self.ignore_tags = {'script', 'style', 'meta', 'link', 'noscript', 'nav', 'footer', 'header'}
        # Track if we're inside an ignored tag
        self.ignore_content = False
        
    def handle_starttag(self, tag, attrs):
        self.current_tag = tag
        if tag.lower() in self.ignore_tags:
            self.ignore_content = True
    
    def handle_endtag(self, tag):
        if tag.lower() in self.ignore_tags:
            self.ignore_content = False
        self.current_tag = None
    
    def handle_data(self, data):
        if not self.ignore_content and data.strip():
            # Clean whitespace and add to content
            cleaned = ' '.join(data.split())
            if cleaned:
                self.text_content.append(cleaned)
    
    def get_text(self) -> str:
        return ' '.join(self.text_content)

class WebsiteIntelligenceExtractor:
    """Main class for extracting website intelligence"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        # Create SSL context that's more permissive
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def load_csv_domains(self, csv_path: str, limit: Optional[int] = None) -> List[Dict]:
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
                            'company_name': row.get('company_name', ''),
                            'row_index': i + 2  # +2 because CSV has header and 0-based index
                        })
        except Exception as e:
            print(f"Error reading CSV: {e}")
        
        return domains
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL to ensure proper format"""
        if not url:
            return ""
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def make_request(self, url: str, timeout: int = 10) -> Optional[Tuple[str, str]]:
        """Make HTTP request with error handling"""
        try:
            normalized_url = self.normalize_url(url)
            req = urllib.request.Request(normalized_url, headers=self.session_headers)
            
            with urllib.request.urlopen(req, timeout=timeout, context=self.ssl_context) as response:
                content = response.read()
                # Try to decode content
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        content = content.decode('latin-1')
                    except UnicodeDecodeError:
                        content = content.decode('utf-8', errors='ignore')
                
                return content, response.geturl()
        
        except Exception as e:
            print(f"Request failed for {url}: {e}")
            return None
    
    def discover_pages(self, domain: str) -> Set[str]:
        """Discover pages on website through sitemap and multi-level crawling"""
        pages = set()
        base_url = self.normalize_url(domain)
        
        # Add base domain
        pages.add(base_url)
        
        # Try to get sitemap first
        sitemap_urls = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemaps.xml"
        ]
        
        for sitemap_url in sitemap_urls:
            sitemap_pages = self.parse_sitemap(sitemap_url)
            if sitemap_pages:
                pages.update(sitemap_pages[:50])  # Limit sitemap pages
                break
        
        # Multi-level crawling for better page discovery
        discovered_urls = set([base_url])
        urls_to_process = set([base_url])
        processed_urls = set()
        
        # Crawl up to 2 levels deep
        for depth in range(2):
            current_batch = urls_to_process - processed_urls
            
            if not current_batch:
                break
                
            new_urls = set()
            
            # Process up to 5 URLs per depth level
            for url in list(current_batch)[:5]:
                if url in processed_urls:
                    continue
                    
                links = self.extract_internal_links(url, domain)
                new_links = set(links) - discovered_urls
                
                new_urls.update(new_links)
                discovered_urls.update(new_links)
                processed_urls.add(url)
                
                # Add small delay to be respectful
                import time
                time.sleep(0.5)
            
            urls_to_process.update(new_urls)
        
        # Combine sitemap and crawled pages
        pages.update(discovered_urls)
        
        return pages
    
    def parse_sitemap(self, sitemap_url: str) -> List[str]:
        """Parse XML sitemap to extract URLs"""
        try:
            content, _ = self.make_request(sitemap_url) or (None, None)
            if not content:
                return []
            
            # Simple regex to extract URLs from sitemap
            url_pattern = r'<loc>(.*?)</loc>'
            urls = re.findall(url_pattern, content, re.IGNORECASE)
            
            # Filter for HTML pages only
            html_urls = []
            for url in urls:
                if not any(ext in url.lower() for ext in ['.xml', '.pdf', '.jpg', '.png', '.gif', '.css', '.js']):
                    html_urls.append(url.strip())
            
            return html_urls
        
        except Exception as e:
            print(f"Sitemap parsing failed for {sitemap_url}: {e}")
            return []
    
    def extract_internal_links(self, url: str, domain: str) -> List[str]:
        """Extract internal links from a page with improved parsing"""
        try:
            content, _ = self.make_request(url) or (None, None)
            if not content:
                return []
            
            # Clean href pattern - only standard quoted hrefs
            href_pattern = r'href=["\']([^"\']+)["\']'
            all_links = re.findall(href_pattern, content, re.IGNORECASE)
            
            internal_links = []
            base_domain = domain.lower().replace('www.', '')
            base_url_clean = self.normalize_url(domain).rstrip('/')
            
            for link in all_links:
                # Skip non-relevant links
                if any(link.startswith(prefix) for prefix in ['#', 'mailto:', 'tel:', 'javascript:', 'data:', 'ftp:']):
                    continue
                
                # Skip external domains early (before processing)  
                if link.startswith(('http://', 'https://')) and base_domain not in link.lower():
                    continue
                
                # Process relative URLs - handle protocol-relative URLs
                if link.startswith('//'):
                    # Protocol-relative URL
                    if base_domain not in link.lower():
                        continue  # Skip if not internal
                    clean_link = 'https:' + link
                elif link.startswith('/'):
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
                    
                    # Skip API endpoints and technical URLs
                    if any(path in clean_link.lower() for path in ['wp-json', 'xmlrpc', 'platform-api']):
                        continue
                    
                    # Normalize www vs non-www - ensure consistent format
                    if '//www.' not in clean_link:
                        clean_link = clean_link.replace(f'://{base_domain}', f'://www.{base_domain}')
                    
                    internal_links.append(clean_link)
            
            return list(set(internal_links))  # Remove duplicates
        
        except Exception as e:
            print(f"Link extraction failed for {url}: {e}")
            return []
    
    def prioritize_pages(self, pages: Set[str], domain: str) -> List[str]:
        """Prioritize pages based on likelihood of containing personalization info"""
        
        # Define priority keywords (order matters - higher priority first)
        priority_keywords = [
            # Highest priority
            ['about-us', 'about_us', 'aboutus'],
            ['about-me', 'about_me', 'aboutme'],  
            ['about-company', 'about-the-company', 'company-info'],
            ['about'],
            ['our-story', 'our_story', 'story'],
            ['team'],
            ['leadership'],
            ['founders'],
            # Medium priority  
            ['company'],
            ['mission'],
            ['values'],
            ['history'],
            ['who-we-are', 'who_we_are'],
            # Lower priority
            ['home', 'homepage'],
            ['services'],
            ['what-we-do', 'what_we_do']
        ]
        
        prioritized_pages = []
        used_pages = set()
        
        # Sort by priority keywords
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
                        
                if len(prioritized_pages) >= 8:  # Limit to top pages
                    break
            
            if len(prioritized_pages) >= 8:
                break
        
        # Add homepage if not already included
        base_url = self.normalize_url(domain)
        if base_url not in used_pages and len(prioritized_pages) < 8:
            prioritized_pages.insert(0, base_url)
        
        return prioritized_pages[:5]  # Return top 5 pages
    
    def extract_page_content(self, url: str) -> Optional[str]:
        """Extract clean text content from a page"""
        try:
            content, _ = self.make_request(url) or (None, None)
            if not content:
                return None
            
            # Parse HTML and extract text
            parser = HTMLContentExtractor()
            parser.feed(content)
            text_content = parser.get_text()
            
            # Additional cleaning
            # Remove extra whitespace
            text_content = ' '.join(text_content.split())
            
            # Remove common navigation/footer text patterns
            clean_patterns = [
                r'Copyright \d{4}.*',
                r'All rights reserved.*',
                r'Privacy Policy.*',
                r'Terms of Service.*',
                r'Cookie Policy.*'
            ]
            
            for pattern in clean_patterns:
                text_content = re.sub(pattern, '', text_content, flags=re.IGNORECASE)
            
            return text_content.strip()
        
        except Exception as e:
            print(f"Content extraction failed for {url}: {e}")
            return None
    
    def extract_personalization_with_openai(self, content: str, company_name: str) -> Dict:
        """Use OpenAI to extract personalization insights from content"""
        
        prompt = f"""
Extract personalization information from this website content for {company_name}. 
Focus on details useful for writing personalized cold email icebreakers.

Content: {content[:4000]}  

Extract and return JSON with these categories:
1. company_focus: Main business focus, services, products
2. company_values: Mission, values, culture, what they care about
3. recent_developments: New initiatives, growth, changes, achievements  
4. team_info: Leadership, team size, key people mentioned
5. industry_insights: Industry they serve, target customers, market position
6. unique_differentiators: What makes them special, competitive advantages
7. pain_points: Challenges they mention facing or solving for clients
8. personality: Company tone, style, personality traits
9. contact_preferences: How they prefer to be contacted (if mentioned)
10. personalization_hooks: Specific details perfect for email personalization

Provide detailed, specific information. Be thorough.
"""

        try:
            import json
            import urllib.request
            import urllib.parse
            
            # Prepare OpenAI API request
            url = "https://api.openai.com/v1/chat/completions"
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an expert at extracting actionable personalization insights from website content for B2B cold outreach. Return detailed JSON with specific, usable information."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.3
            }
            
            # Make request to OpenAI
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={
                    'Authorization': f'Bearer {self.openai_api_key}',
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            ai_content = result['choices'][0]['message']['content']
            
            # Try to parse as JSON, fallback to raw text
            try:
                return json.loads(ai_content)
            except:
                return {"raw_analysis": ai_content}
                
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return {"error": str(e), "fallback_content": content[:500]}
    
    def process_domain(self, domain_info: Dict) -> Dict:
        """Process a single domain and extract intelligence"""
        
        domain = domain_info['domain']
        company_name = domain_info['company_name']
        
        # Handle encoding issues for console output
        try:
            print(f"Processing {domain} ({company_name})...")
        except UnicodeEncodeError:
            print(f"Processing {domain} (company name with special chars)...")
        
        result = {
            'domain': domain,
            'company_name': company_name,
            'processed_at': datetime.now().isoformat(),
            'success': False,
            'pages_found': 0,
            'pages_processed': 0,
            'content_extracted': False,
            'ai_analysis': None,
            'errors': []
        }
        
        try:
            # Step 1: Discover pages
            print(f"  Discovering pages...")
            pages = self.discover_pages(domain)
            result['pages_found'] = len(pages)
            
            if not pages:
                result['errors'].append("No pages discovered")
                return result
            
            # Step 2: Prioritize pages
            print(f"  Prioritizing {len(pages)} pages...")
            priority_pages = self.prioritize_pages(pages, domain)
            
            # Step 3: Extract content from priority pages
            all_content = []
            for page in priority_pages:
                print(f"    Extracting content from {page}")
                content = self.extract_page_content(page)
                if content:
                    all_content.append(content)
                    result['pages_processed'] += 1
                
                time.sleep(1)  # Be respectful with requests
            
            if not all_content:
                result['errors'].append("No content extracted from any pages")
                return result
            
            # Step 4: Combine content
            combined_content = ' '.join(all_content)
            result['content_extracted'] = True
            
            # Step 5: Get AI analysis
            print(f"  Analyzing content with OpenAI...")
            ai_analysis = self.extract_personalization_with_openai(combined_content, company_name)
            result['ai_analysis'] = ai_analysis
            
            result['success'] = True
            print(f"  [SUCCESS] Successfully processed {domain}")
            
        except Exception as e:
            error_msg = f"Processing failed for {domain}: {e}"
            print(f"  [ERROR] {error_msg}")
            result['errors'].append(error_msg)
        
        return result
    
    def process_batch(self, csv_path: str, batch_size: int = 10, start_index: int = 0) -> List[Dict]:
        """Process a batch of domains from CSV"""
        
        print(f"Loading domains from {csv_path}...")
        
        # Load all domains first
        all_domains = self.load_csv_domains(csv_path)
        
        # Get the batch to process
        end_index = min(start_index + batch_size, len(all_domains))
        domains_batch = all_domains[start_index:end_index]
        
        print(f"Processing batch: domains {start_index+1}-{end_index} of {len(all_domains)} total")
        
        results = []
        
        for i, domain_info in enumerate(domains_batch):
            print(f"\n--- Processing {i+1}/{len(domains_batch)} ---")
            
            result = self.process_domain(domain_info)
            results.append(result)
            
            # Save progress after each domain
            self.save_results(results, f"batch_{start_index+1}_{end_index}")
            
            # Brief pause between domains
            time.sleep(2)
        
        return results
    
    def save_results(self, results: List[Dict], filename_suffix: str = None):
        """Save results to JSON file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if filename_suffix:
            filename = f"website_intelligence_{filename_suffix}_{timestamp}.json"
        else:
            filename = f"website_intelligence_{timestamp}.json"
        
        output_path = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'outputs', 
            filename
        )
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create summary
        summary = {
            'total_processed': len(results),
            'successful': len([r for r in results if r['success']]),
            'failed': len([r for r in results if not r['success']]),
            'processed_at': datetime.now().isoformat(),
            'results': results
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\nResults saved to: {output_path}")
        
        # Print summary
        print(f"\n=== BATCH SUMMARY ===")
        print(f"Total domains processed: {summary['total_processed']}")
        print(f"Successful: {summary['successful']}")
        print(f"Failed: {summary['failed']}")
        
        if summary['failed'] > 0:
            print(f"\nFailed domains:")
            for result in results:
                if not result['success']:
                    print(f"  - {result['domain']}: {', '.join(result['errors'])}")

def main():
    """Main execution function"""
    
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
    
    # Initialize extractor
    extractor = WebsiteIntelligenceExtractor(openai_api_key)
    
    # Process test batch (5 domains for testing)
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'leads', 'Lumid - verification - Canada.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return
    
    # Process first 5 domains for testing
    results = extractor.process_batch(csv_path, batch_size=5, start_index=0)
    
    print(f"\n[COMPLETE] Processing complete! Check outputs folder for results.")

if __name__ == "__main__":
    main()