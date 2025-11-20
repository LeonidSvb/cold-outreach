#!/usr/bin/env python3
"""
=== FINAL AUS CLIENT DATA MERGER ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Merge existing clean Excel (1,050 emails) with new scraped emails (~1,300)
Properly distribute across 5 audiences (niches)

FEATURES:
- Merges existing + new scraped data
- Maintains 5 separate sheets (AU cafes, NZ cafes, AU resto, NZ resto, NZ accom)
- Deduplicates by email within each niche
- Preserves all validation results + scraped content
- Smart column standardization

USAGE:
python modules/openai/scripts/merge_final_aus_client.py

OUTPUT:
C:/Users/79818/Downloads/aus_client_FINAL_MERGED_{timestamp}.xlsx
"""

import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

print("=" * 80)
print("FINAL AUS CLIENT DATA MERGER")
print("=" * 80)

DOWNLOADS = "C:/Users/79818/Downloads/"

# Existing clean Excel (1,050 emails)
CLEAN_EXCEL = DOWNLOADS + "aus_client_CLEAN_20251120_182740.xlsx"

# New scraped data
SCRAPED_CSV = "modules/scraping/homepage_email_scraper/results/aus_client_deep_search/incremental_results.csv"

# Mapping: CSV audience names → Excel sheet names
AUDIENCE_MAP = {
    "AU_Cafes": "AU cafes",
    "NZ_Cafes": "NZ cafes",
    "AU_Resto": "AU resto",
    "NZ_Resto": "NZ resto",
    "NZ_Accom": "NZ accom"
}

def load_existing_data():
    """Load existing clean Excel (5 sheets)"""
    print(f"\nLoading existing clean data from: {CLEAN_EXCEL}")

    existing = {}
    with pd.ExcelFile(CLEAN_EXCEL) as excel:
        for sheet_name in excel.sheet_names:
            df = pd.read_excel(excel, sheet_name=sheet_name)
            existing[sheet_name] = df
            print(f"  {sheet_name:15}: {len(df):>4} rows")

    total_existing = sum(len(df) for df in existing.values())
    print(f"\nTotal existing: {total_existing} rows")

    return existing

def load_new_scraped_data():
    """Load new scraped data"""
    print(f"\nLoading new scraped data from: {SCRAPED_CSV}")

    if not Path(SCRAPED_CSV).exists():
        print("  ERROR: Scraped CSV not found!")
        return None

    df = pd.read_csv(SCRAPED_CSV)

    # Filter only rows with emails
    df_with_emails = df[df['email'].notna()].copy()

    print(f"  Total rows: {len(df)}")
    print(f"  With emails: {len(df_with_emails)}")

    # Check if 'audience' column exists
    if 'audience' not in df_with_emails.columns:
        print("\n  WARNING: 'audience' column not found!")
        print("  Cannot distribute across niches. Need to add audience info.")
        return None

    # Group by audience
    print(f"\nBreakdown by audience:")
    for audience, count in df_with_emails['audience'].value_counts().items():
        mapped_name = AUDIENCE_MAP.get(audience, audience)
        print(f"  {audience:15} → {mapped_name:15}: {count:>4} emails")

    return df_with_emails

def standardize_columns(df, is_scraped=False):
    """Standardize column names"""
    # Common columns mapping
    col_map = {
        'Business Name': 'business_name',
        'business_name': 'business_name',
        'name': 'business_name',
        'website': 'website',
        'email': 'email',
        'phone': 'phone',
        'Phone': 'phone',
        'Phone Number': 'phone',
        'city': 'city',
        'City': 'city',
        'Location': 'city',
        'search_city': 'city',
        'Company City': 'city',
        'country': 'country',
        'Country': 'country',
        'Company Country': 'country',
        'category': 'category',
        'Category': 'category',
        'search_keyword': 'category',
        'homepage_content': 'homepage_content',
        'site_type': 'site_type',
        'scrape_status': 'scrape_status',
        'email_source': 'email_source',
        'validation_result': 'validation_result',
        'Result': 'validation_result',
        'validation_score': 'validation_score',
        'Score': 'validation_score',
        'validation_reason': 'validation_reason',
        'Reason': 'validation_reason',
        'email_provider': 'email_provider',
        'Provider': 'email_provider',
        'is_free_email': 'is_free_email',
        'IsFree': 'is_free_email'
    }

    # Rename columns
    df_renamed = df.copy()
    for old_col in df.columns:
        if old_col in col_map:
            new_col = col_map[old_col]
            if new_col not in df_renamed.columns or old_col == new_col:
                df_renamed = df_renamed.rename(columns={old_col: new_col})

    return df_renamed

