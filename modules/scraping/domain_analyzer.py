#!/usr/bin/env python3
"""
=== DOMAIN ANALYZER ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Mass domain analysis and website intelligence extraction with parallel processing

FEATURES:
- Parallel domain analysis: 50+ concurrent requests
- Website content extraction and analysis
- Technology stack detection
- Company size and industry estimation
- Contact information discovery
- Page prioritization and content ranking
- Google Sheets integration for data management

USAGE:
1. Configure domains list in CONFIG section below
2. Set analysis parameters and output settings
3. Run: python domain_analyzer.py
4. Results automatically saved to results/ and Google Sheets

IMPROVEMENTS:
v1.0.0 - Initial version with mass parallel processing
"""

import asyncio
import aiohttp
import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
from shared.logger import auto_log
from shared.google_sheets import GoogleSheetsManager

# ============================================================================
# CONFIG SECTION - EDIT HERE
# ============================================================================

CONFIG = {
    # SCRAPING SETTINGS
    "SCRAPING": {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "TIMEOUT_SECONDS": 30,
        "MAX_REDIRECTS": 5,
        "CONCURRENT_REQUESTS": 50,
        "DELAY_BETWEEN_REQUESTS": 0.1
    },

    # ANALYSIS SETTINGS
    "ANALYSIS": {
        "MAX_PAGES_PER_DOMAIN": 5,
        "PRIORITY_PAGES": [
            "/about", "/about-us", "/team", "/leadership",
            "/contact", "/contact-us", "/careers", "/jobs",
            "/services", "/products", "/solutions"
        ],
        "EXTRACT_EMAILS": True,
        "EXTRACT_PHONES": True,
        "DETECT_TECHNOLOGIES": True,
        "ANALYZE_CONTENT": True
    },

    # TECHNOLOGY DETECTION
    "TECH_PATTERNS": {
        "cms": {
            "wordpress": ["wp-content", "wp-includes", "wordpress"],
            "shopify": ["shopify", "cdn.shopify.com"],
            "wix": ["wix.com", "wixstatic.com"],
            "squarespace": ["squarespace", "sqsp.com"]
        },
        "analytics": {
            "google_analytics": ["google-analytics.com", "gtag", "ga("],
            "facebook_pixel": ["facebook.net/tr", "fbevents.js"],
            "hotjar": ["hotjar.com", "hj("],
            "mixpanel": ["mixpanel.com"]
        },
        "marketing": {
            "hubspot": ["hubspot", "hs-scripts.com"],
            "marketo": ["marketo", "mktoresp.com"],
            "pardot": ["pardot", "pi.pardot.com"],
            "intercom": ["intercom", "widget.intercom.io"]
        }
    },

    # CONTENT ANALYSIS
    "CONTENT_ANALYSIS": {
        "COMPANY_SIZE_INDICATORS": {
            "small": ["startup", "small team", "founded by", "we are a"],
            "medium": ["established", "growing team", "offices in", "100+ employees"],
            "large": ["enterprise", "global", "international", "1000+ employees", "fortune"]
        },
        "INDUSTRY_KEYWORDS": {
            "saas": ["software", "saas", "cloud", "platform", "api"],
            "ecommerce": ["shop", "store", "ecommerce", "retail", "marketplace"],
            "consulting": ["consulting", "advisory", "services", "solutions"],
            "agency": ["agency", "marketing", "advertising", "creative"]
        }
    },

    # GOOGLE SHEETS INTEGRATION
    "GOOGLE_SHEETS": {
        "ENABLED": True,
        "INPUT_SHEET_ID": "your_input_sheet_id_here",
        "OUTPUT_SHEET_ID": "your_output_sheet_id_here",
        "INPUT_WORKSHEET": "Domains to Analyze",
        "OUTPUT_WORKSHEET": "Domain Analysis Results",
        "COLUMN_MAPPING": {
            "domain": "A",
            "company_name": "B",
            "industry": "C",
            "company_size": "D",
            "technologies": "E",
            "emails_found": "F",
            "phones_found": "G",
            "priority_score": "H",
            "analysis_summary": "I"
        }
    },

    # OUTPUT SETTINGS
    "OUTPUT": {
        "SAVE_JSON": True,
        "UPDATE_GOOGLE_SHEETS": True,
        "EXPORT_CSV": True,
        "INCLUDE_RAW_HTML": False,
        "RESULTS_DIR": "results"
    }
}

