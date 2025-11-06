#!/usr/bin/env python3
"""
=== APOLLO ICP VALIDATOR & DATA NORMALIZER ===
Version: 1.0.0 | Created: 2025-11-03

PURPOSE:
Validates Apollo-scraped call center data against ICP criteria and normalizes company/location names

FEATURES:
- ICP scoring (0-2 scale) based on call center fit
- Company name casualization (remove LLC, Inc., etc.)
- Location abbreviation (NYC, LA, SF, UK, Aus)
- Data cleaning and CSV restructuring
- Detailed statistics and filtering report

USAGE:
1. Configure INPUT_FILE and OUTPUT_DIR in CONFIG
2. Run: python apollo_icp_validator.py
3. Results saved to data/processed/ with timestamp

IMPROVEMENTS:
v1.0.0 - Initial version with ICP validation and normalization
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import re

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import pandas as pd
except ImportError:
    print("Installing pandas...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

# Simple logging fallback
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CONFIG = {
    "INPUT_FILE": r"C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv",
    "OUTPUT_DIR": Path(__file__).parent.parent.parent / "data" / "processed",
    "ICP_CRITERIA": {
        "min_employees": 10,
        "max_employees": 100,
        "target_countries": ["United States", "United Kingdom", "Australia"],
        "call_center_keywords": [
            "call center", "call centre", "contact center", "contact centre",
            "customer service", "customer support", "bpo", "business process",
            "telemarketing", "telesales", "outbound", "inbound",
            "customer experience", "cx", "customer care", "help desk",
            "support services", "answering service", "outsourcing"
        ]
    }
}


def normalize_company_name(name: str) -> str:
    """
    Casualize company name for icebreakers
    Remove: LLC, Inc., Incorporated, Ltd., Corporation, Corp., Co., etc.
    """
    if not name or pd.isna(name):
        return ""

    # Remove common suffixes
    suffixes = [
        r'\s+LLC$', r'\s+L\.L\.C\.$', r'\s+Inc\.$', r'\s+Inc$',
        r'\s+Incorporated$', r'\s+Ltd\.$', r'\s+Ltd$', r'\s+Limited$',
        r'\s+Corporation$', r'\s+Corp\.$', r'\s+Corp$',
        r'\s+Co\.$', r'\s+Co$', r'\s+Company$',
        r'\s+PLC$', r'\s+Pty$', r'\s+Pty\.$',
        r',\s+LLC$', r',\s+Inc\.$', r',\s+Ltd\.$'
    ]

    casual_name = name.strip()
    for suffix in suffixes:
        casual_name = re.sub(suffix, '', casual_name, flags=re.IGNORECASE)

    # Remove trailing commas and extra spaces
    casual_name = casual_name.rstrip(',').strip()

    return casual_name


def normalize_location(city: str, state: str, country: str) -> str:
    """
    Casualize location for icebreakers
    Examples: New York -> NYC, San Francisco -> SF, United Kingdom -> UK
    """
    # Handle missing data
    if pd.isna(city) and pd.isna(state) and pd.isna(country):
        return ""

    city = str(city) if not pd.isna(city) else ""
    state = str(state) if not pd.isna(state) else ""
    country = str(country) if not pd.isna(country) else ""

    # Common abbreviations
    location_map = {
        # US Cities
        "New York": "NYC",
        "New York City": "NYC",
        "San Francisco": "SF",
        "Los Angeles": "LA",
        "Las Vegas": "Vegas",
        "Washington": "DC",
        "Washington, D.C.": "DC",
        # Countries
        "United States": "US",
        "United Kingdom": "UK",
        "Australia": "Aus",
        # US States (if city is missing)
        "California": "CA",
        "Texas": "TX",
        "Florida": "FL",
        "New York": "NY"
    }

    # Prioritize city, then state, then country
    if city:
        location = location_map.get(city, city)
    elif state:
        location = location_map.get(state, state)
    elif country:
        location = location_map.get(country, country)
    else:
        location = ""

    return location


def calculate_icp_score(row: pd.Series, config: dict) -> int:
    """
    Calculate ICP score (0-2) based on call center fit
    2 = perfect fit, 1 = maybe, 0 = not a fit
    """
    score = 0

    # Check employee count
    num_employees = row.get('estimated_num_employees', 0)
    if pd.isna(num_employees):
        num_employees = 0

    try:
        num_employees = int(num_employees)
    except (ValueError, TypeError):
        num_employees = 0

    if num_employees < config["ICP_CRITERIA"]["min_employees"]:
        return 0  # Too small

    if num_employees > config["ICP_CRITERIA"]["max_employees"]:
        score = 1  # Larger than ideal, but could be a fit
    else:
        score = 2  # Perfect size range

    # Check call center keywords in company name, headline, title, industry
    keywords = config["ICP_CRITERIA"]["call_center_keywords"]
    text_fields = [
        str(row.get('company_name', '')),
        str(row.get('headline', '')),
        str(row.get('title', '')),
        str(row.get('industry', '')),
        str(row.get('secondary_industries', '')),
        str(row.get('industries', ''))
    ]

    combined_text = ' '.join(text_fields).lower()
    keyword_matches = [kw for kw in keywords if kw in combined_text]

    if not keyword_matches:
        # No clear call center indicators
        if score == 2:
            score = 1  # Downgrade to maybe

    return score


def process_apollo_data(config: dict):
    """Main processing function"""
    logger.info("Starting Apollo ICP validation and normalization")

    # Read CSV
    input_file = config["INPUT_FILE"]
    logger.info(f"Reading CSV from: {input_file}")

    try:
        df = pd.read_csv(input_file, encoding='utf-8')
    except UnicodeDecodeError:
        logger.warning("UTF-8 failed, trying latin1 encoding")
        df = pd.read_csv(input_file, encoding='latin1')

    total_rows = len(df)
    logger.info(f"Total rows loaded: {total_rows}")

    # Calculate ICP scores
    logger.info("Calculating ICP scores...")
    df['icp_score'] = df.apply(lambda row: calculate_icp_score(row, config), axis=1)

    # Normalize company names and locations
    logger.info("Normalizing company names and locations...")
    df['normalized_company_name'] = df['company_name'].apply(normalize_company_name)
    df['normalized_location'] = df.apply(
        lambda row: normalize_location(row.get('city'), row.get('state'), row.get('country')),
        axis=1
    )

    # Statistics
    icp_distribution = df['icp_score'].value_counts().sort_index()
    logger.info("ICP Score Distribution:")
    for score, count in icp_distribution.items():
        percentage = (count / total_rows) * 100
        logger.info(f"  Score {score}: {count} companies ({percentage:.1f}%)")

    perfect_fit = len(df[df['icp_score'] == 2])
    maybe_fit = len(df[df['icp_score'] == 1])
    no_fit = len(df[df['icp_score'] == 0])

    # Clean and restructure dataset
    logger.info("Cleaning and restructuring dataset...")

    # Keep essential columns
    essential_columns = [
        'first_name', 'last_name', 'email', 'title', 'headline',
        'normalized_company_name', 'company_name', 'company_domain',
        'company_linkedin_url', 'linkedin_url',
        'normalized_location', 'city', 'state', 'country',
        'estimated_num_employees', 'phone_number', 'sanitized_phone_number',
        'seniority', 'industry', 'icp_score'
    ]

    # Filter columns that exist in dataframe
    available_columns = [col for col in essential_columns if col in df.columns]
    df_clean = df[available_columns].copy()

    # Save to output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = config["OUTPUT_DIR"] / f"apollo_call_centers_processed_{timestamp}.csv"
    config["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)

    df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
    logger.info(f"Processed data saved to: {output_file}")

    # Detailed report
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print(f"Total rows processed: {total_rows}")
    print(f"")
    print(f"ICP VALIDATION RESULTS:")
    print(f"  Perfect fit (score 2): {perfect_fit} companies ({(perfect_fit/total_rows)*100:.1f}%)")
    print(f"  Maybe fit (score 1): {maybe_fit} companies ({(maybe_fit/total_rows)*100:.1f}%)")
    print(f"  Not a fit (score 0): {no_fit} companies ({(no_fit/total_rows)*100:.1f}%)")
    print(f"")
    print(f"DATA NORMALIZATION:")
    print(f"  Company names casualized: {len(df_clean)} records")
    print(f"  Locations abbreviated: {len(df_clean[df_clean['normalized_location'] != ''])} records")
    print("=" * 60)

    # Sample normalized data
    print("\nSAMPLE NORMALIZED DATA (first 5 perfect fits):")
    perfect_samples = df_clean[df_clean['icp_score'] == 2].head(5)
    for idx, row in perfect_samples.iterrows():
        print(f"  {row['normalized_company_name']} ({row['normalized_location']}) - {row['title']}")

    return {
        "output_file": str(output_file),
        "total_rows": total_rows,
        "perfect_fit": perfect_fit,
        "maybe_fit": maybe_fit,
        "no_fit": no_fit,
        "icp_distribution": icp_distribution.to_dict()
    }


def main():
    """Entry point"""
    logger.info("Apollo ICP Validator started")

    try:
        results = process_apollo_data(CONFIG)
        logger.info("Processing completed successfully")
        return results

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
