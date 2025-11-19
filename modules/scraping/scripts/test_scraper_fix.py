#!/usr/bin/env python3
"""
Quick test script to verify scraper fixes
Tests with 2 websites to check if scraping works correctly
"""

import sys
from pathlib import Path

# Add lib path
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from http_utils import HTTPClient
from text_utils import extract_emails_from_html, clean_html_to_text

print("=" * 70)
print("TESTING SCRAPER FIX")
print("=" * 70)

# Test websites
test_sites = [
    "https://example.com",
    "http://google.com",
]

# Initialize HTTP client
http_client = HTTPClient(timeout=15, retries=3)

for website in test_sites:
    print(f"\nTesting: {website}")
    print("-" * 70)

    try:
        # Fetch homepage
        fetch_result = http_client.fetch(website, check_content_length=True)

        print(f"Status: {fetch_result['status']}")

        if fetch_result['status'] == 'success':
            html = fetch_result['content']

            # Extract content
            content = clean_html_to_text(html)
            print(f"Content length: {len(content)} chars")
            print(f"Content preview: {content[:200]}...")

            # Extract emails
            emails = extract_emails_from_html(html)
            print(f"Emails found: {len(emails)}")
            if emails:
                print(f"Emails: {emails}")

            print("Result: SUCCESS")
        else:
            print(f"Error: {fetch_result.get('error', 'Unknown error')}")
            print("Result: FAILED")

    except Exception as e:
        print(f"Exception: {e}")
        print("Result: EXCEPTION")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
