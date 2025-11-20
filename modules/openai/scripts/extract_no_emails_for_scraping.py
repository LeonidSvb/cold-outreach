#!/usr/bin/env python3
"""
=== EXTRACT NO-EMAIL RECORDS FOR DEEP SEARCH SCRAPING ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Extract all records with website but no email from original CSVs
Prepare for deep search scraping to find more contacts

FEATURES:
- Extracts records where website exists but email is empty
- Combines all 5 audiences into single CSV
- Adds audience tag for tracking
- Standardizes column names

USAGE:
python modules/openai/scripts/extract_no_emails_for_scraping.py
"""

import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

print("=" * 80)
print("EXTRACT NO-EMAIL RECORDS FOR SCRAPING")
print("=" * 80)

DOWNLOADS = "C:/Users/79818/Downloads/"

# All original CSVs
DATASETS = {
    "AU_Cafes": {
        "file": DOWNLOADS + "All Australian Cafes - No Email for Upwork.csv",
        "website_col": "website",
        "email_col": "email",
        "business_col": "Business Name"
    },
    "NZ_Cafes": {
        "file": DOWNLOADS + "All New Zealand Cafes - No Email for Upwork.csv",
        "website_col": "Website",
        "email_col": "Email",
        "business_col": "Company Name"
    },
    "AU_Resto": {
        "file": DOWNLOADS + "All Australian Restaurants - No Email for Upwork.csv",
        "website_col": "Website",
        "email_col": "Email",
        "business_col": "Business Name"
    },
    "NZ_Resto": {
        "file": DOWNLOADS + "All New Zealand Restaurants - No Email for Upwork.csv",
        "website_col": "Website",
        "email_col": "Email",
        "business_col": "Business Name"
    },
    "NZ_Accom": {
        "file": DOWNLOADS + "All New Zealand Accommodation - No Email for Upwork.csv",
        "website_col": "Website",
        "email_col": "Email",
        "business_col": "Business Name"
    }
}

def extract_no_emails(dataset_name, config):
    """Extract records with website but no email"""
    print(f"\n{'='*80}")
    print(f"Processing: {dataset_name}")
    print(f"{'='*80}")

    df = pd.read_csv(config['file'])
    print(f"Loaded: {len(df)} rows")

    website_col = config['website_col']
    email_col = config['email_col']
    business_col = config['business_col']

    # Filter: website exists AND email is empty
    # Convert to string to avoid type errors
    df[website_col] = df[website_col].astype(str)
    df[email_col] = df[email_col].astype(str)

    has_website = df[website_col].notna() & (df[website_col].str.strip() != '') & (df[website_col] != 'nan')
    no_email = (df[email_col].isna()) | (df[email_col].str.strip() == '') | (df[email_col] == 'nan')

    df_filtered = df[has_website & no_email].copy()

    print(f"Records with website but no email: {len(df_filtered)}")

    # Standardize columns for scraping
    df_filtered['audience'] = dataset_name
    df_filtered['name'] = df_filtered[business_col]
    df_filtered['website'] = df_filtered[website_col]

    # Keep only needed columns
    cols_to_keep = ['audience', 'name', 'website']

    # Add any location/city column if exists
    city_cols = [col for col in df_filtered.columns if col.lower() in ['city', 'location', 'search_city', 'company city']]
    if city_cols:
        df_filtered['city'] = df_filtered[city_cols[0]]
        cols_to_keep.append('city')

    # Add country if exists
    country_cols = [col for col in df_filtered.columns if 'country' in col.lower()]
    if country_cols:
        df_filtered['country'] = df_filtered[country_cols[0]]
        cols_to_keep.append('country')

    df_final = df_filtered[cols_to_keep].copy()

    return df_final

def main():
    """Main execution"""
    all_data = []

    for dataset_name, config in DATASETS.items():
        df = extract_no_emails(dataset_name, config)
        all_data.append(df)

    # Combine all datasets
    df_combined = pd.concat(all_data, ignore_index=True)

    print(f"\n{'='*80}")
    print("COMBINED RESULTS")
    print(f"{'='*80}")
    print(f"Total records for scraping: {len(df_combined)}")

    # Summary by audience
    print("\nBreakdown by audience:")
    for audience in df_combined['audience'].unique():
        count = len(df_combined[df_combined['audience'] == audience])
        print(f"  {audience:15}: {count:>5} records")

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{DOWNLOADS}aus_client_NO_EMAILS_FOR_SCRAPING_{timestamp}.csv"

    df_combined.to_csv(output_file, index=False)

    print(f"\n{'='*80}")
    print("OUTPUT")
    print(f"{'='*80}")
    print(f"Saved to: {output_file}")
    print(f"Total rows: {len(df_combined)}")
    print(f"Columns: {list(df_combined.columns)}")

    print("\nNext step:")
    print("Run homepage_email_scraper with deep_search mode on this CSV")
    print("\nDONE!")

if __name__ == "__main__":
    main()
