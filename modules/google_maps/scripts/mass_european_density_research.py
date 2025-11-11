#!/usr/bin/env python3
"""
=== MASS EUROPEAN MARKET DENSITY RESEARCH ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Mass density research across all European countries (excluding CIS/Baltic States)
to identify Soviet/military history market opportunities at scale.

FEATURES:
- 20+ European countries coverage
- Smart keyword selection per country (local + global)
- Parallel processing for speed
- Real-time cost tracking
- Comprehensive market volume analysis

TARGET:
Find 1500-2000 unique places for downstream enrichment

COST ESTIMATE:
- Text Search: $0.011 per query
- 50-100 keywords × 20 countries = 1000-2000 queries
- Total: $11-22 for density research

USAGE:
1. Configure CONFIG section
2. Run: python mass_european_density_research.py
3. Results saved to results/research/european_mass_v1/

WORKFLOW:
Step 1 (THIS SCRIPT) → Step 2 (Place Details) → Step 3 (Scraping) → Step 4 (AI Analysis)
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from modules.logging.shared.universal_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

RESEARCH_CONFIG = {
    "project_name": "european_mass_v1",
    "output_dir": "results/research/european_mass_v1",

    "api_settings": {
        "delay_between_requests": 0.5,
        "max_workers": 10,
        "retry_attempts": 3,
    },

    # Target countries (excluding CIS and Baltic States)
    "regions": [
        # Central Europe
        {"name": "germany", "location": "Germany", "language": "de"},
        {"name": "poland", "location": "Poland", "language": "pl"},
        {"name": "czech_republic", "location": "Czech Republic", "language": "cs"},
        {"name": "austria", "location": "Austria", "language": "de"},
        {"name": "switzerland", "location": "Switzerland", "language": "de"},
        {"name": "hungary", "location": "Hungary", "language": "hu"},
        {"name": "slovakia", "location": "Slovakia", "language": "sk"},
        {"name": "slovenia", "location": "Slovenia", "language": "sl"},

        # Eastern Europe
        {"name": "romania", "location": "Romania", "language": "ro"},
        {"name": "bulgaria", "location": "Bulgaria", "language": "bg"},
        {"name": "serbia", "location": "Serbia", "language": "sr"},
        {"name": "croatia", "location": "Croatia", "language": "hr"},

        # Western Europe
        {"name": "united_kingdom", "location": "United Kingdom", "language": "en"},
        {"name": "france", "location": "France", "language": "fr"},
        {"name": "netherlands", "location": "Netherlands", "language": "nl"},
        {"name": "belgium", "location": "Belgium", "language": "nl"},

        # Southern Europe
        {"name": "italy", "location": "Italy", "language": "it"},
        {"name": "spain", "location": "Spain", "language": "es"},

        # Northern Europe
        {"name": "sweden", "location": "Sweden", "language": "sv"},
        {"name": "finland", "location": "Finland", "language": "fi"},
    ],
}

# ============================================================================
# KEYWORD STRATEGIES PER COUNTRY
# ============================================================================

def get_keywords_for_country(country_name: str, language: str) -> List[str]:
    """
    Generate smart keyword list for each country.

    Strategy:
    - Global English keywords (work everywhere)
    - Local language translations (better local coverage)
    - War-specific keywords (Cold War, WWII, Afghan, Chechen)
    """

    keywords = []

    # Global English keywords (all countries)
    global_keywords = [
        "military history club",
        "Cold War museum",
        "WWII museum",
        "World War 2 museum",
        "military reenactment",
        "historical reenactment",
        "Soviet memorabilia",
        "military museum",
        "war museum",
        "army museum",
        "military collectibles",
        "military antiques",
        "army surplus",
        "Soviet Army history",
        "Red Army museum",
        "Eastern Front museum",
        "Great Patriotic War",
        "Afghan War museum",
        "Vietnam War museum",
        "Korean War museum",
        "military equipment museum",
        "tank museum",
        "aviation museum",
        "military vehicle museum",
    ]

    keywords.extend(global_keywords)

    # Local language keywords (country-specific)
    local_keywords = {
        "de": [  # German
            "Militärgeschichte Museum",
            "Kalter Krieg Museum",
            "Zweiter Weltkrieg Museum",
            "Militärhistorischer Verein",
            "Geschichtsverein Militär",
            "Sowjetarmee Museum",
            "Rote Armee Museum",
            "Militaria Shop",
            "Militär Sammler",
            "Panzermuseum",
            "Luftfahrtmuseum",
        ],
        "pl": [  # Polish
            "muzeum historii wojskowej",
            "klub historii wojskowej",
            "muzeum zimnej wojny",
            "muzeum II wojny światowej",
            "rekonstrukcja historyczna",
            "militaria sklep",
            "sowiecka armia",
            "Armia Czerwona",
            "muzeum wojskowe",
            "sprzęt wojskowy",
            "czołg muzeum",
        ],
        "cs": [  # Czech
            "muzeum vojenské historie",
            "klub vojenské historie",
            "studená válka muzeum",
            "muzeum druhé světové války",
            "historická rekonstrukce",
            "vojenské muzeum",
            "sovětská armáda",
            "Rudá armáda",
            "vojenská technika",
        ],
        "hu": [  # Hungarian
            "katonai történeti múzeum",
            "hidegháborús múzeum",
            "második világháború múzeum",
            "katonai újrajátszás",
            "szovjet hadsereg",
            "Vörös Hadsereg",
            "katonai múzeum",
        ],
        "ro": [  # Romanian
            "muzeu de istorie militară",
            "club de istorie militară",
            "muzeu război rece",
            "muzeu al doilea război mondial",
            "reconstitutie istorica",
            "armata sovietică",
            "Armata Roșie",
            "muzeu militar",
        ],
        "bg": [  # Bulgarian (Cyrillic, but using Latin transliteration)
            "военноисторически музей",
            "студена война музей",
            "военен музей",
            "съветска армия",
        ],
        "sk": [  # Slovak
            "múzeum vojenskej histórie",
            "klub vojenskej histórie",
            "studená vojna múzeum",
            "vojenské múzeum",
            "sovietska armáda",
        ],
        "sl": [  # Slovenian
            "muzej vojaške zgodovine",
            "klub vojaške zgodovine",
            "muzej hladne vojne",
            "vojaški muzej",
        ],
        "sr": [  # Serbian
            "vojni muzej",
            "muzej hladnog rata",
            "vojni klub",
        ],
        "hr": [  # Croatian
            "vojni muzej",
            "muzej hladnog rata",
            "povijest rata",
        ],
        "fr": [  # French
            "musée d'histoire militaire",
            "musée guerre froide",
            "musée seconde guerre mondiale",
            "reconstitution historique",
            "armée soviétique",
            "Armée rouge",
            "musée militaire",
            "matériel militaire",
        ],
        "nl": [  # Dutch
            "militair historisch museum",
            "Koude Oorlog museum",
            "Tweede Wereldoorlog museum",
            "historische re-enactment",
            "militair museum",
            "Sovjet leger",
        ],
        "it": [  # Italian
            "museo di storia militare",
            "museo guerra fredda",
            "museo seconda guerra mondiale",
            "rievocazione storica",
            "museo militare",
            "esercito sovietico",
        ],
        "es": [  # Spanish
            "museo de historia militar",
            "museo guerra fría",
            "museo segunda guerra mundial",
            "recreación histórica",
            "museo militar",
            "ejército soviético",
        ],
        "sv": [  # Swedish
            "militärhistoriskt museum",
            "kalla krigets museum",
            "andra världskriget museum",
            "militärt museum",
        ],
        "fi": [  # Finnish
            "sotahistoriallinen museo",
            "kylmän sodan museo",
            "toisen maailmansodan museo",
            "sotilasmuseo",
        ],
    }

    # Add local keywords if available
    if language in local_keywords:
        keywords.extend(local_keywords[language])

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw.lower() not in seen:
            seen.add(kw.lower())
            unique_keywords.append(kw)

    return unique_keywords

# ============================================================================
# GOOGLE PLACES API CLIENT
# ============================================================================

class MassResearchClient:
    """Client for mass density research across multiple regions"""

    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_results": 0,
            "total_cost": 0.0,
            "by_country": defaultdict(lambda: {"queries": 0, "results": 0, "cost": 0.0}),
        }

    def text_search(self, query: str, location: str, country: str) -> List[Dict]:
        """
        Perform text search for a query in specific location.

        Cost: $0.011 per query (Text Search Basic)
        """
        endpoint = f"{self.BASE_URL}/textsearch/json"

        params = {
            "query": f"{query} in {location}",
            "key": self.api_key,
        }

        all_results = []

        try:
            while True:
                response = self.session.get(endpoint, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                if data.get("status") == "ZERO_RESULTS":
                    break

                if data.get("status") != "OK":
                    logger.warning(f"Search error for '{query}' in {location}", status=data.get("status"))
                    self.stats["failed_queries"] += 1
                    self.stats["by_country"][country]["queries"] += 1
                    break

                results = data.get("results", [])
                all_results.extend(results)

                # Track stats
                self.stats["total_queries"] += 1
                self.stats["successful_queries"] += 1
                self.stats["total_results"] += len(results)
                self.stats["total_cost"] += 0.011
                self.stats["by_country"][country]["queries"] += 1
                self.stats["by_country"][country]["results"] += len(results)
                self.stats["by_country"][country]["cost"] += 0.011

                # Check for next page
                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break

                # Wait for next page token to activate
                time.sleep(2)
                params = {"pagetoken": next_page_token, "key": self.api_key}

            return all_results

        except Exception as e:
            logger.error(f"Search failed for '{query}' in {location}", error=str(e))
            self.stats["failed_queries"] += 1
            self.stats["by_country"][country]["queries"] += 1
            return []

    def get_stats(self) -> Dict:
        """Get research statistics"""
        return {
            "total_queries": self.stats["total_queries"],
            "successful_queries": self.stats["successful_queries"],
            "failed_queries": self.stats["failed_queries"],
            "total_results": self.stats["total_results"],
            "total_cost_usd": round(self.stats["total_cost"], 2),
            "by_country": dict(self.stats["by_country"]),
        }

# ============================================================================
# MASS RESEARCH EXECUTION
# ============================================================================

def research_single_keyword(client: MassResearchClient, keyword: str, region: Dict, config: Dict) -> Dict:
    """Research a single keyword in a specific region"""
    country = region["name"]
    location = region["location"]

    results = client.text_search(keyword, location, country)

    # Add metadata
    for result in results:
        result["source_keyword"] = keyword
        result["source_country"] = country
        result["source_location"] = location

    time.sleep(config["api_settings"]["delay_between_requests"])

    return {
        "keyword": keyword,
        "country": country,
        "results_count": len(results),
        "results": results,
    }

def research_all_regions(client: MassResearchClient, config: Dict) -> Dict:
    """Execute research across all regions with parallel processing"""

    all_results = defaultdict(lambda: defaultdict(list))
    total_tasks = 0
    completed_tasks = 0

    # Calculate total tasks
    for region in config["regions"]:
        keywords = get_keywords_for_country(region["name"], region["language"])
        total_tasks += len(keywords)

    logger.info(f"Starting mass research: {len(config['regions'])} countries, {total_tasks} total queries")
    logger.info(f"Estimated cost: ${total_tasks * 0.011:.2f}")

    # Execute research with parallel processing
    with ThreadPoolExecutor(max_workers=config["api_settings"]["max_workers"]) as executor:
        futures = []

        for region in config["regions"]:
            keywords = get_keywords_for_country(region["name"], region["language"])

            logger.info(f"Queuing {len(keywords)} keywords for {region['location']}")

            for keyword in keywords:
                future = executor.submit(research_single_keyword, client, keyword, region, config)
                futures.append(future)

        # Process results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                completed_tasks += 1

                country = result["country"]
                keyword = result["keyword"]
                count = result["results_count"]

                # Store results
                all_results[country][keyword] = result["results"]

                # Progress update
                progress_pct = (completed_tasks / total_tasks) * 100
                print(f"[{completed_tasks}/{total_tasks}] ({progress_pct:.1f}%) {country}: '{keyword}' = {count} results")

                # Stats every 50 queries
                if completed_tasks % 50 == 0:
                    stats = client.get_stats()
                    logger.info(f"Progress: {completed_tasks}/{total_tasks} | Results: {stats['total_results']} | Cost: ${stats['total_cost_usd']}")

            except Exception as e:
                logger.error(f"Task failed: {str(e)}")
                completed_tasks += 1

    return dict(all_results)

# ============================================================================
# SAVE RESULTS
# ============================================================================

def save_raw_results(results: Dict, config: Dict) -> Path:
    """Save raw results per country"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent.parent / config["output_dir"] / "raw_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    for country, keywords_data in results.items():
        filename = f"{country}_{timestamp}.json"
        output_path = output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(keywords_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {country}: {output_path}")

    return output_dir

def save_summary_report(results: Dict, stats: Dict, config: Dict) -> Path:
    """Generate and save comprehensive summary report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent.parent / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    # Calculate deduplication stats
    all_place_ids = set()
    total_with_duplicates = 0

    for country, keywords_data in results.items():
        for keyword, places in keywords_data.items():
            total_with_duplicates += len(places)
            for place in places:
                all_place_ids.add(place.get("place_id"))

    # Summary report
    summary = {
        "timestamp": timestamp,
        "total_countries": len(results),
        "total_queries": stats["total_queries"],
        "total_results_with_duplicates": total_with_duplicates,
        "unique_place_ids": len(all_place_ids),
        "duplicates_removed": total_with_duplicates - len(all_place_ids),
        "deduplication_rate": round((1 - len(all_place_ids) / max(total_with_duplicates, 1)) * 100, 2),
        "total_cost_usd": stats["total_cost_usd"],
        "cost_per_unique_place": round(stats["total_cost_usd"] / max(len(all_place_ids), 1), 4),
        "by_country": {},
    }

    # Per-country stats
    for country, country_stats in stats["by_country"].items():
        country_results = results.get(country, {})
        country_places = []
        for places in country_results.values():
            country_places.extend(places)

        unique_ids = set(p.get("place_id") for p in country_places)

        summary["by_country"][country] = {
            "queries": country_stats["queries"],
            "results_with_duplicates": country_stats["results"],
            "unique_places": len(unique_ids),
            "cost_usd": country_stats["cost"],
        }

    # Save JSON
    summary_path = output_dir / f"summary_report_{timestamp}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"Summary report saved: {summary_path}")

    return summary_path

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 80)
    logger.info("MASS EUROPEAN DENSITY RESEARCH")
    logger.info("=" * 80)

    # Check API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env")
        return

    # Initialize client
    client = MassResearchClient(api_key)

    # Show plan
    total_queries = sum(len(get_keywords_for_country(r["name"], r["language"])) for r in RESEARCH_CONFIG["regions"])

    logger.info("")
    logger.info("RESEARCH PLAN:")
    logger.info(f"Countries: {len(RESEARCH_CONFIG['regions'])}")
    logger.info(f"Total queries: {total_queries}")
    logger.info(f"Estimated cost: ${total_queries * 0.011:.2f}")
    logger.info(f"Parallel workers: {RESEARCH_CONFIG['api_settings']['max_workers']}")
    logger.info("")

    # Execute research
    logger.info("Starting research...")
    start_time = time.time()

    results = research_all_regions(client, RESEARCH_CONFIG)

    elapsed_time = time.time() - start_time

    # Save results
    logger.info("")
    logger.info("=" * 80)
    logger.info("SAVING RESULTS")
    logger.info("=" * 80)

    raw_dir = save_raw_results(results, RESEARCH_CONFIG)
    stats = client.get_stats()
    summary_path = save_summary_report(results, stats, RESEARCH_CONFIG)

    # Final stats
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESEARCH COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Total queries: {stats['total_queries']}")
    logger.info(f"Total results: {stats['total_results']}")
    logger.info(f"Total cost: ${stats['total_cost_usd']}")
    logger.info(f"Execution time: {elapsed_time/60:.1f} minutes")
    logger.info("")
    logger.info(f"Raw results: {raw_dir}")
    logger.info(f"Summary report: {summary_path}")
    logger.info("=" * 80)
    logger.info("")
    logger.info("NEXT STEP: Review summary report and proceed to Step 2 (Place Details Enrichment)")
    logger.info("")

if __name__ == "__main__":
    main()
