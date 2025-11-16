#!/usr/bin/env python3
"""
=== ENRICH TOP 20 STATES REENACTORS ===
Version: 1.0.0 | Created: 2025-01-16

PURPOSE:
Enrich top 20 states reenactor groups with contact details (website, phone).
Get ready for email scraping + AI analysis.

STRATEGY:
- Take top 20 states by reenactor density
- Total: ~2,900 unique reenactor groups (67% of all US reenactors)
- Get Place Details API: website, phone, address, rating, hours
- Save enriched CSV for email scraping pipeline

TOP 20 STATES:
1. Connecticut (230)
2. West Virginia (187)
3. Wyoming (174)
4. New Hampshire (172)
5. Wisconsin (172)
6. Vermont (162)
7. North Carolina (136)
8. Oregon (133)
9. New Jersey (127)
10. Mississippi (125)
11. Virginia (118)
12. Tennessee (117)
13. North Dakota (117)
14. Massachusetts (115)
15. Florida (115)
16. California (114)
17. Montana (114)
18. Alabama (109)
19. Maryland (108)
20. Nebraska (108)

COST ESTIMATE:
- Place Details (contact fields): $0.023 per place
- ~2,900 places x $0.023 = ~$67
- Expected website coverage: 75-85%
- Expected phone coverage: 80-90%

USAGE:
1. Ensure us_reenactors_nationwide.py results exist
2. Run: python enrich_top20_reenactors.py
3. Results: results/enriched/us_reenactors_top20_TIMESTAMP.csv

IMPROVEMENTS:
v1.0.0 - Initial enrichment for top 20 states
"""

import os
import sys
import time
import json
import csv
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root
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

CONFIG = {
    "input_dir": "results/research/us_reenactors_v1/raw_results",
    "output_dir": "results/enriched",
    "output_filename": "us_reenactors_top20",

    # Top 20 states to enrich
    "top_states": [
        "connecticut",
        "west_virginia",
        "wyoming",
        "new_hampshire",
        "wisconsin",
        "vermont",
        "north_carolina",
        "oregon",
        "new_jersey",
        "mississippi",
        "virginia",
        "tennessee",
        "north_dakota",
        "massachusetts",
        "florida",
        "california",
        "montana",
        "alabama",
        "maryland",
        "nebraska",
    ],

    "api_settings": {
        "delay_between_requests": 0.2,
        "parallel_workers": 30,  # Fast parallel processing
        "max_cost_usd": 100.0,
    },

    "fields_to_fetch": [
        "place_id",
        "name",
        "formatted_address",
        "formatted_phone_number",
        "international_phone_number",
        "website",
        "rating",
        "user_ratings_total",
        "types",
        "opening_hours",
        "geometry",
        "business_status",
    ]
}

# ============================================================================
# GOOGLE PLACES API CLIENT
# ============================================================================

