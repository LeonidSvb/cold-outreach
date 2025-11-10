#!/usr/bin/env python3
"""
=== JSON TO PARQUET CONSOLIDATOR ===
Version: 1.0.0 | Created: 2025-01-10

PURPOSE:
Consolidates all Google Maps JSON results into a single optimized Parquet file.
Parquet is 10-20x smaller than JSON and can be queried directly with DuckDB.

FEATURES:
- Reads all filtered JSON files (excludes raw)
- Deduplicates by place_id
- Saves to compact Parquet format
- Exports sample CSV for verification
- Shows statistics and size comparison

USAGE:
1. Run: python consolidate_to_parquet.py
2. Output: data/raw/all_leads.parquet
3. View: vd data/raw/all_leads.parquet (requires visidata)
4. Query: duckdb -c "SELECT * FROM 'data/raw/all_leads.parquet' LIMIT 10"

IMPROVEMENTS:
v1.0.0 - Initial version
"""

import sys
import json
import logging
import duckdb
import pandas as pd
from pathlib import Path
from datetime import datetime

# Setup logging
try:
    from logger.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

CONFIG = {
    "RESULTS_DIR": Path(__file__).parent.parent / "results",
    "OUTPUT_DIR": Path(__file__).parent.parent / "data" / "raw",
    "EXPORTS_DIR": Path(__file__).parent.parent / "data" / "exports",
    "EXCLUDE_PATTERNS": ["raw", "analysis"],
}

def find_filtered_json_files():
    """Find all filtered JSON files"""
    logger.info(f"Searching for JSON files in: {CONFIG['RESULTS_DIR']}")

    all_files = list(CONFIG["RESULTS_DIR"].glob("**/*.json"))

    filtered_files = [
        f for f in all_files
        if not any(pattern in str(f) for pattern in CONFIG["EXCLUDE_PATTERNS"])
        and f.name.endswith('.json')
    ]

    logger.info(f"Found {len(filtered_files)} filtered JSON files")
    return filtered_files

def load_and_flatten_json(json_files):
    """Load JSON files and flatten to DataFrame structure"""
    logger.info("Loading and flattening JSON data")

    all_leads = []

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                metadata = data.get('metadata', {})

                # Try to get state from metadata, or infer from file path
                state = metadata.get('state', 'unknown')
                if state == 'unknown':
                    # Extract state from path (e.g., results/texas/file.json)
                    parts = str(json_file).split('\\')
                    if 'results' in parts:
                        idx = parts.index('results')
                        if idx + 1 < len(parts):
                            state = parts[idx + 1]

                niche = metadata.get('niche', 'unknown')

                # Extract niche from filename if not in metadata
                if niche == 'unknown':
                    filename = json_file.stem
                    # Remove timestamp pattern
                    import re
                    niche_match = re.match(r'^([a-z_]+)_\d{8}', filename)
                    if niche_match:
                        niche = niche_match.group(1)

                timestamp = metadata.get('timestamp', 'unknown')

                for city_data in data.get('results_by_city', []):
                    city_name = city_data.get('city', 'Unknown')

                    # Support both old and new structure
                    places = city_data.get('filtered_places', []) or city_data.get('places', [])

                    for place in places:
                        lead = {
                            'place_id': place.get('place_id'),
                            'name': place.get('name'),
                            'state': state,
                            'city': city_name,
                            'niche': niche,
                            'address': place.get('address'),
                            'phone': place.get('phone'),
                            'website': place.get('website'),
                            'rating': place.get('rating'),
                            'reviews': place.get('user_ratings_total'),
                            'business_status': place.get('business_status', 'OPERATIONAL'),
                            'scraped_at': timestamp,
                            'has_phone': bool(place.get('phone')),
                            'has_website': bool(place.get('website')),
                            'has_contact': bool(place.get('phone')) and bool(place.get('website')),
                        }
                        all_leads.append(lead)

        except Exception as e:
            logger.error(f"Failed to process {json_file}: {e}")
            continue

    logger.info(f"Loaded {len(all_leads)} total leads")
    return pd.DataFrame(all_leads)

def deduplicate_leads(df):
    """Remove duplicates based on place_id"""
    logger.info(f"Deduplicating leads (before: {len(df)})")

    # Keep first occurrence of each place_id
    df_deduped = df.drop_duplicates(subset=['place_id'], keep='first')

    duplicates_removed = len(df) - len(df_deduped)
    logger.info(f"Removed {duplicates_removed} duplicates (after: {len(df_deduped)})")

    return df_deduped

