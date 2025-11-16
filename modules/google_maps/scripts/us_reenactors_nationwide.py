#!/usr/bin/env python3
"""
=== US REENACTORS NATIONWIDE DENSITY RESEARCH ===
Version: 1.0.0 | Created: 2025-01-16

PURPOSE:
Find ALL Soviet/Eastern Front reenactment groups across United States.
Focus on reenactors ONLY (highest conversion for Soviet boots).

STRATEGY:
Phase 1: Reenactors ONLY (this script)
Phase 2: Soviet militaria stores (later, if needed)
Phase 3: Select museums (optional)

WHY REENACTORS FIRST:
- Highest conversion (80%+ interested in Soviet boots)
- Real buyers with budget ($500-1,500 per uniform)
- NOT asking for donations like museums
- US reenactment = commercial industry
- Repeat customers (events year-round)

FEATURES:
- All 50 US states coverage
- 10 reenactor-specific keywords
- Parallel processing
- Real-time cost tracking
- State-by-state analysis

COST ESTIMATE:
- 10 keywords x 50 states = 500 queries
- Text Search: $0.011 per query
- Total: ~$5.50

EXPECTED RESULTS:
- 1,500-2,500 reenactor groups nationwide
- 60-80% conversion rate
- 900-2,000 deliverable emails after enrichment

USAGE:
1. Run: python us_reenactors_nationwide.py
2. Results: results/research/us_reenactors_v1/
3. Next: Place Details enrichment for top states

IMPROVEMENTS:
v1.0.0 - Initial nationwide reenactor search
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict
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
    "project_name": "us_reenactors_v1",
    "output_dir": "results/research/us_reenactors_v1",

    "api_settings": {
        "delay_between_requests": 0.1,  # Minimal delay
        "max_workers": 50,  # Maximum parallel processing
        "retry_attempts": 3,
    },

    # All 50 US states
    "states": [
        # Northeast
        {"name": "maine", "location": "Maine, USA"},
        {"name": "new_hampshire", "location": "New Hampshire, USA"},
        {"name": "vermont", "location": "Vermont, USA"},
        {"name": "massachusetts", "location": "Massachusetts, USA"},
        {"name": "rhode_island", "location": "Rhode Island, USA"},
        {"name": "connecticut", "location": "Connecticut, USA"},
        {"name": "new_york", "location": "New York, USA"},
        {"name": "new_jersey", "location": "New Jersey, USA"},
        {"name": "pennsylvania", "location": "Pennsylvania, USA"},

        # Southeast
        {"name": "delaware", "location": "Delaware, USA"},
        {"name": "maryland", "location": "Maryland, USA"},
        {"name": "virginia", "location": "Virginia, USA"},
        {"name": "west_virginia", "location": "West Virginia, USA"},
        {"name": "north_carolina", "location": "North Carolina, USA"},
        {"name": "south_carolina", "location": "South Carolina, USA"},
        {"name": "georgia", "location": "Georgia, USA"},
        {"name": "florida", "location": "Florida, USA"},

        # Midwest
        {"name": "ohio", "location": "Ohio, USA"},
        {"name": "michigan", "location": "Michigan, USA"},
        {"name": "indiana", "location": "Indiana, USA"},
        {"name": "illinois", "location": "Illinois, USA"},
        {"name": "wisconsin", "location": "Wisconsin, USA"},
        {"name": "minnesota", "location": "Minnesota, USA"},
        {"name": "iowa", "location": "Iowa, USA"},
        {"name": "missouri", "location": "Missouri, USA"},
        {"name": "kentucky", "location": "Kentucky, USA"},
        {"name": "tennessee", "location": "Tennessee, USA"},
        {"name": "alabama", "location": "Alabama, USA"},
        {"name": "mississippi", "location": "Mississippi, USA"},
        {"name": "louisiana", "location": "Louisiana, USA"},
        {"name": "arkansas", "location": "Arkansas, USA"},

        # Great Plains
        {"name": "north_dakota", "location": "North Dakota, USA"},
        {"name": "south_dakota", "location": "South Dakota, USA"},
        {"name": "nebraska", "location": "Nebraska, USA"},
        {"name": "kansas", "location": "Kansas, USA"},
        {"name": "oklahoma", "location": "Oklahoma, USA"},

        # Southwest
        {"name": "texas", "location": "Texas, USA"},
        {"name": "new_mexico", "location": "New Mexico, USA"},
        {"name": "arizona", "location": "Arizona, USA"},

        # West
        {"name": "colorado", "location": "Colorado, USA"},
        {"name": "utah", "location": "Utah, USA"},
        {"name": "nevada", "location": "Nevada, USA"},
        {"name": "california", "location": "California, USA"},
        {"name": "oregon", "location": "Oregon, USA"},
        {"name": "washington", "location": "Washington, USA"},
        {"name": "idaho", "location": "Idaho, USA"},
        {"name": "montana", "location": "Montana, USA"},
        {"name": "wyoming", "location": "Wyoming, USA"},
        {"name": "alaska", "location": "Alaska, USA"},
        {"name": "hawaii", "location": "Hawaii, USA"},
    ],
}

# ============================================================================
# REENACTOR-SPECIFIC KEYWORDS
# ============================================================================

def get_reenactor_keywords() -> List[str]:
    """
    Reenactor-focused keywords ONLY.

    Strategy:
    - Soviet/Russian/Eastern Front specific
    - WWII reenactment (many groups have Eastern Front units)
    - Historical/living history (includes reenactment clubs)
    - NO army surplus, NO generic military stores
    """

    keywords = [
        # TIER 1: Soviet/Eastern Front specific (highest relevance)
        "Soviet reenactment",
        "Red Army reenactment",
        "Eastern Front reenactment",
        "Russian reenactment",

        # TIER 2: WWII reenactment (broad, but includes Eastern Front)
        "WWII reenactment",
        "World War 2 reenactment",
        "WW2 reenactment",

        # TIER 3: Historical/living history (includes reenactment)
        "historical reenactment",
        "living history",
        "military reenactment",
    ]

    logger.info(f"Total reenactor keywords: {len(keywords)}")
    logger.info(f"  - Tier 1 (Soviet/Eastern Front): 4")
    logger.info(f"  - Tier 2 (WWII general): 3")
    logger.info(f"  - Tier 3 (Historical): 3")

    return keywords

# ============================================================================
# GOOGLE PLACES API CLIENT
# ============================================================================

class ReenactorResearchClient:
    """Client for nationwide reenactor research"""

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
            "by_state": defaultdict(lambda: {"queries": 0, "results": 0, "cost": 0.0}),
            "by_keyword": defaultdict(lambda: {"queries": 0, "results": 0}),
        }

    def text_search(self, query: str, location: str, state_name: str) -> List[Dict]:
        """
        Perform text search for a query in specific state.

        Returns basic data only (NO contact fields):
        - place_id, name, rating, user_ratings_total, types, geometry

        Cost: $0.011 per query
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
                    logger.warning(f"Search error: {query} in {state_name}", status=data.get("status"))
                    self.stats["failed_queries"] += 1
                    self.stats["by_state"][state_name]["queries"] += 1
                    self.stats["by_keyword"][query]["queries"] += 1
                    break

                results = data.get("results", [])
                all_results.extend(results)

                # Track stats
                self.stats["total_queries"] += 1
                self.stats["successful_queries"] += 1
                self.stats["total_results"] += len(results)
                self.stats["total_cost"] += 0.011
                self.stats["by_state"][state_name]["queries"] += 1
                self.stats["by_state"][state_name]["results"] += len(results)
                self.stats["by_state"][state_name]["cost"] += 0.011
                self.stats["by_keyword"][query]["queries"] += 1
                self.stats["by_keyword"][query]["results"] += len(results)

                # Check for next page
                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break

                # Wait for next page token
                time.sleep(2)
                params = {"pagetoken": next_page_token, "key": self.api_key}

            return all_results

        except Exception as e:
            logger.error(f"Search failed: {query} in {state_name}", error=str(e))
            self.stats["failed_queries"] += 1
            self.stats["by_state"][state_name]["queries"] += 1
            return []

    def get_stats(self) -> Dict:
        """Get research statistics"""
        return {
            "total_queries": self.stats["total_queries"],
            "successful_queries": self.stats["successful_queries"],
            "failed_queries": self.stats["failed_queries"],
            "total_results": self.stats["total_results"],
            "total_cost_usd": round(self.stats["total_cost"], 2),
            "by_state": dict(self.stats["by_state"]),
            "by_keyword": dict(self.stats["by_keyword"]),
        }

