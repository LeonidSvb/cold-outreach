#!/usr/bin/env python3
"""
=== FINAL REENACTMENT CLUBS COLLECTOR ===
Version: 2.0.0 | Created: 2025-01-19

PURPOSE:
Collect 300+ reenactment club contacts using multiple strategies:
1. Known groups database (manual additions)
2. Email extraction from group websites
3. Web search for additional groups
4. Apollo API (if available)

TARGET: 300+ contacts from USA, Canada, Europe, Australia
"""

import sys
import os
import json
import re
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "TARGET_CONTACTS": 300,
    "SCRAPING": {
        "delay_min": 2,
        "delay_max": 4,
        "timeout": 15,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    "WEBSITES_TO_SCRAPE": [
        # USA
        "https://www.armygroup1944.org/",
        "https://www.wwiirc.org/",
        "http://www.ww2uso.org/",
        "https://26yd.com/",
        "https://www.chgww2.net/",
        "http://worldwar2reenactors.org/",
        "https://www.ddayohio.us/",
        "https://worldwartwohrs.org/",
        # Australia
        "https://www.ausreenact.com.au/",
        "https://www.nmrg.com.au/",
        "http://geelongmrg.com/",
        "https://www.alhf.org.au/",
        "http://re-enactors.org.au/",
        "https://www.reenactsa.com/",
        # Canada
        "https://www.awwlha.com/",
        # Europe
        "https://www.safar-publishing.com/",  # Afghan War reenactment
    ]
}

# ============================================================================
# UTILITIES
# ============================================================================

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.lower()))

