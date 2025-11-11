#!/usr/bin/env python3
"""
=== MARKET RESEARCH DENSITY MAPPER ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Map market density across regions and keywords WITHOUT expensive Place Details calls
Perfect for estimating market volume before investing in full lead collection

FEATURES:
- Multi-region testing (Poland, Czech Republic, USA, etc.)
- Multi-keyword testing (local + global languages)
- Only Text Search (cheap) - NO Place Details (expensive)
- Density summary table (results per keyword/region)
- Raw results saved for later enrichment
- Cost tracking

COST:
Text Search only: $0.032/1000 = ~$0.000032 per result
Example: 50 queries × 20 results = $0.05 total (practically free!)

USAGE:
1. Configure RESEARCH_CONFIG below
2. Run: python market_research_density.py
3. Review density_summary.csv
4. Use raw results for enrichment later

WORKFLOW:
Step 1: Run this script (density mapping)
Step 2: Analyze density_summary.csv
Step 3: Choose best keywords/regions
Step 4: Run google_maps_api_scraper.py with selected queries (full enrichment)

IMPROVEMENTS:
v1.0.0 - Initial version
"""

import os
import sys
import time
import json
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

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
# RESEARCH CONFIGURATION
# ============================================================================

RESEARCH_CONFIG = {
    "project_name": "soviet_reenactment_clubs_v2",

    "regions": [
        {"name": "poland", "location": "Poland"},
        {"name": "czech_republic", "location": "Czech Republic"},
    ],

    "keywords": {
        "local_polish": [
            "klub rekonstrukcji historycznej",
            "rekonstrukcja armii radzieckiej",
            "klub historii wojskowej ZSRR",
            "rekonstrukcja wojskowa",
            "grupa rekonstrukcyjna",
            "stowarzyszenie historyczne",
        ],
        "local_czech": [
            "historicka rekonstrukce",
            "vojenska historie",
            "klub vojenske historie",
            "rekonstrukcni skupina",
        ],
        "global_english": [
            "soviet reenactment club",
            "red army reenactment",
            "ww2 soviet reenactment",
            "military history club",
            "historical reenactment society",
            "soviet military enthusiasts",
            "eastern front reenactment",
        ],
        "specific_soviet": [
            "soviet army club",
            "red army society",
            "USSR history club",
            "soviet military equipment",
            "soviet uniforms",
            "soviet tanks club",
        ],
        "war_periods": [
            "world war 2 reenactment",
            "cold war reenactment",
            "soviet military history",
            "ww2 eastern front",
            "great patriotic war",
            "second world war soviet",
        ],
        "specific_conflicts": [
            "afghan war reenactment",
            "afghanistan soviet war",
            "chechen war reenactment",
            "soviet afghanistan veterans",
        ]
    },

    "api_settings": {
        "max_results_per_query": 60,
        "delay_between_queries": 2,
        "save_raw_results": True,
    }
}

# ============================================================================
# GOOGLE MAPS API CLIENT
# ============================================================================

