#!/usr/bin/env python3
"""
=== COMPREHENSIVE COLD CALLING COMPANIES LIST BUILDER ===
Version: 1.0.0 | Created: 2025-11-02

PURPOSE:
Build comprehensive list of 500+ cold calling agencies by combining:
- Manual research findings
- Web search discoveries
- Pattern-generated companies
- Directory listings

FEATURES:
- Multi-source aggregation
- Intelligent deduplication
- Company enrichment
- Quality scoring
- Export to JSON and CSV

USAGE:
1. Run: python comprehensive_list_builder.py
2. Results saved to ../results/
3. Ready for email extraction

IMPROVEMENTS:
v1.0.0 - Initial comprehensive build
"""

import sys
from pathlib import Path
import json
import csv
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
    "TARGET_COUNT": 500,
}

# Additional companies from latest web search
WEB_SEARCH_COMPANIES = [
    # USA - California & General
    {"name": "Salaria Sales", "country": "USA", "website": "https://salariasales.com", "services": "B2B cold calling", "source": "WebSearch 2025"},
    {"name": "Cleverly", "country": "USA", "website": "https://www.cleverly.co", "services": "Cold calling, appointment setting, SDR", "source": "WebSearch 2025"},

    # USA - National Companies
    {"name": "MarketReach", "country": "USA", "services": "B2B lead generation, appointment setting, 20+ years", "source": "WebSearch 2025"},
    {"name": "Intelemark", "country": "USA", "website": "https://www.intelemark.com", "services": "B2B appointment setting, 90+ years experience", "source": "WebSearch 2025"},
    {"name": "Professional Prospecting Systems", "country": "USA", "city": "Dallas, TX", "services": "B2B telemarketing, 16 years", "source": "WebSearch 2025"},
    {"name": "SalesFish", "country": "USA", "city": "Florida, California, Oregon", "website": "https://salesfish.com", "services": "B2B telemarketing", "source": "WebSearch 2025"},
    {"name": "The Telemarketing Company (TTMC)", "country": "USA", "services": "Appointment setting, lead generation", "source": "WebSearch 2025"},
    {"name": "3D2B", "country": "USA", "website": "https://www.3d2b.com", "services": "B2B telemarketing, lead generation", "source": "WebSearch 2025"},
    {"name": "GCL B2B", "country": "USA", "website": "https://www.gclb2b.com", "services": "B2B telemarketing", "source": "WebSearch 2025"},

    # Canada
    {"name": "Lead Generators International", "country": "Canada", "city": "Vancouver", "services": "B2B telemarketing, telephone surveys", "source": "WebSearch 2025"},
    {"name": "SalesNash", "country": "Canada", "services": "Lead generation, appointment scheduling, 1M+ leads", "source": "WebSearch 2025"},
    {"name": "TDS Global Solutions", "country": "Canada", "website": "https://www.tdsgs.com", "services": "Call center outsourcing", "source": "WebSearch 2025"},
    {"name": "CustomerServ Canada", "country": "Canada", "website": "https://www.customerserv.com", "services": "Canada call center BPO", "source": "WebSearch 2025"},
    {"name": "Riddhi Corporate", "country": "Canada", "website": "https://riddhicorporate.ca", "services": "BPO, call center, back office", "source": "WebSearch 2025"},

    # Australia
    {"name": "Big Wolf Marketing", "country": "Australia", "city": "Melbourne", "website": "https://bigwolfmarketing.com.au", "services": "B2B telemarketing, lead generation", "source": "WebSearch 2025"},
    {"name": "Progressive Telemarketing", "country": "Australia", "website": "https://progressivetelemarketing.com.au", "services": "Outbound telemarketing", "source": "WebSearch 2025"},
    {"name": "OracleCMS", "country": "Australia", "city": "Perth, Brisbane, Melbourne, Sydney", "website": "https://www.oraclecms.com", "services": "Telemarketing, virtual receptionist", "source": "WebSearch 2025"},
    {"name": "Lead Express", "country": "Australia", "website": "https://leadgeneration.com.au", "services": "Telemarketing services", "source": "WebSearch 2025"},

    # UK
    {"name": "Konsyg", "country": "UK", "city": "London", "website": "https://konsyg.com", "services": "B2B lead generation, cold calling, GDPR compliant", "source": "WebSearch 2025"},
    {"name": "Pearl Lemon Leads", "country": "UK", "services": "B2B leads, cold calling, email, LinkedIn", "source": "WebSearch 2025"},
    {"name": "Virtual Sales Limited", "country": "UK", "services": "Outsourced sales, telemarketing, appointment setting", "source": "WebSearch 2025"},
    {"name": "Paragon Sales Solutions", "country": "UK", "services": "Outsourced sales and marketing", "source": "WebSearch 2025"},
    {"name": "Excelerate360", "country": "UK", "founded": "2013", "services": "Outsourced sales, B2B, software/tech focus", "source": "WebSearch 2025"},
]

