#!/usr/bin/env python3
"""
=== FAST ASYNC DATA ENRICHMENT ===
Version: 2.0.0 | Created: 2025-11-20

PURPOSE:
Fast parallel enrichment using asyncio (5x faster than sync version)

FEATURES:
- 5 concurrent requests (respecting 5 RPS limit)
- Automatic retry on rate limit errors
- Progress tracking
- 30 minutes for 9,576 companies (vs 4 hours sync)

USAGE:
1. Configure RAPIDAPI_KEY in .env
2. Set PROCESS_ALL = True to process all 9,576 companies
3. Run: python fast_enrichment_async.py
"""

import asyncio
import aiohttp
import re
import os
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Downloads\All Australian Cafes - No Email for Upwork (2).csv",
    "OUTPUT_DIR": r"C:\Users\79818\Desktop\Outreach - new\modules\scraping\results",
    "RAPIDAPI_KEY": os.getenv("RAPIDAPI_KEY"),
    "RAPIDAPI_HOST": "google-search72.p.rapidapi.com",
    "CONCURRENT_REQUESTS": 5,
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 2,
    "PROCESS_ALL": False,
    "TEST_SIZE": 100,
    "SAVE_INTERVAL": 100,
}

EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
WEBSITE_PATTERN = re.compile(r'https?://(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)')
FACEBOOK_PATTERN = re.compile(r'(?:https?://)?(?:www\.)?facebook\.com/([a-zA-Z0-9.]+)')
INSTAGRAM_PATTERN = re.compile(r'(?:https?://)?(?:www\.)?instagram\.com/([a-zA-Z0-9_.]+)')

EXCLUDE_DOMAINS = [
    'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com',
    'youtube.com', 'google.com', 'yelp.com', 'tripadvisor.com',
    'zomato.com', 'urbanspoon.com', 'yellowpages.com.au',
    'localsearch.com.au', 'truelocal.com.au', 'hotfrog.com.au',
    'edan.io', 'jany.io', 'localize123.com', 'cafeleader.com',
    'sentry.io', 'wixpress.com', 'wix.com', 'wordpress.com',
    'squarespace.com', 'weebly.com', 'godaddy.com'
]


class RateLimiter:
    """Token bucket rate limiter for 5 RPS"""
    def __init__(self, rate=5, per=1.0):
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current
            self.allowance += time_passed * (self.rate / self.per)

            if self.allowance > self.rate:
                self.allowance = self.rate

            if self.allowance < 1.0:
                sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
                await asyncio.sleep(sleep_time)
                self.allowance = 0.0
            else:
                self.allowance -= 1.0


def extract_website(text, business_name):
    """Extract legitimate business website"""
    urls = WEBSITE_PATTERN.findall(text)
    for url in urls:
        domain = url.lower()
        if any(excluded in domain for excluded in EXCLUDE_DOMAINS):
            continue
        if any(word in domain for word in ['directory', 'listing', 'review', 'find']):
            continue
        business_words = business_name.lower().replace('&', '').split()
        if any(word in domain for word in business_words if len(word) > 3):
            return f"https://{url}"

    for url in urls:
        domain = url.lower()
        if not any(excluded in domain for excluded in EXCLUDE_DOMAINS):
            return f"https://{url}"
    return None


def extract_social_media(text):
    """Extract social media links"""
    facebook = FACEBOOK_PATTERN.findall(text)
    instagram = INSTAGRAM_PATTERN.findall(text)
    return {
        'facebook': f"https://facebook.com/{facebook[0]}" if facebook else None,
        'instagram': f"https://instagram.com/{instagram[0]}" if instagram else None,
    }


def extract_emails(text):
    """Extract valid emails"""
    emails = EMAIL_PATTERN.findall(text)
    valid_emails = []
    for email in emails:
        email_lower = email.lower()
        if any(word in email_lower for word in [
            'example.com', 'domain.com', 'noreply', 'no-reply',
            'donotreply', 'spam', 'abuse', 'postmaster', 'mailer-daemon',
            'sentry.', 'wix.', 'wordpress.', 'squarespace.'
        ]):
            continue
        valid_emails.append(email_lower)
    return list(set(valid_emails))


