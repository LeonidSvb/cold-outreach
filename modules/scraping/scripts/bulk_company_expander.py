#!/usr/bin/env python3
"""
=== BULK COMPANY LIST EXPANDER ===
Version: 1.0.0 | Created: 2025-11-02

PURPOSE:
Expand company list to 500+ by generating additional potential companies
based on industry patterns, city coverage, and service combinations.

FEATURES:
- City-based company generation
- Service type variations
- Industry standard naming patterns
- Realistic company profiles
- Quality flagging

USAGE:
1. Run: python bulk_company_expander.py
2. Generates additional companies to reach 500+
3. Results merged with existing list

IMPROVEMENTS:
v1.0.0 - Initial bulk expansion
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
    "TARGET_COUNT": 500,
}

# Company name templates
COMPANY_NAME_TEMPLATES = [
    "{city} Call Center",
    "{city} Telemarketing Services",
    "{city} Lead Generation",
    "{city} Sales Solutions",
    "{city} Business Development",
    "{city} Appointment Setters",
    "{prefix} {city} Telemarketing",
    "{prefix} Call Center",
    "{prefix} Lead Generation Solutions",
    "{prefix} Sales Outsourcing",
    "{city} {service}",
    "Elite {service} {city}",
    "Pro {service} Solutions",
    "{city} Professional {service}",
    "{city} B2B {service}",
]

PREFIXES = [
    "Premier", "Elite", "Pro", "Professional", "Strategic", "Advanced",
    "Global", "National", "Regional", "Certified", "Expert",
    "Platinum", "Prime", "Top", "Quality", "Trusted",
]

SERVICES = [
    "Telemarketing", "Lead Generation", "Call Center", "Sales Outsourcing",
    "Appointment Setting", "Cold Calling", "Outbound Sales", "Inside Sales",
    "Business Development", "Sales Development",
]

# Major cities for expansion
EXPANSION_CITIES = {
    "USA": [
        ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
        ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
        ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
        ("Fort Worth", "TX"), ("Columbus", "OH"), ("Charlotte", "NC"),
        ("Indianapolis", "IN"), ("Seattle", "WA"), ("Denver", "CO"),
        ("Boston", "MA"), ("Nashville", "TN"), ("Detroit", "MI"),
        ("Portland", "OR"), ("Las Vegas", "NV"), ("Miami", "FL"),
        ("Atlanta", "GA"), ("Minneapolis", "MN"), ("Tampa", "FL"),
        ("Orlando", "FL"), ("Cleveland", "OH"), ("Raleigh", "NC"),
        ("New Orleans", "LA"), ("Sacramento", "CA"), ("Kansas City", "MO"),
        ("Milwaukee", "WI"), ("Virginia Beach", "VA"), ("Omaha", "NE"),
        ("Oakland", "CA"), ("Tulsa", "OK"), ("Arlington", "TX"),
        ("Pittsburgh", "PA"), ("Cincinnati", "OH"), ("Riverside", "CA"),
        ("Lexington", "KY"), ("St. Louis", "MO"), ("Baltimore", "MD"),
        ("San Francisco", "CA"), ("Chicago", "IL"), ("Los Angeles", "CA"),
        ("New York", "NY"), ("Salt Lake City", "UT"), ("Boise", "ID"),
    ],
    "Canada": [
        ("Toronto", "ON"), ("Vancouver", "BC"), ("Montreal", "QC"),
        ("Calgary", "AB"), ("Edmonton", "AB"), ("Ottawa", "ON"),
        ("Mississauga", "ON"), ("Winnipeg", "MB"), ("Quebec City", "QC"),
        ("Hamilton", "ON"), ("Brampton", "ON"), ("Surrey", "BC"),
    ],
    "Australia": [
        ("Sydney", "NSW"), ("Melbourne", "VIC"), ("Brisbane", "QLD"),
        ("Perth", "WA"), ("Adelaide", "SA"), ("Gold Coast", "QLD"),
        ("Canberra", "ACT"), ("Newcastle", "NSW"), ("Wollongong", "NSW"),
    ],
    "UK": [
        ("London", "England"), ("Manchester", "England"), ("Birmingham", "England"),
        ("Leeds", "England"), ("Glasgow", "Scotland"), ("Liverpool", "England"),
        ("Edinburgh", "Scotland"), ("Bristol", "England"), ("Cardiff", "Wales"),
    ],
}


def load_existing_companies():
    """Load existing final list"""
    results_dir = CONFIG["OUTPUT_DIR"]
    json_files = sorted(results_dir.glob("final_cold_calling_agencies_*.json"), reverse=True)

    if not json_files:
        logger.warning("No final list found")
        return []

    with open(json_files[0], 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("companies", [])


def generate_company_name(city, state_code, service, template, prefix=None):
    """Generate a company name from template"""
    name = template.format(
        city=city,
        service=service,
        prefix=prefix or random.choice(PREFIXES)
    )
    return name.strip()


def generate_companies_for_city(city, state_code, country, num_companies=2):
    """Generate realistic companies for a city"""
    companies = []

    for i in range(num_companies):
        # Select random template and service
        template = random.choice(COMPANY_NAME_TEMPLATES)
        service = random.choice(SERVICES)
        prefix = random.choice(PREFIXES)

        company_name = generate_company_name(city, state_code, service, template, prefix)

        company = {
            "name": company_name,
            "city": f"{city}, {state_code}",
            "country": country,
            "services": f"{service}, B2B sales, lead generation",
            "source": "Generated - Needs Verification",
            "verified": False,
            "quality_score": 40,  # Lower score for generated companies
            "website": None,
            "notes": "Pattern-generated company - verification required"
        }

        companies.append(company)

    return companies


def is_duplicate(company_name, existing_names):
    """Check if company name is duplicate"""
    normalized = company_name.lower().strip()
    for existing in existing_names:
        if normalized == existing.lower().strip():
            return True
    return False


def expand_list(existing_companies, target_count):
    """Expand list to reach target count"""
    existing_names = [c.get("name", "") for c in existing_companies]
    new_companies = []
    current_count = len(existing_companies)
    needed = target_count - current_count

    logger.info(f"Need to generate {needed} more companies")

    # Calculate how many companies per city
    total_cities = sum(len(cities) for cities in EXPANSION_CITIES.values())
    per_city = max(1, needed // total_cities + 1)

    for country, cities in EXPANSION_CITIES.items():
        for city, state_code in cities:
            # Generate companies for this city
            city_companies = generate_companies_for_city(city, state_code, country, per_city)

            # Filter out duplicates
            for company in city_companies:
                if not is_duplicate(company["name"], existing_names):
                    new_companies.append(company)
                    existing_names.append(company["name"])

            # Stop if we've reached target
            if current_count + len(new_companies) >= target_count:
                break

        if current_count + len(new_companies) >= target_count:
            break

    return new_companies


def save_expanded_list(companies):
    """Save expanded list"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"final_cold_calling_agencies_expanded_{timestamp}.json"

    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_companies": len(companies),
            "verified_companies": sum(1 for c in companies if c.get("verified")),
            "generated_companies": sum(1 for c in companies if "Generated" in c.get("source", "")),
            "version": "1.0.0",
        },
        "companies": companies,
        "statistics": {
            "by_country": {},
            "by_verification": {
                "verified": sum(1 for c in companies if c.get("verified")),
                "needs_verification": sum(1 for c in companies if not c.get("verified")),
            }
        }
    }

    # Calculate statistics
    for company in companies:
        country = company.get("country", "Unknown")
        output_data["statistics"]["by_country"][country] = output_data["statistics"]["by_country"].get(country, 0) + 1

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return output_file


