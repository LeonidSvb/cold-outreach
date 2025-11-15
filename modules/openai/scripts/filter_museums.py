#!/usr/bin/env python3
"""
=== MUSEUM FILTER ===
Version: 1.0.0 | Created: 2025-01-19

PURPOSE:
Filter only museums from Soviet Boots dataset for specialized outreach

USAGE:
python filter_museums.py
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# Paths
INPUT_FILE = Path(r"C:\Users\79818\Downloads\Soviet Boots - Sheet3.csv")
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=== FILTERING MUSEUMS FROM SOVIET BOOTS DATABASE ===\n")

# Load data
print(f"Loading data from: {INPUT_FILE}")
df = pd.read_csv(INPUT_FILE)

print(f"Total organizations: {len(df)}")

# Filter museums
df_museums = df[df['type'] == 'museum'].copy()

print(f"Museums found: {len(df_museums)}")

# Save filtered data
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = OUTPUT_DIR / f"soviet_boots_museums_only_{timestamp}.csv"

df_museums.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"\n✅ Museums saved to: {output_file}")

# Show statistics
print(f"\n=== MUSEUM STATISTICS ===")
print(f"Total museums: {len(df_museums)}")
print(f"With emails: {df_museums['emails'].notna().sum()}")

# After splitting emails
emails_list = []
for emails_str in df_museums['emails'].dropna():
    emails = [e.strip() for e in str(emails_str).split(',') if e.strip()]
    emails_list.extend(emails)

print(f"Total email contacts (after split): {len(emails_list)}")

# Top countries for museums
if 'address' in df_museums.columns:
    countries = df_museums['address'].dropna().str.extract(r', ([A-Za-z\s]+)$')[0].value_counts()
    print(f"\n=== TOP 10 COUNTRIES (MUSEUMS) ===")
    for country, count in countries.head(10).items():
        pct = count / len(df_museums) * 100
        print(f"{country:20s}: {count:3d} ({pct:4.1f}%)")

print(f"\n✅ Ready for museum-specific email generation!")
