#!/usr/bin/env python3
"""
=== GOOGLE MAPS API LEAD SCRAPER ===
Version: 1.0.0 | Created: 2025-11-09

PURPOSE:
Scrape business leads from Google Maps using official Places API

FEATURES:
- Text Search for finding businesses
- Place Details for phone + website
- Auto-pagination for large results
- CSV export
- Cost tracking
- Free tier optimization

SETUP:
1. Create Google Cloud project: https://console.cloud.google.com
2. Enable Places API
3. Create API key
4. Add key to .env: GOOGLE_MAPS_API_KEY=your_key

USAGE:
1. Configure CONFIG section below
2. Run: python google_maps_api_scraper.py
3. Results saved to results/

COST ESTIMATION:
- Text Search: $32/1000 requests
- Place Details (phone+website): $23/1000 requests
- Free tier: $200/month

Example: 6,000 leads
- Text Search: 6K × $0.032 = $192
- Place Details: 6K × $0.023 = $138
- Total: $330 (-$200 free tier) = $130/month

IMPROVEMENTS:
v1.0.0 - Initial version with Places API
"""

import os
import sys
import time
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import csv

# Add project root to path for imports
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
    "API_KEY": os.getenv("GOOGLE_MAPS_API_KEY", ""),

    "SEARCH": {
        "query": "restaurants in New York",
        "location": None,
        "radius": None,
        "type": None,
        "max_results": 100,
    },

    "FIELDS": {
        "basic": True,
        "contact": True,
        "atmosphere": False,
    },

    "RATE_LIMITING": {
        "delay_between_requests": 0.5,
        "retry_attempts": 3,
        "retry_delay": 2,
    },

    "OUTPUT": {
        "format": "csv",
        "save_raw_json": True,
        "filename_prefix": "google_maps_leads",
    },

    "COST_TRACKING": {
        "enabled": True,
        "warn_threshold": 100.0,
    }
}

# ============================================================================
# API PRICING
# ============================================================================

PRICING = {
    "text_search": 0.032,
    "place_details_basic": 0.017,
    "contact_fields": 0.003,
    "atmosphere_fields": 0.003,
}

# ============================================================================
# GOOGLE MAPS API CLIENT
# ============================================================================

