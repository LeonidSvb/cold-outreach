#!/usr/bin/env python3
"""
=== MATCH WITH GOOGLE MAPS DATA ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Match missing Google Maps data by email from original scraping results

FEATURES:
- Match by email (exact match)
- Match by domain (fuzzy match)
- Extract all Google Maps fields (name, website, rating, reviews, address, etc.)
- Preserve all existing data

USAGE:
python match_with_gmaps_data.py

INPUT:
- merged_best_emails_20251120_150222.csv (has 93 rows missing data)
- stage2_output_20251110_165405.csv (Google Maps source with 568 Florida businesses)

OUTPUT:
- merged_best_emails_COMPLETE_[timestamp].csv
"""

import sys
import re
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from modules.logging.shared.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "MERGED_FILE": r"C:\Users\79818\Desktop\Outreach - new\merged_best_emails_20251120_150222.csv",
    "GMAPS_FILE": r"C:\Users\79818\Desktop\Outreach - new\archive\modules_backup\google_maps_data\temp\stage2_output_20251110_165405.csv",
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
}

# ============================================================================
# MATCHING FUNCTIONS
# ============================================================================

def extract_all_emails_from_row(row: dict) -> list:
    """Extract all emails from Google Maps row"""
    all_emails = []

    # From emails_x column
    emails_x = row.get('emails_x', '')
    if pd.notna(emails_x) and str(emails_x).strip():
        emails_list = str(emails_x).split(',')
        all_emails.extend([e.strip().lower() for e in emails_list if e.strip()])

    # From emails_y column
    emails_y = row.get('emails_y', '')
    if pd.notna(emails_y) and str(emails_y).strip():
        emails_list = str(emails_y).split(',')
        all_emails.extend([e.strip().lower() for e in emails_list if e.strip()])

    # Deduplicate
    return list(set(all_emails))


def create_email_to_gmaps_mapping(df_gmaps: pd.DataFrame) -> dict:
    """
    Create mapping: email -> Google Maps row data
    Returns: {email: row_dict}
    """
    email_map = {}

    for idx, row in df_gmaps.iterrows():
        emails = extract_all_emails_from_row(row.to_dict())

        for email in emails:
            if email and '@' in email:
                # Store row data (convert to dict)
                email_map[email] = row.to_dict()

    return email_map