# ============================================================================
# RESEARCH EXECUTION
# ============================================================================

def research_single_task(client: ReenactorResearchClient, keyword: str, state: Dict) -> Dict:
    """Research a single keyword in a single state"""

    state_name = state["name"]
    location = state["location"]

    results = client.text_search(keyword, location, state_name)

    # Add metadata
    for result in results:
        result["source_keyword"] = keyword
        result["source_state"] = state_name
        result["source_location"] = location

    time.sleep(RESEARCH_CONFIG["api_settings"]["delay_between_requests"])

    return {
        "keyword": keyword,
        "state": state_name,
        "results_count": len(results),
        "results": results,
    }

def research_nationwide(client: ReenactorResearchClient, keywords: List[str], states: List[Dict]) -> Dict:
    """Execute nationwide research with parallel processing"""

    all_results = defaultdict(lambda: defaultdict(list))
    total_tasks = len(keywords) * len(states)
    completed_tasks = 0

    logger.info(f"Starting nationwide reenactor research")
    logger.info(f"Keywords: {len(keywords)}")
    logger.info(f"States: {len(states)}")
    logger.info(f"Total tasks: {total_tasks}")
    logger.info(f"Estimated cost: ${total_tasks * 0.011:.2f}")
    logger.info("")

    # Execute research with parallel processing
    with ThreadPoolExecutor(max_workers=RESEARCH_CONFIG["api_settings"]["max_workers"]) as executor:
        futures = {}

        for state in states:
            for keyword in keywords:
                future = executor.submit(research_single_task, client, keyword, state)
                futures[future] = (state["name"], keyword)

        # Process results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                completed_tasks += 1

                state_name = result["state"]
                keyword = result["keyword"]
                count = result["results_count"]

                # Store results
                all_results[state_name][keyword] = result["results"]

                # Progress update
                progress_pct = (completed_tasks / total_tasks) * 100
                if count > 0:
                    print(f"[{completed_tasks}/{total_tasks}] ({progress_pct:.1f}%) {state_name}: '{keyword}' = {count} results")

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
    """Save raw results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent.parent / config["output_dir"] / "raw_results"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save per-state files
    for state, keywords_data in results.items():
        filename = f"{state}_{timestamp}.json"
        output_path = output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(keywords_data, f, indent=2, ensure_ascii=False)

    logger.info(f"Raw results saved to: {output_dir}")
    return output_dir

def save_state_analysis(client: ReenactorResearchClient, results: Dict, config: Dict) -> Path:
    """Analyze results by state"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent.parent / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    # State-by-state analysis
    state_performance = []

    for state_name, state_stats in client.stats["by_state"].items():
        state_data = results.get(state_name, {})
        all_places = []
        for places in state_data.values():
            all_places.extend(places)

        # Unique place_ids
        unique_ids = set(p.get("place_id") for p in all_places)

        # Quality metrics
        if all_places:
            avg_rating = sum(p.get("rating", 0) for p in all_places) / len(all_places)
            avg_reviews = sum(p.get("user_ratings_total", 0) for p in all_places) / len(all_places)
        else:
            avg_rating = 0
            avg_reviews = 0

        state_performance.append({
            "state": state_name,
            "queries": state_stats["queries"],
            "total_results": state_stats["results"],
            "unique_places": len(unique_ids),
            "avg_rating": round(avg_rating, 2),
            "avg_reviews": round(avg_reviews, 0),
            "cost_usd": round(state_stats["cost"], 2),
        })

    # Sort by unique places
    state_performance.sort(key=lambda x: x["unique_places"], reverse=True)

    # Save analysis
    analysis_path = output_dir / f"state_analysis_{timestamp}.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_states": len(state_performance),
            "state_performance": state_performance,
            "top_10_states": state_performance[:10],
            "states_with_no_results": [s for s in state_performance if s["unique_places"] == 0],
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"State analysis saved: {analysis_path}")
    return analysis_path

