#!/usr/bin/env python3
"""
=== GOOGLE MAPS DATA ANALYZER ===
Version: 1.0.0 | Created: 2025-01-10

PURPOSE:
Analyzes all Google Maps scraping results using DuckDB for efficient multi-file processing.
Provides comprehensive statistics about leads, quality, and readiness for enrichment pipeline.

FEATURES:
- DuckDB-powered analysis of multiple JSON files
- Statistics by state, niche, city
- Data quality assessment (phone/website coverage)
- Enrichment pipeline readiness metrics

USAGE:
1. Run: python google_maps_analyzer.py
2. Results saved to results/analysis_YYYYMMDD_HHMMSS.json
3. Console output shows summary statistics

IMPROVEMENTS:
v1.0.0 - Initial version with DuckDB integration
"""

import sys
import json
import duckdb
import logging
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
    "ANALYSIS_OUTPUT": Path(__file__).parent.parent / "results" / "analysis",
    "FILE_PATTERN": "**/*.json",  # All JSON files in subdirectories
    "EXCLUDE_PATTERNS": ["raw", "analysis"],  # Skip raw files and analysis results
}

SCRIPT_STATS = {
    "version": "1.0.0",
    "total_runs": 0,
    "last_run": None,
    "success_rate": 0.0
}

def find_filtered_json_files():
    """Find all filtered JSON files (exclude raw and analysis)"""
    logger.info(f"Searching for filtered JSON files in: {CONFIG['RESULTS_DIR']}")

    all_files = list(CONFIG["RESULTS_DIR"].glob(CONFIG["FILE_PATTERN"]))

    # Exclude raw files and analysis results
    filtered_files = [
        f for f in all_files
        if not any(pattern in str(f) for pattern in CONFIG["EXCLUDE_PATTERNS"])
        and f.name.endswith('.json')
    ]

    logger.info(f"Found {len(filtered_files)} filtered files")
    return filtered_files