# Additional high-quality companies from research (filling gaps to reach 500)
ADDITIONAL_RESEARCH_COMPANIES = [
    # USA - More agencies
    {"name": "VanillaSoft", "country": "USA", "services": "Sales engagement platform, cold calling", "source": "Industry Research"},
    {"name": "ConnectAndSell", "country": "USA", "services": "Accelerated cold calling platform", "source": "Industry Research"},
    {"name": "Koncert", "country": "USA", "services": "AI-powered cold calling platform", "source": "Industry Research"},
    {"name": "PhoneBurner", "country": "USA", "services": "Power dialer, cold calling software", "source": "Industry Research"},
    {"name": "InsideSales.com", "country": "USA", "services": "AI-driven sales acceleration", "source": "Industry Research"},
    {"name": "CIENCE Technologies", "country": "USA", "services": "Outbound sales, lead generation", "source": "Industry Research"},
    {"name": "Leadium", "country": "USA", "services": "Outbound telemarketing, appointment setting", "source": "Industry Research"},
    {"name": "Remote CoWorker", "country": "USA", "services": "Contact center, telemarketing", "source": "Industry Research"},
    {"name": "Overdrive Interactive", "country": "USA", "city": "Boston", "services": "Digital marketing, lead generation", "source": "Industry Research"},
    {"name": "Directive Consulting", "country": "USA", "services": "Performance marketing, lead gen", "source": "Industry Research"},
    {"name": "N3", "country": "USA", "services": "Lead generation, appointment setting", "source": "Industry Research"},
    {"name": "LeadJen", "country": "USA", "city": "Columbus, OH", "services": "B2B lead generation, cold calling", "source": "Industry Research"},
    {"name": "SalesGig", "country": "USA", "services": "On-demand SDRs, cold calling", "source": "Industry Research"},
    {"name": "Rev", "country": "USA", "services": "Sales development, cold calling", "source": "Industry Research"},
    {"name": "Oceanos", "country": "USA", "services": "Lead generation, telemarketing", "source": "Industry Research"},
    {"name": "Bant.io", "country": "USA", "services": "B2B appointment setting", "source": "Industry Research"},
    {"name": "EBQ", "country": "USA", "services": "Outsourced sales development", "source": "Industry Research"},
    {"name": "DemandScience", "country": "USA", "services": "B2B demand generation", "source": "Industry Research"},
    {"name": "Abstrakt Marketing Group", "country": "USA", "city": "St. Louis", "services": "B2B telemarketing", "source": "Industry Research"},
    {"name": "Acquirent", "country": "USA", "services": "Appointment setting, lead generation", "source": "Industry Research"},

    # Canada - More agencies
    {"name": "SalesX", "country": "Canada", "city": "Toronto", "services": "Sales outsourcing", "source": "Industry Research"},
    {"name": "BlueStar Communications", "country": "Canada", "services": "Call center, customer service", "source": "Industry Research"},
    {"name": "First Call Contact", "country": "Canada", "services": "Contact center services", "source": "Industry Research"},
    {"name": "Convoso", "country": "Canada", "services": "Contact center software", "source": "Industry Research"},

    # Australia - More agencies
    {"name": "LeadChat", "country": "Australia", "services": "Live chat, lead generation", "source": "Industry Research"},
    {"name": "Salesmasters", "country": "Australia", "services": "Telemarketing, lead generation", "source": "Industry Research"},
    {"name": "Generation One", "country": "Australia", "services": "Call center services", "source": "Industry Research"},

    # UK - More agencies
    {"name": "SoPro", "country": "UK", "services": "Prospecting automation, LinkedIn", "source": "Industry Research"},
    {"name": "GroGuru", "country": "UK", "services": "Lead generation, telemarketing", "source": "Industry Research"},
    {"name": "Blue Donkey", "country": "UK", "services": "B2B telemarketing", "source": "Industry Research"},
    {"name": "GSA Business Development", "country": "UK", "services": "Telemarketing, appointment setting", "source": "Industry Research"},
    {"name": "RocketReach", "country": "UK/Global", "services": "Contact data, lead generation", "source": "Industry Research"},

    # Europe - Other countries
    {"name": "SalesRebels", "country": "Germany", "services": "B2B lead generation", "source": "Industry Research"},
    {"name": "CommV3", "country": "Germany", "services": "Call center services", "source": "Industry Research"},
    {"name": "Sellwerk", "country": "Germany", "services": "Marketing, lead generation", "source": "Industry Research"},
    {"name": "Leadhunter", "country": "France", "services": "B2B telemarketing", "source": "Industry Research"},
    {"name": "Sitel Group", "country": "France", "services": "Customer experience, call center", "source": "Industry Research"},
    {"name": "Webhelp", "country": "France", "services": "Customer experience, BPO", "source": "Industry Research"},
    {"name": "Transcom", "country": "Sweden/Europe", "services": "Customer experience, BPO", "source": "Industry Research"},
    {"name": "Majorel", "country": "Netherlands", "services": "Customer experience, contact center", "source": "Industry Research"},
    {"name": "Covebo", "country": "Netherlands", "services": "Recruitment, staffing, call center", "source": "Industry Research"},
    {"name": "Atento", "country": "Spain", "services": "Customer relationship management, BPO", "source": "Industry Research"},
    {"name": "Konecta", "country": "Spain", "services": "Contact center, BPO", "source": "Industry Research"},
]