def extract_emails_from_text(text: str) -> Set[str]:
    """Extract all email addresses from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = set(re.findall(email_pattern, text))
    return {email.lower() for email in emails if is_valid_email(email)}

def make_request(url: str) -> Optional[requests.Response]:
    """Make HTTP request with retry logic"""
    headers = {'User-Agent': CONFIG["SCRAPING"]["user_agent"]}

    for attempt in range(3):
        try:
            time.sleep(random.uniform(
                CONFIG["SCRAPING"]["delay_min"],
                CONFIG["SCRAPING"]["delay_max"]
            ))

            response = requests.get(url, headers=headers, timeout=CONFIG["SCRAPING"]["timeout"])

            if response.status_code == 200:
                return response

        except Exception as e:
            logger.warning(f"Request failed (attempt {attempt + 1}/3): {e}")

    return None

# ============================================================================
# DATA SOURCES
# ============================================================================

def load_known_groups() -> List[Dict]:
    """Load manually researched groups"""
    logger.info("Loading known groups database...")

    known_file = Path("modules/scraping/data/known_groups.json")

    if known_file.exists():
        with open(known_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            groups = data.get("manual_additions", [])
            logger.info(f"Loaded {len(groups)} known groups")
            return groups
    else:
        logger.warning("Known groups file not found")
        return []

def extract_emails_from_website(url: str) -> Set[str]:
    """Extract emails from a website"""
    logger.info(f"Extracting emails from: {url}")
    emails = set()

    pages = [
        url,
        urljoin(url, '/contact'),
        urljoin(url, '/contact-us'),
        urljoin(url, '/about'),
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
            break  # Stop if we found emails

    logger.info(f"Found {len(emails)} emails from {url}")
    return emails

def scrape_all_websites() -> List[Dict]:
    """Scrape all target websites for contact info"""
    logger.info(f"Scraping {len(CONFIG['WEBSITES_TO_SCRAPE'])} websites...")
    results = []

    for i, website in enumerate(CONFIG['WEBSITES_TO_SCRAPE'], 1):
        logger.info(f"[{i}/{len(CONFIG['WEBSITES_TO_SCRAPE'])}] {website}")

        emails = extract_emails_from_website(website)

        if emails or True:  # Add even if no emails (we have website)
            group_data = {
                "name": website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0],
                "website": website,
                "email": list(emails)[0] if emails else "",
                "all_emails": list(emails),
                "location": "",
                "period": "WWII/Cold War",
                "source": "Website Scraping"
            }
            results.append(group_data)

    logger.info(f"Scraping complete: {len(results)} groups")
    return results

def search_apollo_organizations() -> List[Dict]:
    """Search Apollo API for reenactment organizations"""
    logger.info("Searching Apollo API...")

    apollo_key = os.getenv('APOLLO_API_KEY')
    if not apollo_key:
        logger.warning("APOLLO_API_KEY not found")
        return []

    groups = []
    api_url = "https://api.apollo.io/v1/mixed_companies/search"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": apollo_key
    }

    queries = [
        "WWII reenactment",
        "historical reenactment",
        "living history",
        "military reenactment"
    ]

    for query in queries:
        payload = {
            "q_organization_keyword_tags": [query],
            "page": 1,
            "per_page": 100,
            "organization_locations": [
                "United States", "Canada", "United Kingdom",
                "Germany", "Australia", "France"
            ]
        }

        try:
            time.sleep(2)
            response = requests.post(api_url, json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                orgs = data.get('organizations', [])

                for org in orgs:
                    group_data = {
                        "name": org.get('name', ''),
                        "website": org.get('website_url', ''),
                        "email": org.get('primary_email', ''),
                        "location": org.get('country', ''),
                        "period": "WWII/Historical",
                        "source": "Apollo API"
                    }

                    if group_data["name"]:
                        groups.append(group_data)

                logger.info(f"Apollo '{query}': {len(orgs)} found")

        except Exception as e:
            logger.error(f"Apollo error: {e}")

    logger.info(f"Apollo total: {len(groups)} organizations")
    return groups

def search_google_for_groups() -> List[Dict]:
    """
    Placeholder for additional group discovery
    In reality, this would use web search or APIs
    """
    logger.info("Additional group discovery...")

    # List of additional known websites from research
    additional_sites = [
        {"name": "ReenactmentHQ", "website": "https://reenactmenthq.com/", "location": "USA"},
        {"name": "Epic Militaria Groups", "website": "https://www.epicmilitaria.com/reenactment", "location": "UK"},
        {"name": "Milsurpia WW2 Groups", "website": "https://www.milsurpia.com/reenactment-groups/", "location": "International"},
        {"name": "Living History Archive", "website": "https://www.livinghistoryarchive.com/", "location": "International"},
    ]

    groups = []
    for site in additional_sites:
        groups.append({
            **site,
            "email": "",
            "period": "WWII",
            "source": "Directory Sites"
        })

    return groups

# ============================================================================
# DATA PROCESSING
# ============================================================================

def merge_and_deduplicate(all_groups: List[Dict]) -> List[Dict]:
    """Merge from all sources and remove duplicates"""
    logger.info(f"Merging {len(all_groups)} groups...")

    seen_emails = set()
    seen_websites = set()
    unique_groups = []

    for group in all_groups:
        email = group.get("email", "").lower().strip()
        website = group.get("website", "").lower().strip()

        # Skip if no contact method
        if not email and not website:
            continue

        # Skip duplicates
        if email and email in seen_emails:
            continue
        if website and website in seen_websites:
            continue

        # Add to unique list
        unique_groups.append(group)

        if email:
            seen_emails.add(email)
        if website:
            seen_websites.add(website)

    logger.info(f"After deduplication: {len(unique_groups)} unique contacts")
    return unique_groups

def enhance_with_emails(groups: List[Dict]) -> List[Dict]:
    """For groups with websites but no emails, try to find emails"""
    logger.info("Enhancing groups with missing emails...")

    groups_needing_emails = [g for g in groups if g.get("website") and not g.get("email")]
    logger.info(f"{len(groups_needing_emails)} groups need emails")

    for i, group in enumerate(groups_needing_emails, 1):
        if i > 50:  # Limit to first 50 to save time
            break

        logger.info(f"[{i}/50] Extracting from {group['website']}")
        emails = extract_emails_from_website(group["website"])

        if emails:
            group["email"] = list(emails)[0]
            group["all_emails"] = list(emails)
            logger.info(f"Found email: {group['email']}")

    return groups

# ============================================================================
# EXPORT
# ============================================================================

def save_results(groups: List[Dict]) -> str:
    """Save final results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    json_file = results_dir / f"reenactment_clubs_final_{timestamp}.json"

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_contacts": len(groups),
            "target": CONFIG["TARGET_CONTACTS"],
            "target_met": len(groups) >= CONFIG["TARGET_CONTACTS"]
        },
        "contacts": groups,
        "statistics": {
            "with_email": len([g for g in groups if g.get("email")]),
            "with_website": len([g for g in groups if g.get("website")]),
            "by_source": {}
        }
    }

    # Statistics by source
    sources = set(g.get("source", "Unknown") for g in groups)
    for source in sources:
        count = len([g for g in groups if g.get("source") == source])
        output["statistics"]["by_source"][source] = count

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved: {json_file}")

    # Also save CSV
    csv_file = results_dir / f"reenactment_clubs_final_{timestamp}.csv"
    import csv

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if groups:
            fieldnames = ['name', 'email', 'website', 'location', 'period', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(groups)

    logger.info(f"CSV saved: {csv_file}")

    return str(json_file)

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""
    logger.info("=== FINAL REENACTMENT CLUBS COLLECTOR ===")
    logger.info(f"Target: {CONFIG['TARGET_CONTACTS']} contacts")

    all_groups = []

    # Step 1: Load known groups
    logger.info("\n--- STEP 1: Known Groups ---")
    known = load_known_groups()
    all_groups.extend(known)
    logger.info(f"Added {len(known)} known groups")

    # Step 2: Scrape websites
    logger.info("\n--- STEP 2: Website Scraping ---")
    scraped = scrape_all_websites()
    all_groups.extend(scraped)
    logger.info(f"Added {len(scraped)} from scraping")

    # Step 3: Additional directories
    logger.info("\n--- STEP 3: Additional Sources ---")
    additional = search_google_for_groups()
    all_groups.extend(additional)
    logger.info(f"Added {len(additional)} from directories")

    # Step 4: Apollo API
    logger.info("\n--- STEP 4: Apollo API ---")
    apollo_groups = search_apollo_organizations()
    all_groups.extend(apollo_groups)
    logger.info(f"Added {len(apollo_groups)} from Apollo")

    # Step 5: Deduplicate
    logger.info("\n--- STEP 5: Deduplication ---")
    unique_groups = merge_and_deduplicate(all_groups)

    # Step 6: Enhance with emails
    logger.info("\n--- STEP 6: Email Enhancement ---")
    enhanced_groups = enhance_with_emails(unique_groups)

    # Final results
    total = len(enhanced_groups)
    target = CONFIG["TARGET_CONTACTS"]

    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"Total Contacts: {total}")
    print(f"Target: {target}")
    print(f"Status: {'SUCCESS' if total >= target else f'NEED {target - total} MORE'}")
    print(f"\nWith Email: {len([g for g in enhanced_groups if g.get('email')])}")
    print(f"With Website: {len([g for g in enhanced_groups if g.get('website')])}")
    print("\nBy Source:")
    sources = {}
    for group in enhanced_groups:
        source = group.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1

    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")
    print("="*70)

    # Save
    output_file = save_results(enhanced_groups)
    print(f"\nResults saved to: {output_file}")

    logger.info("Collection complete!")

if __name__ == "__main__":
    main()
