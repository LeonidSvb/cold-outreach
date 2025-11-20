#!/usr/bin/env python3
"""
=== AUS CLIENT DATA MERGER & CLEANER ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Merge original CSVs with scraped and validated email data from Excel,
clean duplicate columns, restore company names, and export clean Excel file

FEATURES:
- Merges 5 audiences: AU cafes, NZ cafes, AU resto, NZ resto, NZ accom
- Restores Business Names (replaces website URLs in name column)
- Removes duplicate columns (email/Email, name/Business Name)
- Standardizes column names across all sheets
- Preserves all original data + adds scraped content + validation results
- Removes garbage data

USAGE:
1. Run: python modules/openai/scripts/merge_aus_client_data.py
2. Output: C:/Users/79818/Downloads/aus_client_MERGED_CLEAN_YYYYMMDD_HHMMSS.xlsx

IMPROVEMENTS:
v1.0.0 - Initial version
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

print("=" * 80)
print("AUS CLIENT DATA MERGER & CLEANER v1.0.0")
print("=" * 80)

# File paths
DOWNLOADS = "C:/Users/79818/Downloads/"
EXCEL_FILE = DOWNLOADS + "aus client.xlsx"

# Mapping of sheets to their original source files
DATASETS = {
    "AU cafes": {
        "sheet_name": "AU cafes",
        "original_csv": DOWNLOADS + "All Australian Cafes - No Email for Upwork.csv",
        "business_name_col": "Business Name"
    },
    "NZ cafes": {
        "sheet_name": "NZ cafes",
        "original_csv": DOWNLOADS + "All New Zealand Cafes - No Email for Upwork.csv",
        "business_name_col": "Company Name"
    },
    "AU resto": {
        "sheet_name": "AU resto",
        "original_csv": DOWNLOADS + "All Australian Restaurants - No Email for Upwork.csv",
        "business_name_col": "Business Name"
    },
    "NZ resto": {
        "sheet_name": "NZ resto",
        "original_csv": DOWNLOADS + "All New Zealand Restaurants - No Email for Upwork.csv",
        "business_name_col": "Business Name"
    },
    "NZ accom": {
        "sheet_name": "NZ accom",
        "original_csv": DOWNLOADS + "All New Zealand Accommodation - No Email for Upwork.csv",
        "business_name_col": "Business Name"
    }
}

def normalize_url(url):
    """Normalize URL for matching"""
    if pd.isna(url):
        return ""
    url = str(url).lower().strip()
    # Remove protocol
    url = url.replace("http://", "").replace("https://", "")
    # Remove trailing slash
    url = url.rstrip("/")
    # Remove www.
    url = url.replace("www.", "")
    return url

def clean_and_merge_dataset(dataset_name, config):
    """Clean and merge one dataset"""
    print(f"\n{'='*80}")
    print(f"Processing: {dataset_name}")
    print(f"{'='*80}")

    # 1. Load original CSV (full data, no emails)
    print(f"Loading original CSV: {config['original_csv']}")
    df_original = pd.read_csv(config['original_csv'])
    print(f"  Original data: {len(df_original)} rows, {len(df_original.columns)} columns")

    # 2. Load Excel sheet (scraped + validated emails only)
    print(f"Loading Excel sheet: {config['sheet_name']}")
    df_excel = pd.read_excel(EXCEL_FILE, sheet_name=config['sheet_name'])
    print(f"  Excel data: {len(df_excel)} rows, {len(df_excel.columns)} columns")

    # 3. Create lookup dictionary from original CSV (website -> business name)
    print("Creating business name lookup...")

    # Find website column in original (case-insensitive)
    website_col_original = None
    for col in df_original.columns:
        if 'website' in col.lower():
            website_col_original = col
            break

    if not website_col_original:
        print(f"  ERROR: No website column found in original CSV")
        return None

    # Create lookup dict: normalized_url -> business_name
    business_name_col = config['business_name_col']
    url_to_name = {}
    for _, row in df_original.iterrows():
        url = normalize_url(row[website_col_original])
        name = row.get(business_name_col, '')
        if url and name:
            url_to_name[url] = name

    print(f"  Created lookup with {len(url_to_name)} entries")

    # 4. Fix business names in Excel data
    print("Fixing business names in Excel data...")
    df_excel['website_normalized'] = df_excel['website'].apply(normalize_url)

    # Restore proper business names
    df_excel['Business Name'] = df_excel['website_normalized'].map(url_to_name)

    # If Business Name is still empty, try to use 'name' column if it's not a URL
    if 'name' in df_excel.columns:
        mask = df_excel['Business Name'].isna()
        df_excel.loc[mask, 'Business Name'] = df_excel.loc[mask, 'name']

    # 5. Clean up duplicate columns
    print("Cleaning duplicate columns...")
    df_merged = df_excel.copy()

    # Clean email columns (lowercase email vs uppercase Email)
    email_cols = [col for col in df_merged.columns if col.lower() == 'email']
    if len(email_cols) > 1:
        # Consolidate into single 'email' column
        df_merged['email'] = None
        for col in email_cols:
            df_merged['email'] = df_merged['email'].fillna(df_merged[col])

    # Remove rows with no email (they're not useful)
    before_email_filter = len(df_merged)
    df_merged = df_merged[df_merged['email'].notna() & (df_merged['email'] != '')]
    print(f"  Removed {before_email_filter - len(df_merged)} rows without email")

    # 6. Standardize column names
    print("Standardizing column names...")

    # Core columns to keep
    standard_columns = {
        'Business Name': 'business_name',
        'website': 'website',
        'email': 'email',
        'phone': 'phone',
        'homepage_content': 'homepage_content',
        'site_type': 'site_type',
        'scrape_status': 'scrape_status',
        'email_source': 'email_source',
        'Result': 'validation_result',
        'Score': 'validation_score',
        'Reason': 'validation_reason',
        'Provider': 'email_provider',
        'IsFree': 'is_free_email',
        'Country': 'country',
        'search_keyword': 'category',
        'search_city': 'city'
    }

    # Phone column (different names)
    phone_cols = [col for col in df_merged.columns if 'phone' in col.lower()]
    if phone_cols:
        df_merged['phone'] = df_merged[phone_cols[0]]

    # City/Location column
    city_cols = [col for col in df_merged.columns if col.lower() in ['city', 'location', 'search_city', 'company city']]
    if city_cols:
        df_merged['city'] = df_merged[city_cols[0]]

    # Country column
    country_cols = [col for col in df_merged.columns if 'country' in col.lower()]
    if country_cols:
        df_merged['country'] = df_merged[country_cols[0]]

    # Select and rename columns
    final_columns = []
    for old_name, new_name in standard_columns.items():
        if old_name in df_merged.columns:
            final_columns.append(old_name)

    df_final = df_merged[final_columns].copy()
    df_final = df_final.rename(columns=standard_columns)

    # 7. Remove garbage data
    print("Removing garbage data...")
    before_cleanup = len(df_final)

    # Convert email to string and remove invalid emails
    if 'email' in df_final.columns:
        df_final['email'] = df_final['email'].astype(str)
        df_final = df_final[df_final['email'].str.contains('@', na=False)]
        df_final = df_final[df_final['email'].str.len() > 5]
        df_final = df_final[df_final['email'] != 'nan']
        df_final = df_final[df_final['email'] != 'None']

    # Remove rows where business name is same as website (scraper error)
    if 'business_name' in df_final.columns and 'website' in df_final.columns:
        df_final = df_final[~(df_final['business_name'].fillna('').str.lower() ==
                                df_final['website'].fillna('').str.lower())]

    print(f"  Removed {before_cleanup - len(df_final)} garbage rows")
    print(f"  Final clean data: {len(df_final)} rows, {len(df_final.columns)} columns")

    # 8. Sort by validation score (best emails first)
    if 'validation_score' in df_final.columns:
        df_final = df_final.sort_values('validation_score', ascending=False)

    return df_final

def main():
    """Main execution"""
    print("\nStarting merge and cleanup process...")

    # Process each dataset
    results = {}
    for dataset_name, config in DATASETS.items():
        df_clean = clean_and_merge_dataset(dataset_name, config)
        if df_clean is not None:
            results[dataset_name] = df_clean

    # Export to Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{DOWNLOADS}aus_client_MERGED_CLEAN_{timestamp}.xlsx"

    print(f"\n{'='*80}")
    print("EXPORTING TO EXCEL")
    print(f"{'='*80}")
    print(f"Output file: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, df in results.items():
            print(f"  Writing sheet: {sheet_name} ({len(df)} rows)")
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    for sheet_name, df in results.items():
        print(f"{sheet_name:20} : {len(df):>6} rows x {len(df.columns):>2} columns")

    print(f"\nOutput saved to: {output_file}")
    print("\nDONE!")

if __name__ == "__main__":
    main()