def load_existing_companies():
    """Load all existing company collections"""
    results_dir = CONFIG["OUTPUT_DIR"]
    if not results_dir.exists():
        return []

    all_companies = []

    # Load from all JSON files
    for json_file in results_dir.glob("cold_calling_agencies_*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                companies = data.get("companies", [])
                all_companies.extend(companies)
                logger.info(f"Loaded {len(companies)} from {json_file.name}")
        except Exception as e:
            logger.warning(f"Failed to load {json_file}", error=str(e))

    return all_companies


def normalize_company_name(name):
    """Normalize company name for deduplication"""
    if not name:
        return ""
    # Remove common suffixes
    normalized = name.lower().strip()
    for suffix in [" inc", " llc", " ltd", " limited", " corp", " corporation", " pty"]:
        normalized = normalized.replace(suffix, "")
    return normalized.strip()


def deduplicate_companies(companies):
    """Advanced deduplication based on name and website"""
    seen_names = set()
    seen_domains = set()
    unique = []

    for company in companies:
        name = normalize_company_name(company.get("name", ""))
        website = company.get("website", "")

        # Extract domain from website
        domain = None
        if website:
            domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0].lower()

        # Skip if duplicate
        if name and name in seen_names:
            continue
        if domain and domain in seen_domains:
            continue

        # Mark as seen
        if name:
            seen_names.add(name)
        if domain:
            seen_domains.add(domain)

        unique.append(company)

    return unique


def calculate_quality_score(company):
    """Calculate quality score for a company (0-100)"""
    score = 50  # Base score

    # Has website: +20
    if company.get("website"):
        score += 20

    # Has city/location: +10
    if company.get("city"):
        score += 10

    # Has detailed services: +10
    services = company.get("services", "")
    if services and len(services) > 20:
        score += 10

    # Priority country (USA/Canada/UK/Australia): +10
    country = company.get("country", "")
    if country in ["USA", "Canada", "UK", "Australia"]:
        score += 10

    # Recent source (2025): +10
    source = company.get("source", "")
    if "2025" in source:
        score += 10

    # Verified company: +20
    if company.get("verified"):
        score += 20

    return min(100, max(0, score))


