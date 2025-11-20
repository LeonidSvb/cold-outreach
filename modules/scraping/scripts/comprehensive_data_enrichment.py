#!/usr/bin/env python3
"""
=== COMPREHENSIVE DATA ENRICHMENT ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Find missing data for Australian cafes WITHOUT websites using Google Search API

FINDS:
- Website URL (if exists)
- Email addresses
- Facebook page
- Instagram page
- Google Maps listing
- Additional phone numbers

USAGE:
1. Configure RAPIDAPI_KEY in .env
2. Set TEST_SIZE (default: 500)
3. Run: python comprehensive_data_enrichment.py
4. Results saved to CSV
"""

import re
import time
import random
import os
import json
from datetime import datetime
import requests
import pandas as pd
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Downloads\All Australian Cafes - No Email for Upwork (2).csv",
    "OUTPUT_DIR": r"C:\Users\79818\Desktop\Outreach - new\modules\scraping\results",
    "TEST_SIZE": 500,
    "RAPIDAPI_KEY": os.getenv("RAPIDAPI_KEY"),
    "RAPIDAPI_HOST": "google-search72.p.rapidapi.com",
    "DELAY_BETWEEN_REQUESTS": (1, 2),
    "SAVE_INTERVAL": 50,
}

# Regex patterns
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b(?:\+?61|0)[2-478](?:[ -]?[0-9]){8}\b')
WEBSITE_PATTERN = re.compile(r'https?://(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)')

# Social media patterns
FACEBOOK_PATTERN = re.compile(r'(?:https?://)?(?:www\.)?facebook\.com/([a-zA-Z0-9.]+)')
INSTAGRAM_PATTERN = re.compile(r'(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9_.]+)')
GOOGLE_MAPS_PATTERN = re.compile(r'(?:https?://)?(?:www\.)?google\.com/maps/[^\s]+')

# Exclude domains
EXCLUDE_DOMAINS = [
    'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com',
    'youtube.com', 'google.com', 'yelp.com', 'tripadvisor.com',
    'zomato.com', 'urbanspoon.com', 'yellowpages.com.au',
    'localsearch.com.au', 'truelocal.com.au', 'hotfrog.com.au',
    'edan.io', 'jany.io', 'localize123.com', 'cafeleader.com',
    'sentry.io', 'wixpress.com', 'wix.com', 'wordpress.com',
    'squarespace.com', 'weebly.com', 'godaddy.com'
]


def extract_website(text, business_name):
    """Extract legitimate business website from text"""
    urls = WEBSITE_PATTERN.findall(text)

    for url in urls:
        domain = url.lower()

        # Skip excluded domains
        if any(excluded in domain for excluded in EXCLUDE_DOMAINS):
            continue

        # Skip if domain contains common directory words
        if any(word in domain for word in ['directory', 'listing', 'review', 'find']):
            continue

        # Prefer domains that contain business name
        business_words = business_name.lower().replace('&', '').split()
        if any(word in domain for word in business_words if len(word) > 3):
            return f"https://{url}"

    # Return first non-excluded domain if no match
    for url in urls:
        domain = url.lower()
        if not any(excluded in domain for excluded in EXCLUDE_DOMAINS):
            return f"https://{url}"

    return None


def extract_social_media(text):
    """Extract social media links"""
    facebook = FACEBOOK_PATTERN.findall(text)
    instagram = INSTAGRAM_PATTERN.findall(text)
    google_maps = GOOGLE_MAPS_PATTERN.findall(text)

    return {
        'facebook': f"https://facebook.com/{facebook[0]}" if facebook else None,
        'instagram': f"https://instagram.com/{instagram[0]}" if instagram else None,
        'google_maps': google_maps[0] if google_maps else None
    }


def extract_emails(text):
    """Extract valid email addresses"""
    emails = EMAIL_PATTERN.findall(text)

    valid_emails = []
    for email in emails:
        email_lower = email.lower()

        # Skip generic/spam emails
        if any(word in email_lower for word in [
            'example.com', 'domain.com', 'noreply', 'no-reply',
            'donotreply', 'spam', 'abuse', 'postmaster', 'mailer-daemon',
            'sentry.', 'wix.', 'wordpress.', 'squarespace.'
        ]):
            continue

        valid_emails.append(email_lower)

    return list(set(valid_emails))


def enrich_company_data(business_name, city, phone):
    """Search Google and extract all available data"""
    try:
        # Build comprehensive search query
        query = f'"{business_name}" "{city}" Australia'

        print(f"  Searching: {query}")

        # Make request to Google Search API
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

        response = requests.get(url, headers=headers, params=querystring, timeout=20)
        response.raise_for_status()

        data = response.json()

        # Combine all text for analysis
        all_text = ""
        results_count = 0

        if 'items' in data:
            results_count = len(data['items'])
            for item in data.get('items', []):
                all_text += " " + item.get('title', '')
                all_text += " " + item.get('snippet', '')
                all_text += " " + item.get('link', '')

        # Extract all data
        website = extract_website(all_text, business_name)
        emails = extract_emails(all_text)
        social = extract_social_media(all_text)

        return {
            'success': True,
            'website': website,
            'emails': emails,
            'facebook': social['facebook'],
            'instagram': social['instagram'],
            'google_maps': social['google_maps'],
            'results_count': results_count,
            'found_data': bool(website or emails or social['facebook'] or social['instagram'])
        }

    except requests.exceptions.RequestException as e:
        print(f"  Request error: {e}")
        return {
            'success': False,
            'error': str(e),
            'website': None,
            'emails': [],
            'facebook': None,
            'instagram': None,
            'google_maps': None,
            'found_data': False
        }

    except Exception as e:
        print(f"  Unexpected error: {e}")
        return {
            'success': False,
            'error': str(e),
            'website': None,
            'emails': [],
            'facebook': None,
            'instagram': None,
            'google_maps': None,
            'found_data': False
        }