class GoogleMapsResearchClient:
    """Lightweight client for market research (Text Search only)"""

    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.stats = {
            "total_queries": 0,
            "total_results": 0,
            "total_cost": 0.0,
            "errors": 0,
        }

    def text_search(self, query: str, location: str = None, page_token: str = None) -> Dict:
        """
        Search for places by text query

        Cost: $0.032/1000 requests
        Returns: Basic info (place_id, name, address, rating, types) - FREE fields
        """
        endpoint = f"{self.BASE_URL}/textsearch/json"

        full_query = f"{query} {location}" if location else query

        params = {
            "query": full_query,
            "key": self.api_key,
        }

        if page_token:
            params["pagetoken"] = page_token

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get("status") not in ["OK", "ZERO_RESULTS"]:
                logger.error(f"API error: {data.get('status')}", error_message=data.get("error_message"))
                self.stats["errors"] += 1
                return {"results": [], "status": data.get("status")}

            self.stats["total_queries"] += 1
            self.stats["total_cost"] += 0.032

            results = data.get("results", [])
            self.stats["total_results"] += len(results)

            return data

        except Exception as e:
            logger.error("Text search failed", error=str(e))
            self.stats["errors"] += 1
            return {"results": [], "status": "ERROR"}

    def search_all_pages(self, query: str, location: str, max_results: int = 60) -> List[Dict]:
        """
        Search and paginate through all results

        Note: Google returns max 60 results (3 pages × 20)
        """
        all_results = []
        next_page_token = None
        page = 1

        while len(all_results) < max_results:
            logger.info(f"Query: '{query} {location}' - Page {page}")

            data = self.text_search(query, location, page_token=next_page_token)

            if data.get("status") == "ZERO_RESULTS":
                logger.info("No results found")
                break

            results = data.get("results", [])
            if not results:
                break

            all_results.extend(results)
            logger.info(f"  → Found {len(results)} results (total: {len(all_results)})")

            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break

            if len(all_results) >= max_results:
                break

            page += 1
            time.sleep(2)

        return all_results[:max_results]

    def get_stats(self) -> Dict:
        """Get research statistics"""
        return {
            "total_queries": self.stats["total_queries"],
            "total_results": self.stats["total_results"],
            "avg_results_per_query": round(self.stats["total_results"] / max(self.stats["total_queries"], 1), 1),
            "total_cost_usd": round(self.stats["total_cost"], 2),
            "errors": self.stats["errors"],
        }

# ============================================================================
# RESEARCH ENGINE
# ============================================================================

def run_research(config: Dict, api_key: str) -> Dict:
    """
    Run complete market research across all regions and keywords

    Returns:
        {
            "density_map": [{"region": ..., "keyword": ..., "count": ...}],
            "raw_results": {region: {keyword: [results]}},
            "stats": {...}
        }
    """
    client = GoogleMapsResearchClient(api_key)

    density_map = []
    raw_results = {}

    # Get all keywords (flatten all categories)
    all_keywords = []
    for category, keywords in config["keywords"].items():
        for keyword in keywords:
            all_keywords.append({
                "keyword": keyword,
                "category": category
            })

    total_combinations = len(config["regions"]) * len(all_keywords)
    current = 0

    logger.info(f"Starting market research: {len(config['regions'])} regions × {len(all_keywords)} keywords = {total_combinations} searches")
    logger.info("=" * 80)

    # Iterate through all regions
    for region_info in config["regions"]:
        region_name = region_info["name"]
        location = region_info["location"]

        raw_results[region_name] = {}

        logger.info(f"\n📍 REGION: {region_name.upper()} ({location})")
        logger.info("-" * 80)

        # Iterate through all keywords
        for kw_info in all_keywords:
            keyword = kw_info["keyword"]
            category = kw_info["category"]

            current += 1

            logger.info(f"\n[{current}/{total_combinations}] Testing: '{keyword}' in {location}")

            # Search
            results = client.search_all_pages(
                query=keyword,
                location=location,
                max_results=config["api_settings"]["max_results_per_query"]
            )

            # Record density
            density_entry = {
                "region": region_name,
                "location": location,
                "keyword": keyword,
                "category": category,
                "results_count": len(results),
                "timestamp": datetime.now().isoformat()
            }
            density_map.append(density_entry)

            # Store raw results
            if keyword not in raw_results[region_name]:
                raw_results[region_name][keyword] = []
            raw_results[region_name][keyword] = results

            logger.info(f"  ✓ Results: {len(results)}")

            # Delay between queries
            if current < total_combinations:
                delay = config["api_settings"]["delay_between_queries"]
                logger.info(f"  ⏳ Waiting {delay}s before next query...")
                time.sleep(delay)

    return {
        "density_map": density_map,
        "raw_results": raw_results,
        "stats": client.get_stats()
    }

# ============================================================================
# SAVE RESULTS
# ============================================================================

