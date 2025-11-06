#!/usr/bin/env python3
"""
=== ICEBREAKER GENERATOR ===
Version: 1.0.0 | Created: 2025-11-03

PURPOSE:
Generate personalized icebreaker messages for Apollo CSV leads

FEATURES:
- Company vs person detection
- Smart name/company/region normalization
- Random variation for natural messages
- Context-aware specialization phrases

USAGE:
1. Configure CSV_PATH in CONFIG
2. Run: python icebreaker_generator.py
3. Results saved to data/processed/
"""

import pandas as pd
import random
import re
from pathlib import Path
from datetime import datetime


class SimpleLogger:
    """Simple console logger"""
    @staticmethod
    def info(msg):
        print(f"[INFO] {msg}")

    @staticmethod
    def error(msg, exc_info=False):
        print(f"[ERROR] {msg}")


logger = SimpleLogger()

CONFIG = {
    "CSV_PATH": r"C:\Users\79818\Downloads\call centers US UK Aus 10-100 - 10-50.csv",
    "OUTPUT_DIR": Path(__file__).parent.parent.parent / "data" / "processed",
    "BATCH_SIZE": 200
}

# Opening variations
OPENINGS = [
    "love how you",
    "really like how you",
    "awesome to see you",
    "impressed by how you",
    "great track with how you",
    "cool to see you"
]

# Region phrase templates
REGION_PHRASES = [
    "I'm also in the {region} market",
    "I work across {region} as well",
    "I'm active in {region} too",
    "I also focus on {region}"
]

# Closing phrases
CLOSINGS = [
    "Wanted to run something by you.",
    "Thought I'd share an idea with you.",
    "Had something you might find interesting.",
    "Figured I'd reach out quickly."
]

# Company identifiers
COMPANY_KEYWORDS = [
    "Company", "Inc", "LLC", "Ltd", "Group", "Realty",
    "Properties", "Brokers", "UAE", "Dubai", "Abu Dhabi"
]

# Suffixes to remove from company names
COMPANY_SUFFIXES = [
    "Properties", "Realty", "Group", "Brokers", "LLC",
    "Ltd", "Inc", "UAE", "Dubai", "Abu Dhabi", "Limited",
    "Corporation", "Corp", "Co", "LLP", "PLC"
]

# Specialization keywords and actions
SPECIALIZATIONS = {
    "luxury": "drive luxury sales",
    "marketing": "lead marketing",
    "sales": "push sales",
    "engineering": "build products",
    "engineer": "build products",
    "talent": "grow teams",
    "product": "build products",
    "design": "shape design",
    "consultant": "work with clients",
    "consulting": "work with clients",
    "broker": "push sales",
    "analyst": "dig into insights",
    "executive": "lead strategy",
    "founder": "build companies",
    "ceo": "lead strategy",
    "cto": "drive tech",
    "cfo": "manage growth",
    "coo": "run operations",
    "director": "drive results",
    "manager": "lead teams",
    "specialist": "bring expertise",
    "coordinator": "organize growth"
}


def is_company(full_name: str) -> bool:
    """Check if full_name represents a company rather than a person"""
    if pd.isna(full_name):
        return False

    return any(keyword.lower() in full_name.lower() for keyword in COMPANY_KEYWORDS)


def normalize_company(company_name: str) -> str:
    """Normalize company name: Title Case + remove suffixes"""
    if pd.isna(company_name):
        return ""

    # Convert all-caps to Title Case
    if company_name.isupper():
        company_name = company_name.title()

    # Remove suffixes
    for suffix in COMPANY_SUFFIXES:
        # Remove with comma and space
        company_name = re.sub(rf',\s*{re.escape(suffix)}\b', '', company_name, flags=re.IGNORECASE)
        # Remove without comma
        company_name = re.sub(rf'\s+{re.escape(suffix)}\b', '', company_name, flags=re.IGNORECASE)

    # Remove apostrophes and special characters
    company_name = re.sub(r"['\"]", '', company_name)

    # Clean up extra spaces
    company_name = ' '.join(company_name.split())

    return company_name.strip()


