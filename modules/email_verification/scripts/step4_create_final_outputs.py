#!/usr/bin/env python3
"""
STEP 4: Create final output files
- DELIVERABLE: all verified deliverable emails with icebreakers
- MERGED: landscaping (100) + US 1900 deliverable
- PHONE_ONLY: businesses with no valid email, only phone
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import glob

print("="*70)
print("STEP 4: CREATE FINAL OUTPUT FILES")
print("="*70)

# Paths
RESULTS_DIR = Path(__file__).parent.parent / "results"
LANDSCAPING_FILE = r"C:\Users\79818\Downloads\Master Sheet - 100 landscaping texas.csv"

# Find latest file with icebreakers
icebreaker_files = sorted(glob.glob(str(RESULTS_DIR / "us_1900_WITH_ICEBREAKERS_*.csv")))
if not icebreaker_files:
    print("ERROR: No icebreaker file found! Run step3 first.")
    sys.exit(1)

INPUT_FILE = Path(icebreaker_files[-1])

print(f"\nInput file: {INPUT_FILE.name}")
print(f"Landscaping file: {Path(LANDSCAPING_FILE).name}")

# Read files
df_us = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
df_landscaping = pd.read_csv(LANDSCAPING_FILE, encoding='utf-8-sig')

print(f"\nUS 1900 total: {len(df_us)}")
print(f"Landscaping total: {len(df_landscaping)}")

# Filter deliverable from US 1900
deliverable = df_us[df_us['verification_result'] == 'deliverable'].copy()
print(f"\nUS 1900 deliverable: {len(deliverable)}")

# Create output timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# =========================================================================
# FILE 1: US 1900 DELIVERABLE with icebreakers (ready for Instantly)
# =========================================================================

print("\n" + "="*70)
print("Creating FILE 1: US 1900 DELIVERABLE (Instantly-ready)")
print("="*70)

# Select columns for Instantly
deliverable_output = deliverable[[
    'name', 'email', 'phone', 'website', 'city', 'state', 'address',
    'rating', 'reviews', 'niche', 'business_summary', 'personalization_angle',
    'icebreaker', 'verification_score', 'email_provider'
]].copy()

output_deliverable = RESULTS_DIR / f"US_1900_DELIVERABLE_{timestamp}.csv"
deliverable_output.to_csv(output_deliverable, index=False, encoding='utf-8-sig')

print(f"Saved: {output_deliverable}")
print(f"Rows: {len(deliverable_output)}")
print(f"Ready for upload to Instantly.ai")

# =========================================================================
# FILE 2: MERGED (Landscaping + US 1900 deliverable)
# =========================================================================

print("\n" + "="*70)
print("Creating FILE 2: MERGED (Landscaping + US 1900)")
print("="*70)

# Align columns
common_cols = ['name', 'email', 'phone', 'website', 'city', 'state', 'rating', 'icebreaker', 'source']

# Prepare landscaping data
df_landscaping_aligned = pd.DataFrame()
df_landscaping_aligned['name'] = df_landscaping.iloc[:, 0]  # First column (has BOM)
df_landscaping_aligned['email'] = df_landscaping['emails']
df_landscaping_aligned['phone'] = df_landscaping['phone']
df_landscaping_aligned['website'] = df_landscaping['website']
df_landscaping_aligned['city'] = df_landscaping['city']
df_landscaping_aligned['state'] = df_landscaping['state']
df_landscaping_aligned['rating'] = df_landscaping['totalScore']
df_landscaping_aligned['icebreaker'] = df_landscaping['icebreaker']
df_landscaping_aligned['source'] = 'landscaping_texas'

# Prepare US 1900 data
df_us_aligned = deliverable[['name', 'email', 'phone', 'website', 'city', 'state', 'rating', 'icebreaker']].copy()
df_us_aligned['source'] = 'us_1900_local_biz'

# Merge
df_merged = pd.concat([df_landscaping_aligned, df_us_aligned], ignore_index=True)

output_merged = RESULTS_DIR / f"MERGED_ALL_DELIVERABLE_{timestamp}.csv"
df_merged.to_csv(output_merged, index=False, encoding='utf-8-sig')

print(f"Saved: {output_merged}")
print(f"Rows: {len(df_merged)}")
print(f"  Landscaping: {len(df_landscaping_aligned)}")
print(f"  US 1900: {len(df_us_aligned)}")

# =========================================================================
# FILE 3: PHONE-ONLY (no valid email or verification failed)
# =========================================================================

print("\n" + "="*70)
print("Creating FILE 3: PHONE-ONLY (for voice AI calls)")
print("="*70)

# Filter: no email OR verification failed
phone_only = df_us[
    (df_us['email'] == '') |
    (df_us['verification_result'].isin(['undeliverable', 'unknown', 'error', 'no_email']))
].copy()

# Keep only rows with phone numbers
phone_only = phone_only[phone_only['phone'].notna() & (phone_only['phone'] != '')].copy()

# Remove duplicates by phone number (keep first)
phone_only = phone_only.drop_duplicates(subset=['phone'], keep='first')

# Select relevant columns
phone_only_output = phone_only[[
    'name', 'phone', 'website', 'city', 'state', 'address',
    'rating', 'reviews', 'niche', 'business_summary', 'personalization_angle'
]].copy()

output_phone = RESULTS_DIR / f"US_1900_PHONE_ONLY_{timestamp}.csv"
phone_only_output.to_csv(output_phone, index=False, encoding='utf-8-sig')

print(f"Saved: {output_phone}")
print(f"Rows: {len(phone_only_output)}")
print(f"Ready for voice AI campaigns")

# =========================================================================
# SUMMARY
# =========================================================================

print("\n" + "="*70)
print("ALL FILES CREATED SUCCESSFULLY")
print("="*70)

print(f"\nFILE 1: {output_deliverable.name}")
print(f"  {len(deliverable_output)} deliverable emails with icebreakers")
print(f"  Ready for Instantly.ai upload")

print(f"\nFILE 2: {output_merged.name}")
print(f"  {len(df_merged)} total contacts")
print(f"  Combined: Landscaping ({len(df_landscaping_aligned)}) + US 1900 ({len(df_us_aligned)})")

print(f"\nFILE 3: {output_phone.name}")
print(f"  {len(phone_only_output)} phone-only contacts")
print(f"  For voice AI outreach")

# Stats
total_us_processed = len(df_us)
deliverable_count = len(deliverable)
phone_only_count = len(phone_only_output)
deliverable_rate = deliverable_count / total_us_processed * 100 if total_us_processed > 0 else 0

print(f"\n" + "="*70)
print("PROCESSING STATISTICS")
print("="*70)
print(f"Original US 1900 rows: 1894")
print(f"After email split: {total_us_processed}")
print(f"Deliverable emails: {deliverable_count} ({deliverable_rate:.1f}%)")
print(f"Phone-only (no email): {phone_only_count}")
print(f"Total usable contacts: {deliverable_count + phone_only_count}")

print("\n" + "="*70)
print("WORKFLOW COMPLETE!")
print("="*70)
