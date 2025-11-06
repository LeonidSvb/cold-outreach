#!/usr/bin/env python3
"""
Apollo API Search for Reenactment Organizations
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

API_KEY = os.getenv('APOLLO_API_KEY')

def search_apollo(query, locations, page=1):
    """Search Apollo for organizations"""
    url = "https://api.apollo.io/v1/mixed_companies/search"

    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": API_KEY
    }

    payload = {
        "q_organization_keyword_tags": [query],
        "page": page,
        "per_page": 100,
        "organization_locations": locations
    }

    try:
        time.sleep(2)  # Rate limiting
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code}")
            return None

    except Exception as e:
        print(f"Request failed: {e}")
        return None

def main():
    print("="*70)
    print("APOLLO REENACTMENT ORGANIZATIONS SEARCH")
    print("="*70)

    locations = [
        "United States",
        "Canada",
        "United Kingdom",
        "Germany",
        "Australia",
        "France",
        "Netherlands",
        "Belgium"
    ]

    queries = [
        "historical reenactment",
        "WWII reenactment",
        "living history",
        "military reenactment",
        "war reenactment",
        "WW2 reenactment"
    ]

    all_orgs = []

    for query in queries:
        print(f"\nSearching for: '{query}'")

        result = search_apollo(query, locations)

        if result and 'organizations' in result:
            orgs = result['organizations']
            print(f"  Found: {len(orgs)} organizations")

            for org in orgs:
                org_data = {
                    "name": org.get('name', ''),
                    "website": org.get('website_url', ''),
                    "email": "",  # Apollo doesn't give emails directly
                    "location": org.get('country', ''),
                    "city": org.get('city', ''),
                    "industry": org.get('industry', ''),
                    "description": org.get('short_description', ''),
                    "period": "WWII/Historical",
                    "source": f"Apollo API ({query})"
                }

                if org_data["name"]:
                    all_orgs.append(org_data)

    # Deduplicate by website
    unique_orgs = {}
    for org in all_orgs:
        website = org.get('website', '').lower().strip()
        if website and website not in unique_orgs:
            unique_orgs[website] = org

    final_orgs = list(unique_orgs.values())

    print("\n" + "="*70)
    print(f"TOTAL UNIQUE ORGANIZATIONS: {len(final_orgs)}")
    print("="*70)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    json_file = results_dir / f"apollo_reenactment_{timestamp}.json"

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_organizations": len(final_orgs),
            "queries_used": queries
        },
        "contacts": final_orgs
    }

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # CSV
    csv_file = results_dir / f"apollo_reenactment_{timestamp}.csv"
    import csv

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if final_orgs:
            fieldnames = ['name', 'email', 'website', 'location', 'city', 'period', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(final_orgs)

    print(f"\nSaved to: {json_file}")
    print(f"Saved to: {csv_file}")

    # Show sample
    print("\nSample organizations:")
    for org in final_orgs[:5]:
        print(f"  - {org['name']} ({org['location']})")
        print(f"    Website: {org['website']}")

if __name__ == "__main__":
    main()