class PlacesEnrichmentClient:
    """Client for enriching place_ids with contact details"""

    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.stats = {
            "total_enriched": 0,
            "successful": 0,
            "failed": 0,
            "total_cost": 0.0,
            "with_website": 0,
            "with_phone": 0,
        }

    def get_place_details(self, place_id: str, fields: List[str]) -> Dict:
        """Get detailed information for a place_id"""
        endpoint = f"{self.BASE_URL}/details/json"

        params = {
            "place_id": place_id,
            "fields": ",".join(fields),
            "key": self.api_key,
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "OK":
                logger.warning(f"Place details error for {place_id}", status=data.get("status"))
                self.stats["failed"] += 1
                return {"status": data.get("status"), "place_id": place_id}

            result = data.get("result", {})

            self.stats["successful"] += 1
            self.stats["total_enriched"] += 1

            # Track presence of key fields
            if result.get("website"):
                self.stats["with_website"] += 1
            if result.get("formatted_phone_number"):
                self.stats["with_phone"] += 1

            # Calculate cost
            cost = 0.017  # Basic
            if any(f in fields for f in ["formatted_phone_number", "international_phone_number", "website"]):
                cost += 0.003  # Contact
            if any(f in fields for f in ["opening_hours"]):
                cost += 0.003  # Atmosphere

            self.stats["total_cost"] += cost

            return result

        except Exception as e:
            logger.error(f"Place details request failed: {place_id}", error=str(e))
            self.stats["failed"] += 1
            return {"status": "ERROR", "place_id": place_id, "error": str(e)}

    def get_stats(self) -> Dict:
        """Get enrichment statistics"""
        return {
            "total_enriched": self.stats["total_enriched"],
            "successful": self.stats["successful"],
            "failed": self.stats["failed"],
            "total_cost_usd": round(self.stats["total_cost"], 2),
            "with_website": self.stats["with_website"],
            "with_phone": self.stats["with_phone"],
            "website_coverage_pct": round(self.stats["with_website"] / max(self.stats["successful"], 1) * 100, 1),
            "phone_coverage_pct": round(self.stats["with_phone"] / max(self.stats["successful"], 1) * 100, 1),
        }

# ============================================================================
# LOAD DENSITY RESEARCH RESULTS
# ============================================================================

def load_top20_places(config: Dict) -> List[Dict]:
    """Load unique place_ids from top 20 states"""

    input_dir = Path(__file__).parent.parent / config["input_dir"]

    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        logger.error("Please run us_reenactors_nationwide.py first!")
        return []

    logger.info(f"Loading results from: {input_dir}")

    all_places = []
    place_ids_seen = set()

    # Load only top 20 states
    for state_name in config["top_states"]:
        state_files = list(input_dir.glob(f"{state_name}_*.json"))

        if not state_files:
            logger.warning(f"No results found for state: {state_name}")
            continue

        # Take most recent file
        state_file = sorted(state_files)[-1]

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            # Extract all places from all keywords
            for keyword, places in state_data.items():
                for place in places:
                    place_id = place.get("place_id")

                    if not place_id or place_id in place_ids_seen:
                        continue

                    place_ids_seen.add(place_id)
                    all_places.append({
                        "place_id": place_id,
                        "name": place.get("name", ""),
                        "state": state_name,
                        "source_keyword": place.get("source_keyword", ""),
                    })

        except Exception as e:
            logger.error(f"Failed to load {state_file}", error=str(e))
            continue

    logger.info(f"Loaded {len(all_places)} unique places from {len(config['top_states'])} states")

    return all_places

# ============================================================================
# ENRICHMENT EXECUTION
# ============================================================================

def enrich_single_place(client: PlacesEnrichmentClient, place: Dict, fields: List[str]) -> Dict:
    """Enrich a single place with details"""

    place_id = place["place_id"]
    details = client.get_place_details(place_id, fields)

    # Merge with original data
    enriched = {
        "place_id": place_id,
        "state": place["state"],
        "source_keyword": place["source_keyword"],
        "name": details.get("name", place.get("name", "")),
        "website": details.get("website", ""),
        "phone": details.get("formatted_phone_number", ""),
        "international_phone": details.get("international_phone_number", ""),
        "address": details.get("formatted_address", ""),
        "rating": details.get("rating", ""),
        "reviews": details.get("user_ratings_total", ""),
        "types": ", ".join(details.get("types", [])),
        "business_status": details.get("business_status", ""),
        "lat": details.get("geometry", {}).get("location", {}).get("lat", ""),
        "lng": details.get("geometry", {}).get("location", {}).get("lng", ""),
    }

    time.sleep(CONFIG["api_settings"]["delay_between_requests"])

    return enriched

def enrich_all_places(client: PlacesEnrichmentClient, places: List[Dict]) -> List[Dict]:
    """Enrich all places with parallel processing"""

    enriched_places = []
    total_places = len(places)
    completed = 0

    logger.info(f"Starting enrichment of {total_places} places")
    logger.info(f"Parallel workers: {CONFIG['api_settings']['parallel_workers']}")
    logger.info(f"Estimated cost: ${total_places * 0.023:.2f}")
    logger.info("")

    with ThreadPoolExecutor(max_workers=CONFIG["api_settings"]["parallel_workers"]) as executor:
        futures = {}

        for place in places:
            future = executor.submit(
                enrich_single_place,
                client,
                place,
                CONFIG["fields_to_fetch"]
            )
            futures[future] = place

        # Process results as they complete
        for future in as_completed(futures):
            try:
                enriched = future.result()
                enriched_places.append(enriched)
                completed += 1

                # Progress update
                if completed % 50 == 0:
                    stats = client.get_stats()
                    progress_pct = (completed / total_places) * 100
                    print(f"[{completed}/{total_places}] ({progress_pct:.1f}%) | "
                          f"Cost: ${stats['total_cost_usd']} | "
                          f"Website: {stats['website_coverage_pct']}% | "
                          f"Phone: {stats['phone_coverage_pct']}%")

            except Exception as e:
                logger.error(f"Enrichment failed", error=str(e))
                completed += 1

    return enriched_places

# ============================================================================
# SAVE RESULTS
# ============================================================================

def save_enriched_csv(enriched_places: List[Dict], config: Dict) -> Path:
    """Save enriched results to CSV"""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent.parent / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{config['output_filename']}_{timestamp}.csv"
    output_path = output_dir / filename

    # Convert to DataFrame and save
    df = pd.DataFrame(enriched_places)

    # Reorder columns
    column_order = [
        "place_id",
        "name",
        "state",
        "source_keyword",
        "website",
        "phone",
        "international_phone",
        "address",
        "rating",
        "reviews",
        "types",
        "business_status",
        "lat",
        "lng",
    ]

    df = df[column_order]

    # Save CSV
    df.to_csv(output_path, index=False, encoding='utf-8')

    logger.info(f"Enriched CSV saved: {output_path}")

    return output_path

def print_final_summary(stats: Dict, output_path: Path, enriched_count: int):
    """Print final summary"""

    print("\n" + "=" * 80)
    print("TOP 20 STATES REENACTORS ENRICHMENT - RESULTS")
    print("=" * 80)
    print(f"\nENRICHED: {enriched_count} reenactor groups")
    print(f"SUCCESSFUL: {stats['successful']}")
    print(f"FAILED: {stats['failed']}")
    print(f"\nCONTACT COVERAGE:")
    print(f"  - Websites: {stats['with_website']} ({stats['website_coverage_pct']}%)")
    print(f"  - Phones: {stats['with_phone']} ({stats['phone_coverage_pct']}%)")
    print(f"\nCOST: ${stats['total_cost_usd']}")
    print(f"\nOUTPUT: {output_path}")
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Email scraping for businesses with websites")
    print("2. AI analysis (relevance scoring, icebreakers)")
    print("3. Email verification (mails.so)")
    print("4. Upload to Instantly campaigns")
    print("=" * 80 + "\n")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 80)
    logger.info("TOP 20 STATES REENACTORS ENRICHMENT")
    logger.info("=" * 80)

    # Check API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env")
        return

    # Initialize client
    client = PlacesEnrichmentClient(api_key)

    # Load top 20 states places
    places = load_top20_places(CONFIG)

    if not places:
        logger.error("No places to enrich. Run us_reenactors_nationwide.py first!")
        return

    # Show plan
    logger.info("")
    logger.info(f"Top 20 states: {', '.join(CONFIG['top_states'])}")
    logger.info(f"Total places to enrich: {len(places)}")
    logger.info(f"Estimated cost: ${len(places) * 0.023:.2f}")
    logger.info("")

    # Execute enrichment
    logger.info("Starting enrichment...")
    start_time = time.time()

    enriched_places = enrich_all_places(client, places)

    elapsed_time = time.time() - start_time

    # Get stats
    stats = client.get_stats()

    # Save results
    logger.info("")
    logger.info("=" * 80)
    logger.info("SAVING RESULTS")
    logger.info("=" * 80)

    output_path = save_enriched_csv(enriched_places, CONFIG)

    # Print summary
    print_final_summary(stats, output_path, len(enriched_places))

    logger.info(f"Enrichment completed in {elapsed_time/60:.1f} minutes")

if __name__ == "__main__":
    main()
