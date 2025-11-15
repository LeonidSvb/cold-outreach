#!/usr/bin/env python3
"""
Clean problematic emails and revalidate them
"""

import sys
import json
import re
import time
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from logger.universal_logger import get_logger

logger = get_logger(__name__)

# Configuration
CONFIG = {
    "API_KEY": "c6c76660-b774-4dcc-be3f-64cdb999e70f",
    "API_URL": "https://api.mails.so/v1/validate",
    "INPUT_FILE": r"C:\Users\79818\Desktop\Outreach - new\modules\email_verification\results\verified_emails_20251115_160627.csv",
    "RATE_LIMIT_DELAY": 0.5,
    "TIMEOUT": 10,
}

# Cleanup patterns
CLEANUP_PATTERNS = [
    # Concatenated domains
    (r'@(.+?)\.(huhorizon)$', r'@\1.hu'),
    (r'@(.+?)\.(chder)$', r'@\1.ch'),
    (r'@(.+?)\.(ukregistered)$', r'@\1.uk'),
    (r'@(.+?)\.(nliban)$', r'@\1.nl'),
    (r'@(.+?)\.(chhorizon)$', r'@\1.ch'),
    (r'@(.+?)\.(dehorizon)$', r'@\1.de'),
    # Remove-this pattern
    (r'@remove-this\.', r'@'),
    (r'@remove\.', r'@'),
]


def clean_email(email: str) -> str:
    """Apply cleanup patterns to email"""
    cleaned = email.strip()

    for pattern, replacement in CLEANUP_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned)

    return cleaned


def verify_email(email: str) -> dict:
    """Verify single email using mails.so API"""
    try:
        headers = {"x-mails-api-key": CONFIG["API_KEY"]}
        params = {"email": email}

        response = requests.get(
            CONFIG["API_URL"],
            headers=headers,
            params=params,
            timeout=CONFIG["TIMEOUT"]
        )

        if response.status_code == 200:
            return {"status": "success", "data": response.json()}
        else:
            return {"status": "error", "error": f"API returned {response.status_code}"}

    except Exception as e:
        return {"status": "error", "error": str(e)}


def main():
    import pandas as pd

    logger.info("="*60)
    logger.info("EMAIL CLEANUP AND REVALIDATION")
    logger.info("="*60)

    # Read verified results
    df = pd.read_csv(CONFIG["INPUT_FILE"], encoding='utf-8')

    # Find problematic emails
    problematic = df[df['result'].isin(['undeliverable', 'unknown'])].copy()
    logger.info(f"Found {len(problematic)} problematic emails")

    # Clean and find fixable ones
    cleaned_emails = []
    for idx, row in problematic.iterrows():
        original = row['email']
        cleaned = clean_email(original)

        if cleaned != original:
            cleaned_emails.append({
                'name': row.get('name', ''),
                'original': original,
                'cleaned': cleaned,
                'original_result': row['result'],
                'original_score': row['score']
            })

    logger.info(f"Found {len(cleaned_emails)} emails that can be cleaned")

    if not cleaned_emails:
        logger.info("No emails to clean!")
        return

    # Show what will be cleaned
    print("\n=== EMAILS TO CLEAN ===\n")
    for item in cleaned_emails:
        print(f"{item['original']}")
        print(f"  -> {item['cleaned']}")
        print(f"  (was: {item['original_result']}, score: {item['original_score']})")
        print()

    # Revalidate cleaned emails
    print("\n=== REVALIDATING CLEANED EMAILS ===\n")
    results = []

    for idx, item in enumerate(cleaned_emails, 1):
        cleaned_email = item['cleaned']
        logger.info(f"Verifying {idx}/{len(cleaned_emails)}: {cleaned_email}")

        verification = verify_email(cleaned_email)

        if verification["status"] == "success":
            api_response = verification["data"]
            data = api_response.get("data", {})

            item['new_result'] = data.get("result", "unknown")
            item['new_score'] = data.get("score", 0)
            item['provider'] = data.get("provider", "")
            item['mx_record'] = data.get("mx_record", "")
        else:
            item['new_result'] = "error"
            item['new_score'] = 0
            item['error'] = verification.get("error", "Unknown")

        results.append(item)

        if idx < len(cleaned_emails):
            time.sleep(CONFIG["RATE_LIMIT_DELAY"])

    # Analyze results
    print("\n=== REVALIDATION RESULTS ===\n")

    improved = [r for r in results if r.get('new_result') == 'deliverable']
    still_bad = [r for r in results if r.get('new_result') in ['undeliverable', 'unknown']]
    risky = [r for r in results if r.get('new_result') == 'risky']

    print(f"Total cleaned and revalidated: {len(results)}")
    print(f"Now DELIVERABLE: {len(improved)} ({len(improved)/len(results)*100:.1f}%)")
    print(f"Now RISKY: {len(risky)} ({len(risky)/len(results)*100:.1f}%)")
    print(f"Still problematic: {len(still_bad)} ({len(still_bad)/len(results)*100:.1f}%)")
    print()

    if improved:
        print("RECOVERED EMAILS (now deliverable):")
        for item in improved:
            print(f"  {item['cleaned']} (score: {item['new_score']}, {item.get('provider', 'unknown')})")
            print(f"    was: {item['original']} ({item['original_result']})")
        print()

    if risky:
        print("RISKY (test carefully):")
        for item in risky:
            print(f"  {item['cleaned']} (score: {item['new_score']})")
        print()

    # Save results
    results_file = Path(__file__).parent.parent / "results" / "cleaned_emails_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to: {results_file}")

    # Summary
    print("\n=== SUMMARY ===")
    print(f"Cleaned {len(results)} emails")
    print(f"Recovered {len(improved)} deliverable emails")
    print(f"Found {len(risky)} risky emails")
    print(f"Net gain: +{len(improved) + len(risky)} usable emails")


if __name__ == "__main__":
    main()
