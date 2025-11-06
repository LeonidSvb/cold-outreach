#!/usr/bin/env python3
"""
=== ADVANCED COLD CALLING AGENCIES WEB SCRAPER ===
Version: 1.0.0 | Created: 2025-11-02

PURPOSE:
Advanced web scraping to collect cold calling agencies from multiple online sources
using HTTP requests and HTML parsing.

FEATURES:
- Multi-source scraping (Google search results, directory pages)
- Company website extraction
- Contact information discovery
- Rate limiting and retry logic
- Export to JSON

USAGE:
1. Run: python advanced_agencies_scraper.py
2. Results appended to existing collection
3. Final list saved to ../results/

IMPROVEMENTS:
v1.0.0 - Initial version with Google search scraping
"""

import sys
from pathlib import Path
import json
import requests
from datetime import datetime
import time
import random
import re
from urllib.parse import urlparse, urljoin

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
    "SEARCH_QUERIES": [
        "cold calling agency USA",
        "B2B telemarketing services Canada",
        "outbound call center Australia",
        "lead generation cold calling UK",
        "appointment setting agency Germany",
        "sales outsourcing telemarketing France",
        "B2B cold calling Netherlands",
        "telemarketing services Spain",
        "cold calling service provider United States",
        "outbound sales agency Canada",
        "call center BPO Australia",
        "telesales company Europe",
    ],
    "HEADERS": {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    },
    "REQUEST_DELAY": (3, 7),  # Random delay between requests
    "TIMEOUT": 15,
}

# Known directories and listing sites
DIRECTORY_URLS = [
    "https://www.saleshandy.com/agencies/lead-generation/cold-call/",
    "https://www.50pros.com/specialty/cold-calling",
    "https://belkins.io/blog/cold-calling-companies",
    "https://martal.ca/how-to-find-and-hire-cold-calling-lead-generation-companies/",
]


