#!/usr/bin/env python3
"""
=== PLACES API DETAILS ENRICHMENT V2 ===
Version: 2.0.0 | Created: 2025-11-11

PURPOSE:
Enrich filtered unique places with full contact details using Places API.

INPUT:
filtered_unique_places.json from pre-filter step

OUTPUT:
CSV with all enriched contact details (website, phone, address, rating)

COST:
Place Details (contact fields): $0.023 per place
3,688 places = $84.82

USAGE:
python enrich_places_details_v2.py
"""

import os
import sys
import time
import json
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict
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
    "input_file": "results/research/european_mass_v1/filtered_unique_places.json",
    "output_dir": "results/enriched",
    "output_filename": "european_mass_enriched",

    "api_settings": {
        "delay_between_requests": 0.2,
        "parallel_workers": 30,
        "max_cost_usd": 100.0,  # Stop if cost exceeds this
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
            "with_website": self.stats["with_website"],
            "with_phone": self.stats["with_phone"],
            "website_coverage": round(self.stats["with_website"] / max(self.stats["successful"], 1) * 100, 1),
            "phone_coverage": round(self.stats["with_phone"] / max(self.stats["successful"], 1) * 100, 1),
            "success_rate": round(self.stats["successful"] / max(self.stats["total_enriched"], 1) * 100, 1),
            "total_cost_usd": round(self.stats["total_cost"], 2),
        }

# ============================================================================
# DATA LOADING
# ============================================================================

def load_filtered_places(input_file: Path) -> List[Dict]:
    """Load filtered unique places from JSON"""

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return []

    logger.info(f"Loading filtered places from: {input_file}")

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    places = data.get("unique_places", [])
    logger.info(f"Loaded {len(places)} unique places")

    return places

# ============================================================================
# ENRICHMENT
# ============================================================================

def enrich_place(client: PlacesEnrichmentClient, place: Dict, fields: List[str]) -> Dict:
    """Enrich a single place with details"""
    place_id = place.get("place_id")

    if not place_id:
        logger.warning("Place has no place_id")
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
                has_website = "YES" if enriched.get("website") else "NO"

                # Safe print
                try:
                    print(f"[{i}/{total}] {name[:50]:<50} | Website: {has_website} | {status}")
                except UnicodeEncodeError:
                    print(f"[{i}/{total}] [Unicode name] | Website: {has_website} | {status}")

                # Progress stats every 50 places
                if i % 50 == 0:
                    stats = client.get_stats()
                    logger.info(f"Progress: {i}/{total} | Success: {stats['success_rate']}% | Websites: {stats['website_coverage']}% | Cost: ${stats['total_cost_usd']}")

                    # Budget check
                    if stats['total_cost_usd'] > config["api_settings"].get("max_cost_usd", 999):
                        logger.warning(f"Budget limit reached: ${stats['total_cost_usd']}")
                        break

                # Rate limiting
                time.sleep(config["api_settings"]["delay_between_requests"])

            except Exception as e:
                logger.error(f"Enrichment failed: {str(e)}")

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
        "found_in_countries": place.get("found_in_countries", ""),
        "source_country": place.get("source_country", ""),
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

    # Sort by rating
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
    logger.info("PLACES API DETAILS ENRICHMENT V2")
    logger.info("=" * 80)

    # Check API key
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env")
        return

    # Load filtered places
    input_file = Path(__file__).parent.parent / CONFIG["input_file"]
    places = load_filtered_places(input_file)

    if not places:
        logger.error("No places loaded")
        return

    # Show stats
    logger.info("")
    logger.info("=" * 80)
    logger.info("ENRICHMENT PLAN")
    logger.info("=" * 80)
    logger.info(f"Total places to enrich: {len(places)}")
    logger.info(f"Fields to fetch: {len(CONFIG['fields_to_fetch'])}")
    logger.info(f"Estimated cost: ${len(places) * 0.023:.2f}")
    logger.info("")

    # Initialize client
    client = PlacesEnrichmentClient(api_key)

    # Enrich all places
    logger.info("Starting enrichment...")
    start_time = time.time()

    enriched_places = enrich_all_places(
        client,
        places,
        CONFIG["fields_to_fetch"],
        CONFIG
    )

    elapsed_time = time.time() - start_time

    # Save results
    logger.info("")
    logger.info("=" * 80)
    logger.info("SAVING RESULTS")
    logger.info("=" * 80)

    output_path = save_enriched_results(enriched_places, CONFIG)

    # Final stats
    stats = client.get_stats()

    logger.info("")
    logger.info("=" * 80)
    logger.info("ENRICHMENT COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Total places enriched: {stats['total_enriched']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Success rate: {stats['success_rate']}%")
    logger.info(f"Website coverage: {stats['website_coverage']}%")
    logger.info(f"Phone coverage: {stats['phone_coverage']}%")
    logger.info(f"Total cost: ${stats['total_cost_usd']:.2f}")
    logger.info(f"Execution time: {elapsed_time/60:.1f} minutes")
    logger.info("")
    logger.info(f"Output file: {output_path}")
    logger.info("=" * 80)
    logger.info("")
    logger.info("NEXT STEP: Filter places with websites and proceed to Step 3 (Scraping)")
    logger.info("")

if __name__ == "__main__":
    main()