def save_results(results_df, test_size):
    """Save results to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enriched_data_{test_size}_companies_{timestamp}.csv"
    filepath = os.path.join(CONFIG["OUTPUT_DIR"], filename)

    os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
    results_df.to_csv(filepath, index=False, encoding='utf-8-sig')

    print(f"\n[SAVED] Results saved to: {filepath}")
    return filepath


def main():
    print("="*70)
    print("=== COMPREHENSIVE DATA ENRICHMENT ===")
    print("="*70)

    # Check API key
    if not CONFIG["RAPIDAPI_KEY"]:
        print("\n[ERROR] RAPIDAPI_KEY not found in .env file!")
        return

    # Load data
    print(f"\nLoading data from: {CONFIG['INPUT_FILE']}")
    df = pd.read_csv(CONFIG['INPUT_FILE'])

    # Filter companies WITHOUT websites
    df_no_website = df[df['website'].isna() | (df['website'] == '')].copy()
    print(f"Companies WITHOUT websites: {len(df_no_website)}")

    # Take test sample
    test_size = min(CONFIG['TEST_SIZE'], len(df_no_website))
    sample_df = df_no_website.head(test_size).copy()
    print(f"\nEnriching {test_size} companies")
    print(f"Estimated cost: ${test_size * 0.001:.2f}")
    print(f"Estimated time: ~{test_size * 1.5 / 60:.1f} minutes\n")

    # Add new columns
    sample_df['found_website'] = None
    sample_df['found_email'] = None
    sample_df['found_facebook'] = None
    sample_df['found_instagram'] = None
    sample_df['found_google_maps'] = None
    sample_df['enrichment_success'] = False

    # Process companies
    results = []
    successful_enrichments = 0

    start_time = time.time()

    for idx, row in sample_df.iterrows():
        business_name = row['Business Name']
        city = row['search_city']
        phone = row.get('phone', '')

        progress = idx - sample_df.index[0] + 1
        # Handle unicode characters in business name
        safe_business_name = business_name.encode('ascii', 'replace').decode('ascii')
        safe_city = city.encode('ascii', 'replace').decode('ascii')
        print(f"\n[{progress}/{test_size}] {safe_business_name} ({safe_city})")

        # Enrich data
        result = enrich_company_data(business_name, city, phone)

        # Update dataframe
        sample_df.at[idx, 'found_website'] = result.get('website')
        sample_df.at[idx, 'found_email'] = ', '.join(result.get('emails', []))
        sample_df.at[idx, 'found_facebook'] = result.get('facebook')
        sample_df.at[idx, 'found_instagram'] = result.get('instagram')
        sample_df.at[idx, 'found_google_maps'] = result.get('google_maps')
        sample_df.at[idx, 'enrichment_success'] = result.get('found_data', False)

        # Show results
        if result.get('found_data'):
            successful_enrichments += 1
            print(f"  [SUCCESS] Found data:")
            if result.get('website'):
                print(f"    - Website: {result['website']}")
            if result.get('emails'):
                print(f"    - Emails: {', '.join(result['emails'])}")
            if result.get('facebook'):
                print(f"    - Facebook: {result['facebook']}")
            if result.get('instagram'):
                print(f"    - Instagram: {result['instagram']}")
        else:
            print(f"  [NO DATA] Found {result.get('results_count', 0)} search results but no relevant data")

        # Save progress periodically
        if progress % CONFIG['SAVE_INTERVAL'] == 0:
            save_results(sample_df, test_size)
            print(f"\n[PROGRESS SAVED] {progress}/{test_size} companies processed")

        # Rate limiting
        if progress < test_size:
            delay = random.uniform(*CONFIG['DELAY_BETWEEN_REQUESTS'])
            time.sleep(delay)

    # Final save
    output_file = save_results(sample_df, test_size)

    # Summary statistics
    elapsed_time = time.time() - start_time

    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    total_processed = test_size
    found_website = sample_df['found_website'].notna().sum()
    found_email = sample_df['found_email'].notna().sum() - (sample_df['found_email'] == '').sum()
    found_facebook = sample_df['found_facebook'].notna().sum()
    found_instagram = sample_df['found_instagram'].notna().sum()
    found_google_maps = sample_df['found_google_maps'].notna().sum()

    print(f"\nProcessed: {total_processed} companies")
    print(f"Time elapsed: {elapsed_time/60:.1f} minutes")
    print(f"Actual cost: ${total_processed * 0.001:.2f}")

    print(f"\n--- RESULTS ---")
    print(f"Found Website:     {found_website:4d} ({found_website/total_processed*100:5.1f}%)")
    print(f"Found Email:       {found_email:4d} ({found_email/total_processed*100:5.1f}%)")
    print(f"Found Facebook:    {found_facebook:4d} ({found_facebook/total_processed*100:5.1f}%)")
    print(f"Found Instagram:   {found_instagram:4d} ({found_instagram/total_processed*100:5.1f}%)")
    print(f"Found Google Maps: {found_google_maps:4d} ({found_google_maps/total_processed*100:5.1f}%)")

    any_data = (sample_df['found_website'].notna() |
                (sample_df['found_email'].notna() & (sample_df['found_email'] != '')) |
                sample_df['found_facebook'].notna() |
                sample_df['found_instagram'].notna()).sum()

    print(f"\nCompanies with ANY data found: {any_data} ({any_data/total_processed*100:.1f}%)")

    print(f"\n[OUTPUT] Results saved to:")
    print(f"  {output_file}")

    print("\n" + "="*70)
    print("Enrichment completed!")
    print("="*70)

    return sample_df


if __name__ == "__main__":
    main()