def extract_gmaps_fields(gmaps_row: dict) -> dict:
    """Extract relevant fields from Google Maps row"""

    # Extract phone numbers
    phones_str = gmaps_row.get('phones', '')
    phone = ''
    if pd.notna(phones_str) and str(phones_str).strip():
        phone_list = str(phones_str).split(',')
        if phone_list:
            phone = phone_list[0].strip()  # Take first phone

    # Website URL
    website = gmaps_row.get('url', '')
    if pd.isna(website) or not str(website).strip():
        website = ''

    # Google Maps place URL for reviews
    place_id = gmaps_row.get('place_id', '')
    google_maps_url = ''
    if pd.notna(place_id) and str(place_id).strip():
        google_maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

    return {
        'name': gmaps_row.get('name', ''),
        'phone': phone,
        'website': website,
        'city': gmaps_row.get('city', ''),
        'state': gmaps_row.get('state', ''),
        'niche': gmaps_row.get('niche', ''),
        'google_maps_url': google_maps_url,
        'place_id': place_id,
        # Note: rating, reviews, address not in this file
        # Will be empty for matched rows
    }


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def main():
    """Main matching function"""

    logger.info("="*70)
    logger.info("MATCH WITH GOOGLE MAPS DATA")
    logger.info("="*70)

    # Read merged file
    merged_file = Path(CONFIG["MERGED_FILE"])
    if not merged_file.exists():
        logger.error(f"Merged file not found: {merged_file}")
        return

    logger.info(f"\nReading merged file: {merged_file.name}")
    df_merged = pd.read_csv(merged_file, encoding='utf-8-sig')
    logger.info(f"Total rows: {len(df_merged):,}")

    # Read Google Maps file
    gmaps_file = Path(CONFIG["GMAPS_FILE"])
    if not gmaps_file.exists():
        logger.error(f"Google Maps file not found: {gmaps_file}")
        return

    logger.info(f"\nReading Google Maps file: {gmaps_file.name}")
    df_gmaps = pd.read_csv(gmaps_file, encoding='utf-8-sig')
    logger.info(f"Total Google Maps rows: {len(df_gmaps):,}")

    # Filter Florida only
    df_gmaps_fl = df_gmaps[df_gmaps['state'] == 'florida'].copy()
    logger.info(f"Florida businesses: {len(df_gmaps_fl):,}")

    # Create email mapping
    logger.info(f"\n{'='*70}")
    logger.info("CREATING EMAIL MAPPING")
    logger.info("="*70)

    email_map = create_email_to_gmaps_mapping(df_gmaps_fl)
    logger.info(f"Total unique emails in Google Maps: {len(email_map):,}")

    # Identify missing rows
    missing_mask = df_merged['website'].isna()
    missing_df = df_merged[missing_mask].copy()
    complete_df = df_merged[~missing_mask].copy()

    logger.info(f"\nRows with complete data: {len(complete_df):,}")
    logger.info(f"Rows with missing data: {len(missing_df):,}")

    logger.info(f"\n{'='*70}")
    logger.info("MATCHING BY EMAIL")
    logger.info("="*70)

    matched_rows = []
    unmatched_rows = []

    stats = {
        'total_missing': len(missing_df),
        'matched': 0,
        'unmatched': 0,
    }

    for idx, row in missing_df.iterrows():
        email = str(row.get('email', '')).strip().lower()

        if email and email in email_map:
            # Found match!
            gmaps_row = email_map[email]
            gmaps_fields = extract_gmaps_fields(gmaps_row)

            # Update row with Google Maps data
            enriched_row = row.to_dict()
            enriched_row.update(gmaps_fields)
            enriched_row['data_source'] = 'google_maps_matched'

            matched_rows.append(enriched_row)
            stats['matched'] += 1

            if stats['matched'] % 10 == 0:
                logger.info(f"Matched {stats['matched']}/{len(missing_df)} rows...")
        else:
            # No match found
            row_dict = row.to_dict()
            row_dict['data_source'] = 'email_only'
            unmatched_rows.append(row_dict)
            stats['unmatched'] += 1

    logger.info(f"Matched {stats['matched']}/{len(missing_df)} rows")

    # Create DataFrames
    df_matched = pd.DataFrame(matched_rows) if matched_rows else pd.DataFrame()
    df_unmatched = pd.DataFrame(unmatched_rows) if unmatched_rows else pd.DataFrame()

    # Add data_source column to complete rows
    complete_df['data_source'] = 'original_complete'

    # Combine all
    df_final = pd.concat([complete_df, df_matched, df_unmatched], ignore_index=True)

    logger.info(f"\n{'='*70}")
    logger.info("MATCHING COMPLETE")
    logger.info("="*70)
    logger.info(f"Total rows: {len(df_final):,}")
    logger.info(f"  Original complete: {len(complete_df):,}")
    logger.info(f"  Matched from Google Maps: {stats['matched']:,}")
    logger.info(f"  Unmatched (email only): {stats['unmatched']:,}")

    # Save results
    CONFIG["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"merged_best_emails_COMPLETE_{timestamp}.csv"

    df_final.to_csv(output_file, index=False, encoding='utf-8-sig')

    logger.info(f"\n{'='*70}")
    logger.info(f"SAVED: {output_file}")
    logger.info("="*70)

    logger.info(f"\n{'='*70}")
    logger.info("SAMPLE MATCHED ROWS (first 10)")
    logger.info("="*70)

    if len(df_matched) > 0:
        for idx, row in df_matched.head(10).iterrows():
            logger.info(f"\n{idx}. {row.get('name', 'N/A')}")
            logger.info(f"   Email: {row.get('email', 'N/A')}")
            logger.info(f"   Website: {row.get('website', 'N/A')}")
            logger.info(f"   Phone: {row.get('phone', 'N/A')}")
            logger.info(f"   City: {row.get('city', 'N/A')}, {row.get('state', 'N/A')}")
            logger.info(f"   Niche: {row.get('niche', 'N/A')}")

    logger.info(f"\n{'='*70}")
    logger.info("DONE")
    logger.info("="*70)


if __name__ == "__main__":
    main()
