#!/usr/bin/env python3
"""Extract emails from known websites that don't have contacts yet"""

import re
import time
import random
import json
from pathlib import Path
from datetime import datetime
from typing import Set
import requests
from bs4 import BeautifulSoup

# Known websites without emails
WEBSITES = [
    "https://www.ausreenact.com.au/",
    "https://www.nmrg.com.au/",
    "http://geelongmrg.com/",
    "https://www.alhf.org.au/",
    "http://re-enactors.org.au/",
    "https://www.awwlha.com/",
    "https://worldwartwohrs.org/",
    "https://26yd.com/",
    "https://www.ddayohio.us/",
    "https://www.chgww2.net/",
    "https://eastpennreenactorsgroup.weebly.com/",
    "http://worldwar2reenactors.org/",
    "https://www.armygroup1944.org/",
    "https://www.wwiirc.org/",
    "http://www.ww2uso.org/",
    "https://sites.google.com/view/coldwarrreenactmentgroup/",
    "http://www.29thdivision.com/",
]

def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.lower()))

def extract_emails_from_text(text: str) -> Set[str]:
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = set(re.findall(email_pattern, text))
    return {email.lower() for email in emails if is_valid_email(email)}

def get_emails_from_website(url: str):
    """Extract emails from website"""
    print(f"\n[{WEBSITES.index(url)+1}/{len(WEBSITES)}] Processing: {url}")

    pages = [url, url.rstrip('/') + '/contact', url.rstrip('/') + '/about']
    emails = set()

    for page in pages:
        try:
            time.sleep(random.uniform(2, 4))
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(page, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract from text
                text = soup.get_text()
                found = extract_emails_from_text(text)
                emails.update(found)

                # Extract from mailto
                mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
                for link in mailto_links:
                    email = link['href'].replace('mailto:', '').split('?')[0].strip()
                    if is_valid_email(email):
                        emails.add(email.lower())

                if emails:
                    break
        except Exception as e:
            print(f"  Error: {e}")
            continue

    if emails:
        print(f"  [OK] Found {len(emails)} email(s): {', '.join(list(emails)[:2])}")
    else:
        print(f"  [NONE] No emails found")

    return list(emails)

def main():
    print("="*70)
    print("EXTRACTING EMAILS FROM KNOWN WEBSITES")
    print("="*70)
    print(f"Processing {len(WEBSITES)} websites...\n")

    results = []

    for url in WEBSITES:
        emails = get_emails_from_website(url)
        results.append({
            "website": url,
            "emails": emails
        })

    # Load existing data
    known_file = Path("modules/scraping/data/known_groups.json")
    with open(known_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        groups = data["manual_additions"]

    # Update groups with found emails
    updated = 0
    for group in groups:
        group_website = group.get("website", "")
        for result in results:
            if result["website"] == group_website and result["emails"]:
                if not group.get("email"):
                    group["email"] = result["emails"][0]
                    group["all_emails"] = result["emails"]
                    updated += 1

    # Save updated data
    with open(known_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print(f"RESULTS: Updated {updated} groups with email addresses")
    print("="*70)

    # Save extraction results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = Path(f"modules/scraping/results/email_extraction_{timestamp}.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({"extraction_results": results}, f, indent=2)

    print(f"Saved to: {results_file}")

if __name__ == "__main__":
    main()
