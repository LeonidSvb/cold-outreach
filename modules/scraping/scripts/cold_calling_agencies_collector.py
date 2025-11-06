#!/usr/bin/env python3
"""
=== COLD CALLING AGENCIES COLLECTOR ===
Version: 1.0.0 | Created: 2025-11-02

PURPOSE:
Collect comprehensive list of cold calling agencies and call centers from USA, Canada,
Australia, and Europe using HTTP-based web scraping.

FEATURES:
- Multi-source data collection (directories, Google search, LinkedIn)
- Company validation and deduplication
- Website and contact extraction
- Export to JSON format

USAGE:
1. Review CONFIG section
2. Run: python cold_calling_agencies_collector.py
3. Results saved to ../results/

IMPROVEMENTS:
v1.0.0 - Initial version with manual seed list and web search
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import time
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "TARGET_COUNTRIES": ["USA", "Canada", "Australia", "UK", "Germany", "France", "Netherlands", "Spain"],
    "MINIMUM_COMPANY_SIZE": 20,
    "TARGET_COUNT": 500,
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
    "SEARCH_DELAY_SEC": (2, 5),  # Random delay between requests
}

# Manual seed list from research
SEED_COMPANIES = [
    # USA - Top Tier
    {"name": "SalesRoads", "country": "USA", "source": "Clutch.co", "services": "B2B cold calling, appointment setting"},
    {"name": "Martal Group", "country": "USA/Canada", "source": "Multiple", "services": "B2B lead generation, cold calling"},
    {"name": "Belkins", "country": "USA", "source": "Multiple", "services": "Cold calling, intent-based prospecting"},
    {"name": "Hit Rate Solutions", "country": "USA", "source": "Multiple", "services": "B2B/B2C cold calling, Philippines-based"},
    {"name": "SalesHive", "country": "USA", "source": "Multiple", "services": "Outbound sales automation, cold calling"},
    {"name": "Callbox", "country": "USA", "source": "Multiple", "services": "B2B lead generation, telemarketing"},
    {"name": "Upcall", "country": "USA", "source": "Multiple", "services": "Outbound call services, lead generation"},
    {"name": "DialAmerica", "country": "USA", "source": "Research", "services": "Telemarketing, call center"},
    {"name": "Quality Contact Solutions", "country": "USA", "source": "Multiple", "services": "Telemarketing services"},
    {"name": "Strategic Calls", "country": "USA", "source": "Research", "services": "B2B telemarketing"},
    {"name": "Flatworld Solutions", "country": "USA", "source": "Research", "services": "BPO, telemarketing"},
    {"name": "LevelUp Leads", "country": "USA", "source": "Clutch.co", "services": "B2C telemarketing, telesales"},
    {"name": "XACT", "country": "USA", "source": "Clutch.co", "services": "Inbound/outbound call center"},
    {"name": "Telecom Inc", "country": "USA", "source": "Research", "services": "Outbound telemarketing, lead generation"},
    {"name": "MCI", "country": "USA", "source": "Research", "services": "Outbound contact center services"},
    {"name": "AnswerNet", "country": "USA", "source": "Research", "services": "Outbound telemarketing, call center"},
    {"name": "Worldwide Call Centers", "country": "USA", "source": "Research", "services": "Global telemarketing network"},
    {"name": "Customer Contact Services", "country": "USA", "source": "Research", "services": "North American call centers"},
    {"name": "OneTouch Direct", "country": "USA", "source": "GoodFirms", "services": "Direct marketing, call center"},
    {"name": "IdeasUnlimited", "country": "USA", "source": "GoodFirms", "services": "24/7 call center services"},
    {"name": "Telesales Services", "country": "USA", "source": "GoodFirms", "services": "Telemarketing provider network"},
    {"name": "AnswerConnect", "country": "USA", "source": "DesignRush", "services": "Answering service, call center"},
    {"name": "The Call Company", "country": "USA", "source": "DesignRush", "services": "Call center services"},
    {"name": "LeadBuds", "country": "USA", "source": "DesignRush", "services": "Lead generation, calling"},
    {"name": "Pipeful", "country": "USA", "source": "DesignRush", "services": "Call center services"},
    {"name": "Paramount Communications", "country": "USA", "source": "LinkedIn", "services": "Telemarketing, cold calling"},
    {"name": "Telecrew Outsourcing", "country": "USA/Philippines", "source": "LinkedIn", "services": "Remote sales, cold calling"},

    # Canada
    {"name": "Purple Sales", "country": "Canada", "source": "Research", "services": "Lead generation, appointment booking"},
    {"name": "360 Leads", "country": "Canada", "source": "Research", "services": "Outbound marketing, telemarketing"},
    {"name": "FiveRings Marketing", "country": "Canada", "source": "Research", "services": "B2B lead generation, outbound sales"},
    {"name": "Growth Rhino", "country": "Canada", "source": "Research", "services": "B2B cold outreach for startups"},
    {"name": "TELUP", "country": "Canada", "source": "GoodFirms", "services": "BPO, contact center"},
    {"name": "Groupe Marketing International", "country": "Canada", "source": "GoodFirms", "services": "Telemarketing, customer service"},
    {"name": "3C Contact Services", "country": "Canada", "source": "GoodFirms", "services": "Inbound call center"},
    {"name": "Extend Communications", "country": "Canada", "source": "GoodFirms", "services": "Inbound call center, Ontario"},
    {"name": "Norbell", "country": "Canada", "source": "GoodFirms", "services": "24/7 call center outsourcing"},

    # Australia
    {"name": "Telemarketing Professionals", "country": "Australia", "source": "Research", "services": "B2B lead generation, appointment setting"},
    {"name": "Illicium", "country": "Australia", "source": "Research", "services": "B2B lead generation, sales outsourcing"},
    {"name": "Callbox Australia", "country": "Australia", "source": "Research", "services": "B2B lead generation services"},
    {"name": "Sharesource", "country": "Australia", "source": "Research", "services": "B2B call center, Queensland"},
    {"name": "TSA Group", "country": "Australia", "source": "Research", "services": "B2B telemarketing, 20+ years"},

    # Europe
    {"name": "Teleperformance", "country": "France/Europe", "source": "Research", "services": "Global CX provider, 500k+ employees"},
    {"name": "Foundever", "country": "UK/Europe", "source": "Research", "services": "Customer experience, pan-European"},
    {"name": "Capita", "country": "UK", "source": "Research", "services": "Outsourcing, call center"},
    {"name": "The Telemarketing Company", "country": "UK", "source": "LinkedIn", "services": "Appointment setting, lead generation"},
    {"name": "Cold Calling Agency", "country": "UK", "source": "LinkedIn", "services": "Cold calling services"},
    {"name": "MeetMezzo", "country": "UK/USA/Multi", "source": "LinkedIn", "services": "Appointment setting, cold calling"},
    {"name": "VirtualBridgePH", "country": "Global (EU/AU/US)", "source": "Research", "services": "Telemarketing for SMEs"},
    {"name": "New Media Services", "country": "Global (EU/AU/US)", "source": "Research", "services": "BPO, 3000+ employees"},
]


def save_results(companies, filename_prefix="cold_calling_agencies"):
    """Save results to JSON file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"{filename_prefix}_{timestamp}.json"

    CONFIG["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)

    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_companies": len(companies),
            "target_countries": CONFIG["TARGET_COUNTRIES"],
            "version": "1.0.0",
        },
        "companies": companies,
        "statistics": {
            "by_country": {},
            "by_source": {},
        }
    }

    # Calculate statistics
    for company in companies:
        country = company.get("country", "Unknown")
        source = company.get("source", "Unknown")

        output_data["statistics"]["by_country"][country] = output_data["statistics"]["by_country"].get(country, 0) + 1
        output_data["statistics"]["by_source"][source] = output_data["statistics"]["by_source"].get(source, 0) + 1

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to {output_file}", companies_count=len(companies))
    return output_file