def save_to_parquet(df, output_file):
    """Save DataFrame to Parquet format"""
    logger.info(f"Saving to Parquet: {output_file}")

    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save to Parquet
    df.to_parquet(output_file, index=False, compression='snappy')

    # Get file size
    size_mb = output_file.stat().st_size / (1024 * 1024)
    logger.info(f"Saved successfully: {size_mb:.2f} MB")

    return size_mb

def export_sample_csv(df, sample_size=100):
    """Export a sample CSV for verification"""
    logger.info(f"Exporting sample CSV ({sample_size} rows)")

    # Create exports directory
    CONFIG["EXPORTS_DIR"].mkdir(parents=True, exist_ok=True)

    # Export sample
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sample_file = CONFIG["EXPORTS_DIR"] / f"sample_{timestamp}.csv"

    df.head(sample_size).to_csv(sample_file, index=False)
    logger.info(f"Sample exported: {sample_file}")

    return sample_file

def calculate_json_size(json_files):
    """Calculate total size of JSON files"""
    total_size = sum(f.stat().st_size for f in json_files)
    return total_size / (1024 * 1024)  # MB

def print_summary(df, parquet_size_mb, json_size_mb, parquet_file, sample_file):
    """Print human-readable summary"""
    print("\n" + "="*80)
    print("PARQUET CONSOLIDATION COMPLETED")
    print("="*80)

    print(f"\nDATA SUMMARY:")
    print(f"  Total Leads: {len(df):,}")
    print(f"  States: {df['state'].nunique()}")
    print(f"  Niches: {df['niche'].nunique()}")
    print(f"  Cities: {df['city'].nunique()}")
    print(f"  Ready for Outreach: {df['has_contact'].sum():,} ({df['has_contact'].mean()*100:.1f}%)")

    print(f"\nFILE SIZE COMPARISON:")
    print(f"  JSON files total: {json_size_mb:.2f} MB")
    print(f"  Parquet file: {parquet_size_mb:.2f} MB")
    print(f"  Compression ratio: {json_size_mb/parquet_size_mb:.1f}x smaller")

    print(f"\nOUTPUT FILES:")
    print(f"  Main Parquet: {parquet_file}")
    print(f"  Sample CSV: {sample_file}")

    print(f"\nVIEW DATA IN CLI:")
    print(f"  # Install visidata (one-time):")
    print(f"  pip install visidata")
    print(f"  ")
    print(f"  # View interactively:")
    print(f"  vd \"{parquet_file}\"")
    print(f"  ")
    print(f"  # Or with DuckDB:")
    print(f"  duckdb -c \"SELECT * FROM '{parquet_file}' LIMIT 10\"")

    print(f"\nQUERY EXAMPLES (DuckDB):")
    print(f"  # Count by state:")
    print(f"  duckdb -c \"SELECT state, COUNT(*) FROM '{parquet_file}' GROUP BY state\"")
    print(f"  ")
    print(f"  # Find HVAC in Florida with 4.5+ rating:")
    print(f"  duckdb -c \"SELECT name, city, rating FROM '{parquet_file}' WHERE state='florida' AND niche='hvac' AND rating >= 4.5 LIMIT 10\"")

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("  1. View data with: vd data/raw/all_leads.parquet")
    print("  2. Run email scraper (coming next)")
    print("  3. Check sample CSV for quality verification")
    print("="*80 + "\n")

def main():
    """Main execution flow"""
    logger.info("Parquet Consolidation started")

    try:
        # Find JSON files
        json_files = find_filtered_json_files()

        if not json_files:
            logger.error("No JSON files found")
            print("ERROR: No data files found")
            return

        # Calculate JSON size
        json_size_mb = calculate_json_size(json_files)

        # Load and flatten
        df = load_and_flatten_json(json_files)

        if df.empty:
            logger.error("No data loaded")
            print("ERROR: No data extracted from JSON files")
            return

        # Deduplicate
        df = deduplicate_leads(df)

        # Save to Parquet
        parquet_file = CONFIG["OUTPUT_DIR"] / "all_leads.parquet"
        parquet_size_mb = save_to_parquet(df, parquet_file)

        # Export sample CSV
        sample_file = export_sample_csv(df)

        # Print summary
        print_summary(df, parquet_size_mb, json_size_mb, parquet_file, sample_file)

        logger.info("Consolidation completed successfully")

    except Exception as e:
        logger.error(f"Consolidation failed: {e}", exc_info=True)
        print(f"\nERROR: {e}")
        raise

if __name__ == "__main__":
    main()
