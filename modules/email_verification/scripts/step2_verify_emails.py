#!/usr/bin/env python3
"""
STEP 2: Verify emails using mails.so API
"""

import sys
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import glob

print("="*70)
print("STEP 2: VERIFY EMAILS VIA MAILS.SO API")
print("="*70)

# Configuration
MAILS_SO_API_KEY = "c6c76660-b774-4dcc-be3f-64cdb999e70f"
MAILS_SO_API_URL = "https://api.mails.so/v1/validate"
RATE_LIMIT_DELAY = 0.5  # seconds
TIMEOUT = 10

# Find latest cleaned file
RESULTS_DIR = Path(__file__).parent.parent / "results"
cleaned_files = sorted(glob.glob(str(RESULTS_DIR / "us_1900_CLEANED_SPLIT_*.csv")))
if not cleaned_files:
    print("ERROR: No cleaned file found! Run step1 first.")
    sys.exit(1)

INPUT_FILE = Path(cleaned_files[-1])

print(f"\nInput file: {INPUT_FILE.name}")


def verify_email(email: str) -> dict:
    """Verify email using mails.so API"""
    try:
        headers = {"x-mails-api-key": MAILS_SO_API_KEY}
        params = {"email": email}

        response = requests.get(
            MAILS_SO_API_URL,
            headers=headers,
            params=params,
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            api_data = response.json().get("data", {})
            return {
                "status": "success",
                "result": api_data.get("result", "unknown"),
                "score": api_data.get("score", 0),
                "format_valid": api_data.get("isv_format", "unknown"),
                "domain_valid": api_data.get("isv_domain", "unknown"),
                "mx_valid": api_data.get("isv_mx", "unknown"),
                "is_disposable": api_data.get("is_disposable", "unknown"),
                "is_free": api_data.get("is_free", "unknown"),
                "provider": api_data.get("provider", ""),
            }
        else:
            return {
                "status": "error",
                "result": "error",
                "error": f"HTTP {response.status_code}"
            }

    except Exception as e:
        return {
            "status": "error",
            "result": "error",
            "error": str(e)
        }


# Read cleaned file
df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
print(f"Total rows: {len(df)}")

# Filter only rows with emails
df_with_email = df[df['email'] != ''].copy()
print(f"Rows with email: {len(df_with_email)}")

print("\n" + "="*70)
print("STARTING VERIFICATION")
print(f"Estimated time: ~{len(df_with_email) * RATE_LIMIT_DELAY / 60:.1f} minutes")
print("="*70 + "\n")

# Initialize verification columns
for col in ['verification_result', 'verification_score', 'format_valid', 'domain_valid',
            'mx_valid', 'is_disposable', 'is_free', 'provider', 'verification_error']:
    if col not in df.columns:
        df[col] = ""

# Verify emails
start_time = datetime.now()
verified_count = 0
stats = {
    'deliverable': 0,
    'undeliverable': 0,
    'risky': 0,
    'unknown': 0,
    'error': 0
}

for idx in df_with_email.index:
    email = df.at[idx, 'email']

    verified_count += 1

    # Progress update every 50 emails
    if verified_count % 50 == 0:
        elapsed = (datetime.now() - start_time).total_seconds()
        rate = verified_count / elapsed if elapsed > 0 else 0
        remaining = (len(df_with_email) - verified_count) / rate if rate > 0 else 0
        print(f"[{verified_count}/{len(df_with_email)}] Verified: {email[:40]:<40} | "
              f"Deliverable: {stats['deliverable']} | Rate: {rate:.1f}/s | "
              f"ETA: {remaining/60:.1f} min")

    verification = verify_email(email)

    if verification["status"] == "success":
        df.at[idx, 'verification_result'] = verification['result']
        df.at[idx, 'verification_score'] = verification.get('score', 0)
        df.at[idx, 'format_valid'] = verification.get('format_valid', '')
        df.at[idx, 'domain_valid'] = verification.get('domain_valid', '')
        df.at[idx, 'mx_valid'] = verification.get('mx_valid', '')
        df.at[idx, 'is_disposable'] = verification.get('is_disposable', '')
        df.at[idx, 'is_free'] = verification.get('is_free', '')
        df.at[idx, 'provider'] = verification.get('provider', '')
        df.at[idx, 'verification_error'] = ""

        # Update stats
        result = verification['result']
        stats[result] = stats.get(result, 0) + 1
    else:
        df.at[idx, 'verification_result'] = "error"
        df.at[idx, 'verification_error'] = verification.get('error', 'Unknown error')
        stats['error'] += 1

    # Rate limiting
    time.sleep(RATE_LIMIT_DELAY)

# Fill verification status for rows without emails
df.loc[df['email'] == '', 'verification_result'] = 'no_email'

# Save verified results
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = RESULTS_DIR / f"us_1900_VERIFIED_{timestamp}.csv"
df.to_csv(output_file, index=False, encoding='utf-8-sig')

duration = (datetime.now() - start_time).total_seconds()

print("\n" + "="*70)
print("VERIFICATION COMPLETE")
print("="*70)
print(f"Total processed: {verified_count}")
print(f"  Deliverable: {stats['deliverable']} ({stats['deliverable']/verified_count*100:.1f}%)")
print(f"  Risky: {stats.get('risky', 0)} ({stats.get('risky', 0)/verified_count*100:.1f}%)")
print(f"  Undeliverable: {stats['undeliverable']} ({stats['undeliverable']/verified_count*100:.1f}%)")
print(f"  Unknown: {stats['unknown']} ({stats['unknown']/verified_count*100:.1f}%)")
print(f"  Error: {stats['error']} ({stats['error']/verified_count*100:.1f}%)")
print(f"\nDuration: {duration:.2f} seconds ({duration/60:.1f} minutes)")
print(f"Average rate: {verified_count/duration:.2f} emails/sec")
print(f"\nSaved to: {output_file}")
print("="*70)
print("\nNext step: Run step3_generate_icebreakers.py")
print("="*70)
