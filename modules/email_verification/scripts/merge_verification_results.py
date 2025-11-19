#!/usr/bin/env python3
"""Merge mails.so verification results with original data"""

import pandas as pd
from pathlib import Path
import glob
from datetime import datetime

print("="*70)
print("MERGING VERIFICATION RESULTS WITH ORIGINAL DATA")
print("="*70)

# Paths
RESULTS_DIR = Path(__file__).parent.parent / "results"
VERIFICATION_FILE = Path(r"C:\Users\79818\Downloads\batch_18758a12-b275-431c-a009-449d0db08ff7_deliverable_risky.csv")

# Find latest cleaned file
cleaned_files = sorted(glob.glob(str(RESULTS_DIR / "us_1900_CLEANED_SPLIT_*.csv")))
ORIGINAL_FILE = Path(cleaned_files[-1])

print(f"\nOriginal data: {ORIGINAL_FILE.name}")
print(f"Verification results: {VERIFICATION_FILE.name}")

# Read files
df_original = pd.read_csv(ORIGINAL_FILE, encoding='utf-8-sig')
df_verified = pd.read_csv(VERIFICATION_FILE, encoding='utf-8-sig')

print(f"\nOriginal rows: {len(df_original)}")
print(f"Verified emails: {len(df_verified)}")

# Normalize email column in verification data
df_verified = df_verified.rename(columns={'Email': 'email'})

# Keep only useful verification columns
verification_cols = {
    'email': 'email',
    'Result': 'verification_result',
    'Score': 'verification_score',
    'Provider': 'email_provider',
    'IsvFormat': 'format_valid',
    'IsvDomain': 'domain_valid',
    'IsvMx': 'mx_valid',
    'IsFree': 'is_free_email'
}

df_verified = df_verified.rename(columns=verification_cols)
df_verified = df_verified[list(verification_cols.values())]

# Remove duplicates - keep first occurrence
print(f"Verified before dedup: {len(df_verified)}")
df_verified = df_verified.drop_duplicates(subset='email', keep='first')
print(f"Verified after dedup: {len(df_verified)}")

# Merge with original data (left join to keep all original rows)
df_merged = df_original.merge(
    df_verified,
    on='email',
    how='left'
)

# Fill NaN for rows without verification (no email)
df_merged['verification_result'] = df_merged['verification_result'].fillna('no_email')

# Statistics
stats = df_merged['verification_result'].value_counts().to_dict()
print("\n" + "="*70)
print("VERIFICATION STATISTICS")
print("="*70)
for status, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / len(df_merged)) * 100
    print(f"{status:20} : {count:4} ({percentage:5.1f}%)")

# Calculate deliverable count
deliverable = df_merged[df_merged['verification_result'] == 'deliverable']
risky = df_merged[df_merged['verification_result'] == 'risky']
print(f"\nDeliverable + Risky : {len(deliverable) + len(risky)} ({((len(deliverable) + len(risky))/len(df_merged))*100:.1f}%)")

# Save merged file
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = RESULTS_DIR / f"us_1900_VERIFIED_MERGED_{timestamp}.csv"
df_merged.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\nSUCCESS: Saved as {output_file.name}")
print(f"\nNext step: Generate icebreakers for deliverable emails")
print(f"Run: step3_generate_icebreakers.py")
