#!/usr/bin/env python3
"""Extract just email addresses for manual upload to mails.so"""

import pandas as pd
from pathlib import Path
import glob

# Find latest cleaned file
RESULTS_DIR = Path(__file__).parent.parent / "results"
cleaned_files = sorted(glob.glob(str(RESULTS_DIR / "us_1900_CLEANED_SPLIT_*.csv")))
INPUT_FILE = Path(cleaned_files[-1])

print(f"Reading: {INPUT_FILE.name}")

# Read CSV
df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
print(f"Total rows: {len(df)}")

# Extract emails only (non-empty)
emails = df[df['email'].notna() & (df['email'] != '')]['email'].values
print(f"Emails found: {len(emails)}")

# Save to simple CSV (just one column)
output_file = RESULTS_DIR / "emails_only_for_verification.csv"
pd.DataFrame({'email': emails}).to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\nSaved to: {output_file}")
print(f"\nYou can now upload this file to mails.so for bulk verification")
