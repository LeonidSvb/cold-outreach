#!/usr/bin/env python3
"""
=== HVAC WEBSITE SCRAPER FOR PERSONALIZATION ===
Version: 1.0.0 | Created: 2025-11-09

PURPOSE:
Scrape HVAC company websites to extract personalization data for cold outreach

FEATURES:
- HTTP-only scraping (no external services)
- Extracts: services, specialization, about info
- Rate limiting and error handling
- Progress tracking

USAGE:
1. Input: data/processed/texas_hvac_test_*.csv
2. Run: python scripts/hvac_website_scraper.py
3. Output: data/processed/hvac_websites_enriched_*.csv
"""

import sys
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from urllib.parse import urljoin, urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from modules.shared.logging.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

CONFIG = {
    "INPUT_FILE": "data/processed/texas_hvac_test_20251109_134404.csv",
    "OUTPUT_DIR": "data/processed",
    "TIMEOUT": 15,
    "DELAY_BETWEEN_REQUESTS": 2
}

STATS = {
    "total_websites": 0,
    "success": 0,
    "failed": 0,
    "start_time": None
}

def extract_services(text: str) -> List[str]:
    """Extract services from website text"""
    services = []
    text_lower = text.lower()

    # Service types
    if 'residential' in text_lower:
        services.append('Residential')
    if 'commercial' in text_lower:
        services.append('Commercial')
    if any(x in text_lower for x in ['24/7', 'emergency', '24 hour']):
        services.append('24/7 Emergency')

    # Specific services
    if 'installation' in text_lower or 'install' in text_lower:
        services.append('Installation')
    if 'repair' in text_lower:
        services.append('Repair')
    if 'maintenance' in text_lower:
        services.append('Maintenance')

    return list(set(services))

def extract_specialization(text: str) -> str:
    """Determine company specialization"""
    text_lower = text.lower()

    has_residential = 'residential' in text_lower
    has_commercial = 'commercial' in text_lower

    if has_residential and has_commercial:
        return 'Residential & Commercial'
    elif has_residential:
        return 'Residential Only'
    elif has_commercial:
        return 'Commercial Only'
    else:
        return 'General HVAC'

def scrape_website(url: str, company_name: str) -> Dict:
    """Scrape single website for personalization data"""

    try:
        # Clean URL
        if not url.startswith('http'):
            url = 'https://' + url

        # Remove UTM parameters
        clean_url = url.split('?')[0]

        # Fetch with timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(clean_url, headers=headers, timeout=CONFIG["TIMEOUT"], allow_redirects=True)

        if response.status_code != 200:
            return {
                'status': 'FAILED',
                'error': f'HTTP {response.status_code}',
                'services': '',
                'specialization': '',
                'content_preview': '',
                'scraped_url': clean_url
            }

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove scripts and styles
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Extract text
        text = soup.get_text(separator=' ', strip=True)
        text_clean = ' '.join(text.split())

        # Extract data
        services = extract_services(text_clean)
        specialization = extract_specialization(text_clean)

        # Get preview (first 500 chars)
        content_preview = text_clean[:500] if text_clean else ''

        return {
            'status': 'SUCCESS',
            'error': '',
            'services': '; '.join(services) if services else 'N/A',
            'specialization': specialization,
            'content_preview': content_preview,
            'scraped_url': response.url
        }

    except requests.Timeout:
        return {
            'status': 'TIMEOUT',
            'error': 'Request timeout',
            'services': '',
            'specialization': '',
            'content_preview': '',
            'scraped_url': url
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e)[:100],
            'services': '',
            'specialization': '',
            'content_preview': '',
            'scraped_url': url
        }

def main():
    """Main execution"""
    logger.info("=== HVAC WEBSITE SCRAPER ===")

    # Load companies
    input_path = Path(CONFIG["INPUT_FILE"])
    if not input_path.exists():
        logger.error(f"Input file not found: {CONFIG['INPUT_FILE']}")
        return

    df = pd.read_csv(input_path)

    # Filter companies with emails and websites
    has_email = df['emails'].notna() & (df['emails'] != '')
    has_website = df['website'].notna() & (df['website'] != '')
    to_scrape = df[has_email & has_website].copy()

    STATS["total_websites"] = len(to_scrape)
    STATS["start_time"] = time.time()

    logger.info(f"Companies to scrape: {len(to_scrape)}")
    print(f"\n{'='*70}")
    print(f"HVAC WEBSITE SCRAPING")
    print(f"{'='*70}")
    print(f"Companies with emails: {len(to_scrape)}")
    print(f"Estimated time: {len(to_scrape) * CONFIG['DELAY_BETWEEN_REQUESTS'] / 60:.1f} min")
    print(f"{'='*70}\n")

    # Scrape websites
    results = []

    for idx, row in to_scrape.iterrows():
        company_name = row['company_name']
        website = row['website']

        progress = f"[{STATS['success'] + STATS['failed'] + 1}/{len(to_scrape)}]"
        print(f"{progress} {company_name[:40]:<40} ", end='', flush=True)

        # Scrape
        scrape_result = scrape_website(website, company_name)

        # Combine with original data
        result = {
            'company_name': company_name,
            'city': row['city'],
            'state': row['state'],
            'phone': row['phone'],
            'website': website,
            'emails': row['emails'],
            'rating': row['rating'],
            'reviews': row['reviews'],
            **scrape_result
        }

        results.append(result)

        # Update stats
        if scrape_result['status'] == 'SUCCESS':
            STATS['success'] += 1
            print(f"OK - {scrape_result['specialization']}")
        else:
            STATS['failed'] += 1
            print(f"FAIL - {scrape_result['error'][:30]}")

        # Rate limiting
        time.sleep(CONFIG["DELAY_BETWEEN_REQUESTS"])

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(CONFIG["OUTPUT_DIR"])
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"hvac_websites_enriched_{timestamp}.csv"

    df_results = pd.DataFrame(results)
    df_results.to_csv(output_file, index=False)

    # Summary
    elapsed = (time.time() - STATS["start_time"]) / 60
    success_rate = (STATS["success"] / STATS["total_websites"]) * 100 if STATS["total_websites"] > 0 else 0

    print(f"\n{'='*70}")
    print(f"SCRAPING COMPLETED")
    print(f"{'='*70}")
    print(f"Total websites: {STATS['total_websites']}")
    print(f"Success:        {STATS['success']} ({success_rate:.1f}%)")
    print(f"Failed:         {STATS['failed']}")
    print(f"Time elapsed:   {elapsed:.1f} min")
    print(f"Output file:    {output_file}")
    print(f"{'='*70}\n")

    # Sample results
    successful = df_results[df_results['status'] == 'SUCCESS']
    if len(successful) > 0:
        print("=== SAMPLE ENRICHED DATA ===\n")
        for idx, row in successful.head(3).iterrows():
            print(f"{row['company_name']}")
            print(f"  Specialization: {row['specialization']}")
            print(f"  Services: {row['services']}")
            print(f"  Preview: {row['content_preview'][:100]}...")
            print()

    logger.info("=== COMPLETED ===")

if __name__ == "__main__":
    main()