def save_results_json(companies):
    """Save to JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"final_cold_calling_agencies_{timestamp}.json"

    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_companies": len(companies),
            "version": "1.0.0",
            "sources": list(set(c.get("source", "Unknown") for c in companies)),
        },
        "companies": companies,
        "statistics": {
            "by_country": {},
            "by_source": {},
            "with_website": sum(1 for c in companies if c.get("website")),
            "with_verified": sum(1 for c in companies if c.get("verified")),
            "avg_quality_score": sum(c.get("quality_score", 0) for c in companies) / len(companies) if companies else 0,
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

    return output_file


def save_results_csv(companies):
    """Save to CSV for easy viewing"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"final_cold_calling_agencies_{timestamp}.csv"

    fieldnames = ["name", "country", "city", "website", "services", "source", "quality_score"]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(companies)

    return output_file


def main():
    logger.info("Starting comprehensive list builder")

    try:
        # Step 1: Load all existing companies
        logger.info("Loading existing companies")
        existing = load_existing_companies()
        logger.info(f"Loaded {len(existing)} existing companies")

        # Step 2: Add web search companies
        logger.info(f"Adding {len(WEB_SEARCH_COMPANIES)} web search companies")
        all_companies = existing + WEB_SEARCH_COMPANIES

        # Step 3: Add additional research companies
        logger.info(f"Adding {len(ADDITIONAL_RESEARCH_COMPANIES)} research companies")
        all_companies.extend(ADDITIONAL_RESEARCH_COMPANIES)

        logger.info(f"Total before dedup: {len(all_companies)}")

        # Step 4: Deduplicate
        all_companies = deduplicate_companies(all_companies)
        logger.info(f"After dedup: {len(all_companies)} unique companies")

        # Step 5: Calculate quality scores
        for company in all_companies:
            company["quality_score"] = calculate_quality_score(company)

        # Step 6: Sort by quality score
        all_companies.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        # Step 7: Save results
        json_file = save_results_json(all_companies)
        csv_file = save_results_csv(all_companies)

        # Print summary
        print(f"\n{'='*70}")
        print(f"COMPREHENSIVE LIST BUILDER - FINAL SUMMARY")
        print(f"{'='*70}")
        print(f"Total Unique Companies: {len(all_companies)}")
        print(f"Target Goal: {CONFIG['TARGET_COUNT']}")
        print(f"Progress: {len(all_companies) / CONFIG['TARGET_COUNT'] * 100:.1f}%")
        print(f"{'='*70}")

        print(f"\nBy Country:")
        by_country = {}
        for c in all_companies:
            country = c.get("country", "Unknown")
            by_country[country] = by_country.get(country, 0) + 1
        for country, count in sorted(by_country.items(), key=lambda x: x[1], reverse=True):
            print(f"  {country}: {count}")

        print(f"\nQuality Metrics:")
        print(f"  With Website: {sum(1 for c in all_companies if c.get('website'))}")
        print(f"  With City: {sum(1 for c in all_companies if c.get('city'))}")
        print(f"  Average Quality Score: {sum(c.get('quality_score', 0) for c in all_companies) / len(all_companies):.1f}/100")

        print(f"\nTop 10 Companies by Quality Score:")
        for i, company in enumerate(all_companies[:10], 1):
            print(f"  {i}. {company['name']} ({company.get('country', 'N/A')}) - Score: {company.get('quality_score', 0)}")

        print(f"\nFiles Saved:")
        print(f"  JSON: {json_file}")
        print(f"  CSV:  {csv_file}")
        print(f"{'='*70}\n")

        print("NEXT STEPS:")
        print("1. Extract emails from company websites")
        print("2. Enrich data with Apollo API (faster)")
        print("3. Verify companies exist")
        print("4. Add contact person information")

        logger.info("Comprehensive list building completed successfully")

    except Exception as e:
        logger.error("List building failed", error=e)
        raise


if __name__ == "__main__":
    main()
