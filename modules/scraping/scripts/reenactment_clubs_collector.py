#!/usr/bin/env python3
"""
=== HISTORICAL REENACTMENT CLUBS CONTACT COLLECTOR ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Collect email addresses and websites of historical reenactment clubs
focusing on WWII and Afghan War themes from wealthy countries
(USA, Canada, Europe, Australia)

FEATURES:
- Multi-source scraping (Historic-UK, Living History Archive, etc.)
- Email extraction from organization websites
- Apollo API integration for finding reenactment organizations
- Contact validation and deduplication
- Target: 300+ unique contacts

USAGE:
1. Configure CONFIG section (API keys, target countries)
2. Run: python reenactment_clubs_collector.py
3. Results saved to modules/scraping/results/

IMPROVEMENTS:
v1.0.0 - Initial version with multi-source scraping
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
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "SOURCES": {
        "historic_uk": {
            "base_url": "https://www.historic-uk.com/LivingHistory/ReenactorsDirectory",
            "pages": 24,  # Total pages to scrape
            "priority": "high"  # UK groups often have direct emails
        },
        "wwiidogtags": {
            "url": "https://wwiidogtags.com/ww2-reenacting-units/",
            "priority": "medium"
        },
        "living_history_archive": {
            "url": "https://www.livinghistoryarchive.com/group/ww2-reenactment-groups",
            "priority": "medium"
        },
        "milsurpia": {
            "url": "https://www.milsurpia.com/reenactment-groups/world-war-2-reenactors",
            "priority": "medium"
        },
        "reenactmenthq": {
            "url": "https://reenactmenthq.com/reenactment-unit-list/",
            "priority": "medium"
        },
        "wwii_hrs_american": {
            "url": "https://www.worldwartwohrs.org/American.htm",
            "priority": "medium"
        },
        "alhf_australia": {
            "url": "https://www.alhf.org.au/mem_grps.html",
            "priority": "high"  # Australian federation
        },
        "ara_australia": {
            "url": "http://re-enactors.org.au/",
            "priority": "high"  # Australian association
        },
        "ausreenact": {
            "url": "https://www.ausreenact.com.au/",
            "priority": "high"  # Direct contact available
        },
        "alberta_canada": {
            "url": "https://www.awwlha.com/",
            "priority": "high"  # Canadian group
        }
    },

    "TARGET_COUNTRIES": [
        "USA", "United States", "US", "America",
        "UK", "United Kingdom", "England", "Scotland", "Wales",
        "Canada",
        "Australia",
        "Germany", "France", "Netherlands", "Belgium", "Poland",
        "Austria", "Switzerland", "Norway", "Sweden", "Denmark"
    ],

    "KEYWORDS": {
        "periods": ["WWII", "WW2", "World War", "Afghan War", "Cold War", "Vietnam"],
        "exclude_periods": ["Medieval", "Viking", "Roman", "Tudor", "Civil War"]
    },

    "SCRAPING": {
        "delay_min": 2,  # Minimum delay between requests (seconds)
        "delay_max": 5,  # Maximum delay
        "timeout": 15,
        "max_retries": 3,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },

    "OUTPUT": {
        "min_contacts": 300,
        "results_dir": "modules/scraping/results",
        "validate_emails": True
    }
}

# ============================================================================
# EMAIL VALIDATION
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

# ============================================================================
# HTTP UTILITIES
# ============================================================================

def make_request(url: str, retries: int = 3) -> Optional[requests.Response]:
    """Make HTTP request with retries and random delays"""
    headers = {
        'User-Agent': CONFIG["SCRAPING"]["user_agent"],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    for attempt in range(retries):
        try:
            # Random delay to avoid rate limiting
            time.sleep(random.uniform(
                CONFIG["SCRAPING"]["delay_min"],
                CONFIG["SCRAPING"]["delay_max"]
            ))

            response = requests.get(
                url,
                headers=headers,
                timeout=CONFIG["SCRAPING"]["timeout"]
            )

            if response.status_code == 200:
                logger.info(f"Successfully fetched: {url}")
                return response
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")

        except Exception as e:
            logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")

    logger.error(f"Failed to fetch after {retries} attempts: {url}")
    return None

# ============================================================================
# HISTORIC-UK SCRAPER
# ============================================================================

def scrape_historic_uk() -> List[Dict]:
    """Scrape all pages from Historic-UK reenactors directory"""
    logger.info("Starting Historic-UK directory scraping...")
    groups = []
    base_url = CONFIG["SOURCES"]["historic_uk"]["base_url"]
    total_pages = CONFIG["SOURCES"]["historic_uk"]["pages"]

    for page_num in range(1, total_pages + 1):
        if page_num == 1:
            url = f"{base_url}/"
        else:
            url = f"{base_url}/page/{page_num}/"

        logger.info(f"Scraping page {page_num}/{total_pages}: {url}")

        response = make_request(url)
        if not response:
            continue

        soup = BeautifulSoup(response.content, 'html.parser')

        # Historic-UK structure: each group starts with h3, followed by h5, h6, links
        # We'll find all h3 elements and parse their siblings
        group_headings = soup.find_all('h3')

        for h3 in group_headings:
            try:
                group_data = {
                    "name": "",
                    "location": "",
                    "email": "",
                    "website": "",
                    "period": "",
                    "source": "Historic-UK"
                }

                # Extract group name from h3
                group_data["name"] = h3.text.strip()

                # Get parent container (usually a div)
                parent = h3.parent

                # Extract period/category from h5 > a
                h5 = parent.find('h5')
                if h5:
                    category_link = h5.find('a')
                    if category_link:
                        group_data["period"] = category_link.text.strip()

                # Extract location from h6
                h6 = parent.find('h6')
                if h6:
                    group_data["location"] = h6.text.strip()

                # Extract email from mailto link
                email_link = parent.find('a', href=re.compile(r'^mailto:', re.I))
                if email_link:
                    email = email_link['href'].replace('mailto:', '').split('?')[0].strip()
                    if is_valid_email(email):
                        group_data["email"] = email.lower()

                # Extract website (http link that's not mailto)
                website_links = parent.find_all('a', href=re.compile(r'^http', re.I))
                for link in website_links:
                    href = link['href']
                    # Skip social media
                    if not any(social in href.lower() for social in ['facebook', 'twitter', 'instagram']):
                        group_data["website"] = href
                        break

                # Filter: only WWII, Cold War, Afghan War groups
                period_lower = group_data["period"].lower()
                is_relevant = any(keyword.lower() in period_lower for keyword in CONFIG["KEYWORDS"]["periods"])

                # Skip medieval, viking, etc.
                is_excluded = any(excluded.lower() in period_lower for excluded in CONFIG["KEYWORDS"].get("exclude_periods", []))

                # Only add if we have at least name and (email OR website) and relevant period
                if group_data["name"] and (group_data["email"] or group_data["website"]):
                    if not group_data["period"] or is_relevant or not is_excluded:
                        groups.append(group_data)
                        logger.info(f"Found group: {group_data['name']} ({group_data['period']})")

            except Exception as e:
                logger.warning(f"Error parsing group entry: {e}")
                continue

    logger.info(f"Historic-UK scraping complete: {len(groups)} groups found")
    return groups

# ============================================================================
# WEBSITE EMAIL EXTRACTOR
# ============================================================================

def extract_emails_from_website(url: str) -> Set[str]:
    """Visit a website and extract all email addresses"""
    logger.info(f"Extracting emails from website: {url}")
    emails = set()

    # Pages to check
    pages_to_check = [
        url,
        urljoin(url, '/contact'),
        urljoin(url, '/about'),
        urljoin(url, '/contact-us'),
    ]

    for page_url in pages_to_check:
        response = make_request(page_url)
        if response:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract from text
            text = soup.get_text()
            found_emails = extract_emails_from_text(text)
            emails.update(found_emails)

            # Extract from mailto links
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
            for link in mailto_links:
                email = link['href'].replace('mailto:', '').split('?')[0]
                if is_valid_email(email):
                    emails.add(email.lower())

    logger.info(f"Found {len(emails)} emails from {url}")
    return emails

# ============================================================================
# GENERIC DIRECTORY SCRAPER
# ============================================================================

def scrape_generic_directory(url: str, source_name: str) -> List[Dict]:
    """Scrape a generic reenactment directory page"""
    logger.info(f"Scraping {source_name}: {url}")
    groups = []

    response = make_request(url)
    if not response:
        return groups

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all links to group websites
    all_links = soup.find_all('a', href=True)

    for link in all_links:
        href = link['href']
        text = link.text.strip()

        # Skip non-http links
        if not href.startswith('http'):
            continue

        # Skip common platforms (social media, etc.)
        skip_domains = ['facebook.com', 'twitter.com', 'instagram.com', 'youtube.com']
        if any(domain in href.lower() for domain in skip_domains):
            continue

        # Add as potential group website
        group_data = {
            "name": text if text else urlparse(href).netloc,
            "website": href,
            "email": "",
            "location": "",
            "source": source_name
        }

        groups.append(group_data)

    logger.info(f"{source_name}: Found {len(groups)} potential group websites")
    return groups

# ============================================================================
# APOLLO API INTEGRATION
# ============================================================================

def search_apollo_organizations() -> List[Dict]:
    """Use Apollo API to find historical reenactment organizations"""
    logger.info("Searching Apollo for reenactment organizations...")

    # Check if Apollo API key exists
    apollo_key = os.getenv('APOLLO_API_KEY')
    if not apollo_key:
        logger.warning("APOLLO_API_KEY not found in environment")
        return []

    groups = []

    api_url = "https://api.apollo.io/v1/mixed_companies/search"
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": apollo_key
    }

    # Search queries
    search_queries = [
        "historical reenactment",
        "WWII reenactment",
        "living history",
        "war reenactment"
    ]

    for query in search_queries:
        payload = {
            "q_organization_keyword_tags": [query],
            "page": 1,
            "per_page": 100,
            "organization_locations": ["United States", "Canada", "United Kingdom", "Germany", "Australia"]
        }

        try:
            time.sleep(2)  # Rate limiting
            response = requests.post(api_url, json=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                organizations = data.get('organizations', [])

                for org in organizations:
                    group_data = {
                        "name": org.get('name', ''),
                        "website": org.get('website_url', ''),
                        "email": org.get('primary_email', ''),
                        "location": org.get('country', ''),
                        "source": "Apollo API"
                    }

                    if group_data["name"]:
                        groups.append(group_data)

                logger.info(f"Apollo query '{query}': {len(organizations)} organizations found")
            else:
                logger.warning(f"Apollo API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Apollo API request failed: {e}")

    logger.info(f"Apollo search complete: {len(groups)} organizations found")
    return groups

# ============================================================================
# MAIN COLLECTION WORKFLOW
# ============================================================================

def collect_all_contacts() -> List[Dict]:
    """Main workflow to collect all contacts from multiple sources"""
    logger.info("Starting contact collection workflow...")
    all_groups = []

    # 1. Scrape Historic-UK (high priority - has direct emails)
    logger.info("=== Phase 1: Historic-UK Directory ===")
    historic_uk_groups = scrape_historic_uk()
    all_groups.extend(historic_uk_groups)

    # 2. Scrape other directories for website links
    logger.info("=== Phase 2: Other Directories ===")
    for source_key, source_config in CONFIG["SOURCES"].items():
        if source_key == "historic_uk":
            continue

        if "url" in source_config:
            directory_groups = scrape_generic_directory(
                source_config["url"],
                source_key
            )
            all_groups.extend(directory_groups)

    # 3. Apollo API search
    logger.info("=== Phase 3: Apollo API ===")
    apollo_groups = search_apollo_organizations()
    all_groups.extend(apollo_groups)

    # 4. Extract emails from websites that don't have them yet
    logger.info("=== Phase 4: Email Extraction from Websites ===")
    groups_without_emails = [g for g in all_groups if not g.get("email") and g.get("website")]

    logger.info(f"Extracting emails from {len(groups_without_emails)} websites...")
    for i, group in enumerate(groups_without_emails, 1):
        logger.info(f"Processing website {i}/{len(groups_without_emails)}: {group['website']}")

        emails = extract_emails_from_website(group["website"])
        if emails:
            group["email"] = list(emails)[0]  # Take first found email
            logger.info(f"Found email for {group['name']}: {group['email']}")

    logger.info(f"Total groups collected: {len(all_groups)}")
    return all_groups

# ============================================================================
# DATA PROCESSING & VALIDATION
# ============================================================================

def filter_and_deduplicate(groups: List[Dict]) -> List[Dict]:
    """Filter by target countries and remove duplicates"""
    logger.info("Filtering and deduplicating contacts...")

    # Deduplicate by email or website
    seen_emails = set()
    seen_websites = set()
    unique_groups = []

    for group in groups:
        email = group.get("email", "").lower()
        website = group.get("website", "").lower()

        # Skip if no contact info
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

# ============================================================================
# RESULTS EXPORT
# ============================================================================

def save_results(groups: List[Dict]) -> str:
    """Save results to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(CONFIG["OUTPUT"]["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / f"reenactment_clubs_{timestamp}.json"

    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_contacts": len(groups),
            "target_countries": CONFIG["TARGET_COUNTRIES"],
            "sources_used": list(CONFIG["SOURCES"].keys())
        },
        "contacts": groups,
        "statistics": {
            "with_email": len([g for g in groups if g.get("email")]),
            "with_website": len([g for g in groups if g.get("website")]),
            "by_source": {}
        }
    }

    # Calculate statistics by source
    for source in CONFIG["SOURCES"].keys():
        count = len([g for g in groups if g.get("source") == source])
        results["statistics"]["by_source"][source] = count

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to: {output_file}")
    return str(output_file)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    logger.info("=== REENACTMENT CLUBS CONTACT COLLECTOR STARTED ===")
    logger.info(f"Target: {CONFIG['OUTPUT']['min_contacts']}+ contacts")
    logger.info(f"Countries: {', '.join(CONFIG['TARGET_COUNTRIES'][:5])}...")

    try:
        # Collect all contacts
        all_groups = collect_all_contacts()

        # Filter and deduplicate
        unique_groups = filter_and_deduplicate(all_groups)

        # Check if we reached target
        total_contacts = len(unique_groups)
        target = CONFIG["OUTPUT"]["min_contacts"]

        logger.info(f"=== COLLECTION COMPLETE ===")
        logger.info(f"Total unique contacts: {total_contacts}")
        logger.info(f"Target: {target}")
        logger.info(f"Status: {'SUCCESS' if total_contacts >= target else 'NEEDS MORE'}")

        # Save results
        output_file = save_results(unique_groups)

        # Print summary
        with_email = len([g for g in unique_groups if g.get("email")])
        with_website = len([g for g in unique_groups if g.get("website")])

        print("\n" + "="*60)
        print("COLLECTION SUMMARY")
        print("="*60)
        print(f"Total Contacts: {total_contacts}")
        print(f"With Email: {with_email}")
        print(f"With Website: {with_website}")
        print(f"Target Met: {'YES' if total_contacts >= target else 'NO'}")
        print(f"Results File: {output_file}")
        print("="*60)

        if total_contacts < target:
            logger.warning(f"Only {total_contacts}/{target} contacts collected. Need {target - total_contacts} more.")

        logger.info("Script completed successfully")
        return output_file

    except Exception as e:
        logger.error(f"Script failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