def normalize_region(region: str) -> str:
    """Normalize region names to short forms"""
    if pd.isna(region):
        return ""

    region = region.strip()

    # Region mappings
    mappings = {
        "Dubai": "Dubai",
        "Abu Dhabi": "Dubai",
        "San Francisco": "SF",
        "New York City": "NYC",
        "New York": "NYC"
    }

    return mappings.get(region, region)


def extract_specialization(headline: str, title: str) -> str:
    """Extract specialization phrase from headline or title"""
    text = f"{headline} {title}".lower()

    # Check for specialization keywords
    for keyword, action in SPECIALIZATIONS.items():
        if keyword in text:
            return action

    # Default fallback
    return "bring industry experience"


def generate_icebreaker(row: dict) -> str:
    """Generate personalized icebreaker for a row"""
    full_name = row.get('full_name', '')

    # Check if company
    if is_company(full_name):
        return "its a company"

    # Extract first name
    first_name = full_name.split()[0] if full_name else "there"

    # Normalize company
    company_name = row.get('company_name', '')
    short_company = normalize_company(company_name)

    # Normalize region (city or state)
    city = row.get('city', '')
    state = row.get('state', '')
    short_region = normalize_region(city if city else state)

    # Extract specialization
    headline = row.get('headline', '')
    title = row.get('title', '')
    specialization_phrase = extract_specialization(headline, title)

    # Random selections
    opening = random.choice(OPENINGS)
    region_template = random.choice(REGION_PHRASES)
    closing = random.choice(CLOSINGS)

    # Build region phrase
    region_phrase = region_template.format(region=short_region) if short_region else "I'm also in the area"

    # Build final icebreaker
    icebreaker = f"Hey {first_name}, {opening} {specialization_phrase} at {short_company} - {region_phrase}. {closing}"

    return icebreaker


def process_batch(df_batch: pd.DataFrame, batch_num: int, total_batches: int) -> pd.DataFrame:
    """Process a batch of rows"""
    logger.info(f"Processing batch {batch_num}/{total_batches} ({len(df_batch)} rows)")

    # Generate icebreakers
    df_batch['icebreaker'] = df_batch.apply(
        lambda row: generate_icebreaker(row.to_dict()),
        axis=1
    )

    # Count companies vs persons
    companies = (df_batch['icebreaker'] == "its a company").sum()
    persons = len(df_batch) - companies

    logger.info(f"Batch {batch_num} complete: {persons} persons, {companies} companies")

    return df_batch


def main():
    logger.info("=== ICEBREAKER GENERATOR START ===")

    try:
        # Read CSV
        csv_path = Path(CONFIG["CSV_PATH"])
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        logger.info(f"Reading CSV: {csv_path}")
        df = pd.read_csv(csv_path)

        total_rows = len(df)
        logger.info(f"Total rows: {total_rows}")

        # Calculate batches
        batch_size = CONFIG["BATCH_SIZE"]
        total_batches = (total_rows + batch_size - 1) // batch_size
        logger.info(f"Processing in {total_batches} batches of {batch_size}")

        # Process in batches
        results = []
        for i in range(total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, total_rows)

            batch = df.iloc[start_idx:end_idx].copy()
            processed_batch = process_batch(batch, i + 1, total_batches)
            results.append(processed_batch)

        # Combine all batches
        logger.info("Merging all batches...")
        df_final = pd.concat(results, ignore_index=True)

        # Statistics
        total_companies = (df_final['icebreaker'] == "its a company").sum()
        total_persons = len(df_final) - total_companies

        logger.info("=== FINAL STATISTICS ===")
        logger.info(f"Total processed: {len(df_final)}")
        logger.info(f"Persons: {total_persons}")
        logger.info(f"Companies: {total_companies}")

        # Sample icebreakers (persons only)
        logger.info("=== SAMPLE ICEBREAKERS ===")
        samples = df_final[df_final['icebreaker'] != "its a company"]['icebreaker'].head(10)
        for idx, sample in enumerate(samples, 1):
            logger.info(f"{idx}. {sample}")

        # Save results
        output_dir = CONFIG["OUTPUT_DIR"]
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"apollo_icebreakers_{timestamp}.csv"

        df_final.to_csv(output_file, index=False)
        logger.info(f"Results saved to: {output_file}")

        logger.info("=== ICEBREAKER GENERATOR COMPLETE ===")

    except Exception as e:
        logger.error(f"Script failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