# ============================================================================
# SCRIPT STATISTICS - AUTO-UPDATED
# ============================================================================

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "last_run": None,
    "total_domains_analyzed": 0,
    "success_rate": 0.0,
    "avg_processing_time": 0.0,
    "total_pages_scraped": 0
}

# ============================================================================
# MAIN LOGIC
# ============================================================================

class DomainAnalyzer:
    """High-performance domain analysis with parallel processing"""

    def __init__(self):
        self.config = CONFIG
        self.session = None
        self.results_dir = Path(__file__).parent / self.config["OUTPUT"]["RESULTS_DIR"]
        self.results_dir.mkdir(exist_ok=True)
        self.domains_analyzed = 0
        self.pages_scraped = 0

    @auto_log("domain_analyzer")
    async def analyze_domains(self, domains: List[str]) -> List[Dict[str, Any]]:
        """Main function to analyze domains massively"""

        print(f"Starting Domain Analysis")
        print(f"Total domains: {len(domains):,}")
        print(f"Concurrency: {self.config['SCRAPING']['CONCURRENT_REQUESTS']} threads")
        print(f"Max pages per domain: {self.config['ANALYSIS']['MAX_PAGES_PER_DOMAIN']}")

        start_time = time.time()

        # Initialize session
        timeout = aiohttp.ClientTimeout(total=self.config["SCRAPING"]["TIMEOUT_SECONDS"])
        async with aiohttp.ClientSession(timeout=timeout) as session:
            self.session = session

            # Create analysis batches
            batches = self._create_analysis_batches(domains)
            print(f"Created {len(batches)} analysis batches")

            # Process all batches in parallel
            analysis_results = await self._process_batches_parallel(batches)

        # Save results
        await self._save_results(analysis_results, start_time)

        # Update Google Sheets if enabled
        if self.config["GOOGLE_SHEETS"]["ENABLED"] and analysis_results:
            await self._update_google_sheets(analysis_results)

        self._update_script_stats(len(analysis_results), time.time() - start_time)

        print(f"Analysis completed!")
        print(f"Total analyzed: {len(analysis_results):,}")
        print(f"Pages scraped: {self.pages_scraped:,}")
        print(f"Processing time: {time.time() - start_time:.2f}s")

        return analysis_results

    def _create_analysis_batches(self, domains: List[str]) -> List[List[str]]:
        """Create domain batches for parallel processing"""
        batch_size = 20  # Smaller batches for domain analysis
        batches = []
        
        for i in range(0, len(domains), batch_size):
            batch = domains[i:i + batch_size]
            batches.append(batch)
            
        return batches

    async def _process_batches_parallel(self, batches: List[List[str]]) -> List[Dict[str, Any]]:
        """Process all batches in parallel"""
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.config["SCRAPING"]["CONCURRENT_REQUESTS"])

        async def process_with_semaphore(batch):
            async with semaphore:
                return await self._process_single_batch(batch)

        # Process all batches
        print(f"Processing {len(batches)} batches in parallel...")
        tasks = [process_with_semaphore(batch) for batch in batches]

        # Track progress
        all_results = []
        for i, task in enumerate(asyncio.as_completed(tasks)):
            batch_results = await task
            all_results.extend(batch_results)

            # Progress update
            if (i + 1) % 5 == 0 or (i + 1) == len(tasks):
                progress = (i + 1) / len(tasks) * 100
                print(f"Progress: {progress:.1f}% ({i + 1}/{len(tasks)} batches)")

        return all_results

    async def _process_single_batch(self, batch: List[str]) -> List[Dict[str, Any]]:
        """Process a single batch of domains"""
        
        batch_results = []
        
        for domain in batch:
            try:
                result = await self._analyze_single_domain(domain)
                if result:
                    batch_results.append(result)
                    
                # Small delay between requests
                await asyncio.sleep(self.config["SCRAPING"]["DELAY_BETWEEN_REQUESTS"])
                
            except Exception as e:
                print(f"Error analyzing domain {domain}: {e}")
                continue
                
        return batch_results

    async def _analyze_single_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """Analyze a single domain comprehensively"""
        
        try:
            # Normalize domain
            if not domain.startswith(('http://', 'https://')):
                domain = 'https://' + domain
                
            # Initialize analysis result
            analysis = {
                "domain": domain,
                "analyzed_at": datetime.now().isoformat(),
                "pages_analyzed": [],
                "technologies": [],
                "emails_found": [],
                "phones_found": [],
                "company_info": {},
                "priority_score": 0
            }
            
            # Get main page
            main_content = await self._fetch_page_content(domain)
            if not main_content:
                return None
                
            analysis["pages_analyzed"].append({
                "url": domain,
                "title": main_content.get("title", ""),
                "content_length": len(main_content.get("text", ""))
            })
            
            # Analyze main page
            self._analyze_page_content(main_content, analysis)
            
            # Get additional priority pages
            priority_urls = self._get_priority_urls(domain, main_content.get("links", []))
            
            for url in priority_urls[:self.config["ANALYSIS"]["MAX_PAGES_PER_DOMAIN"]-1]:
                page_content = await self._fetch_page_content(url)
                if page_content:
                    analysis["pages_analyzed"].append({
                        "url": url,
                        "title": page_content.get("title", ""),
                        "content_length": len(page_content.get("text", ""))
                    })
                    self._analyze_page_content(page_content, analysis)
                    
            # Calculate priority score
            analysis["priority_score"] = self._calculate_priority_score(analysis)
            
            # Clean up and finalize
            analysis["technologies"] = list(set(analysis["technologies"]))
            analysis["emails_found"] = list(set(analysis["emails_found"]))
            analysis["phones_found"] = list(set(analysis["phones_found"]))
            
            self.domains_analyzed += 1
            self.pages_scraped += len(analysis["pages_analyzed"])
            
            return analysis
            
        except Exception as e:
            print(f"Error in domain analysis for {domain}: {e}")
            return None

    async def _fetch_page_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse page content"""
        
        try:
            headers = {
                "User-Agent": self.config["SCRAPING"]["USER_AGENT"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Extract content
                    content = {
                        "html": html if self.config["OUTPUT"]["INCLUDE_RAW_HTML"] else None,
                        "title": soup.title.string if soup.title else "",
                        "text": soup.get_text(),
                        "links": [a.get('href') for a in soup.find_all('a', href=True)],
                        "meta_description": "",
                        "headings": [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3'])]
                    }
                    
                    # Get meta description
                    meta_desc = soup.find("meta", attrs={"name": "description"})
                    if meta_desc:
                        content["meta_description"] = meta_desc.get("content", "")
                    
                    return content
                    
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _analyze_page_content(self, content: Dict[str, Any], analysis: Dict[str, Any]):
        """Analyze page content for insights"""
        
        text = content.get("text", "").lower()
        html = content.get("html", "")
        
        # Extract emails
        if self.config["ANALYSIS"]["EXTRACT_EMAILS"]:
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, content.get("text", ""), re.IGNORECASE)
            analysis["emails_found"].extend(emails)
        
        # Extract phone numbers
        if self.config["ANALYSIS"]["EXTRACT_PHONES"]:
            phone_pattern = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
            phones = re.findall(phone_pattern, content.get("text", ""))
            analysis["phones_found"].extend(['-'.join(phone) for phone in phones])
        
        # Detect technologies
        if self.config["ANALYSIS"]["DETECT_TECHNOLOGIES"] and html:
            for category, tech_dict in self.config["TECH_PATTERNS"].items():
                for tech_name, patterns in tech_dict.items():
                    for pattern in patterns:
                        if pattern.lower() in html.lower():
                            analysis["technologies"].append(f"{category}:{tech_name}")
        
        # Analyze company size
        for size, indicators in self.config["CONTENT_ANALYSIS"]["COMPANY_SIZE_INDICATORS"].items():
            for indicator in indicators:
                if indicator in text:
                    analysis["company_info"]["estimated_size"] = size
                    break
        
        # Analyze industry
        for industry, keywords in self.config["CONTENT_ANALYSIS"]["INDUSTRY_KEYWORDS"].items():
            for keyword in keywords:
                if keyword in text:
                    analysis["company_info"]["likely_industry"] = industry
                    break

    def _get_priority_urls(self, base_domain: str, links: List[str]) -> List[str]:
        """Get priority URLs to analyze"""
        
        priority_urls = []
        base_parsed = urlparse(base_domain)
        
        for link in links:
            if not link:
                continue
                
            # Convert relative URLs to absolute
            if link.startswith('/'):
                full_url = f"{base_parsed.scheme}://{base_parsed.netloc}{link}"
            elif link.startswith(('http://', 'https://')):
                full_url = link
            else:
                continue
                
            # Check if it's a priority page
            for priority_path in self.config["ANALYSIS"]["PRIORITY_PAGES"]:
                if priority_path in link.lower():
                    if full_url not in priority_urls:
                        priority_urls.append(full_url)
                        
        return priority_urls

    def _calculate_priority_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate priority score based on analysis results"""
        
        score = 0
        
        # Base score for successful analysis
        score += 3
        
        # Email addresses found
        score += min(len(analysis["emails_found"]), 3) * 2
        
        # Phone numbers found
        score += min(len(analysis["phones_found"]), 2) * 1
        
        # Technologies detected
        score += min(len(analysis["technologies"]), 5) * 1
        
        # Company size estimation
        if analysis["company_info"].get("estimated_size") == "large":
            score += 3
        elif analysis["company_info"].get("estimated_size") == "medium":
            score += 2
        elif analysis["company_info"].get("estimated_size") == "small":
            score += 1
            
        # Priority pages found
        score += len(analysis["pages_analyzed"]) * 1
        
        return min(score, 10)  # Cap at 10

    async def _save_results(self, results: List[Dict[str, Any]], start_time: float):
        """Save results to JSON and optionally CSV"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        processing_time = time.time() - start_time
        
        # Prepare results data
        results_data = {
            "metadata": {
                "timestamp": timestamp,
                "total_domains": len(results),
                "processing_time_seconds": round(processing_time, 2),
                "total_pages_scraped": self.pages_scraped,
                "config_used": self.config,
                "script_version": SCRIPT_STATS["version"]
            },
            "results": results
        }
        
        # Save JSON
        if self.config["OUTPUT"]["SAVE_JSON"]:
            json_filename = f"domain_analysis_{timestamp}.json"
            json_filepath = self.results_dir / json_filename
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
                
            print(f"JSON saved: {json_filename}")

    async def _update_google_sheets(self, results: List[Dict[str, Any]]):
        """Update Google Sheets with analysis results"""
        
        try:
            print(f"Updating Google Sheets...")
            
            # Flatten results for sheets
            flattened_results = []
            for result in results:
                flattened = {
                    "domain": result["domain"],
                    "company_name": result["company_info"].get("name", ""),
                    "industry": result["company_info"].get("likely_industry", ""),
                    "company_size": result["company_info"].get("estimated_size", ""),
                    "technologies": ", ".join(result["technologies"]),
                    "emails_found": ", ".join(result["emails_found"]),
                    "phones_found": ", ".join(result["phones_found"]),
                    "priority_score": result["priority_score"],
                    "analysis_summary": f"Analyzed {len(result['pages_analyzed'])} pages"
                }
                flattened_results.append(flattened)
            
            gs_manager = GoogleSheetsManager(
                self.config["GOOGLE_SHEETS"]["OUTPUT_SHEET_ID"],
                self.config["GOOGLE_SHEETS"]["OUTPUT_WORKSHEET"]
            )
            
            success = await gs_manager.batch_write_leads(
                flattened_results,
                self.config["GOOGLE_SHEETS"]["COLUMN_MAPPING"]
            )
            
            if success:
                print(f"Google Sheets updated with {len(results):,} domains")
            else:
                print(f"Failed to update Google Sheets")
                
        except Exception as e:
            print(f"Google Sheets update error: {e}")

    def _update_script_stats(self, domains_count: int, processing_time: float):
        """Update script statistics"""
        global SCRIPT_STATS
        
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()
        SCRIPT_STATS["total_domains_analyzed"] += domains_count
        SCRIPT_STATS["avg_processing_time"] = processing_time
        SCRIPT_STATS["total_pages_scraped"] += self.pages_scraped
        
        # Calculate success rate
        SCRIPT_STATS["success_rate"] = (domains_count / len(domains)) * 100 if domains_count > 0 else 0

# ============================================================================
# EXECUTION
# ============================================================================

async def main():
    """Main execution function"""
    
    print("=" * 60)
    print("DOMAIN ANALYZER v1.0.0")
    print("=" * 60)
    
    analyzer = DomainAnalyzer()
    
    # Sample domains for testing
    sample_domains = [
        "example.com",
        "google.com",
        "github.com"
    ]
    
    # Analyze domains
    results = await analyzer.analyze_domains(sample_domains)
    
    print("=" * 60)
    print(f"Analysis completed: {len(results):,} domains")
    print(f"Pages scraped: {SCRIPT_STATS['total_pages_scraped']:,}")
    print(f"Success rate: {SCRIPT_STATS['success_rate']:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())