#!/usr/bin/env python3
"""
=== US TEXAS SOVIET BOOTS MARKET DENSITY RESEARCH ===
Version: 1.0.0 | Created: 2025-01-16

PURPOSE:
Density research for Soviet boots market in Texas (test state).
Find militaria stores, reenactment clubs, and museums interested in Soviet military items.

FEATURES:
- Texas-wide coverage (Text Search API)
- Soviet-specific keywords (45 total)
- Parallel processing for speed
- Real-time cost tracking
- Quality analysis (reviews, ratings, keyword performance)

WORKFLOW:
Step 1 (THIS SCRIPT) - Density Research:
  - Text Search for all keywords
  - Get basic data: place_id, name, rating, reviews, types
  - NO contact details (website, phone) yet
  - Analyze which keywords work best

Step 2 (LATER) - Place Details Enrichment:
  - After selecting best keywords
  - Get website, phone, address for top results
  - Cost: $0.023 per place

Step 3 (LATER) - Email Scraping + AI Analysis

COST ESTIMATE (Step 1 only):
- Text Search: $0.011 per query
- 45 keywords = $0.495 (single query per keyword)
- With pagination: ~$1-2 total

USAGE:
1. Run: python us_texas_density_research.py
2. Results: results/research/us_texas_v1/
3. Analyze keyword quality
4. Select best keywords for full US rollout

IMPROVEMENTS:
v1.0.0 - Initial Texas test based on European pipeline
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
    "project_name": "us_texas_v1",
    "output_dir": "results/research/us_texas_v1",

    "api_settings": {
        "delay_between_requests": 0.5,
        "max_workers": 10,
        "retry_attempts": 3,
    },

    # Target region
    "regions": [
        {"name": "texas", "location": "Texas, USA", "language": "en"},
    ],
}

# ============================================================================
# SOVIET-SPECIFIC KEYWORDS FOR US MARKET
# ============================================================================

def get_soviet_keywords() -> List[str]:
    """
    Soviet-specific keywords for US market.

    Strategy:
    - Focus on Soviet/Russian/Eastern Front ONLY
    - Exclude Civil War, Revolutionary War (not Soviet)
    - Include Cold War, WWII Eastern Front, Afghan War
    - Militaria stores that sell Soviet items
    """

    keywords = []

    # TIER 1: Soviet-specific (highest priority)
    tier_1 = [
        # Soviet Reenactment
        "Soviet reenactment",
        "Russian reenactment",
        "Red Army reenactment",
        "Eastern Front reenactment",

        # WWII Eastern Front specific
        "WWII Eastern Front",
        "Battle of Stalingrad",
        "Battle of Kursk",
        "Operation Barbarossa",

        # Soviet Militaria
        "Soviet militaria",
        "Russian militaria",
        "Soviet memorabilia",
        "Soviet collectibles",
        "Eastern Bloc militaria",
    ]

    # TIER 2: Cold War + Afghan War
    tier_2 = [
        # Cold War (Soviet era)
        "Cold War museum",
        "Cold War memorabilia",
        "Cold War collectibles",
        "Soviet Cold War",

        # Afghan War (Soviet conflict 1979-1989)
        "Afghan War memorabilia",
        "Soviet Afghan War",

        # General Soviet military
        "Soviet Army history",
        "Soviet military equipment",
        "Red Army museum",
        "Soviet Army memorabilia",
    ]

    # TIER 3: Militaria stores (broad - many sell Soviet items)
    tier_3 = [
        # Stores
        "military collectibles",
        "military antiques",
        "army surplus",
        "military memorabilia",
        "vintage military",
        "military surplus store",
        "army navy store",
        "militaria shop",

        # Museums with Soviet sections
        "military museum",
        "military equipment museum",
        "tank museum",
        "military vehicle museum",
    ]

    # TIER 4: WWII general (many have Soviet units)
    tier_4 = [
        "WWII reenactment",
        "World War 2 reenactment",
        "WW2 museum",
        "World War II museum",
        "military history club",
        "living history museum",
        "historical reenactment",
    ]

    # Combine all tiers
    keywords.extend(tier_1)
    keywords.extend(tier_2)
    keywords.extend(tier_3)
    keywords.extend(tier_4)

    logger.info(f"Total keywords: {len(keywords)}")
    logger.info(f"  - Tier 1 (Soviet-specific): {len(tier_1)}")
    logger.info(f"  - Tier 2 (Cold War/Afghan): {len(tier_2)}")
    logger.info(f"  - Tier 3 (Militaria stores): {len(tier_3)}")
    logger.info(f"  - Tier 4 (WWII general): {len(tier_4)}")

    return keywords

# ============================================================================
# GOOGLE PLACES API CLIENT
# ============================================================================

class TexasDensityResearchClient:
    """Client for Texas density research"""

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
            "by_keyword": {},
        }

    def text_search(self, query: str, location: str) -> List[Dict]:
        """
        Perform text search for a query in Texas.

        Returns basic data only (NO contact fields):
        - place_id
        - name
        - rating
        - user_ratings_total
        - types
        - geometry (lat/lng)
        - business_status

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
                    logger.info(f"No results for: {query}")
                    break

                if data.get("status") != "OK":
                    logger.warning(f"Search error for '{query}'", status=data.get("status"))
                    self.stats["failed_queries"] += 1
                    break

                results = data.get("results", [])
                all_results.extend(results)

                # Track stats
                self.stats["total_queries"] += 1
                self.stats["successful_queries"] += 1
                self.stats["total_results"] += len(results)
                self.stats["total_cost"] += 0.011

                # Check for next page
                next_page_token = data.get("next_page_token")
                if not next_page_token:
                    break

                # Wait for next page token to activate
                logger.info(f"Getting next page for: {query}")
                time.sleep(2)
                params = {"pagetoken": next_page_token, "key": self.api_key}

            return all_results

        except Exception as e:
            logger.error(f"Search failed for '{query}'", error=str(e))
            self.stats["failed_queries"] += 1
            return []

    def get_stats(self) -> Dict:
        """Get research statistics"""
        return {
            "total_queries": self.stats["total_queries"],
            "successful_queries": self.stats["successful_queries"],
            "failed_queries": self.stats["failed_queries"],
            "total_results": self.stats["total_results"],
            "total_cost_usd": round(self.stats["total_cost"], 2),
        }

