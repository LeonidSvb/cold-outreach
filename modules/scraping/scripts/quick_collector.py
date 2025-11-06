#!/usr/bin/env python3
"""Quick reenactment contacts collector - simplified version"""

import json
from pathlib import Path
from datetime import datetime

def load_known_groups():
    """Load manually researched groups"""
    print("Loading known groups...")
    known_file = Path("modules/scraping/data/known_groups.json")

    if known_file.exists():
        with open(known_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            groups = data.get("manual_additions", [])
            print(f"Loaded {len(groups)} known groups")
            return groups
    return []

def save_results(groups):
    """Save results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("modules/scraping/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    json_file = results_dir / f"reenactment_clubs_quick_{timestamp}.json"

    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_contacts": len(groups)
        },
        "contacts": groups
    }

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # CSV
    csv_file = results_dir / f"reenactment_clubs_quick_{timestamp}.csv"
    import csv

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if groups:
            fieldnames = ['name', 'email', 'website', 'location', 'period', 'source']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(groups)

    print(f"\nSaved to: {json_file}")
    print(f"Saved to: {csv_file}")

    return str(json_file)

def main():
    print("="*60)
    print("QUICK REENACTMENT COLLECTOR")
    print("="*60)

    # Load known groups
    groups = load_known_groups()

    print(f"\nTotal: {len(groups)} groups")
    print(f"With email: {len([g for g in groups if g.get('email')])}")
    print(f"With website: {len([g for g in groups if g.get('website')])}")

    # Save
    save_results(groups)

    print("\nDone!")

if __name__ == "__main__":
    main()