class GoogleMapsClient:
    """Google Maps Places API client"""

    BASE_URL = "https://maps.googleapis.com/maps/api/place"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.stats = {
            "text_search_calls": 0,
            "place_details_calls": 0,
            "total_cost": 0.0,
            "errors": 0,
        }

    def text_search(self, query: str, page_token: Optional[str] = None) -> Dict:
        """
        Search for places by text query

        Docs: https://developers.google.com/maps/documentation/places/web-service/search-text
        Cost: $32/1000 requests
        """
        endpoint = f"{self.BASE_URL}/textsearch/json"

        params = {
            "query": query,
            "key": self.api_key,
        }

        if page_token:
            params["pagetoken"] = page_token

        try:
            logger.info(f"Text search: {query}", page_token=bool(page_token))
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if data.get("status") != "OK" and data.get("status") != "ZERO_RESULTS":
                logger.error(f"API error: {data.get('status')}", error_message=data.get("error_message"))
                self.stats["errors"] += 1
                return {"results": [], "status": data.get("status")}

            self.stats["text_search_calls"] += 1
            self.stats["total_cost"] += PRICING["text_search"]

            return data

        except Exception as e:
            logger.error("Text search failed", error=str(e))
            self.stats["errors"] += 1
            return {"results": [], "status": "ERROR"}

    def place_details(self, place_id: str, fields: List[str]) -> Dict:
        """
        Get detailed information about a place

        Docs: https://developers.google.com/maps/documentation/places/web-service/details
        Cost: $17-$23/1000 depending on fields
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
                self.stats["errors"] += 1
                return {"result": {}, "status": data.get("status")}

            self.stats["place_details_calls"] += 1

            cost = PRICING["place_details_basic"]
            if any(f in fields for f in ["formatted_phone_number", "international_phone_number", "website"]):
                cost += PRICING["contact_fields"]
            if any(f in fields for f in ["opening_hours", "price_level"]):
                cost += PRICING["atmosphere_fields"]

            self.stats["total_cost"] += cost

            return data

        except Exception as e:
            logger.error("Place details failed", place_id=place_id, error=str(e))
            self.stats["errors"] += 1
            return {"result": {}, "status": "ERROR"}

    def get_cost_estimate(self) -> Dict:
        """Get cost estimate and stats"""
        return {
            "text_search_calls": self.stats["text_search_calls"],
            "place_details_calls": self.stats["place_details_calls"],
            "total_cost_usd": round(self.stats["total_cost"], 2),
            "errors": self.stats["errors"],
        }

# ============================================================================
# SCRAPER
# ============================================================================

def build_fields_list(config: Dict) -> List[str]:
    """Build list of fields to request based on config"""
    fields = [
        "place_id",
        "name",
        "formatted_address",
        "geometry",
        "types",
        "rating",
        "user_ratings_total",
    ]

    if config["FIELDS"]["contact"]:
        fields.extend([
            "formatted_phone_number",
            "international_phone_number",
            "website",
        ])

    if config["FIELDS"]["atmosphere"]:
        fields.extend([
            "opening_hours",
            "price_level",
        ])

    return fields

def search_places(client: GoogleMapsClient, query: str, max_results: int) -> List[Dict]:
    """
    Search for places and get all results with pagination

    Note: Google returns max 60 results (3 pages × 20)
    """
    all_results = []
    next_page_token = None
    page = 1

    while len(all_results) < max_results:
        logger.info(f"Fetching page {page}")

        data = client.text_search(query, page_token=next_page_token)

        if data.get("status") == "ZERO_RESULTS":
            logger.info("No more results")
            break

        results = data.get("results", [])
        all_results.extend(results)

        logger.info(f"Got {len(results)} results (total: {len(all_results)})")

        next_page_token = data.get("next_page_token")

        if not next_page_token:
            logger.info("No more pages")
            break

        if len(all_results) >= max_results:
            logger.info(f"Reached max results limit: {max_results}")
            break

        page += 1

        time.sleep(2)

    return all_results[:max_results]

def enrich_with_details(client: GoogleMapsClient, places: List[Dict], fields: List[str]) -> List[Dict]:
    """Enrich places with detailed information"""
    enriched = []

    for i, place in enumerate(places, 1):
        place_id = place.get("place_id")

        if not place_id:
            logger.warning(f"No place_id for place {i}")
            enriched.append(place)
            continue

        logger.info(f"Enriching {i}/{len(places)}: {place.get('name')}")

        details_data = client.place_details(place_id, fields)
        details = details_data.get("result", {})

        merged = {**place, **details}
        enriched.append(merged)

        time.sleep(CONFIG["RATE_LIMITING"]["delay_between_requests"])

        if (i % 10 == 0) and CONFIG["COST_TRACKING"]["enabled"]:
            cost_info = client.get_cost_estimate()
            logger.info(f"Progress: {i}/{len(places)} | Cost so far: ${cost_info['total_cost_usd']}")

    return enriched

def flatten_place_data(place: Dict) -> Dict:
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
        "price_level": place.get("price_level", ""),
        "types": ", ".join(place.get("types", [])),
        "latitude": place.get("geometry", {}).get("location", {}).get("lat", ""),
        "longitude": place.get("geometry", {}).get("location", {}).get("lng", ""),
    }

    opening_hours = place.get("opening_hours", {})
    if opening_hours:
        flat["is_open_now"] = opening_hours.get("open_now", "")
        weekday_text = opening_hours.get("weekday_text", [])
        if weekday_text:
            flat["hours"] = " | ".join(weekday_text)

    return flat

# ============================================================================
# SAVE RESULTS
# ============================================================================

def save_results(places: List[Dict], config: Dict):
    """Save results to files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(__file__).parent.parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    prefix = config["OUTPUT"]["filename_prefix"]

    if config["OUTPUT"]["save_raw_json"]:
        json_file = results_dir / f"{prefix}_{timestamp}_raw.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(places, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved raw JSON: {json_file}")

    if config["OUTPUT"]["format"] == "csv":
        csv_file = results_dir / f"{prefix}_{timestamp}.csv"

        flattened = [flatten_place_data(p) for p in places]

        if flattened:
            fieldnames = flattened[0].keys()

            with open(csv_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened)

            logger.info(f"Saved CSV: {csv_file}")
            return csv_file

    return None

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""
    logger.info("Google Maps API Lead Scraper started")

    if not CONFIG["API_KEY"]:
        logger.error("GOOGLE_MAPS_API_KEY not found in .env")
        logger.info("Get API key: https://console.cloud.google.com")
        return

    logger.info(f"Search query: {CONFIG['SEARCH']['query']}")
    logger.info(f"Max results: {CONFIG['SEARCH']['max_results']}")

    client = GoogleMapsClient(CONFIG["API_KEY"])

    logger.info("Step 1: Searching for places...")
    places = search_places(
        client,
        CONFIG["SEARCH"]["query"],
        CONFIG["SEARCH"]["max_results"]
    )

    logger.info(f"Found {len(places)} places")

    if not places:
        logger.warning("No places found")
        return

    fields = build_fields_list(CONFIG)
    logger.info(f"Step 2: Enriching with details (fields: {len(fields)})")

    enriched_places = enrich_with_details(client, places, fields)

    logger.info("Step 3: Saving results...")
    output_file = save_results(enriched_places, CONFIG)

    cost_info = client.get_cost_estimate()

    logger.info("=" * 60)
    logger.info("SCRAPING COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Total places: {len(enriched_places)}")
    logger.info(f"Output file: {output_file}")
    logger.info("")
    logger.info("COST SUMMARY:")
    logger.info(f"  Text Search calls: {cost_info['text_search_calls']}")
    logger.info(f"  Place Details calls: {cost_info['place_details_calls']}")
    logger.info(f"  Total cost: ${cost_info['total_cost_usd']:.2f}")
    logger.info(f"  Errors: {cost_info['errors']}")
    logger.info("")

    free_tier_remaining = 200.0 - cost_info['total_cost_usd']
    if free_tier_remaining > 0:
        logger.info(f"Free tier remaining this month: ${free_tier_remaining:.2f}")
    else:
        logger.warning(f"Exceeded free tier by: ${abs(free_tier_remaining):.2f}")

    logger.info("=" * 60)

if __name__ == "__main__":
    main()
