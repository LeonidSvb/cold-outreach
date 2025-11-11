#!/usr/bin/env python3
"""
=== PLACES API DETAILS ENRICHMENT ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Enrich existing place_ids from density research with full contact details
(phone, website, email) using Places API Place Details endpoint

FEATURES:
- Reads raw JSON results from density research
- Extracts unique place_ids (auto-deduplication)
- Enriches with Place Details API (contact fields)
- Exports to CSV with all contact info
- Cost tracking

COST:
Place Details (contact fields): $0.023 per place
Example: 200 places = $4.60

USAGE:
1. Run density research first (market_research_density.py)
2. Configure INPUT_DIR to point to raw_results folder
3. Run: python enrich_places_details.py
4. Results saved to results/enriched/

WORKFLOW:
density_research (Text Search) → raw place_ids → THIS SCRIPT → enriched contacts

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
from typing import List, Dict, Set
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
# CONFIGURATION
# ============================================================================

CONFIG = {
    "input_dir": "results/research/soviet_reenactment_clubs_v2/raw_results",
    "output_dir": "results/enriched",
    "output_filename": "soviet_reenactment_enriched",

    "api_settings": {
        "delay_between_requests": 0.5,
        "batch_size": 10,
        "parallel_workers": 5,
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
        }

    def get_place_details(self, place_id: str, fields: List[str]) -> Dict:
        """
        Get detailed information for a place_id

        Cost: $0.017 (basic) + $0.003 (contact fields) + $0.003 (atmosphere) = $0.023
        """
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

            self.stats["successful"] += 1
            self.stats["total_enriched"] += 1

            # Calculate cost based on fields
            cost = 0.017  # Basic
            if any(f in fields for f in ["formatted_phone_number", "international_phone_number", "website"]):
                cost += 0.003  # Contact
            if any(f in fields for f in ["opening_hours"]):
                cost += 0.003  # Atmosphere

            self.stats["total_cost"] += cost

            return data.get("result", {})

        except Exception as e:
            logger.error("Place details request failed", place_id=place_id, error=str(e))
            self.stats["failed"] += 1
            return {"status": "ERROR", "place_id": place_id, "error": str(e)}

    def get_stats(self) -> Dict:
        """Get enrichment statistics"""
        return {
            "total_enriched": self.stats["total_enriched"],
            "successful": self.stats["successful"],
            "failed": self.stats["failed"],
            "success_rate": round(self.stats["successful"] / max(self.stats["total_enriched"], 1) * 100, 1),
            "total_cost_usd": round(self.stats["total_cost"], 2),
        }

# ============================================================================
# DATA LOADING
# ============================================================================

def load_raw_results(input_dir: Path) -> List[Dict]:
    """
    Load all raw JSON results from density research

    Returns:
        List of all places (with potential duplicates)
    """
    all_places = []

    json_files = list(input_dir.glob("*.json"))

    if not json_files:
        logger.error(f"No JSON files found in {input_dir}")
        return []

    logger.info(f"Found {len(json_files)} raw result files")

    for json_file in json_files:
        logger.info(f"Loading: {json_file.name}")

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # data is dict: {keyword: [places]}
        for keyword, places in data.items():
            for place in places:
                # Add metadata
                place["source_keyword"] = keyword
                place["source_file"] = json_file.stem
                all_places.append(place)

    logger.info(f"Loaded {len(all_places)} places (with duplicates)")

    return all_places

def deduplicate_places(places: List[Dict]) -> List[Dict]:
    """
    Remove duplicates by place_id, keeping first occurrence

    Also tracks which keywords found each place
    """
    seen_ids: Set[str] = set()
    unique_places = []
    duplicates_count = 0

    # Track keywords per place
    place_keywords = {}

    for place in places:
        place_id = place.get("place_id")

        if not place_id:
            continue

        if place_id not in seen_ids:
            seen_ids.add(place_id)
            place_keywords[place_id] = [place.get("source_keyword", "")]
            unique_places.append(place)
        else:
            # Duplicate - just add keyword to tracking
            place_keywords[place_id].append(place.get("source_keyword", ""))
            duplicates_count += 1

    # Add keywords list to each unique place
    for place in unique_places:
        place_id = place.get("place_id")
        place["found_in_keywords"] = ", ".join(place_keywords.get(place_id, []))

    logger.info(f"Unique places: {len(unique_places)}")
    logger.info(f"Duplicates removed: {duplicates_count}")

    return unique_places

# ============================================================================
# ENRICHMENT
# ============================================================================

def enrich_place(client: PlacesEnrichmentClient, place: Dict, fields: List[str]) -> Dict:
    """Enrich a single place with details"""
    place_id = place.get("place_id")

    if not place_id:
        logger.warning("Place has no place_id", place=place)
        return place

    # Get details from API
    details = client.get_place_details(place_id, fields)

    # Merge with original data
    enriched = {**place, **details}

    return enriched

def enrich_all_places(client: PlacesEnrichmentClient, places: List[Dict], fields: List[str], config: Dict) -> List[Dict]:
    """Enrich all places with parallel processing"""
    enriched_places = []
    total = len(places)

    logger.info(f"Starting enrichment of {total} places...")
    logger.info(f"Workers: {config['api_settings']['parallel_workers']}")

    with ThreadPoolExecutor(max_workers=config["api_settings"]["parallel_workers"]) as executor:
        futures = {executor.submit(enrich_place, client, place, fields): place for place in places}

        for i, future in enumerate(as_completed(futures), 1):
            try:
                enriched = future.result()
                enriched_places.append(enriched)

                name = enriched.get("name", "Unknown")
                status = enriched.get("status", "success")

                # Safe print with encoding handling
                try:
                    print(f"[{i}/{total}] {name[:50]:<50} - {status}")
                except UnicodeEncodeError:
                    print(f"[{i}/{total}] {name.encode('ascii', 'ignore').decode()[:50]:<50} - {status}")

                # Progress stats every 10 places
                if i % 10 == 0:
                    stats = client.get_stats()
                    logger.info(f"Progress: {i}/{total} | Success rate: {stats['success_rate']}% | Cost: ${stats['total_cost_usd']}")

                # Rate limiting
                time.sleep(config["api_settings"]["delay_between_requests"])

            except Exception as e:
                logger.error(f"Enrichment failed for place: {str(e)}")

    return enriched_places

# ============================================================================
# EXPORT
# ============================================================================

def flatten_place_for_csv(place: Dict) -> Dict:
    """Flatten nested place data for CSV export"""
    flat = {
        "place_id": place.get("place_id", ""),
        "name": place.get("name", ""),
        "address": place.get("formatted_address", ""),
        "phone": place.get("formatted_phone_number", ""),
        "international_phone": place.get("international_phone_number", ""),
        "website": place.get("website", ""),
        "rating": place.get("rating", ""),
        "total_ratings": place.get("user_ratings_total", ""),
        "business_status": place.get("business_status", ""),
        "types": ", ".join(place.get("types", [])),
        "latitude": place.get("geometry", {}).get("location", {}).get("lat", ""),
        "longitude": place.get("geometry", {}).get("location", {}).get("lng", ""),
        "found_in_keywords": place.get("found_in_keywords", ""),
        "source_file": place.get("source_file", ""),
    }

    # Opening hours
    opening_hours = place.get("opening_hours", {})
    if opening_hours:
        flat["is_open_now"] = opening_hours.get("open_now", "")
        weekday_text = opening_hours.get("weekday_text", [])
        if weekday_text:
            flat["hours"] = " | ".join(weekday_text)

    return flat

def save_enriched_results(places: List[Dict], config: Dict) -> Path:
    """Save enriched results to CSV"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_dir = Path(__file__).parent.parent / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{config['output_filename']}_{timestamp}.csv"
    output_path = output_dir / filename

    # Flatten data
    flattened = [flatten_place_for_csv(p) for p in places]

    # Create DataFrame
    df = pd.DataFrame(flattened)

    # Sort by rating (descending) - convert to numeric first
    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        df = df.sort_values("rating", ascending=False)

    # Save to CSV
    df.to_csv(output_path, index=False, encoding="utf-8")

    logger.info(f"Saved enriched results: {output_path}")

    return output_path

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 80)
    logger.info("PLACES API DETAILS ENRICHMENT")
    logger.info("=" * 80)

    # Check API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env")
        return

    # Load raw results
    input_dir = Path(__file__).parent.parent / CONFIG["input_dir"]

    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        logger.info("Run market_research_density.py first!")
        return

    logger.info(f"Loading raw results from: {input_dir}")
    all_places = load_raw_results(input_dir)

    if not all_places:
        logger.error("No places loaded")
        return

    # Deduplicate
    logger.info("\nDeduplicating places...")
    unique_places = deduplicate_places(all_places)

    # Show stats
    logger.info("\n" + "=" * 80)
    logger.info("ENRICHMENT PLAN")
    logger.info("=" * 80)
    logger.info(f"Total places (with duplicates): {len(all_places)}")
    logger.info(f"Unique places: {len(unique_places)}")
    logger.info(f"Duplicates removed: {len(all_places) - len(unique_places)}")
    logger.info(f"Fields to fetch: {len(CONFIG['fields_to_fetch'])}")
    logger.info(f"Estimated cost: ${len(unique_places) * 0.023:.2f}")
    logger.info("")

    # Initialize client
    client = PlacesEnrichmentClient(api_key)

    # Enrich all places
    logger.info("Starting enrichment...\n")
    start_time = time.time()

    enriched_places = enrich_all_places(
        client,
        unique_places,
        CONFIG["fields_to_fetch"],
        CONFIG
    )

    elapsed_time = time.time() - start_time

    # Save results
    logger.info("\n" + "=" * 80)
    logger.info("SAVING RESULTS")
    logger.info("=" * 80)

    output_path = save_enriched_results(enriched_places, CONFIG)

    # Final stats
    stats = client.get_stats()

    logger.info("\n" + "=" * 80)
    logger.info("ENRICHMENT COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Total places enriched: {stats['total_enriched']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Success rate: {stats['success_rate']}%")
    logger.info(f"Total cost: ${stats['total_cost_usd']:.2f}")
    logger.info(f"Execution time: {elapsed_time/60:.1f} minutes")
    logger.info("")
    logger.info(f"Output file: {output_path}")
    logger.info("=" * 80)
    logger.info("")
    logger.info("NEXT STEPS:")
    logger.info("1. Review CSV file for contact data (website, phone, email)")
    logger.info("2. Filter places with websites")
    logger.info("3. Run website scraping for content analysis")
    logger.info("")

if __name__ == "__main__":
    main()
