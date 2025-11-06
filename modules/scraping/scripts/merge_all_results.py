#!/usr/bin/env python3
"""
Merge All Results - Combine all collected contacts into single dataset
"""

import json
from pathlib import Path
from datetime import datetime

def load_known_groups():
    """Load known groups"""
    file_path = Path("modules/scraping/data/known_groups.json")
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("manual_additions", [])
    return []

def load_mega_collection():
    """Load mega collection results"""
    results_dir = Path("modules/scraping/results")
    mega_files = list(results_dir.glob("mega_collection_*.json"))

    if mega_files:
        # Get most recent
        latest = max(mega_files, key=lambda p: p.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("contacts", [])
    return []

def load_historic_uk():
    """Load Historic-UK results"""
    results_dir = Path("modules/scraping/results")
    uk_files = list(results_dir.glob("historic_uk_full_*.json"))

    if uk_files:
        latest = max(uk_files, key=lambda p: p.stat().st_mtime)
        with open(latest, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("contacts", [])
    return []

def deduplicate(contacts):
    """Deduplicate by website URL"""
    seen_websites = set()
    seen_emails = set()
    unique = []

    for contact in contacts:
        website = contact.get("website", "").lower().strip()
        email = contact.get("email", "").lower().strip()

        # Create unique key
        key = website if website else email

        if not key:
            continue  # Skip if no contact method

        # Check if already seen
        if website and website in seen_websites:
            continue
        if email and email in seen_emails:
            continue

        # Add to unique list
        unique.append(contact)

        if website:
            seen_websites.add(website)
        if email:
            seen_emails.add(email)

    return unique

def main():
    print("="*70)
    print("MERGE ALL RESULTS")
    print("="*70)

    # Load all sources
    print("\nLoading data sources...")

    known = load_known_groups()
    print(f"  Known groups: {len(known)}")

    mega = load_mega_collection()
    print(f"  MEGA collection: {len(mega)}")

    uk = load_historic_uk()
    print(f"  Historic-UK: {len(uk)}")

    # Combine
    all_contacts = []
    all_contacts.extend(known)
    all_contacts.extend(mega)
    all_contacts.extend(uk)

    print(f"\n  Total before dedup: {len(all_contacts)}")

    # Deduplicate
    unique_contacts = deduplicate(all_contacts)

    print(f"  Total after dedup: {len(unique_contacts)}")

    # Statistics
    with_email = len([c for c in unique_contacts if c.get("email")])
    with_website = len([c for c in unique_contacts if c.get("website")])

    print("\n" + "="*70)
    print("FINAL STATISTICS")
    print("="*70)
    print(f"Total Contacts: {len(unique_contacts)}")
    print(f"With Email: {with_email}")
    print(f"With Website: {with_website}")

    # By source
    sources = {}
    for contact in unique_contacts:
        source = contact.get("source", "Unknown")
        sources[source] = sources.get(source, 0) + 1

    print("\nBy Source:")
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")

    json_file = results_dir / f"FINAL_reenactment_contacts_{timestamp}.json"

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_contacts": len(unique_contacts),
            "with_emails": with_email,
            "with_websites": with_website,
            "target_met": len(unique_contacts) >= 300
        },
        "contacts": unique_contacts,
        "statistics": {
            "by_source": sources
        }
    }

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # CSV
    csv_file = results_dir / f"FINAL_reenactment_contacts_{timestamp}.csv"
    import csv

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if unique_contacts:
            fieldnames = ['name', 'email', 'website', 'location', 'period', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(unique_contacts)

    print("\nSaved to:")
    print(f"  JSON: {json_file}")
    print(f"  CSV: {csv_file}")
    print("="*70)

    # Check if target met
    if len(unique_contacts) >= 300:
        print("\n🎉 TARGET ACHIEVED: 300+ contacts collected!")
    else:
        need = 300 - len(unique_contacts)
        print(f"\nNeed {need} more contacts to reach 300 target")

if __name__ == "__main__":
    main()
