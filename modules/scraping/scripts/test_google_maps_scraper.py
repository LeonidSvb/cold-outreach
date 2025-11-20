#!/usr/bin/env python3
"""
=== GOOGLE MAPS EMAIL SCRAPER TEST ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Test Google Maps/Places scraping for email extraction

FEATURES:
- Google Search API for Maps listings
- Email extraction from business profiles
- Test on companies WITHOUT websites

USAGE:
1. Configure RapidAPI key in .env
2. Run: python test_google_maps_scraper.py
3. Results printed to console
"""

import re
import time
import random
import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Downloads\All Australian Cafes - No Email for Upwork (2).csv",
    "TEST_SAMPLE_SIZE": 10,
    "RAPIDAPI_KEY": os.getenv("RAPIDAPI_KEY"),
    "RAPIDAPI_HOST": "google-search72.p.rapidapi.com",
    "DELAY_BETWEEN_REQUESTS": (2, 4),
}

EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)


def search_business_on_google(business_name, city, phone):
    """Search for business on Google and extract contact info"""
    try:
        # Build search query
        query = f'"{business_name}" "{city}" Australia email contact'

        print(f"Searching Google: {query}")

        # Make request to RapidAPI Google Search
        url = "https://google-search72.p.rapidapi.com/search"

        querystring = {
            "q": query,
            "gl": "au",
            "lr": "lang_en",
            "num": "10",
            "start": "0"
        }

        headers = {
            "x-rapidapi-host": CONFIG["RAPIDAPI_HOST"],
            "x-rapidapi-key": CONFIG["RAPIDAPI_KEY"]
        }

        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status()

        data = response.json()

        # Extract emails from search results
        emails = set()

        # Check if results exist
        if 'items' in data:
            for item in data.get('items', []):
                # Check snippet
                snippet = item.get('snippet', '')
                found_emails = EMAIL_PATTERN.findall(snippet)
                emails.update([e.lower() for e in found_emails])

                # Check title
                title = item.get('title', '')
                found_emails = EMAIL_PATTERN.findall(title)
                emails.update([e.lower() for e in found_emails])

        return {
            'success': True,
            'emails': list(emails),
            'results_count': len(data.get('items', [])),
            'query': query
        }

    except requests.exceptions.RequestException as e:
        print(f"  Request error: {e}")
        return {'success': False, 'error': str(e), 'query': query}

    except Exception as e:
        print(f"  Unexpected error: {e}")
        return {'success': False, 'error': str(e), 'query': query}


def main():
    print("="*60)
    print("=== Google Maps/Search Email Scraper Test ===")
    print("="*60)

    # Check API key
    if not CONFIG["RAPIDAPI_KEY"]:
        print("\n[ERROR] RAPIDAPI_KEY not found in .env file!")
        print("Please add: RAPIDAPI_KEY=your_key_here")
        return

    # Load data
    print(f"\nLoading data from: {CONFIG['INPUT_FILE']}")
    df = pd.read_csv(CONFIG['INPUT_FILE'])

    # Filter companies WITHOUT websites (harder to find emails)
    df_no_website = df[df['website'].isna() | (df['website'] == '')].copy()
    print(f"Companies WITHOUT websites: {len(df_no_website)}")

    # Take test sample
    sample_df = df_no_website.head(CONFIG['TEST_SAMPLE_SIZE'])
    print(f"Testing on {len(sample_df)} companies\n")

    # Test scraping
    results = []

    for idx, row in sample_df.iterrows():
        business_name = row['Business Name']
        city = row['search_city']
        phone = row.get('phone', '')

        print(f"\n[{idx+1}/{len(sample_df)}] {business_name} ({city})")
        print(f"Phone: {phone}")

        # Search on Google
        result = search_business_on_google(business_name, city, phone)

        result['business_name'] = business_name
        result['city'] = city
        result['phone'] = phone
        results.append(result)

        # Show result
        if result['success']:
            if result['emails']:
                print(f"[SUCCESS] Found {len(result['emails'])} email(s): {', '.join(result['emails'])}")
            else:
                print(f"[WARNING] No emails in {result.get('results_count', 0)} search results")
        else:
            print(f"[FAILED] {result.get('error', 'unknown')}")

        # Rate limiting
        if idx < len(sample_df) - 1:
            delay = random.uniform(*CONFIG['DELAY_BETWEEN_REQUESTS'])
            print(f"  Waiting {delay:.1f}s...")
            time.sleep(delay)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    successful = [r for r in results if r['success']]
    with_emails = [r for r in successful if r['emails']]

    print(f"Total tested: {len(results)}")
    print(f"Successful searches: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Found emails: {len(with_emails)} ({len(with_emails)/len(results)*100:.1f}%)")

    print("\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['business_name']} ({result['city']})")
        print(f"   Phone: {result['phone']}")
        if result['success']:
            if result['emails']:
                print(f"   [SUCCESS] Emails: {', '.join(result['emails'])}")
            else:
                print(f"   [WARNING] No emails found ({result.get('results_count', 0)} results)")
        else:
            print(f"   [FAILED] Error: {result.get('error', 'unknown')}")

    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)

    return results


if __name__ == "__main__":
    main()
