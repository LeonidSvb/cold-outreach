#!/usr/bin/env python3
"""
Test with REAL websites from user's CSV
"""

import sys
from pathlib import Path

# Add lib path
lib_path = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from http_utils import HTTPClient
from text_utils import extract_emails_from_html, clean_html_to_text

print("=" * 70)
print("TESTING WITH REAL BUSINESS WEBSITES")
print("=" * 70)

# Real test sites from user's CSV
test_sites = [
    "http://18pertobe.com/",
    "http://503onprincesdrive.com/",
    "http://aamericanglass.com/",
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
            print(f"Content preview: {content[:300]}...")

            # Extract emails
            emails = extract_emails_from_html(html)
            print(f"Emails found: {len(emails)}")
            if emails:
                print(f"Emails: {', '.join(emails)}")

            print("Result: SUCCESS")
        else:
            print(f"Error: {fetch_result.get('error', 'Unknown error')}")
            print("Result: FAILED (but this is OK - site might be down)")

    except Exception as e:
        print(f"Exception: {e}")
        print("Result: EXCEPTION")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