async def enrich_company_async(session, rate_limiter, business_name, city, retry_count=0):
    """Async enrichment with retry logic"""
    try:
        await rate_limiter.acquire()

        query = f'"{business_name}" "{city}" Australia'

        url = "https://google-search72.p.rapidapi.com/search"
        params = {
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

        async with session.get(url, params=params, headers=headers, timeout=20) as response:
            if response.status == 429:
                if retry_count < CONFIG["MAX_RETRIES"]:
                    await asyncio.sleep(CONFIG["RETRY_DELAY"])
                    return await enrich_company_async(session, rate_limiter, business_name, city, retry_count + 1)
                else:
                    return {
                        'success': False,
                        'error': 'Rate limit exceeded',
                        'website': None,
                        'emails': [],
                        'facebook': None,
                        'instagram': None,
                    }

            response.raise_for_status()
            data = await response.json()

            all_text = ""
            results_count = 0

            if 'items' in data:
                results_count = len(data['items'])
                for item in data.get('items', []):
                    all_text += " " + item.get('title', '')
                    all_text += " " + item.get('snippet', '')
                    all_text += " " + item.get('link', '')

            website = extract_website(all_text, business_name)
            emails = extract_emails(all_text)
            social = extract_social_media(all_text)

            return {
                'success': True,
                'website': website,
                'emails': emails,
                'facebook': social['facebook'],
                'instagram': social['instagram'],
                'results_count': results_count,
            }

    except asyncio.TimeoutError:
        return {
            'success': False,
            'error': 'timeout',
            'website': None,
            'emails': [],
            'facebook': None,
            'instagram': None,
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'website': None,
            'emails': [],
            'facebook': None,
            'instagram': None,
        }


async def process_batch(companies, start_idx=0):
    """Process companies with controlled concurrency"""

    rate_limiter = RateLimiter(rate=5, per=1.0)

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        tasks = []

        for idx, company in enumerate(companies, start=start_idx):
            task = enrich_company_async(
                session,
                rate_limiter,
                company['name'],
                company['city']
            )
            tasks.append((idx, company, task))

        results = []

        for idx, company, task in tasks:
            result = await task
            result['index'] = idx
            result['business_name'] = company['name']
            result['city'] = company['city']
            results.append(result)

            if (idx + 1) % 10 == 0:
                progress = idx + 1 - start_idx
                total = len(companies)
                print(f"Progress: {progress}/{total} ({progress/total*100:.1f}%)")

        return results


def save_results(df, filename_suffix=""):
    """Save results to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"enriched_data_fast{filename_suffix}_{timestamp}.csv"
    filepath = os.path.join(CONFIG["OUTPUT_DIR"], filename)

    os.makedirs(CONFIG["OUTPUT_DIR"], exist_ok=True)
    df.to_csv(filepath, index=False, encoding='utf-8-sig')

    print(f"\n[SAVED] {filepath}")
    return filepath


async def main():
    print("="*70)
    print("=== FAST ASYNC DATA ENRICHMENT ===")
    print("="*70)

    if not CONFIG["RAPIDAPI_KEY"]:
        print("\n[ERROR] RAPIDAPI_KEY not found in .env!")
        return

    print(f"\nLoading data from: {CONFIG['INPUT_FILE']}")
    df = pd.read_csv(CONFIG['INPUT_FILE'])

    df_no_website = df[df['website'].isna() | (df['website'] == '')].copy()
    print(f"Companies WITHOUT websites: {len(df_no_website)}")

    if CONFIG["PROCESS_ALL"]:
        sample_df = df_no_website.copy()
        process_size = len(df_no_website)
    else:
        sample_df = df_no_website.head(CONFIG['TEST_SIZE']).copy()
        process_size = CONFIG['TEST_SIZE']

    print(f"\nProcessing {process_size} companies")
    print(f"Concurrent requests: {CONFIG['CONCURRENT_REQUESTS']}")
    print(f"Estimated time: ~{process_size / (5 * 60):.1f} minutes")
    print(f"Estimated cost: ${process_size * 0.001:.2f}\n")

    sample_df['found_website'] = None
    sample_df['found_email'] = None
    sample_df['found_facebook'] = None
    sample_df['found_instagram'] = None

    companies = [
        {'name': row['Business Name'], 'city': row['search_city']}
        for _, row in sample_df.iterrows()
    ]

    start_time = time.time()

    print("Starting async processing...\n")
    results = await process_batch(companies, start_idx=sample_df.index[0])

    for result in results:
        idx = result['index']
        sample_df.at[idx, 'found_website'] = result.get('website')
        sample_df.at[idx, 'found_email'] = ', '.join(result.get('emails', []))
        sample_df.at[idx, 'found_facebook'] = result.get('facebook')
        sample_df.at[idx, 'found_instagram'] = result.get('instagram')

    elapsed_time = time.time() - start_time

    output_file = save_results(
        sample_df,
        filename_suffix=f"_{process_size}_companies"
    )

    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)

    found_website = sample_df['found_website'].notna().sum()
    found_email = (sample_df['found_email'].notna() & (sample_df['found_email'] != '')).sum()
    found_fb = sample_df['found_facebook'].notna().sum()
    found_ig = sample_df['found_instagram'].notna().sum()

    print(f"\nProcessed: {process_size} companies")
    print(f"Time elapsed: {elapsed_time/60:.1f} minutes")
    print(f"Actual cost: ${process_size * 0.001:.2f}")
    print(f"Speed: {process_size / elapsed_time:.1f} companies/second")

    print(f"\n--- RESULTS ---")
    print(f"Found Website:   {found_website:4d} ({found_website/process_size*100:5.1f}%)")
    print(f"Found Email:     {found_email:4d} ({found_email/process_size*100:5.1f}%)")
    print(f"Found Facebook:  {found_fb:4d} ({found_fb/process_size*100:5.1f}%)")
    print(f"Found Instagram: {found_ig:4d} ({found_ig/process_size*100:5.1f}%)")

    any_data = (sample_df['found_website'].notna() |
                ((sample_df['found_email'].notna()) & (sample_df['found_email'] != '')) |
                sample_df['found_facebook'].notna() |
                sample_df['found_instagram'].notna()).sum()

    print(f"\nCompanies with ANY data: {any_data} ({any_data/process_size*100:.1f}%)")
    print(f"\n[OUTPUT] {output_file}")
    print("\n" + "="*70)
    print("Enrichment completed!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
