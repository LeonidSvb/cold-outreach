#!/usr/bin/env python3
"""
=== Apollo Call Centers CSV Processor ===
Version: 1.0.0 | Created: 2025-11-03

PURPOSE:
Process Apollo scraped call center data:
- Normalize company names (remove Inc., LLC, make casual)
- Normalize locations (NY, SF, etc.)
- Score ICP match for call analytics service

USAGE:
python process_call_centers.py
"""

import sys
import pandas as pd
import re
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv",
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
}

# Location normalization mapping
LOCATION_NORMALIZATIONS = {
    # US Cities
    "New York": "NYC",
    "New York City": "NYC",
    "San Francisco": "SF",
    "Los Angeles": "LA",
    "Las Vegas": "Vegas",
    "Washington": "DC",
    "Philadelphia": "Philly",
    # US States (keep short ones as-is, abbreviate long ones)
    "California": "CA",
    "Florida": "FL",
    "Illinois": "IL",
    "Pennsylvania": "PA",
    "Massachusetts": "MA",
    # Countries
    "United States": "US",
    "United Kingdom": "UK",
    "Australia": "AUS",
}

def normalize_company_name(company_name):
    """
    Normalize company name to casual short form.
    Remove: Inc., LLC, Ltd., Corporation, Corp., Co., etc.
    """
    if pd.isna(company_name):
        return ""

    name = str(company_name)

    # Remove common legal suffixes
    suffixes = [
        r',?\s+Inc\.?$',
        r',?\s+LLC\.?$',
        r',?\s+Ltd\.?$',
        r',?\s+Limited$',
        r',?\s+Corporation$',
        r',?\s+Corp\.?$',
        r',?\s+Co\.?$',
        r',?\s+Company$',
        r',?\s+Group$',
        r',?\s+International$',
        r',?\s+Incorporated$',
        r',?\s+L\.L\.C\.?$',
        r',?\s+PLC$',
        r',?\s+Pty\.?\s+Ltd\.?$',
    ]

    for suffix in suffixes:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)

    # Remove extra whitespace
    name = ' '.join(name.split())

    # If name is too long, try to abbreviate
    if len(name) > 30:
        # Keep first word if it's the main brand
        parts = name.split()
        if len(parts) > 1 and len(parts[0]) >= 3:
            name = parts[0]

    return name.strip()

def normalize_location(location):
    """
    Normalize location to casual short form.
    NY, SF, San Fran, etc.
    """
    if pd.isna(location):
        return ""

    loc = str(location).strip()

    # Check mapping first
    for full_name, abbrev in LOCATION_NORMALIZATIONS.items():
        if full_name.lower() in loc.lower():
            return abbrev

    # If already short (<=5 chars), keep as-is
    if len(loc) <= 5:
        return loc

    # Try to extract state abbreviation if present (e.g., "Austin, TX")
    match = re.search(r',\s*([A-Z]{2})$', loc)
    if match:
        return match.group(1)

    # Keep as-is if can't normalize
    return loc

def score_icp_match(row):
    """
    Score ICP match based on company data.
    2 = perfect match (call center with high call volume)
    1 = maybe (related industry or unclear)
    0 = not a match
    """
    company_name = str(row.get('company_name', '')).lower()
    title = str(row.get('title', '')).lower()
    keywords = str(row.get('keywords', '')).lower()
    industry = str(row.get('industry', '')).lower()
    headline = str(row.get('headline', '')).lower()

    # Combine all text for analysis
    combined_text = f"{company_name} {title} {keywords} {industry} {headline}"

    # Perfect match indicators (score 2)
    perfect_indicators = [
        'call center',
        'contact center',
        'customer service center',
        'telemarketing',
        'outbound call',
        'inbound call',
        'bpo',  # Business Process Outsourcing
        'call centre',
        'telefundraising',
        'outbound sales',
        'inside sales team',
        'telesales',
        'phone sales',
        'call operations',
        'dialer',
        'predictive dialing',
    ]

    # Good indicators (score 1)
    good_indicators = [
        'customer support',
        'customer service',
        'customer experience',
        'sales calls',
        'phone support',
        'technical support',
        'help desk',
        'customer success',
        'lead generation',
        'appointment setting',
        'cold calling',
        'outsourcing',
        'offshoring',
        'telecommunications',
    ]

    # Perfect match - industry based
    perfect_industries = [
        'outsourcing/offshoring',
        'call center',
        'contact center',
    ]

    # Check industry first
    for perfect_ind in perfect_industries:
        if perfect_ind in industry:
            return 2

    # Check for perfect match in keywords/title/name
    for indicator in perfect_indicators:
        if indicator in combined_text:
            return 2

    # Check for good match
    for indicator in good_indicators:
        if indicator in combined_text:
            return 1

    # Default: not a clear match
    return 0