def merge_niche_data(existing_df, new_df, niche_name):
    """Merge existing and new data for one niche"""
    print(f"\n  Merging {niche_name}...")
    print(f"    Existing: {len(existing_df)} rows")
    print(f"    New scraped: {len(new_df)} rows")

    # Standardize columns for both
    existing_std = standardize_columns(existing_df, is_scraped=False)
    new_std = standardize_columns(new_df, is_scraped=True)

    # Add source column for tracking
    existing_std['data_source'] = 'original'
    new_std['data_source'] = 'deep_search'

    # Combine
    combined = pd.concat([existing_std, new_std], ignore_index=True)
    print(f"    Combined: {len(combined)} rows")

    # Deduplicate by email (keep first = prioritize original data)
    before_dedup = len(combined)
    combined_dedup = combined.drop_duplicates(subset='email', keep='first')
    duplicates_removed = before_dedup - len(combined_dedup)

    print(f"    After dedup: {len(combined_dedup)} rows (-{duplicates_removed} duplicates)")

    # Sort by validation score if available
    if 'validation_score' in combined_dedup.columns:
        combined_dedup = combined_dedup.sort_values('validation_score', ascending=False, na_position='last')

    return combined_dedup

def main():
    """Main execution"""
    print("\nStarting merge process...\n")

    # Load existing data
    existing_data = load_existing_data()

    # Load new scraped data
    new_scraped = load_new_scraped_data()

    if new_scraped is None:
        print("\nERROR: Cannot proceed without scraped data")
        return

    # Merge each niche
    print("\n" + "="*80)
    print("MERGING DATA BY NICHE")
    print("="*80)

    final_results = {}

    for audience_csv, sheet_name in AUDIENCE_MAP.items():
        # Get new data for this audience
        new_for_audience = new_scraped[new_scraped['audience'] == audience_csv].copy()

        # Get existing data
        existing_for_audience = existing_data.get(sheet_name, pd.DataFrame())

        if len(new_for_audience) == 0 and len(existing_for_audience) == 0:
            print(f"\n  {sheet_name}: No data, skipping")
            continue

        # Merge
        merged = merge_niche_data(existing_for_audience, new_for_audience, sheet_name)
        final_results[sheet_name] = merged

    # Export to Excel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{DOWNLOADS}aus_client_FINAL_MERGED_{timestamp}.xlsx"

    print(f"\n{'='*80}")
    print("EXPORTING TO EXCEL")
    print(f"{'='*80}")
    print(f"File: {output_file}\n")

    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for sheet_name, df in final_results.items():
            deliverable_count = 0
            if 'validation_result' in df.columns:
                deliverable_count = (df['validation_result'] == 'deliverable').sum()

            print(f"  {sheet_name:15}: {len(df):>5} rows ({deliverable_count:>4} deliverable)")
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    total_rows = sum(len(df) for df in final_results.values())
    total_deliverable = sum(
        (df['validation_result'] == 'deliverable').sum()
        if 'validation_result' in df.columns else 0
        for df in final_results.values()
    )

    print(f"Total rows: {total_rows}")
    print(f"Deliverable emails: {total_deliverable}")
    print(f"\nOutput: {output_file}")
    print("\nDONE!")

if __name__ == "__main__":
    main()