# ============================================================================
# RESEARCH EXECUTION
# ============================================================================

def research_single_keyword(client: TexasDensityResearchClient, keyword: str, location: str) -> Dict:
    """Research a single keyword in Texas"""

    results = client.text_search(keyword, location)

    # Add metadata to each result
    for result in results:
        result["source_keyword"] = keyword
        result["source_location"] = location

    # Track keyword performance
    client.stats["by_keyword"][keyword] = {
        "results_count": len(results),
        "avg_rating": round(sum(r.get("rating", 0) for r in results) / max(len(results), 1), 2),
        "avg_reviews": round(sum(r.get("user_ratings_total", 0) for r in results) / max(len(results), 1), 0),
    }

    time.sleep(RESEARCH_CONFIG["api_settings"]["delay_between_requests"])

    return {
        "keyword": keyword,
        "results_count": len(results),
        "results": results,
    }

def research_all_keywords(client: TexasDensityResearchClient, keywords: List[str], location: str) -> Dict:
    """Execute research for all keywords with parallel processing"""

    all_results = {}
    total_tasks = len(keywords)
    completed_tasks = 0

    logger.info(f"Starting Texas research: {total_tasks} keywords")
    logger.info(f"Estimated cost: ${total_tasks * 0.011:.2f}")
    logger.info("")

    # Execute research with parallel processing
    with ThreadPoolExecutor(max_workers=RESEARCH_CONFIG["api_settings"]["max_workers"]) as executor:
        futures = {}

        for keyword in keywords:
            future = executor.submit(research_single_keyword, client, keyword, location)
            futures[future] = keyword

        # Process results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                completed_tasks += 1

                keyword = result["keyword"]
                count = result["results_count"]

                # Store results
                all_results[keyword] = result["results"]

                # Progress update
                progress_pct = (completed_tasks / total_tasks) * 100
                print(f"[{completed_tasks}/{total_tasks}] ({progress_pct:.1f}%) '{keyword}' = {count} results")

                # Stats every 10 queries
                if completed_tasks % 10 == 0:
                    stats = client.get_stats()
                    logger.info(f"Progress: {completed_tasks}/{total_tasks} | Results: {stats['total_results']} | Cost: ${stats['total_cost_usd']}")

            except Exception as e:
                logger.error(f"Task failed: {str(e)}")
                completed_tasks += 1

    return all_results

# ============================================================================
# SAVE RESULTS
# ============================================================================

