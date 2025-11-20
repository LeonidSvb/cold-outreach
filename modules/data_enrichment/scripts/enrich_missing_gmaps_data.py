#!/usr/bin/env python3
"""
=== ENRICH MISSING GOOGLE MAPS DATA ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Enrich rows that have email but missing Google Maps data (website, rating, reviews, etc.)

FEATURES:
- Extract company name from email domain
- Generate website URL from domain
- Infer niche from email/domain
- Create placeholder data for missing fields

USAGE:
python enrich_missing_gmaps_data.py

INPUT:
merged_best_emails_20251120_150222.csv

OUTPUT:
merged_best_emails_ENRICHED_[timestamp].csv
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
    "INPUT_FILE": r"C:\Users\79818\Desktop\Outreach - new\merged_best_emails_20251120_150222.csv",
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
}

# Niche keywords for inference
NICHE_KEYWORDS = {
    'hvac': ['hvac', 'heat', 'air', 'cooling', 'ac', 'conditioning', 'furnace', 'climate'],
    'electricians': ['electric', 'electrical', 'electrician', 'elec', 'power', 'wiring'],
    'plumbers': ['plumb', 'plumbing', 'drain', 'pipe', 'water', 'sewer'],
    'locksmiths': ['lock', 'locksmith', 'key', 'security', 'safe'],
    'garage_door': ['garage', 'door', 'overhead'],
    'towing': ['tow', 'towing', 'wrecker', 'roadside'],
    'roofing': ['roof', 'roofing', 'shingle', 'gutter'],
    'carpet': ['carpet', 'flooring', 'rug', 'floor'],
}

# ============================================================================
# ENRICHMENT FUNCTIONS
# ============================================================================

def extract_company_name_from_domain(domain: str) -> str:
    """
    Extract company name from domain
    Example: airconditioningservicesofflagler.com -> Air Conditioning Services Of Flagler
    """
    if not domain or pd.isna(domain):
        return ""

    # Remove common TLDs
    name = domain.lower()
    for tld in ['.com', '.net', '.org', '.co', '.us', '.io', '.biz']:
        name = name.replace(tld, '')

    # Remove common prefixes
    for prefix in ['www.', 'http://', 'https://']:
        name = name.replace(prefix, '')

    # Split by common separators
    # Try to find word boundaries
    words = re.findall(r'[a-z]+', name)

    # Capitalize each word
    company_name = ' '.join(word.capitalize() for word in words if len(word) > 1)

    return company_name if company_name else domain


def infer_niche_from_text(text: str) -> str:
    """
    Infer business niche from email/domain text
    """
    if not text or pd.isna(text):
        return 'unknown'

    text_lower = str(text).lower()

    # Check each niche
    for niche, keywords in NICHE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return niche

    return 'unknown'


def generate_website_from_domain(domain: str) -> str:
    """
    Generate website URL from domain
    """
    if not domain or pd.isna(domain):
        return ""

    # If already looks like URL, return as is
    if domain.startswith('http'):
        return domain

    # Otherwise, add https://
    return f"https://{domain}"


def extract_phone_from_email(email: str) -> str:
    """
    Try to extract phone from email (some emails have embedded phone numbers)
    Example: us407.618.9029info@ngenservices.com -> (407) 618-9029
    """
    if not email or pd.isna(email):
        return ""

    # Pattern: digits in email
    phone_match = re.search(r'(\d{3})\.?(\d{3})\.?(\d{4})', email)
    if phone_match:
        area, prefix, line = phone_match.groups()
        return f"({area}) {prefix}-{line}"

    return ""


def enrich_missing_row(row: dict) -> dict:
    """
    Enrich a row that has email but missing Google Maps data
    """
    email = row.get('email', '')

    if not email or pd.isna(email):
        return row

    # Extract domain
    if '@' in str(email):
        username, domain = email.split('@', 1)
    else:
        return row

    # Skip free email providers
    if domain.lower() in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']:
        # For free emails, try to extract name from username
        company_name = extract_company_name_from_domain(username)
        website = ""
        niche = infer_niche_from_text(username)
    else:
        # Business domain
        company_name = extract_company_name_from_domain(domain)
        website = generate_website_from_domain(domain)
        niche = infer_niche_from_text(domain)

    # Try to extract phone from email
    phone = extract_phone_from_email(email)

    # Update row
    if not row.get('name') or pd.isna(row.get('name')):
        row['name'] = company_name

    if not row.get('website') or pd.isna(row.get('website')):
        row['website'] = website

    if not row.get('niche') or pd.isna(row.get('niche')):
        row['niche'] = niche

    if not row.get('phone') or pd.isna(row.get('phone')):
        row['phone'] = phone

    # Add note that this was enriched
    row['enrichment_status'] = 'enriched_from_email'

    return row


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def main():
    """Main enrichment function"""

    logger.info("="*70)
    logger.info("ENRICH MISSING GOOGLE MAPS DATA")
    logger.info("="*70)

    # Read input file
    input_file = Path(CONFIG["INPUT_FILE"])
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return

    logger.info(f"\nReading: {input_file.name}")
    df = pd.read_csv(input_file, encoding='utf-8-sig')

    logger.info(f"Total rows: {len(df):,}")

    # Add enrichment_status column (default: 'original')
    df['enrichment_status'] = 'original'

    # Identify rows with missing data
    missing_mask = df['website'].isna()
    missing_df = df[missing_mask].copy()
    complete_df = df[~missing_mask].copy()

    logger.info(f"\nRows with complete Google Maps data: {len(complete_df):,}")
    logger.info(f"Rows with missing data: {len(missing_df):,}")

    if len(missing_df) == 0:
        logger.info("\nNo missing data found. Nothing to enrich.")
        return

    logger.info(f"\n{'='*70}")
    logger.info("ENRICHING MISSING ROWS")
    logger.info("="*70)

    enriched_rows = []
    stats = {
        'total_missing': len(missing_df),
        'enriched': 0,
        'could_not_enrich': 0,
        'niches_inferred': {},
    }

    for idx, row in missing_df.iterrows():
        enriched_row = enrich_missing_row(row.to_dict())

        # Check if enrichment was successful
        if enriched_row.get('name') and enriched_row.get('name') != 'nan':
            stats['enriched'] += 1

            # Track niche
            niche = enriched_row.get('niche', 'unknown')
            stats['niches_inferred'][niche] = stats['niches_inferred'].get(niche, 0) + 1
        else:
            stats['could_not_enrich'] += 1

        enriched_rows.append(enriched_row)

        if (stats['enriched'] + stats['could_not_enrich']) % 10 == 0:
            logger.info(f"Processed {stats['enriched'] + stats['could_not_enrich']}/{len(missing_df)} rows...")

    logger.info(f"Processed {len(missing_df)} rows")

    # Create enriched DataFrame
    df_enriched_missing = pd.DataFrame(enriched_rows)

    # Combine with complete rows
    df_final = pd.concat([complete_df, df_enriched_missing], ignore_index=True)

    logger.info(f"\n{'='*70}")
    logger.info("ENRICHMENT COMPLETE")
    logger.info("="*70)
    logger.info(f"Total missing rows: {stats['total_missing']:,}")
    logger.info(f"Successfully enriched: {stats['enriched']:,}")
    logger.info(f"Could not enrich: {stats['could_not_enrich']:,}")

    logger.info(f"\nNiches inferred:")
    for niche, count in sorted(stats['niches_inferred'].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {niche}: {count}")

    # Save results
    CONFIG["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"merged_best_emails_ENRICHED_{timestamp}.csv"

    df_final.to_csv(output_file, index=False, encoding='utf-8-sig')

    logger.info(f"\n{'='*70}")
    logger.info(f"SAVED: {output_file}")
    logger.info("="*70)
    logger.info(f"Total rows: {len(df_final):,}")
    logger.info(f"  Original complete: {len(complete_df):,}")
    logger.info(f"  Enriched from email: {stats['enriched']:,}")
    logger.info(f"  Could not enrich: {stats['could_not_enrich']:,}")

    logger.info(f"\n{'='*70}")
    logger.info("SAMPLE ENRICHED ROWS (first 5)")
    logger.info("="*70)
    enriched_sample = df_final[df_final['enrichment_status'] == 'enriched_from_email'].head(5)
    for idx, row in enriched_sample.iterrows():
        logger.info(f"\nRow {idx}:")
        logger.info(f"  Email: {row['email']}")
        logger.info(f"  Name: {row['name']}")
        logger.info(f"  Website: {row['website']}")
        logger.info(f"  Niche: {row['niche']}")
        if row.get('phone'):
            logger.info(f"  Phone: {row['phone']}")

    logger.info(f"\n{'='*70}")
    logger.info("DONE")
    logger.info("="*70)


if __name__ == "__main__":
    main()
