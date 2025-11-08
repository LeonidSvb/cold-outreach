#!/usr/bin/env python3
"""
=== EMAIL EXTRACTOR FROM REENACTMENT WEBSITES ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Extract email addresses from reenactment group websites
Takes a list of websites and finds contact emails

USAGE:
1. Provide list of websites (JSON or URLs)
2. Run: python extract_emails_from_websites.py
3. Results with emails saved to results/
"""

import sys
import json
import re
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from logger.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "DELAY_MIN": 2,
    "DELAY_MAX": 4,
    "TIMEOUT": 15,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.lower()))

def extract_emails_from_text(text: str) -> Set[str]:
    """Extract all email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = set(re.findall(email_pattern, text))
    return {email.lower() for email in emails if is_valid_email(email)}

def extract_emails_from_website(url: str) -> Dict:
    """Extract emails from a website"""
    logger.info(f"Processing: {url}")
    result = {
        "website": url,
        "emails": [],
        "status": "pending"
    }

    pages_to_check = [
        url,
        urljoin(url, '/contact'),
        urljoin(url, '/contact-us'),
        urljoin(url, '/about'),
        urljoin(url, '/about-us'),
    ]

    all_emails = set()

    for page_url in pages_to_check:
        try:
            time.sleep(random.uniform(CONFIG["DELAY_MIN"], CONFIG["DELAY_MAX"]))

            response = requests.get(
                page_url,
                headers={'User-Agent': CONFIG["USER_AGENT"]},
                timeout=CONFIG["TIMEOUT"]
            )

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract from text
                text = soup.get_text()
                emails = extract_emails_from_text(text)
                all_emails.update(emails)

                # Extract from mailto links
                mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
                for link in mailto_links:
                    email = link['href'].replace('mailto:', '').split('?')[0].strip()
                    if is_valid_email(email):
                        all_emails.add(email.lower())

        except Exception as e:
            logger.warning(f"Failed to fetch {page_url}: {e}")
            continue

    result["emails"] = list(all_emails)
    result["status"] = "success" if all_emails else "no_emails_found"

    if all_emails:
        logger.info(f"Found {len(all_emails)} emails from {url}")
    else:
        logger.warning(f"No emails found on {url}")

    return result

def process_websites(websites: List[str]) -> List[Dict]:
    """Process multiple websites"""
    logger.info(f"Processing {len(websites)} websites...")
    results = []

    for i, website in enumerate(websites, 1):
        logger.info(f"[{i}/{len(websites)}] Processing: {website}")
        result = extract_emails_from_website(website)
        results.append(result)

    return results

def save_results(results: List[Dict]) -> str:
    """Save results to JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"extracted_emails_{timestamp}.json"

    output_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_websites": len(results),
            "with_emails": len([r for r in results if r["emails"]])
        },
        "results": results
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to: {output_file}")
    return str(output_file)

def main():
    """Main execution"""
    logger.info("=== EMAIL EXTRACTOR STARTED ===")

    # Example websites (replace with your list)
    websites = [
        "https://www.ausreenact.com.au/",
        "https://www.nmrg.com.au/",
        "http://geelongmrg.com/",
        "https://www.awwlha.com/",
        "https://26yd.com/",
        "https://www.chgww2.net/",
        "https://www.armygroup1944.org/",
        "https://www.wwiirc.org/",
        "http://www.ww2uso.org/",
    ]

    results = process_websites(websites)

    # Print summary
    with_emails = [r for r in results if r["emails"]]
    print(f"\n{'='*60}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Websites: {len(results)}")
    print(f"With Emails: {len(with_emails)}")
    print(f"Success Rate: {len(with_emails)/len(results)*100:.1f}%")
    print(f"{'='*60}\n")

    for result in with_emails:
        print(f"{result['website']}")
        for email in result['emails']:
            print(f"  - {email}")
        print()

    output_file = save_results(results)
    logger.info(f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()
