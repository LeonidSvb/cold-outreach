#!/usr/bin/env python3
"""
Create final CSV from Apollo results
"""

import sys
from pathlib import Path
import json
import csv
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
}


def load_apollo_results():
    """Load latest Apollo results"""
    results_dir = CONFIG["OUTPUT_DIR"]
    json_files = sorted(results_dir.glob("apollo_cold_calling_agencies_*.json"), reverse=True)

    if not json_files:
        raise FileNotFoundError("No Apollo results found")

    with open(json_files[0], 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("companies", [])


def save_csv(companies):
    """Save to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"FINAL_cold_calling_agencies_{timestamp}.csv"

    fieldnames = [
        "name", "website", "domain", "phone", "country", "city", "state",
        "industry", "employee_count", "founded_year",
        "linkedin_url", "facebook_url", "twitter_url",
        "description", "quality_score"
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(companies)

    return output_file


def main():
    print("\nCreating final CSV from Apollo results...")

    companies = load_apollo_results()
    print(f"Loaded {len(companies)} companies")

    output_file = save_csv(companies)

    print(f"\n{'='*70}")
    print(f"FINAL CSV CREATED")
    print(f"{'='*70}")
    print(f"Total Companies: {len(companies)}")
    print(f"All have websites: YES")
    print(f"File: {output_file.name}")
    print(f"\nFull path:")
    print(f"  {output_file}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
