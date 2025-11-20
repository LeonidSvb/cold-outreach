#!/usr/bin/env python3
"""
=== ABN REGISTRY LOOKUP TEST ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Test Australian Business Number (ABN) Registry for contact info

FEATURES:
- Search ABN by business name
- Extract contact details from registry
- FREE government API

USAGE:
1. Run: python test_abn_lookup.py
2. Results printed to console

API: https://abr.business.gov.au/
"""

import re
import time
import random
import requests
import pandas as pd
from urllib.parse import quote

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Downloads\All Australian Cafes - No Email for Upwork (2).csv",
    "TEST_SAMPLE_SIZE": 10,
    "ABN_SEARCH_URL": "https://abr.business.gov.au/json/AbnDetails.aspx",
    "ABN_NAME_SEARCH_URL": "https://abr.business.gov.au/json/MatchingNames.aspx",
    "DELAY_BETWEEN_REQUESTS": (2, 4),
    "GUID": "106abc7e-25fd-4feb-84d2-02798dbba9de"  # Public test GUID
}

EMAIL_PATTERN = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
)


def search_abn_by_name(business_name, state="VIC"):
    """Search for ABN by business name"""
    try:
        print(f"  Searching ABN Registry for: {business_name}")

        params = {
            "name": business_name,
            "postcode": "",
            "legalName": "",
            "tradingName": "Y",
            "NSW": "Y" if state == "NSW" else "",
            "SA": "Y" if state == "SA" else "",
            "ACT": "Y" if state == "ACT" else "",
            "VIC": "Y" if state == "VIC" else "",
            "WA": "Y" if state == "WA" else "",
            "NT": "Y" if state == "NT" else "",
            "QLD": "Y" if state == "QLD" else "",
            "TAS": "Y" if state == "TAS" else "",
            "guid": CONFIG["GUID"],
            "callback": "callback"
        }

        response = requests.get(
            CONFIG["ABN_NAME_SEARCH_URL"],
            params=params,
            timeout=15
        )

        # Parse JSONP response
        text = response.text
        if text.startswith("callback("):
            text = text[9:-1]  # Remove callback( and )

        # Try to find ABN numbers in response
        abn_pattern = re.compile(r'"Abn":"(\d+)"')
        abns = abn_pattern.findall(text)

        if abns:
            print(f"  Found {len(abns)} potential ABN(s)")
            return {
                'success': True,
                'abns': abns[:3],  # Return top 3
                'count': len(abns)
            }
        else:
            print(f"  No ABN found")
            return {
                'success': True,
                'abns': [],
                'count': 0
            }

    except Exception as e:
        print(f"  Error: {e}")
        return {
            'success': False,
            'error': str(e),
            'abns': []
        }


def get_abn_details(abn):
    """Get detailed info for an ABN"""
    try:
        params = {
            "abn": abn,
            "guid": CONFIG["GUID"],
            "callback": "callback"
        }

        response = requests.get(
            CONFIG["ABN_SEARCH_URL"],
            params=params,
            timeout=15
        )

        # Parse response
        text = response.text
        if text.startswith("callback("):
            text = text[9:-1]

        # Search for emails in response
        emails = EMAIL_PATTERN.findall(text)

        return {
            'success': True,
            'emails': list(set(emails)),
            'abn': abn
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'emails': []
        }


def main():
    print("="*60)
    print("=== ABN Registry Lookup Test ===")
    print("="*60)

    # Load data
    print(f"\nLoading data from: {CONFIG['INPUT_FILE']}")
    df = pd.read_csv(CONFIG['INPUT_FILE'])

    # Filter companies WITHOUT websites
    df_no_website = df[df['website'].isna() | (df['website'] == '')].copy()
    print(f"Companies WITHOUT websites: {len(df_no_website)}")

    # Take test sample
    sample_df = df_no_website.head(CONFIG['TEST_SAMPLE_SIZE'])
    print(f"Testing on {len(sample_df)} companies\n")

    # Test lookup
    results = []

    for idx, row in sample_df.iterrows():
        business_name = row['Business Name']
        city = row['search_city']
        phone = row.get('phone', '')

        print(f"\n[{idx+1}/{len(sample_df)}] {business_name} ({city})")

        # Search for ABN
        abn_result = search_abn_by_name(business_name)

        result = {
            'business_name': business_name,
            'city': city,
            'phone': phone,
            'abns_found': abn_result.get('count', 0),
            'emails': []
        }

        # Get details for each ABN
        if abn_result['success'] and abn_result['abns']:
            all_emails = []
            for abn in abn_result['abns']:
                print(f"  Checking ABN: {abn}")
                details = get_abn_details(abn)
                if details['success'] and details['emails']:
                    all_emails.extend(details['emails'])

            result['emails'] = list(set(all_emails))

        results.append(result)

        # Show result
        if result['emails']:
            print(f"[SUCCESS] Found {len(result['emails'])} email(s): {', '.join(result['emails'])}")
        else:
            print(f"[WARNING] No emails found (ABNs: {result['abns_found']})")

        # Rate limiting
        if idx < len(sample_df) - 1:
            delay = random.uniform(*CONFIG['DELAY_BETWEEN_REQUESTS'])
            print(f"  Waiting {delay:.1f}s...")
            time.sleep(delay)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    with_abns = [r for r in results if r['abns_found'] > 0]
    with_emails = [r for r in results if r['emails']]

    print(f"Total tested: {len(results)}")
    print(f"Found ABN: {len(with_abns)} ({len(with_abns)/len(results)*100:.1f}%)")
    print(f"Found emails: {len(with_emails)} ({len(with_emails)/len(results)*100:.1f}%)")

    print("\n" + "="*60)
    print("DETAILED RESULTS")
    print("="*60)

    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['business_name']} ({result['city']})")
        print(f"   ABNs found: {result['abns_found']}")
        if result['emails']:
            print(f"   [SUCCESS] Emails: {', '.join(result['emails'])}")
        else:
            print(f"   [WARNING] No emails found")

    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)

    return results


if __name__ == "__main__":
    main()