def save_raw_results(results: Dict, config: Dict) -> Path:
    """Save raw results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent.parent / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"texas_raw_results_{timestamp}.json"
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Raw results saved: {output_path}")
    return output_path

def save_keyword_analysis(client: TexasDensityResearchClient, results: Dict, config: Dict) -> Path:
    """Analyze keyword performance and save report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent.parent / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    # Keyword performance analysis
    keyword_performance = []

    for keyword, keyword_stats in client.stats["by_keyword"].items():
        places = results.get(keyword, [])

        # Calculate quality metrics
        high_rating_count = sum(1 for p in places if p.get("rating", 0) >= 4.0)
        with_reviews_count = sum(1 for p in places if p.get("user_ratings_total", 0) >= 10)

        keyword_performance.append({
            "keyword": keyword,
            "results_count": keyword_stats["results_count"],
            "avg_rating": keyword_stats["avg_rating"],
            "avg_reviews": keyword_stats["avg_reviews"],
            "high_rating_pct": round(high_rating_count / max(len(places), 1) * 100, 1),
            "with_reviews_pct": round(with_reviews_count / max(len(places), 1) * 100, 1),
            "quality_score": round(
                (keyword_stats["avg_rating"] / 5.0 * 40) +
                (min(keyword_stats["avg_reviews"], 100) / 100.0 * 30) +
                (high_rating_count / max(len(places), 1) * 30),
                1
            )
        })

    # Sort by quality score
    keyword_performance.sort(key=lambda x: x["quality_score"], reverse=True)

    # Save keyword analysis
    analysis_path = output_dir / f"keyword_analysis_{timestamp}.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_keywords": len(keyword_performance),
            "keyword_performance": keyword_performance,
            "top_10_keywords": keyword_performance[:10],
            "bottom_10_keywords": keyword_performance[-10:],
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"Keyword analysis saved: {analysis_path}")
    return analysis_path

def save_summary_report(results: Dict, stats: Dict, config: Dict) -> Path:
    """Generate and save comprehensive summary report"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent.parent / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    # Calculate deduplication stats
    all_place_ids = set()
    total_with_duplicates = 0

    for keyword, places in results.items():
        total_with_duplicates += len(places)
        for place in places:
            all_place_ids.add(place.get("place_id"))

    # Summary report
    summary = {
        "timestamp": timestamp,
        "state": "Texas",
        "total_keywords": len(results),
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
            "1": "Review keyword_analysis.json to see which keywords performed best",
            "2": "Select top 15-20 keywords for full US rollout",
            "3": "Run Place Details enrichment (cost: $0.023 per place)",
            "4": "Email scraping + AI analysis pipeline"
        }
    }

    # Save JSON
    summary_path = output_dir / f"summary_report_{timestamp}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    logger.info(f"Summary report saved: {summary_path}")

    return summary_path

def print_final_summary(summary: Dict, keyword_analysis_path: Path):
    """Print human-readable summary"""
    print("\n" + "=" * 80)
    print("TEXAS SOVIET BOOTS MARKET DENSITY RESEARCH - RESULTS")
    print("=" * 80)
    print(f"\nTOTAL QUERIES: {summary['total_queries']}")
    print(f"SUCCESSFUL: {summary['successful_queries']}")
    print(f"FAILED: {summary['failed_queries']}")
    print(f"\nRESULTS:")
    print(f"  - Total (with duplicates): {summary['total_results_with_duplicates']}")
    print(f"  - Unique places: {summary['unique_place_ids']}")
    print(f"  - Duplicates removed: {summary['duplicates_removed']}")
    print(f"  - Deduplication rate: {summary['deduplication_rate_pct']}%")
    print(f"\nCOST:")
    print(f"  - Total: ${summary['total_cost_usd']}")
    print(f"  - Per unique place: ${summary['cost_per_unique_place']}")
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print(f"1. Review keyword analysis: {keyword_analysis_path}")
    print("2. Select top 15-20 keywords based on quality_score")
    print("3. Run full US density research with best keywords")
    print("4. Then: Place Details enrichment → Email scraping → AI analysis")
    print("=" * 80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 80)
    logger.info("US TEXAS SOVIET BOOTS MARKET DENSITY RESEARCH")
    logger.info("=" * 80)

    # Check API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env")
        return

    # Initialize client
    client = TexasDensityResearchClient(api_key)

    # Get keywords
    keywords = get_soviet_keywords()
    location = "Texas, USA"

    # Show plan
    logger.info("")
    logger.info("RESEARCH PLAN:")
    logger.info(f"State: Texas")
    logger.info(f"Keywords: {len(keywords)}")
    logger.info(f"Estimated cost: ${len(keywords) * 0.011:.2f}")
    logger.info(f"Parallel workers: {RESEARCH_CONFIG['api_settings']['max_workers']}")
    logger.info("")

    # Execute research
    logger.info("Starting research...")
    start_time = time.time()

    results = research_all_keywords(client, keywords, location)

    elapsed_time = time.time() - start_time

    # Get final stats
    stats = client.get_stats()

    # Save results
    logger.info("")
    logger.info("=" * 80)
    logger.info("SAVING RESULTS")
    logger.info("=" * 80)

    raw_path = save_raw_results(results, RESEARCH_CONFIG)
    keyword_analysis_path = save_keyword_analysis(client, results, RESEARCH_CONFIG)
    summary_path = save_summary_report(results, stats, RESEARCH_CONFIG)

    # Load summary for final print
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    # Print final summary
    print_final_summary(summary, keyword_analysis_path)

    logger.info(f"Research completed in {elapsed_time:.1f} seconds")
    logger.info(f"Results saved to: {RESEARCH_CONFIG['output_dir']}")

if __name__ == "__main__":
    main()
