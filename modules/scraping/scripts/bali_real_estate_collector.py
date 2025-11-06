#!/usr/bin/env python3
"""
=== BALI REAL ESTATE AGENCIES COLLECTOR ===
Version: 1.0.0 | Created: 2025-11-02

PURPOSE:
Collect large real estate agencies in Bali using Google Places API
and extract contact information including emails.

FEATURES:
- Google Places API integration (Text Search + Place Details)
- Multi-query search for comprehensive coverage
- Filter for established agencies (rating, review count)
- Website and email extraction
- Rate limiting and retry logic
- Export to JSON with statistics

USAGE:
1. Get Google Places API key from: https://console.cloud.google.com/
   - Enable Places API (New)
   - Create credentials -> API key
2. Set GOOGLE_PLACES_API_KEY in .env or update CONFIG below
3. Run: python bali_real_estate_collector.py
4. Results saved to ../results/

CONFIGURATION:
- Target: 300+ agencies
- Min rating: 4.0
- Min reviews: 10
- Location: Bali, Indonesia

IMPROVEMENTS:
v1.0.0 - Initial version with Places API integration
"""

import sys
from pathlib import Path
import json
import requests
import os
import time
import random
import re
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv()

CONFIG = {
    "API_KEY": os.getenv("GOOGLE_PLACES_API_KEY", ""),
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",

    # Search parameters
    "SEARCH_QUERIES": [
        "real estate agency Bali",
        "property agency Bali",
        "villa sales Bali",
        "real estate agent Bali Indonesia",
        "property consultant Bali",
        "real estate office Bali",
        "property developer Bali",
        "villa rental agency Bali",
        "land sales agency Bali",
        "investment property Bali",
        "luxury real estate Bali",
        "commercial property Bali",
        "real estate Seminyak Bali",
        "real estate Canggu Bali",
        "real estate Ubud Bali",
        "real estate Sanur Bali",
        "real estate Denpasar Bali",
        "property management Bali",
        "villa investment Bali",
        "land developer Bali",
    ],

    # Location parameters
    "LOCATION": {
        "lat": -8.4095,  # Bali center (Ubud area)
        "lng": 115.1889,
        "radius": 50000,  # 50km radius covers most of Bali
    },

    # Filtering criteria for large agencies
    "MIN_RATING": 3.5,
    "MIN_REVIEWS": 5,
    "TARGET_COUNT": 300,

    # API settings
    "REQUEST_DELAY": (2, 4),  # Random delay between requests
    "MAX_RETRIES": 3,
    "TIMEOUT": 15,

    # Headers for website scraping
    "HEADERS": {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
}


def validate_api_key():
    """Check if API key is configured"""
    if not CONFIG["API_KEY"]:
        print("\n" + "="*70)
        print("ERROR: Google Places API key not found!")
        print("="*70)
        print("\nTo get your API key:")
        print("1. Go to: https://console.cloud.google.com/")
        print("2. Create new project or select existing")
        print("3. Enable 'Places API (New)'")
        print("4. Go to Credentials -> Create Credentials -> API Key")
        print("5. Copy the key and either:")
        print("   - Add to .env: GOOGLE_PLACES_API_KEY=your_key_here")
        print("   - Or update CONFIG['API_KEY'] in this script")
        print("\nNote: Places API has free tier ($200 credit/month)")
        print("Estimated cost for 300 agencies: ~$5-10")
        print("="*70 + "\n")
        raise ValueError("API key required")

    logger.info("API key configured")


def search_places(query, next_page_token=None):
    """
    Search for places using Google Places API Text Search

    Args:
        query: Search query string
        next_page_token: Token for pagination

    Returns:
        dict with 'results' and 'next_page_token'
    """
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': CONFIG["API_KEY"],
        'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,places.location,places.types,nextPageToken'
    }

    payload = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": CONFIG["LOCATION"]["lat"],
                    "longitude": CONFIG["LOCATION"]["lng"]
                },
                "radius": CONFIG["LOCATION"]["radius"]
            }
        },
        "maxResultCount": 20,  # Max per request
    }

    if next_page_token:
        payload["pageToken"] = next_page_token

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=CONFIG["TIMEOUT"])
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        logger.warning(f"Search failed for query: {query}", error=str(e))
        return {"places": []}


