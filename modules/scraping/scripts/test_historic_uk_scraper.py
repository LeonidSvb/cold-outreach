#!/usr/bin/env python3
"""
Quick test scraper for Historic-UK to validate approach
"""

import sys
import json
import re
import time
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.lower()))

def scrape_single_page(page_num: int):
    """Scrape a single page from Historic-UK"""
    if page_num == 1:
        url = "https://www.historic-uk.com/LivingHistory/ReenactorsDirectory/"
    else:
        url = f"https://www.historic-uk.com/LivingHistory/ReenactorsDirectory/page/{page_num}/"

    logger.info(f"Fetching: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        logger.info(f"Status code: {response.status_code}")

        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        groups = []

        # Find all h3 headings (group names)
        group_headings = soup.find_all('h3')
        logger.info(f"Found {len(group_headings)} h3 elements")

        for h3 in group_headings:
            group_data = {
                "name": h3.text.strip(),
                "location": "",
                "email": "",
                "website": "",
                "period": ""
            }

            parent = h3.parent

            # Extract period
            h5 = parent.find('h5')
            if h5:
                category_link = h5.find('a')
                if category_link:
                    group_data["period"] = category_link.text.strip()

            # Extract location
            h6 = parent.find('h6')
            if h6:
                group_data["location"] = h6.text.strip()

            # Extract email
            email_link = parent.find('a', href=re.compile(r'^mailto:', re.I))
            if email_link:
                email = email_link['href'].replace('mailto:', '').split('?')[0].strip()
                if is_valid_email(email):
                    group_data["email"] = email.lower()

            # Extract website
            website_links = parent.find_all('a', href=re.compile(r'^http', re.I))
            for link in website_links:
                href = link['href']
                if not any(social in href.lower() for social in ['facebook', 'twitter', 'instagram']):
                    group_data["website"] = href
                    break

            if group_data["name"]:
                groups.append(group_data)
                print(f"Found: {group_data['name']}")
                print(f"  Period: {group_data['period']}")
                print(f"  Location: {group_data['location']}")
                print(f"  Email: {group_data['email']}")
                print(f"  Website: {group_data['website']}")
                print()

        return groups

    except Exception as e:
        logger.error(f"Error scraping page {page_num}: {e}")
        return []

def main():
    """Test scraping first 3 pages"""
    logger.info("=== TESTING HISTORIC-UK SCRAPER ===")

    all_groups = []

    # Test first 3 pages
    for page_num in [1, 2, 3]:
        logger.info(f"\n--- PAGE {page_num} ---")
        groups = scrape_single_page(page_num)
        all_groups.extend(groups)
        time.sleep(3)  # Delay between pages

    print(f"\n{'='*60}")
    print(f"TOTAL GROUPS FOUND: {len(all_groups)}")
    print(f"With Email: {len([g for g in all_groups if g['email']])}")
    print(f"With Website: {len([g for g in all_groups if g['website']])}")
    print(f"{'='*60}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"historic_uk_test_{timestamp}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"groups": all_groups}, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
