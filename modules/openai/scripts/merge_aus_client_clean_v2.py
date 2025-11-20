#!/usr/bin/env python3
"""
=== AUS CLIENT DATA MERGER & CLEANER V2 ===
Version: 2.0.0 | Created: 2025-11-20

PURPOSE:
Simpler approach - just clean Excel data, restore business names, standardize columns

LOGIC:
- Take Excel data as base (already has scraped + validated)
- Restore Business Names from original CSVs
- Clean duplicate columns
- Standardize naming
- Remove garbage

USAGE:
python modules/openai/scripts/merge_aus_client_clean_v2.py
"""

import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

print("=" * 80)
print("AUS CLIENT DATA CLEANER V2.0.0")
print("=" * 80)

DOWNLOADS = "C:/Users/79818/Downloads/"
EXCEL_FILE = DOWNLOADS + "aus client.xlsx"

# Mapping of sheets to original CSVs
SHEET_CONFIG = {
    "AU cafes": {
        "original_csv": DOWNLOADS + "All Australian Cafes - No Email for Upwork.csv",
        "business_col": "Business Name",
        "website_col": "website",
        "has_website": True
    },
    "NZ cafes": {
        "original_csv": DOWNLOADS + "All New Zealand Cafes - No Email for Upwork.csv",
        "business_col": "Company Name",
        "website_col": "Website",
        "has_website": True
    },
    "AU resto": {
        "original_csv": DOWNLOADS + "All Australian Restaurants - No Email for Upwork.csv",
        "business_col": "Business Name",
        "website_col": "Website",
        "has_website": True
    },
    "NZ resto": {
        "original_csv": DOWNLOADS + "All New Zealand Restaurants - No Email for Upwork.csv",
        "business_col": "Business Name",
        "website_col": "Website",
        "has_website": False  # Excel has validation only
    },
    "NZ accom": {
        "original_csv": DOWNLOADS + "All New Zealand Accommodation - No Email for Upwork.csv",
        "business_col": "Business Name",
        "website_col": "Website",
        "has_website": True
    }
}

def normalize_url(url):
    """Normalize URL for matching"""
    if pd.isna(url):
        return ""
    url = str(url).lower().strip()
    url = url.replace("http://", "").replace("https://", "")
    url = url.rstrip("/").replace("www.", "")
    return url

def clean_sheet(sheet_name, config):
    """Clean one sheet"""
    print(f"\n{'='*80}")
    print(f"Processing: {sheet_name}")
    print(f"{'='*80}")

    # Load Excel sheet
    df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
    print(f"Loaded {len(df)} rows from Excel")

    # Load original CSV
    df_original = pd.read_csv(config['original_csv'])
    print(f"Loaded {len(df_original)} rows from original CSV")

    # Special handling for NZ resto (validation-only)
    if not config['has_website']:
        print("Validation-only sheet - using Excel data as-is (original CSV has no emails)")
        # Original CSV is "No Email for Upwork" - all emails are NaN
        # Just use validation data from Excel
        print(f"Using {len(df)} validated emails from Excel")

    # Create lookup: website -> business name
    website_col_orig = config['website_col']
    business_col_orig = config['business_col']

    url_to_name = {}
    for _, row in df_original.iterrows():
        url = normalize_url(row.get(website_col_orig, ''))
        name = row.get(business_col_orig, '')
        if url and name:
            url_to_name[url] = name

    print(f"Created business name lookup: {len(url_to_name)} entries")

    # Find website column in Excel
    website_col = 'website' if 'website' in df.columns else (config['website_col'] if config['website_col'] in df.columns else None)

    if website_col:
        # Restore business names
        df['website_norm'] = df[website_col].apply(normalize_url)
        df['Business Name'] = df['website_norm'].map(url_to_name)

        # If Business Name still empty, keep 'name' column if exists
        if 'name' in df.columns:
            df['Business Name'] = df['Business Name'].fillna(df['name'])

        print(f"Restored {df['Business Name'].notna().sum()} business names")
    else:
        print("No website column - using Business Name from merge")
        df['Business Name'] = df.get(business_col_orig, '')

    # Consolidate email columns (Email vs email vs Email.1)
    email_cols = [col for col in df.columns if 'email' in col.lower()]
    print(f"Found email columns: {email_cols}")

    # Priority: lowercase 'email' (scraped), then 'Email' (original), then 'Email.1' (validation)
    df['email'] = None
    if 'email' in df.columns:
        df['email'] = df['email']
    if df['email'].isna().all() and 'Email' in df.columns:
        df['email'] = df['Email']
    if df['email'].isna().any():
        for col in email_cols:
            df['email'] = df['email'].fillna(df[col])

    # Convert to string and clean
    df['email'] = df['email'].astype(str)

    # Keep only valid emails
    before = len(df)
    df = df[df['email'].str.contains('@', na=False)]
    df = df[df['email'].str.len() > 5]
    df = df[df['email'] != 'nan']
    df = df[df['email'] != 'None']
    print(f"Removed {before - len(df)} invalid emails")

    # Standard columns mapping
    col_map = {
        'Business Name': 'business_name',
        'website': 'website',
        'email': 'email',
        'phone': 'phone',
        'Phone': 'phone',
        'Phone Number': 'phone',
        'search_city': 'city',
        'City': 'city',
        'Location': 'city',
        'Company City': 'city',
        'Country': 'country',
        'country': 'country',
        'Company Country': 'country',
        'search_keyword': 'category',
        'Category': 'category',
        'homepage_content': 'homepage_content',
        'site_type': 'site_type',
        'scrape_status': 'scrape_status',
        'email_source': 'email_source',
        'Result': 'validation_result',
        'Score': 'validation_score',
        'Reason': 'validation_reason',
        'Provider': 'email_provider',
        'IsFree': 'is_free_email'
    }

    # Select columns that exist
    final_cols = []
    for old_col, new_col in col_map.items():
        if old_col in df.columns and new_col not in final_cols:
            final_cols.append(old_col)

    df_final = df[final_cols].copy()
    df_final = df_final.rename(columns=col_map)

    # Sort by validation score if available
    if 'validation_score' in df_final.columns:
        df_final = df_final.sort_values('validation_score', ascending=False, na_position='last')

    print(f"Final: {len(df_final)} rows x {len(df_final.columns)} columns")

    return df_final

def main():
    """Main"""
    results = {}

    for sheet_name, config in SHEET_CONFIG.items():
        try:
            df_clean = clean_sheet(sheet_name, config)
            results[sheet_name] = df_clean
        except Exception as e:
            print(f"ERROR processing {sheet_name}: {e}")
            import traceback
            traceback.print_exc()

    # Export to Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{DOWNLOADS}aus_client_CLEAN_{timestamp}.xlsx"

    print(f"\n{'='*80}")
    print("EXPORTING TO EXCEL")
    print(f"{'='*80}")
    print(f"File: {output_file}")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, df in results.items():
            print(f"  {sheet_name:20}: {len(df):>5} rows x {len(df.columns):>2} cols")
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    total_rows = sum(len(df) for df in results.values())
    print(f"Total rows: {total_rows}")
    for sheet_name, df in results.items():
        valid_emails = df[df.get('validation_result', '') == 'deliverable'].shape[0] if 'validation_result' in df.columns else 0
        print(f"  {sheet_name:15}: {len(df):>5} rows ({valid_emails:>4} deliverable)")

    print(f"\nSaved to: {output_file}")
    print("\nDONE!")

if __name__ == "__main__":
    main()
