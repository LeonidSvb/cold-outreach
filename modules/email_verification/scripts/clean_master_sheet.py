#!/usr/bin/env python3
"""
=== MASTER SHEET CLEANER ===
Version: 1.0.0 | Created: 2025-11-20

PURPOSE:
Clean Master Sheet CSV from duplicates and email format issues

FEATURES:
- Remove duplicate emails
- Clean concatenated text after domains
- Split multiple emails into separate rows
- Remove URL encoding and special characters
- Validate email format

USAGE:
1. Configure INPUT_FILE path
2. Run: python clean_master_sheet.py
3. Review cleaned file in results/

IMPROVEMENTS:
v1.0.0 - Initial version
"""

import sys
import re
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add project root to path
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
    "INPUT_FILE": r"C:\Users\79818\Downloads\Master Sheet - test (4).csv",
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
}

# Email cleanup patterns (enhanced with aggressive cleaning)
CLEANUP_PATTERNS = [
    # URL encoding
    (r'^%20+', ''),
    (r'%20', ''),

    # Phone numbers and numbers before email (AGGRESSIVE)
    # Match any sequence of digits, dots, dashes, parentheses before email
    (r'^[\d\.\-\(\)\s]+(?=[a-z]+@)', ''),

    # Zip codes with text before email (e.g., "34110phoneemailinfo@" -> "info@")
    (r'^\d{5}[a-z]*email[a-z]*', ''),
    (r'^\d{5}[a-z]*phone[a-z]*', ''),
    (r'^\d{5}[a-z]+', ''),

    # Any numbers before @ with letters
    (r'^\d+[a-z]+(?=@)', ''),
    (r'^\d+(?=[a-z]*@)', ''),

    # Phone/contact in middle (e.g., "contact312.719.6721name@" -> "name@")
    (r'^[a-z]+[\d\.\-]+([a-z]+@)', r'\1'),

    # Specific concatenated patterns we found in data
    # Only match KNOWN problematic patterns to avoid false positives

    # Strategy: match .com/.net/etc + ANY garbage characters after it
    # Capture the TLD and remove everything after
    (r'(\.com)(?:[a-z]+.*?)$', r'\1'),
    (r'(\.net)(?:[a-z]+.*?)$', r'\1'),
    (r'(\.org)(?:[a-z]+.*?)$', r'\1'),
    (r'(\.edu)(?:[a-z]+.*?)$', r'\1'),
    (r'(\.gov)(?:[a-z]+.*?)$', r'\1'),
    (r'(\.biz)(?:[a-z]+.*?)$', r'\1'),
    (r'(\.info)(?:[a-z]+.*?)$', r'\1'),
    (r'(\.site)(?:[a-z]+.*?)$', r'\1'),
    (r'(\.email)(?:[a-z]+.*?)$', r'\1'),
    (r'(\.io)(?:[a-z]+.*?)$', r'\1'),

    # Single extra character after TLD (specific fixes)
    (r'(\.com)[a-z]$', r'\1'),
    (r'(\.net)[a-z]$', r'\1'),
    (r'(\.org)[a-z]$', r'\1'),

    # Concatenated domains (specific patterns from data)
    (r'@(.+?)\.(huhorizon)$', r'@\1.hu'),
    (r'@(.+?)\.(chder)$', r'@\1.ch'),
    (r'@(.+?)\.(ukregistered)$', r'@\1.uk'),
    (r'@(.+?)\.(nliban)$', r'@\1.nl'),
    (r'@(.+?)\.(chhorizon)$', r'@\1.ch'),
    (r'@(.+?)\.(dehorizon)$', r'@\1.de'),

    # Remove-this pattern
    (r'@remove-this\.', r'@'),
    (r'@remove\.', r'@'),

    # Phone numbers (remove them)
    (r'\(\d{3}\)\s*\d{3}-\d{4}', ''),
    (r'\d{3}-\d{3}-\d{4}', ''),
    (r'\d{3}-\d{4}', ''),

    # Text before @ (only clear garbage patterns)
    (r'^email(?=[a-z]+@)', ''),  # "emailinfo@" -> "info@" but keep if just "email@"
]

# ============================================================================
# EMAIL CLEANING FUNCTIONS
# ============================================================================

def clean_email(email: str) -> str:
    """Clean single email address"""
    if not email or pd.isna(email):
        return ""

    cleaned = str(email).strip()

    # Apply cleanup patterns
    for pattern, replacement in CLEANUP_PATTERNS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    cleaned = cleaned.strip().lower()

    # Basic validation
    if '@' not in cleaned or '.' not in cleaned.split('@')[-1]:
        return ""

    # Remove trailing/leading special chars
    cleaned = cleaned.strip('.,;:() ')

    # Final validation: basic email format
    if not re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', cleaned):
        return ""

    return cleaned