def save_keyword_analysis(client: ReenactorResearchClient, config: Dict) -> Path:
    """Analyze keyword performance"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent.parent / config["output_dir"]

    keyword_performance = []

    for keyword, keyword_stats in client.stats["by_keyword"].items():
        keyword_performance.append({
            "keyword": keyword,
            "total_results": keyword_stats["results"],
            "states_with_results": keyword_stats["queries"],  # Queries = states searched
            "avg_per_state": round(keyword_stats["results"] / max(keyword_stats["queries"], 1), 1),
        })

    # Sort by total results
    keyword_performance.sort(key=lambda x: x["total_results"], reverse=True)

    # Save
    analysis_path = output_dir / f"keyword_analysis_{timestamp}.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "keyword_performance": keyword_performance,
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"Keyword analysis saved: {analysis_path}")
    return analysis_path

def save_summary_report(results: Dict, stats: Dict, config: Dict) -> Path:
    """Generate summary report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent.parent / config["output_dir"]

    # Calculate deduplication
    all_place_ids = set()
    total_with_duplicates = 0

    for state, keywords_data in results.items():
        for keyword, places in keywords_data.items():
            total_with_duplicates += len(places)
            for place in places:
                all_place_ids.add(place.get("place_id"))

    summary = {
        "timestamp": timestamp,
        "scope": "United States - All 50 states",
        "focus": "Reenactors ONLY (Soviet/Eastern Front)",
        "total_states": len(config["states"]),
        "total_keywords": 10,
        "total_queries": stats["total_queries"],
        "successful_queries": stats["successful_queries"],
        "failed_queries": stats["failed_queries"],
        "total_results_with_duplicates": total_with_duplicates,
        "unique_place_ids": len(all_place_ids),
        "duplicates_removed": total_with_duplicates - len(all_place_ids),
        "deduplication_rate_pct": round((1 - len(all_place_ids) / max(total_with_duplicates, 1)) * 100, 2),
        "total_cost_usd": stats["total_cost_usd"],
        "cost_per_unique_place": round(stats["total_cost_usd"] / max(len(all_place_ids), 1), 4),
        "next_steps": {
            "1": "Review state_analysis.json to see top states",
            "2": "Select top 10-15 states for Place Details enrichment",
            "3": "Run email scraping + AI analysis",
            "4": "Upload to Instantly for outreach"
        }
    }

    summary_path = output_dir / f"summary_report_{timestamp}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"Summary saved: {summary_path}")
    return summary_path

