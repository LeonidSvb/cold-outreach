#!/usr/bin/env python3
"""
MEGA COLLECTOR - Collect hundreds of reenactment contacts
Systematically scrape all major directories
"""

import re
import time
import random
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

CONFIG = {
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "DELAY_MIN": 1.5,
    "DELAY_MAX": 3,
    "TIMEOUT": 15
}

def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.lower()))

def extract_emails(text: str) -> Set[str]:
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = set(re.findall(pattern, text))
    return {e.lower() for e in emails if is_valid_email(e)}

def make_request(url: str):
    """HTTP request with retry"""
    for attempt in range(2):
        try:
            time.sleep(random.uniform(CONFIG["DELAY_MIN"], CONFIG["DELAY_MAX"]))
            headers = {'User-Agent': CONFIG["USER_AGENT"]}
            response = requests.get(url, headers=headers, timeout=CONFIG["TIMEOUT"])
            if response.status_code == 200:
                return response
        except Exception as e:
            if attempt == 1:
                print(f"    Failed: {e}")
    return None

def scrape_wwiidogtags() -> List[Dict]:
    """Scrape WWIIDogTags.com units list"""
    print("\n=== WWIIDogTags.com ===")
    url = "https://wwiidogtags.com/ww2-reenacting-units/"
    groups = []

    response = make_request(url)
    if not response:
        return groups

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all links to external sites (group websites)
    all_links = soup.find_all('a', href=True)
    skip_domains = ['facebook', 'twitter', 'wwiidogtags.com', 'google']

    for link in all_links:
        href = link['href']
        text = link.text.strip()

        if not href.startswith('http') or len(text) < 3:
            continue

        domain = urlparse(href).netloc.lower()
        if any(skip in domain for skip in skip_domains):
            continue

        groups.append({
            "name": text[:100],
            "website": href,
            "email": "",
            "location": "USA",
            "period": "WWII",
            "source": "WWIIDogTags"
        })

    print(f"  Found {len(groups)} groups")
    return groups

def scrape_living_history_archive() -> List[Dict]:
    """Scrape Living History Archive"""
    print("\n=== Living History Archive ===")
    url = "https://www.livinghistoryarchive.com/group/ww2-reenactment-groups"
    groups = []

    response = make_request(url)
    if not response:
        return groups

    soup = BeautifulSoup(response.content, 'html.parser')
    all_links = soup.find_all('a', href=True)
    skip_domains = ['facebook', 'twitter', 'livinghistoryarchive.com', 'google']

    for link in all_links:
        href = link['href']
        text = link.text.strip()

        if not href.startswith('http') or len(text) < 3:
            continue

        domain = urlparse(href).netloc.lower()
        if any(skip in domain for skip in skip_domains):
            continue

        groups.append({
            "name": text[:100],
            "website": href,
            "email": "",
            "location": "International",
            "period": "WWII",
            "source": "LivingHistoryArchive"
        })

    print(f"  Found {len(groups)} groups")
    return groups

def scrape_milsurpia() -> List[Dict]:
    """Scrape Milsurpia directory"""
    print("\n=== Milsurpia.com ===")
    url = "https://www.milsurpia.com/reenactment-groups/world-war-2-reenactors"
    groups = []

    response = make_request(url)
    if not response:
        return groups

    soup = BeautifulSoup(response.content, 'html.parser')
    all_links = soup.find_all('a', href=True)
    skip_domains = ['facebook', 'twitter', 'milsurpia.com', 'google']

    for link in all_links:
        href = link['href']
        text = link.text.strip()

        if not href.startswith('http') or len(text) < 3:
            continue

        domain = urlparse(href).netloc.lower()
        if any(skip in domain for skip in skip_domains):
            continue

        groups.append({
            "name": text[:100],
            "website": href,
            "email": "",
            "location": "USA",
            "period": "WWII",
            "source": "Milsurpia"
        })

    print(f"  Found {len(groups)} groups")
    return groups

def scrape_reenactor_net() -> List[Dict]:
    """Scrape Reenactor.net"""
    print("\n=== Reenactor.net ===")
    url = "https://www.reenactor.net/index.php?page=70"
    groups = []

    response = make_request(url)
    if not response:
        return groups

    soup = BeautifulSoup(response.content, 'html.parser')
    all_links = soup.find_all('a', href=True)
    skip_domains = ['facebook', 'twitter', 'reenactor.net', 'google']

    for link in all_links:
        href = link['href']
        text = link.text.strip()

        if not href.startswith('http') or len(text) < 3:
            continue

        domain = urlparse(href).netloc.lower()
        if any(skip in domain for skip in skip_domains):
            continue

        groups.append({
            "name": text[:100],
            "website": href,
            "email": "",
            "location": "USA",
            "period": "WWII",
            "source": "ReenactorNet"
        })

    print(f"  Found {len(groups)} groups")
    return groups

def extract_email_from_site(url: str) -> str:
    """Quick email extraction from website"""
    try:
        response = make_request(url)
        if not response:
            return ""

        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        emails = extract_emails(text)

        # Check mailto links
        mailto = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
        for link in mailto:
            email = link['href'].replace('mailto:', '').split('?')[0].strip()
            if is_valid_email(email):
                emails.add(email.lower())

        return list(emails)[0] if emails else ""
    except:
        return ""

def main():
    print("="*70)
    print("MEGA COLLECTOR - Collecting hundreds of contacts")
    print("="*70)

    all_groups = []

    # Step 1: Collect websites from directories
    print("\n--- PHASE 1: Collecting websites from directories ---")

    all_groups.extend(scrape_wwiidogtags())
    all_groups.extend(scrape_living_history_archive())
    all_groups.extend(scrape_milsurpia())
    all_groups.extend(scrape_reenactor_net())

    # Deduplicate by website
    unique_websites = {}
    for group in all_groups:
        website = group.get("website", "").lower().strip()
        if website and website not in unique_websites:
            unique_websites[website] = group

    unique_groups = list(unique_websites.values())

    print(f"\n--- PHASE 1 COMPLETE ---")
    print(f"Total unique websites collected: {len(unique_groups)}")

    # Step 2: Extract emails from websites (limit to first 150 to save time)
    print(f"\n--- PHASE 2: Extracting emails from websites (limit: 150) ---")

    for i, group in enumerate(unique_groups[:150], 1):
        website = group["website"]
        print(f"[{i}/150] {website[:50]}...", end=" ")

        email = extract_email_from_site(website)
        if email:
            group["email"] = email
            print(f"[OK] {email}")
        else:
            print("[NONE]")

        if i % 10 == 0:
            print(f"  Progress: {i}/150 websites processed")

    # Step 3: Save results
    print("\n--- SAVING RESULTS ---")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    json_file = results_dir / f"mega_collection_{timestamp}.json"

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_contacts": len(unique_groups),
            "with_emails": len([g for g in unique_groups if g.get("email")])
        },
        "contacts": unique_groups
    }

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # CSV
    csv_file = results_dir / f"mega_collection_{timestamp}.csv"
    import csv
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if unique_groups:
            fieldnames = ['name', 'email', 'website', 'location', 'period', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(unique_groups)

    print("\n" + "="*70)
    print("MEGA COLLECTION COMPLETE")
    print("="*70)
    print(f"Total websites: {len(unique_groups)}")
    print(f"With emails: {len([g for g in unique_groups if g.get('email')])}")
    print(f"\nSaved to:")
    print(f"  JSON: {json_file}")
    print(f"  CSV: {csv_file}")
    print("="*70)

if __name__ == "__main__":
    main()