def extract_emails_from_text(text):
    """Extract email addresses from text"""
    if not text:
        return []

    # Email regex pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)

    # Filter out common false positives
    exclude_patterns = [
        'example.com', 'test.com', 'domain.com',
        'sentry.io', 'googleapis.com', 'jquery.com'
    ]

    valid_emails = []
    for email in emails:
        if not any(pattern in email.lower() for pattern in exclude_patterns):
            valid_emails.append(email.lower())

    return list(set(valid_emails))  # Remove duplicates


def scrape_website_for_emails(website_url):
    """Scrape website to find email addresses"""
    if not website_url:
        return []

    try:
        # Try homepage
        response = requests.get(website_url, headers=CONFIG["HEADERS"], timeout=CONFIG["TIMEOUT"])
        response.raise_for_status()
        emails = extract_emails_from_text(response.text)

        if emails:
            return emails

        # Try contact page if no emails on homepage
        parsed = urlparse(website_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        contact_paths = ['/contact', '/contact-us', '/about', '/about-us']
        for path in contact_paths:
            try:
                contact_url = base_url + path
                response = requests.get(contact_url, headers=CONFIG["HEADERS"], timeout=CONFIG["TIMEOUT"])
                response.raise_for_status()
                emails = extract_emails_from_text(response.text)
                if emails:
                    return emails
            except:
                continue

        return []

    except Exception as e:
        logger.debug(f"Failed to scrape emails from {website_url}", error=str(e))
        return []


def process_place(place_data):
    """Process raw place data into structured format"""
    try:
        # Extract basic info
        company = {
            "name": place_data.get("displayName", {}).get("text", "Unknown"),
            "address": place_data.get("formattedAddress", ""),
            "phone": place_data.get("internationalPhoneNumber", ""),
            "website": place_data.get("websiteUri", ""),
            "rating": place_data.get("rating", 0),
            "reviews_count": place_data.get("userRatingCount", 0),
            "place_id": place_data.get("id", ""),
            "location": place_data.get("location", {}),
            "types": place_data.get("types", []),
            "emails": [],
            "source": "Google Places API",
            "collected_at": datetime.now().isoformat(),
        }

        # Extract emails from website if available
        if company["website"]:
            logger.info(f"Scraping emails for: {company['name']}")
            company["emails"] = scrape_website_for_emails(company["website"])
            time.sleep(random.uniform(1, 2))  # Rate limiting for website scraping

        return company

    except Exception as e:
        logger.warning(f"Failed to process place", error=str(e))
        return None


def filter_large_agencies(companies):
    """Filter for established, reputable agencies"""
    filtered = []

    for company in companies:
        rating = company.get("rating", 0)
        reviews = company.get("reviews_count", 0)

        # Keep agencies with good ratings and enough reviews
        if rating >= CONFIG["MIN_RATING"] and reviews >= CONFIG["MIN_REVIEWS"]:
            filtered.append(company)

    return filtered


def deduplicate_companies(companies):
    """Remove duplicates based on place_id, name, and phone"""
    seen_ids = set()
    seen_names = set()
    seen_phones = set()
    unique = []

    for company in companies:
        place_id = company.get("place_id", "")
        name = company.get("name", "").lower().strip()
        phone = company.get("phone", "").strip()

        # Skip if duplicate
        if place_id and place_id in seen_ids:
            continue
        if name in seen_names:
            continue
        if phone and phone in seen_phones:
            continue

        # Add to unique list
        if place_id:
            seen_ids.add(place_id)
        if name:
            seen_names.add(name)
        if phone:
            seen_phones.add(phone)

        unique.append(company)

    return unique


def save_results(companies, filename="bali_real_estate_agencies"):
    """Save results to JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"{filename}_{timestamp}.json"

    CONFIG["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)

    # Calculate statistics
    with_emails = sum(1 for c in companies if c.get("emails"))
    with_website = sum(1 for c in companies if c.get("website"))
    avg_rating = sum(c.get("rating", 0) for c in companies) / len(companies) if companies else 0
    avg_reviews = sum(c.get("reviews_count", 0) for c in companies) / len(companies) if companies else 0

    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "location": "Bali, Indonesia",
            "total_agencies": len(companies),
            "target_count": CONFIG["TARGET_COUNT"],
            "progress_percent": round((len(companies) / CONFIG["TARGET_COUNT"]) * 100, 1),
            "version": "1.0.0",
        },
        "filters": {
            "min_rating": CONFIG["MIN_RATING"],
            "min_reviews": CONFIG["MIN_REVIEWS"],
        },
        "companies": companies,
        "statistics": {
            "with_emails": with_emails,
            "with_website": with_website,
            "without_contact": len(companies) - with_emails - with_website,
            "average_rating": round(avg_rating, 2),
            "average_reviews": round(avg_reviews, 1),
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved", file=str(output_file), count=len(companies))
    return output_file


def print_summary(companies, output_file):
    """Print collection summary"""
    print(f"\n{'='*70}")
    print(f"BALI REAL ESTATE AGENCIES COLLECTION SUMMARY")
    print(f"{'='*70}")
    print(f"Total Agencies Collected: {len(companies)}")
    print(f"Target: {CONFIG['TARGET_COUNT']}")
    print(f"Progress: {len(companies)} / {CONFIG['TARGET_COUNT']} ({len(companies)/CONFIG['TARGET_COUNT']*100:.1f}%)")
    print(f"\nQuality Metrics:")
    print(f"  Agencies with Email: {sum(1 for c in companies if c.get('emails'))}")
    print(f"  Agencies with Website: {sum(1 for c in companies if c.get('website'))}")
    print(f"  Agencies with Phone: {sum(1 for c in companies if c.get('phone'))}")

    if companies:
        avg_rating = sum(c.get("rating", 0) for c in companies) / len(companies)
        avg_reviews = sum(c.get("reviews_count", 0) for c in companies) / len(companies)
        print(f"\nAverage Rating: {avg_rating:.2f}")
        print(f"Average Reviews: {avg_reviews:.1f}")

        # Top agencies by rating
        print(f"\nTop 5 Agencies by Rating:")
        sorted_by_rating = sorted(companies, key=lambda x: (x.get("rating", 0), x.get("reviews_count", 0)), reverse=True)[:5]
        for i, company in enumerate(sorted_by_rating, 1):
            print(f"  {i}. {company['name']} - {company.get('rating', 0):.1f} ({company.get('reviews_count', 0)} reviews)")

    print(f"\nResults saved to: {output_file}")
    print(f"{'='*70}\n")


def main():
    logger.info("Starting Bali real estate agencies collector")

    try:
        # Validate API key
        validate_api_key()

        all_companies = []
        processed_queries = 0

        print(f"\nSearching for real estate agencies in Bali...")
        print(f"Target: {CONFIG['TARGET_COUNT']} agencies")
        print(f"Filters: Rating >= {CONFIG['MIN_RATING']}, Reviews >= {CONFIG['MIN_REVIEWS']}\n")

        # Process each search query
        for query in CONFIG["SEARCH_QUERIES"]:
            if len(all_companies) >= CONFIG["TARGET_COUNT"]:
                logger.info(f"Reached target count of {CONFIG['TARGET_COUNT']}")
                break

            logger.info(f"Searching: {query}")
            print(f"[{processed_queries + 1}/{len(CONFIG['SEARCH_QUERIES'])}] Searching: {query}")

            # Search places
            result = search_places(query)
            places = result.get("places", [])

            logger.info(f"Found {len(places)} places for query: {query}")

            # Process each place
            for place in places:
                company = process_place(place)
                if company:
                    all_companies.append(company)

            processed_queries += 1

            # Rate limiting between queries
            time.sleep(random.uniform(*CONFIG["REQUEST_DELAY"]))

        # Filter for large agencies
        logger.info(f"Total companies before filtering: {len(all_companies)}")
        filtered_companies = filter_large_agencies(all_companies)
        logger.info(f"After filtering (rating >= {CONFIG['MIN_RATING']}, reviews >= {CONFIG['MIN_REVIEWS']}): {len(filtered_companies)}")

        # Deduplicate
        unique_companies = deduplicate_companies(filtered_companies)
        logger.info(f"After deduplication: {len(unique_companies)}")

        # Sort by rating and review count
        unique_companies.sort(key=lambda x: (x.get("rating", 0), x.get("reviews_count", 0)), reverse=True)

        # Save results
        output_file = save_results(unique_companies)

        # Print summary
        print_summary(unique_companies, output_file)

        # Next steps
        if len(unique_companies) < CONFIG["TARGET_COUNT"]:
            print("SUGGESTION: To reach 300+ agencies:")
            print("1. Lower MIN_RATING to 3.5")
            print("2. Lower MIN_REVIEWS to 5")
            print("3. Add more search queries")
            print("4. Expand search radius\n")

        logger.info("Collection completed successfully")

    except Exception as e:
        logger.error("Collection failed", error=e)
        raise


if __name__ == "__main__":
    main()