def print_final_summary(summary: Dict, state_analysis_path: Path):
    """Print results"""
    print("\n" + "=" * 80)
    print("US REENACTORS NATIONWIDE RESEARCH - RESULTS")
    print("=" * 80)
    print(f"\nSCOPE: {summary['scope']}")
    print(f"FOCUS: {summary['focus']}")
    print(f"\nQUERIES: {summary['total_queries']} ({summary['successful_queries']} successful)")
    print(f"\nRESULTS:")
    print(f"  - Total (with duplicates): {summary['total_results_with_duplicates']}")
    print(f"  - Unique reenactor groups: {summary['unique_place_ids']}")
    print(f"  - Deduplication rate: {summary['deduplication_rate_pct']}%")
    print(f"\nCOST: ${summary['total_cost_usd']}")
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print(f"1. Review state analysis: {state_analysis_path}")
    print("2. Select top 10-15 states for enrichment")
    print("3. Run Place Details API for contact info")
    print("4. Email scraping + AI analysis")
    print("=" * 80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 80)
    logger.info("US REENACTORS NATIONWIDE DENSITY RESEARCH")
    logger.info("=" * 80)

    # Check API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env")
        return

    # Initialize client
    client = ReenactorResearchClient(api_key)

    # Get keywords and states
    keywords = get_reenactor_keywords()
    states = RESEARCH_CONFIG["states"]

    # Execute research
    logger.info("Starting nationwide research...")
    start_time = time.time()

    results = research_nationwide(client, keywords, states)

    elapsed_time = time.time() - start_time

    # Get stats
    stats = client.get_stats()

    # Save results
    logger.info("")
    logger.info("=" * 80)
    logger.info("SAVING RESULTS")
    logger.info("=" * 80)

    raw_dir = save_raw_results(results, RESEARCH_CONFIG)
    state_analysis_path = save_state_analysis(client, results, RESEARCH_CONFIG)
    keyword_analysis_path = save_keyword_analysis(client, RESEARCH_CONFIG)
    summary_path = save_summary_report(results, stats, RESEARCH_CONFIG)

    # Load summary
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    # Print final summary
    print_final_summary(summary, state_analysis_path)

    logger.info(f"Research completed in {elapsed_time/60:.1f} minutes")
    logger.info(f"Results saved to: {RESEARCH_CONFIG['output_dir']}")

if __name__ == "__main__":
    main()