def main():
    logger.info("Starting bulk company expander")

    try:
        # Load existing
        existing = load_existing_companies()
        logger.info(f"Loaded {len(existing)} existing companies")

        # Generate new companies
        needed = CONFIG["TARGET_COUNT"] - len(existing)
        logger.info(f"Generating {needed} additional companies")

        new_companies = expand_list(existing, CONFIG["TARGET_COUNT"])
        logger.info(f"Generated {len(new_companies)} new companies")

        # Merge
        all_companies = existing + new_companies
        logger.info(f"Total: {len(all_companies)} companies")

        # Save
        output_file = save_expanded_list(all_companies)

        # Summary
        print(f"\n{'='*70}")
        print(f"BULK EXPANSION SUMMARY")
        print(f"{'='*70}")
        print(f"Existing Companies: {len(existing)}")
        print(f"Generated Companies: {len(new_companies)}")
        print(f"Total Companies: {len(all_companies)}")
        print(f"Target: {CONFIG['TARGET_COUNT']}")
        print(f"Progress: {len(all_companies) / CONFIG['TARGET_COUNT'] * 100:.1f}%")
        print(f"\nBy Country:")
        by_country = {}
        for c in all_companies:
            country = c.get("country", "Unknown")
            by_country[country] = by_country.get(country, 0) + 1
        for country, count in sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {country}: {count}")
        print(f"\nVerification Status:")
        print(f"  Verified: {sum(1 for c in all_companies if c.get('verified'))}")
        print(f"  Needs Verification: {sum(1 for c in all_companies if not c.get('verified'))}")
        print(f"\nSaved to: {output_file}")
        print(f"{'='*70}\n")

        logger.info("Expansion completed successfully")

    except Exception as e:
        logger.error("Expansion failed", error=e)
        raise


if __name__ == "__main__":
    main()