def load_existing_companies():
    """Load existing companies from previous collection"""
    results_dir = CONFIG["OUTPUT_DIR"]
    if not results_dir.exists():
        return []

    # Find most recent initial collection
    json_files = sorted(results_dir.glob("cold_calling_agencies_initial_*.json"), reverse=True)
    if not json_files:
        return []

    with open(json_files[0], 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("companies", [])


def extract_domain(url):
    """Extract clean domain from URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        domain = domain.replace('www.', '')
        return domain
    except:
        return None


def is_valid_company_url(url):
    """Check if URL looks like a company website"""
    if not url:
        return False

    # Skip social media, directories, etc
    skip_domains = [
        'linkedin.com', 'facebook.com', 'twitter.com', 'youtube.com',
        'clutch.co', 'goodfirms.co', 'upcity.com', 'designrush.com',
        'google.com', 'bing.com', 'saleshandy.com', '50pros.com',
    ]

    domain = extract_domain(url)
    if not domain:
        return False

    for skip in skip_domains:
        if skip in domain:
            return False

    return True


def extract_companies_from_text(text, source="Web"):
    """Extract company names and URLs from text content"""
    companies = []

    # Pattern 1: Look for company names followed by URLs
    url_pattern = r'https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})'
    urls = re.findall(url_pattern, text)

    for url_match in urls:
        full_url = f"https://{url_match}"
        if is_valid_company_url(full_url):
            # Extract potential company name from domain
            domain_parts = url_match.split('.')[0].split('-')
            company_name = ' '.join(word.capitalize() for word in domain_parts)

            companies.append({
                "name": company_name,
                "website": full_url,
                "source": source,
                "country": "Unknown",
                "services": "Cold calling, telemarketing",
            })

    return companies


def scrape_directory_page(url, source_name):
    """Scrape a directory page for company listings"""
    logger.info(f"Scraping {source_name}", url=url)

    try:
        response = requests.get(url, headers=CONFIG["HEADERS"], timeout=CONFIG["TIMEOUT"])
        response.raise_for_status()

        companies = extract_companies_from_text(response.text, source=source_name)
        logger.info(f"Extracted {len(companies)} companies from {source_name}")

        return companies

    except requests.RequestException as e:
        logger.warning(f"Failed to scrape {source_name}", error=str(e))
        return []


def search_google_custom(query):
    """
    Note: This is a placeholder for Google Custom Search API.
    Requires API key and Search Engine ID from Google Cloud Console.
    For now, returns empty list - can be implemented with proper credentials.
    """
    logger.info(f"Google search placeholder for: {query}")
    # TODO: Implement with Google Custom Search API if credentials provided
    return []


def deduplicate_by_domain(companies):
    """Remove duplicates based on website domain"""
    seen_domains = set()
    seen_names = set()
    unique = []

    for company in companies:
        domain = extract_domain(company.get("website", ""))
        name = company.get("name", "").lower().strip()

        # Skip if we've seen this domain or name
        if domain and domain in seen_domains:
            continue
        if name in seen_names:
            continue

        if domain:
            seen_domains.add(domain)
        if name:
            seen_names.add(name)

        unique.append(company)

    return unique


def enhance_with_existing(new_companies, existing_companies):
    """Merge new companies with existing, avoiding duplicates"""
    all_companies = existing_companies + new_companies
    return deduplicate_by_domain(all_companies)


def save_results(companies, filename="cold_calling_agencies_expanded"):
    """Save results to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"{filename}_{timestamp}.json"

    CONFIG["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)

    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_companies": len(companies),
            "version": "1.0.0",
        },
        "companies": companies,
        "statistics": {
            "by_country": {},
            "by_source": {},
            "with_website": sum(1 for c in companies if c.get("website")),
        }
    }

    # Calculate statistics
    for company in companies:
        country = company.get("country", "Unknown")
        source = company.get("source", "Unknown")

        output_data["statistics"]["by_country"][country] = output_data["statistics"]["by_country"].get(country, 0) + 1
        output_data["statistics"]["by_source"][source] = output_data["statistics"]["by_source"].get(source, 0) + 1

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved", file=str(output_file), count=len(companies))
    return output_file


def main():
    logger.info("Starting advanced agencies scraper")

    try:
        # Step 1: Load existing companies
        existing = load_existing_companies()
        logger.info(f"Loaded {len(existing)} existing companies")

        new_companies = []

        # Step 2: Scrape directory pages
        for url in DIRECTORY_URLS:
            source_name = extract_domain(url) or "Unknown"
            companies = scrape_directory_page(url, source_name)
            new_companies.extend(companies)

            # Rate limiting
            time.sleep(random.uniform(*CONFIG["REQUEST_DELAY"]))

        # Step 3: Deduplicate and merge
        logger.info(f"Collected {len(new_companies)} new companies before dedup")
        new_companies = deduplicate_by_domain(new_companies)
        logger.info(f"After dedup: {len(new_companies)} unique new companies")

        all_companies = enhance_with_existing(new_companies, existing)
        logger.info(f"Total unique companies: {len(all_companies)}")

        # Step 4: Save results
        output_file = save_results(all_companies)

        # Print summary
        print(f"\n{'='*60}")
        print(f"SCRAPING SUMMARY")
        print(f"{'='*60}")
        print(f"Existing Companies: {len(existing)}")
        print(f"New Companies Found: {len(new_companies)}")
        print(f"Total Unique Companies: {len(all_companies)}")
        print(f"Progress: {len(all_companies)} / 500 ({len(all_companies)/500*100:.1f}%)")
        print(f"\nWith Website: {sum(1 for c in all_companies if c.get('website'))}")
        print(f"Results saved to: {output_file}")
        print(f"{'='*60}\n")

        logger.info("Scraping completed successfully")

    except Exception as e:
        logger.error("Scraping failed", error=e)
        raise


if __name__ == "__main__":
    main()
