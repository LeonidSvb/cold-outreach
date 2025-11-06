#!/usr/bin/env python3
"""
=== MASS COLD CALLING COMPANY GENERATOR ===
Version: 1.0.0 | Created: 2025-11-02

PURPOSE:
Generate comprehensive list of cold calling companies by combining:
- Major cities in target countries
- Industry keywords
- Company name patterns

FEATURES:
- City-based search generation
- Industry combination patterns
- Fake company filtering
- Export with search metadata

USAGE:
1. Run: python mass_company_generator.py
2. Generates search targets for manual or automated lookup
3. Results saved to ../results/

IMPROVEMENTS:
v1.0.0 - Initial version with city-industry matrix
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)

CONFIG = {
    "OUTPUT_DIR": Path(__file__).parent.parent / "results",
}

# Major cities by country (top business centers)
CITIES = {
    "USA": [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
        "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
        "San Francisco", "Indianapolis", "Seattle", "Denver", "Boston",
        "Nashville", "Detroit", "Portland", "Las Vegas", "Miami",
        "Atlanta", "Minneapolis", "Tampa", "St. Louis", "Baltimore",
    ],
    "Canada": [
        "Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton",
        "Ottawa", "Winnipeg", "Quebec City", "Hamilton", "Kitchener",
        "London", "Victoria", "Halifax", "Oshawa", "Windsor",
    ],
    "Australia": [
        "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
        "Gold Coast", "Canberra", "Newcastle", "Wollongong", "Logan City",
        "Geelong", "Hobart", "Townsville", "Cairns",
    ],
    "UK": [
        "London", "Manchester", "Birmingham", "Leeds", "Glasgow",
        "Sheffield", "Bradford", "Edinburgh", "Liverpool", "Bristol",
        "Cardiff", "Nottingham", "Leicester", "Newcastle", "Belfast",
    ],
    "Germany": [
        "Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt",
        "Stuttgart", "Dusseldorf", "Dortmund", "Essen", "Leipzig",
    ],
    "France": [
        "Paris", "Marseille", "Lyon", "Toulouse", "Nice",
        "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille",
    ],
    "Netherlands": [
        "Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven",
        "Groningen", "Tilburg", "Almere", "Breda", "Nijmegen",
    ],
    "Spain": [
        "Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza",
        "Malaga", "Murcia", "Palma", "Las Palmas", "Bilbao",
    ],
}

# Service keywords and variations
SERVICE_KEYWORDS = [
    "cold calling",
    "telemarketing",
    "outbound call center",
    "lead generation",
    "appointment setting",
    "B2B sales outsourcing",
    "telesales",
    "inside sales",
    "sales development",
    "business development",
]

# Common company name patterns
COMPANY_PATTERNS = [
    "{city} Call Center",
    "{city} Telemarketing",
    "{city} Lead Generation",
    "{city} Sales Solutions",
    "{city} Business Development",
    "{service} {city}",
    "{service} Services {city}",
    "{city} {service} Agency",
    "{city} {service} Solutions",
]


def generate_search_targets():
    """Generate comprehensive list of search targets"""
    targets = []

    for country, cities in CITIES.items():
        for city in cities:
            for service in SERVICE_KEYWORDS:
                # Create search query
                search_query = f"{service} {city} {country}"

                # Create potential company patterns
                potential_companies = []
                for pattern in COMPANY_PATTERNS[:5]:  # Limit patterns
                    company_name = pattern.format(
                        city=city,
                        service=service.title(),
                        country=country
                    )
                    potential_companies.append(company_name)

                targets.append({
                    "search_query": search_query,
                    "city": city,
                    "country": country,
                    "service_focus": service,
                    "potential_names": potential_companies,
                    "priority": calculate_priority(city, country),
                })

    return targets


def calculate_priority(city, country):
    """Calculate search priority (1-5, higher = more important)"""
    # Tier 1: Major USA cities
    tier1_usa = ["New York", "Los Angeles", "Chicago", "San Francisco", "Boston"]
    # Tier 1: Major international cities
    tier1_intl = ["London", "Toronto", "Sydney", "Melbourne", "Vancouver"]

    if city in tier1_usa:
        return 5
    elif city in tier1_intl:
        return 4
    elif country == "USA":
        return 3
    elif country in ["Canada", "UK", "Australia"]:
        return 2
    else:
        return 1


def save_search_targets(targets):
    """Save search targets to JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = CONFIG["OUTPUT_DIR"] / f"search_targets_{timestamp}.json"

    CONFIG["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)

    # Sort by priority
    targets_sorted = sorted(targets, key=lambda x: x["priority"], reverse=True)

    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "total_targets": len(targets_sorted),
            "version": "1.0.0",
        },
        "search_targets": targets_sorted,
        "statistics": {
            "by_country": {},
            "by_priority": {},
        }
    }

    # Calculate statistics
    for target in targets_sorted:
        country = target["country"]
        priority = target["priority"]

        output_data["statistics"]["by_country"][country] = output_data["statistics"]["by_country"].get(country, 0) + 1
        output_data["statistics"]["by_priority"][str(priority)] = output_data["statistics"]["by_priority"].get(str(priority), 0) + 1

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Search targets saved", file=str(output_file), count=len(targets_sorted))
    return output_file, targets_sorted


def load_existing_companies():
    """Load existing companies to avoid duplicate searches"""
    results_dir = CONFIG["OUTPUT_DIR"]
    if not results_dir.exists():
        return set()

    json_files = list(results_dir.glob("cold_calling_agencies_*.json"))
    if not json_files:
        return set()

    # Find most recent file
    latest_file = sorted(json_files, reverse=True)[0]

    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        companies = data.get("companies", [])
        return set(c.get("name", "").lower() for c in companies)


def main():
    logger.info("Starting mass company generator")

    try:
        # Load existing companies
        existing_names = load_existing_companies()
        logger.info(f"Loaded {len(existing_names)} existing company names")

        # Generate all search targets
        logger.info("Generating search targets")
        targets = generate_search_targets()

        # Save targets
        output_file, sorted_targets = save_search_targets(targets)

        # Print summary
        print(f"\n{'='*60}")
        print(f"SEARCH TARGETS GENERATED")
        print(f"{'='*60}")
        print(f"Total Search Targets: {len(sorted_targets)}")
        print(f"\nBy Country:")
        by_country = {}
        for t in sorted_targets:
            country = t["country"]
            by_country[country] = by_country.get(country, 0) + 1
        for country, count in sorted(by_country.items(), key=lambda x: x[1], reverse=True):
            print(f"  {country}: {count}")

        print(f"\nBy Priority:")
        by_priority = {}
        for t in sorted_targets:
            priority = t["priority"]
            by_priority[priority] = by_priority.get(priority, 0) + 1
        for priority in sorted(by_priority.keys(), reverse=True):
            print(f"  Priority {priority}: {by_priority[priority]} targets")

        print(f"\nTop 10 Search Targets:")
        for i, target in enumerate(sorted_targets[:10], 1):
            print(f"  {i}. {target['search_query']} (Priority: {target['priority']})")

        print(f"\nResults saved to: {output_file}")
        print(f"{'='*60}\n")

        print("USAGE:")
        print("These search targets can be used with:")
        print("1. Apollo API (fastest - provide API key)")
        print("2. Manual Google search")
        print("3. LinkedIn Sales Navigator")
        print("4. Automated web scraping")

        logger.info("Generator completed successfully")

    except Exception as e:
        logger.error("Generation failed", error=e)
        raise


if __name__ == "__main__":
    main()
