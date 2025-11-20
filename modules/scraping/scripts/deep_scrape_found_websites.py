#!/usr/bin/env python3
"""
=== DEEP SCRAPE FOUND WEBSITES ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Take websites found by Google Search API and scrape them for emails

USAGE:
1. Reads enriched_data CSV with found_website column
2. Scrapes each website for emails
3. Outputs CSV with emails
"""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Desktop\Outreach - new\modules\scraping\results\enriched_data_500_companies_20251120_193016.csv",
    "OUTPUT_FILE": r"C:\Users\79818\Desktop\Outreach - new\modules\scraping\results\deep_scraped_emails.csv",
    "REQUEST_TIMEOUT": 10,
    "DELAY_BETWEEN_REQUESTS": (1, 2),
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

EXCLUDE_PATTERNS = [
    'example.com', 'domain.com', 'yoursite.com', 'yourdomain.com',
    'noreply@', 'no-reply@', 'donotreply@', 'spam@', 'abuse@',
    'postmaster@', 'mailer-daemon@', 'wix.com', 'wordpress.com',
    'squarespace.com', 'sentry.', 'privacy@', 'legal@', 'dmca@'
]


def is_valid_email(email):
    """Check if email is valid"""
    email_lower = email.lower()
    for pattern in EXCLUDE_PATTERNS:
        if pattern in email_lower:
            return False
    return True


def extract_emails_from_html(html_content):
    """Extract all valid emails from HTML"""
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
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        print(f"  Scraping: {url}")

        headers = {'User-Agent': CONFIG['USER_AGENT']}
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        emails = extract_emails_from_html(response.text)

        # Try contact/about pages if no emails
        if not emails:
            contact_pages = ['/contact', '/contact-us', '/about', '/about-us']
            for page in contact_pages:
                try:
                    contact_url = urljoin(url, page)
                    contact_response = requests.get(contact_url, headers=headers, timeout=timeout)
                    if contact_response.status_code == 200:
                        page_emails = extract_emails_from_html(contact_response.text)
                        emails.extend(page_emails)
                        if emails:
                            break
                except Exception:
                    continue

        return {
            'success': True,
            'emails': list(set(emails)),
            'url': url
        }

    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'timeout', 'emails': [], 'url': url}
    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': str(e), 'emails': [], 'url': url}
    except Exception as e:
        return {'success': False, 'error': str(e), 'emails': [], 'url': url}


def main():
    print("="*70)
    print("=== DEEP SCRAPE FOUND WEBSITES ===")
    print("="*70)

    # Load enriched data
    print(f"\nLoading: {CONFIG['INPUT_FILE']}")
    df = pd.read_csv(CONFIG['INPUT_FILE'])

    # Filter companies with found websites
    df_with_websites = df[df['found_website'].notna()].copy()
    print(f"Companies with websites: {len(df_with_websites)}")

    # Add new column for scraped emails
    df_with_websites['scraped_emails'] = None
    df_with_websites['scrape_success'] = False

    results = []

    for idx, row in df_with_websites.iterrows():
        business_name = row['Business Name']
        website = row['found_website']
        city = row['search_city']

        # Safe print
        safe_name = business_name.encode('ascii', 'replace').decode('ascii')
        print(f"\n[{idx+1}/{len(df_with_websites)}] {safe_name}")
        print(f"  Website: {website}")

        # Scrape
        result = scrape_website_for_emails(website, timeout=CONFIG['REQUEST_TIMEOUT'])

        if result['success']:
            if result['emails']:
                print(f"  [SUCCESS] Found {len(result['emails'])} email(s): {', '.join(result['emails'])}")
                df_with_websites.at[idx, 'scraped_emails'] = ', '.join(result['emails'])
                df_with_websites.at[idx, 'scrape_success'] = True
            else:
                print(f"  [NO EMAILS] Website accessible but no emails found")
        else:
            print(f"  [FAILED] {result.get('error', 'unknown')}")

        results.append(result)

        # Rate limiting
        if idx < df_with_websites.index[-1]:
            delay = random.uniform(*CONFIG['DELAY_BETWEEN_REQUESTS'])
            time.sleep(delay)

    # Save results
    df_with_websites.to_csv(CONFIG['OUTPUT_FILE'], index=False, encoding='utf-8-sig')

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    successful = [r for r in results if r['success']]
    with_emails = [r for r in successful if r['emails']]

    print(f"\nTotal websites scraped: {len(results)}")
    print(f"Successful scrapes: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Found emails: {len(with_emails)} ({len(with_emails)/len(results)*100:.1f}%)")

    # Count total unique emails
    all_emails = set()
    for r in with_emails:
        all_emails.update(r['emails'])

    print(f"Total unique emails: {len(all_emails)}")

    print("\n" + "="*70)
    print("DETAILED RESULTS")
    print("="*70)

    for i, result in enumerate(results, 1):
        website = result.get('url', 'N/A')
        print(f"\n{i}. {website}")
        if result['success']:
            if result['emails']:
                print(f"   [SUCCESS] Emails: {', '.join(result['emails'])}")
            else:
                print(f"   [NO EMAILS] Accessible but no emails")
        else:
            print(f"   [FAILED] {result.get('error', 'unknown')}")

    print("\n" + "="*70)
    print(f"Results saved to: {CONFIG['OUTPUT_FILE']}")
    print("="*70)


if __name__ == "__main__":
    main()