def split_multi_emails(email_str: str) -> list:
    """Split comma/semicolon-separated emails"""
    if not email_str or pd.isna(email_str):
        return []

    # Split by comma or semicolon
    emails = re.split(r'[,;]\s*', str(email_str))

    # Clean each
    cleaned_emails = []
    for email in emails:
        cleaned = clean_email(email)
        if cleaned and '@' in cleaned and len(cleaned) > 5:
            cleaned_emails.append(cleaned)

    return cleaned_emails

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def main():
    """Main processing function"""

    logger.info("="*70)
    logger.info("MASTER SHEET CLEANER")
    logger.info("="*70)

    # Read input file
    input_file = Path(CONFIG["INPUT_FILE"])
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return

    logger.info(f"\nReading: {input_file.name}")
    df = pd.read_csv(input_file, encoding='utf-8')

    logger.info(f"Total rows: {len(df):,}")

    # Initial statistics
    email_col = 'email'
    if email_col not in df.columns:
        logger.error(f"Email column not found in CSV")
        return

    initial_stats = {
        'total_rows': len(df),
        'empty_emails': df[email_col].isna().sum(),
        'duplicates': df[email_col].duplicated().sum(),
        'unique_emails': df[email_col].nunique()
    }

    logger.info(f"\nINITIAL STATS:")
    logger.info(f"  Total rows: {initial_stats['total_rows']:,}")
    logger.info(f"  Empty emails: {initial_stats['empty_emails']:,}")
    logger.info(f"  Duplicate rows: {initial_stats['duplicates']:,}")
    logger.info(f"  Unique emails: {initial_stats['unique_emails']:,}")

    # Process each row
    logger.info(f"\n{'='*70}")
    logger.info("PROCESSING: Cleaning and splitting emails...")
    logger.info("="*70)

    expanded_rows = []
    stats = {
        'original_rows': len(df),
        'rows_with_no_email': 0,
        'rows_with_single_email': 0,
        'rows_with_multi_email': 0,
        'total_emails_extracted': 0,
        'emails_cleaned': 0,
    }

    for idx, row in df.iterrows():
        if (idx + 1) % 500 == 0:
            logger.info(f"Processed {idx + 1:,}/{len(df):,} rows...")

        email_str = row[email_col]
        emails = split_multi_emails(email_str)

        # Track if email was cleaned
        original_email = str(email_str).strip().lower() if not pd.isna(email_str) else ""

        if not emails:
            # No valid email - skip row
            stats['rows_with_no_email'] += 1
        elif len(emails) == 1:
            # Single email
            row_copy = row.copy()
            row_copy[email_col] = emails[0]
            expanded_rows.append(row_copy)
            stats['rows_with_single_email'] += 1
            stats['total_emails_extracted'] += 1

            # Check if cleaned
            if emails[0] != original_email:
                stats['emails_cleaned'] += 1
        else:
            # Multiple emails - create one row per email
            for email in emails:
                row_copy = row.copy()
                row_copy[email_col] = email
                expanded_rows.append(row_copy)
            stats['rows_with_multi_email'] += 1
            stats['total_emails_extracted'] += len(emails)
            stats['emails_cleaned'] += 1  # Multi-email rows were definitely cleaned

    logger.info(f"Processed {len(df):,} rows")

    # Create DataFrame
    df_cleaned = pd.DataFrame(expanded_rows)

    logger.info(f"\n{'='*70}")
    logger.info("REMOVING DUPLICATES")
    logger.info("="*70)

    before_dedup = len(df_cleaned)
    df_cleaned = df_cleaned.drop_duplicates(subset=[email_col], keep='first')
    after_dedup = len(df_cleaned)
    duplicates_removed = before_dedup - after_dedup

    logger.info(f"Before deduplication: {before_dedup:,}")
    logger.info(f"After deduplication: {after_dedup:,}")
    logger.info(f"Duplicates removed: {duplicates_removed:,}")

    # Final statistics
    logger.info(f"\n{'='*70}")
    logger.info("CLEANING COMPLETE")
    logger.info("="*70)
    logger.info(f"Original rows: {stats['original_rows']:,}")
    logger.info(f"  No valid email: {stats['rows_with_no_email']:,}")
    logger.info(f"  Single email: {stats['rows_with_single_email']:,}")
    logger.info(f"  Multi-email (split): {stats['rows_with_multi_email']:,}")
    logger.info(f"\nAfter cleaning and splitting: {before_dedup:,}")
    logger.info(f"After deduplication: {after_dedup:,}")
    logger.info(f"Emails cleaned/fixed: {stats['emails_cleaned']:,}")
    logger.info(f"\nNet change: {after_dedup - stats['original_rows']:+,} rows")
    logger.info(f"Duplicate reduction: {duplicates_removed:,} rows")

    # Save results
    CONFIG["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"master_sheet_CLEANED_{timestamp}.csv"

    df_cleaned.to_csv(output_file, index=False, encoding='utf-8-sig')

    logger.info(f"\n{'='*70}")
    logger.info(f"SAVED: {output_file}")
    logger.info("="*70)

    # Show examples of cleaned emails
    logger.info(f"\nSample cleaned emails (first 10):")
    for i, email in enumerate(df_cleaned[email_col].head(10), 1):
        logger.info(f"  {i}. {email}")

    logger.info(f"\n{'='*70}")
    logger.info("DONE")
    logger.info("="*70)


if __name__ == "__main__":
    main()
