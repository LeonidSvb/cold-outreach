#!/usr/bin/env python3
"""
Mass Website Collector - Extract group websites from directories
Then extract emails from each website
"""

import re
import time
import random
import json
from pathlib import Path
from datetime import datetime
from typing import List, Set
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Configuration
CONFIG = {
    "DIRECTORIES": [
        "https://wwiidogtags.com/ww2-reenacting-units/",
        "https://www.milsurpia.com/reenactment-groups/world-war-2-reenactors",
        "https://www.livinghistoryarchive.com/group/ww2-reenactment-groups",
        "https://www.reenactor.net/index.php?page=70",
    ],
    "DELAY_MIN": 2,
    "DELAY_MAX": 4,
    "TIMEOUT": 15,
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def is_valid_email(email: str) -> bool:
    """Validate email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.lower()))

def extract_emails_from_text(text: str) -> Set[str]:
    """Extract emails from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = set(re.findall(email_pattern, text))
    return {email.lower() for email in emails if is_valid_email(email)}

def make_request(url: str):
    """HTTP request with retry"""
    headers = {'User-Agent': CONFIG["USER_AGENT"]}

    for attempt in range(3):
        try:
            time.sleep(random.uniform(CONFIG["DELAY_MIN"], CONFIG["DELAY_MAX"]))
            response = requests.get(url, headers=headers, timeout=CONFIG["TIMEOUT"])
            if response.status_code == 200:
                return response
        except Exception as e:
            print(f"  Request failed ({attempt+1}/3): {e}")
    return None

def extract_group_websites_from_directory(directory_url: str) -> Set[str]:
    """Extract all group website URLs from a directory page"""
    print(f"\nScanning directory: {directory_url}")
    websites = set()

    response = make_request(directory_url)
    if not response:
        return websites

    soup = BeautifulSoup(response.content, 'html.parser')
    all_links = soup.find_all('a', href=True)

    # Filter for actual group websites
    skip_domains = ['facebook', 'twitter', 'instagram', 'youtube', 'pinterest',
                    'wwiidogtags.com', 'milsurpia.com', 'livinghistoryarchive.com',
                    'reenactor.net', 'google.com', 'wordpress.com']

    for link in all_links:
        href = link['href']

        if not href.startswith('http'):
            continue

        # Parse domain
        domain = urlparse(href).netloc.lower()

        # Skip social media and directory sites themselves
        if any(skip in domain for skip in skip_domains):
            continue

        websites.add(href)

    print(f"  Found {len(websites)} potential group websites")
    return websites

def extract_email_from_website(website_url: str) -> List[str]:
    """Extract emails from a specific website"""
    print(f"  Checking: {website_url}")
    emails = set()

    # Pages to check
    pages = [
        website_url,
        website_url.rstrip('/') + '/contact',
        website_url.rstrip('/') + '/about',
    ]

    for page_url in pages:
        response = make_request(page_url)
        if not response:
            continue

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract from text
        text = soup.get_text()
        found = extract_emails_from_text(text)
        emails.update(found)

        # Extract from mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto_links:
            email = link['href'].replace('mailto:', '').split('?')[0].strip()
            if is_valid_email(email):
                emails.add(email.lower())

        if emails:
            break  # Found emails, no need to check more pages

    if emails:
        print(f"    Found {len(emails)} email(s): {', '.join(list(emails)[:2])}")

    return list(emails)

def main():
    print("="*70)
    print("MASS WEBSITE & EMAIL COLLECTOR")
    print("="*70)

    # Step 1: Collect all group websites from directories
    print("\n--- STEP 1: Collecting group websites from directories ---")
    all_websites = set()

    for directory in CONFIG["DIRECTORIES"]:
        websites = extract_group_websites_from_directory(directory)
        all_websites.update(websites)

    print(f"\nTotal unique websites found: {len(all_websites)}")

    # Step 2: Extract emails from each website
    print("\n--- STEP 2: Extracting emails from websites ---")
    results = []

    for i, website in enumerate(sorted(all_websites), 1):
        print(f"\n[{i}/{len(all_websites)}] Processing: {website}")

        emails = extract_email_from_website(website)

        group_data = {
            "name": urlparse(website).netloc,
            "website": website,
            "email": emails[0] if emails else "",
            "all_emails": emails,
            "location": "",
            "period": "WWII",
            "source": "Directory Crawl"
        }

        results.append(group_data)

        # Limit to first 100 to save time
        if i >= 100:
            print(f"\nReached limit of 100 websites. Stopping...")
            break

    # Save results
    print("\n--- SAVING RESULTS ---")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    json_file = results_dir / f"mass_collected_{timestamp}.json"

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_websites": len(results),
            "with_emails": len([r for r in results if r["email"]])
        },
        "contacts": results
    }

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # CSV
    csv_file = results_dir / f"mass_collected_{timestamp}.csv"
    import csv

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if results:
            fieldnames = ['name', 'email', 'website', 'location', 'period', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Total websites processed: {len(results)}")
    print(f"With emails: {len([r for r in results if r['email']])}")
    print(f"\nSaved to: {json_file}")
    print(f"Saved to: {csv_file}")
    print("="*70)

if __name__ == "__main__":
    main()