def analyze_with_duckdb(json_files):
    """Use DuckDB to analyze all JSON files efficiently"""
    logger.info(f"Starting DuckDB analysis on {len(json_files)} files")

    # Initialize DuckDB connection (in-memory)
    con = duckdb.connect(database=':memory:')

    # Load all JSON files and flatten the structure
    all_leads = []

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                metadata = data.get('metadata', {})
                state = metadata.get('state', 'unknown')
                niche = metadata.get('niche', 'unknown')
                timestamp = metadata.get('timestamp', 'unknown')

                # Extract leads from nested structure
                for city_data in data.get('results_by_city', []):
                    city_name = city_data.get('city', 'Unknown')

                    for place in city_data.get('filtered_places', []):
                        lead = {
                            'state': state,
                            'niche': niche,
                            'city': city_name,
                            'timestamp': timestamp,
                            'place_id': place.get('place_id'),
                            'name': place.get('name'),
                            'rating': place.get('rating'),
                            'reviews': place.get('user_ratings_total'),
                            'phone': place.get('phone'),
                            'website': place.get('website'),
                            'address': place.get('address'),
                            'has_phone': bool(place.get('phone')),
                            'has_website': bool(place.get('website')),
                            'has_contact': bool(place.get('phone')) and bool(place.get('website')),
                        }
                        all_leads.append(lead)

        except Exception as e:
            logger.error(f"Failed to process file {json_file}: {e}")
            continue

    if not all_leads:
        logger.warning("No leads found in any files")
        return None

    # Create DuckDB table from leads (DuckDB can read Python lists directly)
    import pandas as pd
    df = pd.DataFrame(all_leads)
    con.execute("CREATE TABLE leads AS SELECT * FROM df")

    logger.info(f"DuckDB table created with {len(all_leads)} total leads")

    # Run analytics queries
    analytics = {}

    # Overall statistics
    analytics['overview'] = con.execute("""
        SELECT
            COUNT(*) as total_leads,
            COUNT(DISTINCT state) as total_states,
            COUNT(DISTINCT niche) as total_niches,
            COUNT(DISTINCT city) as total_cities,
            ROUND(AVG(rating), 2) as avg_rating,
            ROUND(AVG(reviews), 0) as avg_reviews,
            SUM(CASE WHEN has_phone THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as phone_coverage_pct,
            SUM(CASE WHEN has_website THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as website_coverage_pct,
            SUM(CASE WHEN has_contact THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as full_contact_pct
        FROM leads
    """).fetchdf().to_dict('records')[0]

    # By state
    analytics['by_state'] = con.execute("""
        SELECT
            state,
            COUNT(*) as leads,
            COUNT(DISTINCT city) as cities,
            COUNT(DISTINCT niche) as niches,
            ROUND(AVG(rating), 2) as avg_rating,
            SUM(CASE WHEN has_contact THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as contact_coverage_pct
        FROM leads
        GROUP BY state
        ORDER BY leads DESC
    """).fetchdf().to_dict('records')

    # By niche
    analytics['by_niche'] = con.execute("""
        SELECT
            niche,
            COUNT(*) as leads,
            COUNT(DISTINCT state) as states,
            ROUND(AVG(rating), 2) as avg_rating,
            ROUND(AVG(reviews), 0) as avg_reviews,
            SUM(CASE WHEN has_contact THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as contact_coverage_pct
        FROM leads
        GROUP BY niche
        ORDER BY leads DESC
    """).fetchdf().to_dict('records')

    # Top cities
    analytics['top_cities'] = con.execute("""
        SELECT
            city,
            state,
            niche,
            COUNT(*) as leads,
            ROUND(AVG(rating), 2) as avg_rating
        FROM leads
        GROUP BY city, state, niche
        ORDER BY leads DESC
        LIMIT 20
    """).fetchdf().to_dict('records')

    # Data quality assessment
    analytics['data_quality'] = con.execute("""
        SELECT
            SUM(CASE WHEN has_phone AND has_website THEN 1 ELSE 0 END) as ready_for_outreach,
            SUM(CASE WHEN has_phone AND NOT has_website THEN 1 ELSE 0 END) as needs_website,
            SUM(CASE WHEN has_website AND NOT has_phone THEN 1 ELSE 0 END) as needs_phone,
            SUM(CASE WHEN NOT has_phone AND NOT has_website THEN 1 ELSE 0 END) as needs_both,
            ROUND(SUM(CASE WHEN rating >= 4.5 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as high_rating_pct,
            ROUND(SUM(CASE WHEN reviews >= 50 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as established_pct
        FROM leads
    """).fetchdf().to_dict('records')[0]

    # Enrichment pipeline metrics
    analytics['enrichment_needs'] = {
        'email_scraping_needed': analytics['data_quality']['ready_for_outreach'],
        'website_enrichment_needed': analytics['data_quality']['needs_website'],
        'phone_enrichment_needed': analytics['data_quality']['needs_phone'],
        'estimated_email_scrape_hours': round(analytics['data_quality']['ready_for_outreach'] * 2 / 3600, 2)  # 2 seconds per business
    }

    con.close()
    logger.info("DuckDB analysis completed")

    return analytics