def save_research_results(research_data: Dict, config: Dict):
    """Save research results to files"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = config["project_name"]

    # Create results directory
    results_dir = Path(__file__).parent.parent / "results" / "research" / project_name
    results_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save density summary CSV
    density_df = pd.DataFrame(research_data["density_map"])

    # Add summary statistics
    density_df = density_df.sort_values(["region", "results_count"], ascending=[True, False])

    density_file = results_dir / f"density_summary_{timestamp}.csv"
    density_df.to_csv(density_file, index=False)
    logger.info(f"\n✓ Saved density summary: {density_file}")

    # 2. Save raw results by region (if enabled)
    if config["api_settings"]["save_raw_results"]:
        raw_dir = results_dir / "raw_results"
        raw_dir.mkdir(exist_ok=True)

        for region_name, keywords_data in research_data["raw_results"].items():
            region_file = raw_dir / f"{region_name}_{timestamp}.json"

            with open(region_file, "w", encoding="utf-8") as f:
                json.dump(keywords_data, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Saved raw results: {region_file}")

    # 3. Create analysis summary
    summary = {
        "project": project_name,
        "timestamp": timestamp,
        "total_regions": len(config["regions"]),
        "total_keywords": sum(len(kws) for kws in config["keywords"].values()),
        "total_searches": research_data["stats"]["total_queries"],
        "total_results_found": research_data["stats"]["total_results"],
        "avg_results_per_query": research_data["stats"]["avg_results_per_query"],
        "total_cost_usd": research_data["stats"]["total_cost_usd"],
        "errors": research_data["stats"]["errors"],

        "top_keywords_by_results": density_df.nlargest(10, "results_count")[["keyword", "region", "results_count"]].to_dict("records"),

        "results_by_region": density_df.groupby("region")["results_count"].sum().to_dict(),
        "results_by_category": density_df.groupby("category")["results_count"].sum().to_dict(),
    }

    summary_file = results_dir / f"analysis_summary_{timestamp}.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"✓ Saved analysis summary: {summary_file}")

    return {
        "density_file": density_file,
        "summary_file": summary_file,
        "results_dir": results_dir
    }

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 80)
    logger.info("MARKET RESEARCH DENSITY MAPPER")
    logger.info("=" * 80)

    # Check API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env")
        logger.info("Get API key: https://console.cloud.google.com")
        return

    # Display configuration
    total_keywords = sum(len(kws) for kws in RESEARCH_CONFIG["keywords"].values())
    total_searches = len(RESEARCH_CONFIG["regions"]) * total_keywords
    estimated_cost = total_searches * 0.032

    logger.info(f"\nProject: {RESEARCH_CONFIG['project_name']}")
    logger.info(f"Regions: {len(RESEARCH_CONFIG['regions'])}")
    logger.info(f"Keywords: {total_keywords}")
    logger.info(f"Total searches: {total_searches}")
    logger.info(f"Estimated cost: ${estimated_cost:.2f}")
    logger.info(f"Max results per query: {RESEARCH_CONFIG['api_settings']['max_results_per_query']}")
    logger.info("")

    # Run research
    logger.info("\nStarting research...\n")
    start_time = time.time()

    research_data = run_research(RESEARCH_CONFIG, api_key)

    elapsed_time = time.time() - start_time

    # Save results
    logger.info("\n" + "=" * 80)
    logger.info("SAVING RESULTS")
    logger.info("=" * 80)

    saved_files = save_research_results(research_data, RESEARCH_CONFIG)

    # Final summary
    stats = research_data["stats"]

    logger.info("\n" + "=" * 80)
    logger.info("RESEARCH COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Total searches: {stats['total_queries']}")
    logger.info(f"Total results found: {stats['total_results']}")
    logger.info(f"Average per query: {stats['avg_results_per_query']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info(f"Total cost: ${stats['total_cost_usd']:.2f}")
    logger.info(f"Execution time: {elapsed_time/60:.1f} minutes")
    logger.info("")
    logger.info(f"📊 Density summary: {saved_files['density_file']}")
    logger.info(f"📈 Analysis summary: {saved_files['summary_file']}")
    logger.info(f"📁 All results in: {saved_files['results_dir']}")
    logger.info("=" * 80)
    logger.info("")
    logger.info("NEXT STEPS:")
    logger.info("1. Review density_summary.csv to see results per keyword/region")
    logger.info("2. Identify best performing keywords")
    logger.info("3. Run google_maps_api_scraper.py with chosen keywords for full details")
    logger.info("")

if __name__ == "__main__":
    main()
