#!/usr/bin/env python3
"""
STEP 1: Clean and split emails from US 1900 file
"""

import sys
import re
import pandas as pd
from pathlib import Path
from datetime import datetime

print("="*70)
print("STEP 1: CLEAN AND SPLIT EMAILS")
print("="*70)

# Configuration
INPUT_FILE = r"C:\Users\79818\Downloads\Master Sheet - US 1900 local biz+.csv"
OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Email cleanup patterns
CLEANUP_PATTERNS = [
    # URL encoding
    (r'^%20+', ''),
    (r'%20', ''),

    # Concatenated text after email (e.g., .comhoursavailable -> .com)
    (r'@([a-zA-Z0-9\-\.]+\.[a-z]{2,})([a-z]{4,}.*?)$', r'@\1'),

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

    # Phone numbers (remove them)
    (r'\(\d{3}\)\s*\d{3}-\d{4}', ''),
    (r'\d{3}-\d{3}-\d{4}', ''),
    (r'\d{3}-\d{4}', ''),  # Short phone format
]


def clean_email(email: str) -> str:
    """Clean single email"""
    if not email or pd.isna(email):
        return ""

    cleaned = email.strip()

    for pattern, replacement in CLEANUP_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    cleaned = cleaned.strip().lower()

    # Basic validation
    if '@' not in cleaned or '.' not in cleaned.split('@')[-1]:
        return ""

    # Remove trailing/leading special chars
    cleaned = cleaned.strip('.,;: ')

    return cleaned


def split_multi_emails(email_str: str) -> list:
    """Split comma/semicolon-separated emails"""
    if not email_str or pd.isna(email_str):
        return []

    # Split by comma or semicolon
    emails = re.split(r'[,;]\s*', email_str)

    # Clean each
    cleaned_emails = []
    for email in emails:
        cleaned = clean_email(email)
        if cleaned and '@' in cleaned and len(cleaned) > 5:
            cleaned_emails.append(cleaned)

    return cleaned_emails


print(f"\nReading: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE, encoding='utf-8')
print(f"Total rows: {len(df)}")

# Analyze emails before processing
multi_email_rows = df['email'].str.contains(',', na=False).sum()
empty_emails = df['email'].isna().sum()
print(f"Multi-email rows: {multi_email_rows}")
print(f"Empty emails: {empty_emails}")

print("\n" + "="*70)
print("PROCESSING: Cleaning and splitting emails...")
print("="*70)

# Process each row
expanded_rows = []
stats = {
    'original_rows': len(df),
    'rows_with_no_email': 0,
    'rows_with_single_email': 0,
    'rows_with_multi_email': 0,
    'total_emails_extracted': 0
}

for idx, row in df.iterrows():
    if (idx + 1) % 100 == 0:
        print(f"Processed {idx + 1}/{len(df)} rows...")

    email_str = row['email']
    emails = split_multi_emails(email_str)

    if not emails:
        # No valid email - keep row but mark it
        row_copy = row.copy()
        row_copy['email'] = ""
        row_copy['email_cleaned'] = ""
        row_copy['email_status'] = "no_valid_email"
        expanded_rows.append(row_copy)
        stats['rows_with_no_email'] += 1
    elif len(emails) == 1:
        # Single email
        row_copy = row.copy()
        row_copy['email'] = emails[0]
        row_copy['email_cleaned'] = emails[0]
        row_copy['email_status'] = "single_email"
        expanded_rows.append(row_copy)
        stats['rows_with_single_email'] += 1
        stats['total_emails_extracted'] += 1
    else:
        # Multiple emails - create one row per email
        for email in emails:
            row_copy = row.copy()
            row_copy['email'] = email
            row_copy['email_cleaned'] = email
            row_copy['email_status'] = "multi_email_split"
            expanded_rows.append(row_copy)
        stats['rows_with_multi_email'] += 1
        stats['total_emails_extracted'] += len(emails)

df_expanded = pd.DataFrame(expanded_rows)

print("\n" + "="*70)
print("CLEANING COMPLETE")
print("="*70)
print(f"Original rows: {stats['original_rows']}")
print(f"  No valid email: {stats['rows_with_no_email']}")
print(f"  Single email: {stats['rows_with_single_email']}")
print(f"  Multi-email (split): {stats['rows_with_multi_email']}")
print(f"\nExpanded rows: {len(df_expanded)}")
print(f"Total emails extracted: {stats['total_emails_extracted']}")

# Save results
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = OUTPUT_DIR / f"us_1900_CLEANED_SPLIT_{timestamp}.csv"
df_expanded.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\nSaved to: {output_file}")
print("="*70)
print("\nNext step: Run step2_verify_emails.py")
print("="*70)
