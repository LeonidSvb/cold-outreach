#!/usr/bin/env python3
"""
Historic-UK Full Scraper - All 24 pages
UK groups often have direct email contacts on their listings
"""

import re
import time
import random
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
import requests
from bs4 import BeautifulSoup

CONFIG = {
    "BASE_URL": "https://www.historic-uk.com/LivingHistory/ReenactorsDirectory",
    "TOTAL_PAGES": 24,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "DELAY_MIN": 2,
    "DELAY_MAX": 4
}

def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.lower()))

def extract_emails(text: str) -> Set[str]:
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = set(re.findall(pattern, text))
    return {e.lower() for e in emails if is_valid_email(e)}

def make_request(url: str):
    """HTTP request"""
    try:
        time.sleep(random.uniform(CONFIG["DELAY_MIN"], CONFIG["DELAY_MAX"]))
        headers = {'User-Agent': CONFIG["USER_AGENT"]}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response
    except Exception as e:
        print(f"  Error: {e}")
    return None

def scrape_page(page_num: int) -> List[Dict]:
    """Scrape a single page"""
    if page_num == 1:
        url = f"{CONFIG['BASE_URL']}/"
    else:
        url = f"{CONFIG['BASE_URL']}/page/{page_num}/"

    print(f"\nPage {page_num}/{CONFIG['TOTAL_PAGES']}: {url}")

    response = make_request(url)
    if not response:
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    groups = []

    # Each group has h3 title
    h3_elements = soup.find_all('h3')

    for h3 in h3_elements:
        try:
            parent = h3.parent

            group_data = {
                "name": h3.text.strip(),
                "location": "",
                "email": "",
                "website": "",
                "phone": "",
                "period": "",
                "source": "Historic-UK"
            }

            # Skip if name is generic
            if group_data["name"] in ["Your Organisation Here", "Events Diary", "Follow us", "Popular searches"]:
                continue

            # Period from h5
            h5 = parent.find('h5')
            if h5:
                category = h5.find('a')
                if category:
                    group_data["period"] = category.text.strip()

            # Location from h6
            h6 = parent.find('h6')
            if h6:
                group_data["location"] = h6.text.strip()

            # Email from mailto
            mailto = parent.find('a', href=re.compile(r'^mailto:', re.I))
            if mailto:
                email = mailto['href'].replace('mailto:', '').split('?')[0].strip()
                if is_valid_email(email):
                    group_data["email"] = email.lower()

            # Website
            website_links = parent.find_all('a', href=re.compile(r'^http', re.I))
            for link in website_links:
                href = link['href']
                # Skip internal historic-uk links and social media
                if 'historic-uk.com' in href.lower() or any(s in href.lower() for s in ['facebook', 'twitter']):
                    continue
                group_data["website"] = href
                break

            # Extract emails from text if not found
            if not group_data["email"]:
                text = parent.get_text()
                emails = extract_emails(text)
                if emails:
                    group_data["email"] = list(emails)[0]

            # Only add if has name and some contact method
            if group_data["name"] and (group_data["email"] or group_data["website"]):
                groups.append(group_data)
                print(f"  [OK] {group_data['name'][:40]}", end="")
                if group_data["email"]:
                    print(f" - {group_data['email']}")
                else:
                    print()

        except Exception as e:
            print(f"  [ERROR] Parsing group: {e}")
            continue

    return groups

def main():
    print("="*70)
    print("HISTORIC-UK FULL SCRAPER - All 24 Pages")
    print("="*70)

    all_groups = []

    for page_num in range(1, CONFIG["TOTAL_PAGES"] + 1):
        groups = scrape_page(page_num)
        all_groups.extend(groups)
        print(f"  Collected: {len(groups)} groups (Total: {len(all_groups)})")

    print("\n--- SCRAPING COMPLETE ---")
    print(f"Total groups: {len(all_groups)}")
    print(f"With emails: {len([g for g in all_groups if g.get('email')])}")

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    json_file = results_dir / f"historic_uk_full_{timestamp}.json"

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_contacts": len(all_groups),
            "with_emails": len([g for g in all_groups if g.get("email")])
        },
        "contacts": all_groups
    }

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # CSV
    csv_file = results_dir / f"historic_uk_full_{timestamp}.csv"
    import csv
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if all_groups:
            fieldnames = ['name', 'email', 'website', 'location', 'period', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_groups)

    print(f"\nSaved to:")
    print(f"  JSON: {json_file}")
    print(f"  CSV: {csv_file}")
    print("="*70)

if __name__ == "__main__":
    main()