def get_relevant_columns(df):
    """
    Identify and keep only relevant columns.
    """
    # Common Apollo columns we want to keep
    keep_patterns = [
        'first name',
        'last name',
        'name',
        'title',
        'email',
        'phone',
        'mobile',
        'organization',
        'company',
        'website',
        'linkedin',
        'city',
        'state',
        'country',
        'industry',
        'employees',
        'revenue',
        'keywords',
        'headline',
    ]

    columns_to_keep = []
    for col in df.columns:
        col_lower = col.lower()
        if any(pattern in col_lower for pattern in keep_patterns):
            columns_to_keep.append(col)

    return columns_to_keep

def main():
    logger.info("Starting call center CSV processing")

    try:
        # Read CSV
        logger.info("Reading input CSV", file=CONFIG["INPUT_FILE"])
        df = pd.read_csv(CONFIG["INPUT_FILE"])
        logger.info("CSV loaded", rows=len(df), columns=len(df.columns))

        # Show column names
        logger.info("Available columns", columns=list(df.columns))

        # Keep only relevant columns
        relevant_cols = get_relevant_columns(df)
        logger.info("Keeping relevant columns", count=len(relevant_cols))
        df_clean = df[relevant_cols].copy()

        # Add normalized columns
        logger.info("Normalizing company names")
        df_clean['Normalized Company Name'] = df.apply(
            lambda row: normalize_company_name(row.get('company_name', '')),
            axis=1
        )

        logger.info("Normalizing locations")
        # Try to find location column (could be City, State, Country, or Location)
        location_col = None
        for col in df.columns:
            if any(x in col.lower() for x in ['city', 'location', 'state']):
                location_col = col
                break

        if location_col:
            df_clean['Normalized Location'] = df[location_col].apply(normalize_location)
        else:
            df_clean['Normalized Location'] = ""
            logger.warning("No location column found")

        logger.info("Scoring ICP matches")
        df_clean['ICP Match Score'] = df.apply(score_icp_match, axis=1)

        # Sort by ICP score (best matches first)
        df_clean = df_clean.sort_values('ICP Match Score', ascending=False)

        # Save result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = CONFIG["OUTPUT_DIR"] / f"call_centers_processed_{timestamp}.csv"
        CONFIG["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)

        df_clean.to_csv(output_file, index=False)
        logger.info("Processed CSV saved", file=str(output_file))

        # Show statistics
        score_counts = df_clean['ICP Match Score'].value_counts().to_dict()
        logger.info("ICP Score distribution",
                   perfect=score_counts.get(2, 0),
                   maybe=score_counts.get(1, 0),
                   no_match=score_counts.get(0, 0))

        # Show sample of best matches
        logger.info("Sample of top matches (ICP Score = 2)")
        top_matches = df_clean[df_clean['ICP Match Score'] == 2].head(10)
        for idx, row in top_matches.iterrows():
            logger.info("Top match",
                       company=row.get('Normalized Company Name', ''),
                       location=row.get('Normalized Location', ''),
                       original=row.get('company_name', ''))

        return output_file

    except Exception as e:
        logger.error("Processing failed", error=str(e))
        raise

if __name__ == "__main__":
    output = main()
    print(f"\nProcessed file saved to: {output}")
