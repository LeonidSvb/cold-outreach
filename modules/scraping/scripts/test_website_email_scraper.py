#!/usr/bin/env python3
"""
=== WEBSITE EMAIL SCRAPER TEST ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Test website scraping for email extraction from Australian cafe websites

FEATURES:
- HTTP-only scraping (requests + BeautifulSoup)
- Email regex pattern matching
- Rate limiting and error handling
- Test on 10 sample companies

USAGE:
1. Run: python test_website_email_scraper.py
2. Results printed to console
"""

import re
import time
import random
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import pandas as pd

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Downloads\All Australian Cafes - No Email for Upwork (2).csv",
    "TEST_SAMPLE_SIZE": 10,
    "REQUEST_TIMEOUT": 10,
    "DELAY_BETWEEN_REQUESTS": (1, 3),  # Random delay in seconds
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Email regex pattern
EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)

# Emails to exclude (generic/spam)
EXCLUDE_PATTERNS = [
    'example.com',
    'domain.com',
    'yoursite.com',
    'yourdomain.com',
    'noreply@',
    'no-reply@',
    'donotreply@',
    'spam@',
    'abuse@',
    'postmaster@',
    'mailer-daemon@',
    'wix.com',
    'wordpress.com',
    'squarespace.com'
]


def is_valid_email(email):
    """Check if email is valid and not generic"""
    email_lower = email.lower()

    # Check exclusion patterns
    for pattern in EXCLUDE_PATTERNS:
        if pattern in email_lower:
            return False

    return True


def extract_emails_from_html(html_content, base_url):
    """Extract all valid emails from HTML content"""
    emails = set()

    # Find emails in HTML text
    found_emails = EMAIL_PATTERN.findall(html_content)

    for email in found_emails:
        if is_valid_email(email):
            emails.add(email.lower())

    # Also check mailto: links
    soup = BeautifulSoup(html_content, 'html.parser')
    mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))

    for link in mailto_links:
        href = link.get('href', '')
        email_match = EMAIL_PATTERN.search(href)
        if email_match:
            email = email_match.group(0)
            if is_valid_email(email):
                emails.add(email.lower())

    return list(emails)


def scrape_website_for_emails(url, timeout=10):
    """Scrape website and extract emails"""
    try:
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        print(f"Scraping: {url}")

        # Make request
        headers = {'User-Agent': CONFIG['USER_AGENT']}
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        # Extract emails
        emails = extract_emails_from_html(response.text, url)

        # Try to scrape contact/about pages if no emails found
        if not emails:
            contact_pages = ['/contact', '/contact-us', '/about', '/about-us']
            for page in contact_pages:
                try:
                    contact_url = urljoin(url, page)
                    print(f"  Trying: {contact_url}")
                    contact_response = requests.get(contact_url, headers=headers, timeout=timeout)
                    if contact_response.status_code == 200:
                        page_emails = extract_emails_from_html(contact_response.text, contact_url)
                        emails.extend(page_emails)
                        if emails:
                            break
                except Exception:
                    continue

        return {
            'success': True,
            'emails': list(set(emails)),  # Remove duplicates
            'url': url,
            'status_code': response.status_code
        }

    except requests.exceptions.Timeout:
        print(f"  Timeout: {url}")
        return {'success': False, 'error': 'timeout', 'url': url}

    except requests.exceptions.RequestException as e:
        print(f"  Request error: {e}")
        return {'success': False, 'error': str(e), 'url': url}

    except Exception as e:
        print(f"  Unexpected error: {e}")
        return {'success': False, 'error': str(e), 'url': url}


def main():
    print("="*60)
    print("=== Website Email Scraper Test ===")
    print("="*60)

    # Load data
    print(f"\nLoading data from: {CONFIG['INPUT_FILE']}")
    df = pd.read_csv(CONFIG['INPUT_FILE'])

    # Filter companies WITH websites
    df_with_websites = df[df['website'].notna() & (df['website'] != '')].copy()
    print(f"Companies with websites: {len(df_with_websites)}")

    # Take test sample
    sample_df = df_with_websites.head(CONFIG['TEST_SAMPLE_SIZE'])
    print(f"Testing on {len(sample_df)} companies\n")

    # Test scraping
    results = []

    for idx, row in sample_df.iterrows():
        business_name = row['Business Name']
        website = row['website']
        city = row['search_city']

        print(f"\n[{idx+1}/{len(sample_df)}] {business_name} ({city})")
        print(f"Website: {website}")

        # Scrape
        result = scrape_website_for_emails(website, timeout=CONFIG['REQUEST_TIMEOUT'])

        result['business_name'] = business_name
        result['city'] = city
        result['original_website'] = website
        results.append(result)

        # Show result
        if result['success']:
            if result['emails']:
                print(f"[SUCCESS] Found {len(result['emails'])} email(s): {', '.join(result['emails'])}")
            else:
                print("[WARNING] No emails found")
        else:
            print(f"[FAILED] {result.get('error', 'unknown')}")

        # Rate limiting
        if idx < len(sample_df) - 1:
            delay = random.uniform(*CONFIG['DELAY_BETWEEN_REQUESTS'])
            time.sleep(delay)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    successful = [r for r in results if r['success']]
    with_emails = [r for r in successful if r['emails']]

    print(f"Total tested: {len(results)}")
    print(f"Successful scrapes: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Found emails: {len(with_emails)} ({len(with_emails)/len(results)*100:.1f}%)")

    print("\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['business_name']}")
        print(f"   Website: {result['original_website']}")
        if result['success']:
            if result['emails']:
                print(f"   [SUCCESS] Emails: {', '.join(result['emails'])}")
            else:
                print(f"   [WARNING] No emails found")
        else:
            print(f"   [FAILED] Error: {result.get('error', 'unknown')}")

    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)

    return results


if __name__ == "__main__":
    main()