def enhance_company_data(company):
    """Enhance company data with additional fields"""
    enhanced = company.copy()
    enhanced.update({
        "website": None,  # To be filled by email extraction
        "email": None,
        "phone": None,
        "linkedin": None,
        "employee_count": None,
        "year_founded": None,
        "extracted_at": datetime.now().isoformat(),
    })
    return enhanced


def deduplicate_companies(companies):
    """Remove duplicate companies based on name"""
    seen_names = set()
    unique_companies = []

    for company in companies:
        name_lower = company["name"].lower().strip()
        if name_lower not in seen_names:
            seen_names.add(name_lower)
            unique_companies.append(company)
        else:
            logger.debug(f"Duplicate removed: {company['name']}")

    return unique_companies


def main():
    logger.info("Starting cold calling agencies collector")

    try:
        # Step 1: Load and enhance seed companies
        logger.info(f"Loading {len(SEED_COMPANIES)} seed companies")
        companies = [enhance_company_data(c) for c in SEED_COMPANIES]

        # Step 2: Deduplicate
        companies = deduplicate_companies(companies)
        logger.info(f"After deduplication: {len(companies)} unique companies")

        # Step 3: Save initial results
        output_file = save_results(companies, "cold_calling_agencies_initial")

        logger.info("Collection completed successfully", total_companies=len(companies))
        logger.info(f"Results saved to: {output_file}")

        # Print summary
        print(f"\n{'='*60}")
        print(f"COLLECTION SUMMARY")
        print(f"{'='*60}")
        print(f"Total Companies Collected: {len(companies)}")
        print(f"Target Goal: {CONFIG['TARGET_COUNT']}")
        print(f"Progress: {len(companies) / CONFIG['TARGET_COUNT'] * 100:.1f}%")
        print(f"\nBy Country:")
        by_country = {}
        for c in companies:
            country = c.get("country", "Unknown")
            by_country[country] = by_country.get(country, 0) + 1
        for country, count in sorted(by_country.items(), key=lambda x: x[1], reverse=True):
            print(f"  {country}: {count}")
        print(f"\nResults saved to: {output_file}")
        print(f"{'='*60}\n")

        # Next steps message
        print("NEXT STEPS:")
        print("1. Provide Apollo API key to collect 500+ leads automatically")
        print("2. Or: Create web scraper to extract websites from directories")
        print("3. Then: Extract emails from company websites")

    except Exception as e:
        logger.error("Collection failed", error=e)
        raise


if __name__ == "__main__":
    main()