def print_summary(analytics):
    """Print human-readable summary to console"""
    print("\n" + "="*80)
    print("GOOGLE MAPS DATA ANALYSIS SUMMARY")
    print("="*80)

    overview = analytics['overview']
    print(f"\nOVERALL STATISTICS:")
    print(f"  Total Leads: {int(overview['total_leads']):,}")
    print(f"  States Covered: {int(overview['total_states'])}")
    print(f"  Niches: {int(overview['total_niches'])}")
    print(f"  Cities: {int(overview['total_cities'])}")
    print(f"  Average Rating: {overview['avg_rating']}")
    print(f"  Average Reviews: {int(overview['avg_reviews']):,}")

    print(f"\nCONTACT DATA COVERAGE:")
    print(f"  Phone Numbers: {overview['phone_coverage_pct']:.1f}%")
    print(f"  Websites: {overview['website_coverage_pct']:.1f}%")
    print(f"  Full Contact Info: {overview['full_contact_pct']:.1f}%")

    print(f"\nBY STATE:")
    for state in analytics['by_state'][:10]:  # Top 10 states
        print(f"  {state['state'].upper()}: {int(state['leads']):,} leads | {int(state['cities'])} cities | {state['contact_coverage_pct']:.1f}% contact coverage")

    print(f"\nBY NICHE:")
    for niche in analytics['by_niche']:
        print(f"  {niche['niche'].upper()}: {int(niche['leads']):,} leads | {int(niche['states'])} states | Rating {niche['avg_rating']}")

    quality = analytics['data_quality']
    print(f"\nDATA QUALITY:")
    print(f"  Ready for Outreach: {int(quality['ready_for_outreach']):,} (have phone + website)")
    print(f"  Need Website Only: {int(quality['needs_website']):,}")
    print(f"  Need Phone Only: {int(quality['needs_phone']):,}")
    print(f"  Need Both: {int(quality['needs_both']):,}")
    print(f"  High Rating (4.5+): {quality['high_rating_pct']}%")
    print(f"  Established (50+ reviews): {quality['established_pct']}%")

    needs = analytics['enrichment_needs']
    print(f"\nENRICHMENT PIPELINE:")
    print(f"  Businesses Ready for Email Scraping: {int(needs['email_scraping_needed']):,}")
    print(f"  Estimated Email Scraping Time: {needs['estimated_email_scrape_hours']} hours")
    print(f"  Websites to Enrich: {int(needs['website_enrichment_needed']):,}")

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("  1. Email scraping for ready businesses")
    print("  2. AI icebreaker generation")
    print("  3. Website content scraping for context")
    print("  4. Business categorization & segmentation")
    print("="*80 + "\n")

def save_analysis_report(analytics):
    """Save detailed analysis report to JSON"""
    # Create analysis directory if doesn't exist
    CONFIG["ANALYSIS_OUTPUT"].mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["ANALYSIS_OUTPUT"] / f"analysis_{timestamp}.json"

    report = {
        "generated_at": datetime.now().isoformat(),
        "script_version": SCRIPT_STATS["version"],
        "analytics": analytics,
        "recommendations": {
            "priority_1": "Start email scraping for ready businesses (have phone + website)",
            "priority_2": "Enrich businesses missing websites using business name + address",
            "priority_3": "Set up AI icebreaker generation pipeline",
            "priority_4": "Scrape website content for personalization context"
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Analysis report saved to: {output_file}")
    return output_file

def main():
    """Main execution flow"""
    logger.info("Google Maps Data Analyzer started")

    try:
        # Find all filtered JSON files
        json_files = find_filtered_json_files()

        if not json_files:
            logger.error("No filtered JSON files found")
            print("ERROR: No data files found. Run scraper first.")
            return

        # Analyze with DuckDB
        analytics = analyze_with_duckdb(json_files)

        if not analytics:
            logger.error("Analysis failed - no data extracted")
            return

        # Print summary to console
        print_summary(analytics)

        # Save detailed report
        output_file = save_analysis_report(analytics)

        # Update script stats
        SCRIPT_STATS["total_runs"] += 1
        SCRIPT_STATS["last_run"] = datetime.now().isoformat()
        SCRIPT_STATS["success_rate"] = 100.0

        logger.info(f"Analysis completed successfully: {analytics['overview']['total_leads']} total leads, "
                   f"{analytics['data_quality']['ready_for_outreach']} ready for outreach")

        print(f"\nDetailed report saved to: {output_file}")

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        print(f"\nERROR: Analysis failed - {str(e)}")
        raise

if __name__ == "__main__":
    main()
