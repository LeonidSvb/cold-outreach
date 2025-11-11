#!/usr/bin/env python3
"""
=== PRE-FILTER AND DEDUPLICATION ===
Version: 1.0.0 | Created: 2025-11-11

PURPOSE:
Filter out irrelevant places BEFORE expensive Place Details enrichment.
Saves money by only enriching quality leads.

FILTERING CRITERIA:
- Include: museums, tourist attractions, stores, galleries, etc.
- Exclude: restaurants, cafes, travel agencies, shopping malls, etc.
- Name pattern matching for military/history keywords
- Rating threshold (optional)

DEDUPLICATION:
- Remove duplicate place_ids across all countries
- Track keyword sources for each unique place

USAGE:
1. Run: python pre_filter_and_deduplicate.py
2. Review filtered stats
3. Proceed to Step 2 with filtered dataset
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Set
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

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG = {
    "input_dir": "results/research/european_mass_v1/raw_results",
    "output_dir": "results/research/european_mass_v1",
    "output_filename": "filtered_unique_places.json",

    # Filtering rules
    "filters": {
        # INCLUDE these Google Place types
        "include_types": {
            "museum",
            "tourist_attraction",
            "store",
            "clothing_store",
            "home_goods_store",
            "book_store",
            "art_gallery",
            "cemetery",  # war cemeteries
            "park",  # memorial parks
            "library",
            "school",  # military schools
            "university",
        },

        # EXCLUDE these types (overrides include)
        "exclude_types": {
            "restaurant",
            "cafe",
            "bar",
            "night_club",
            "travel_agency",
            "real_estate_agency",
            "car_dealer",
            "car_repair",
            "gas_station",
            "parking",
            "atm",
            "bank",
            "pharmacy",
            "doctor",
            "hospital",
            "dentist",
            "veterinary_care",
            "pet_store",
            "hair_care",
            "beauty_salon",
            "spa",
            "gym",
            "movie_theater",
            "shopping_mall",
            "supermarket",
            "convenience_store",
            "electronics_store",
            "furniture_store",
            "hardware_store",
            "jewelry_store",
            "shoe_store",
            "bicycle_store",
            "florist",
            "laundry",
            "locksmith",
            "moving_company",
            "painter",
            "plumber",
            "roofing_contractor",
            "storage",
            "taxi_stand",
            "transit_station",
            "subway_station",
            "train_station",
            "bus_station",
            "airport",
            "lodging",
            "hotel",
            "campground",
            "rv_park",
            "church",
            "hindu_temple",
            "mosque",
            "synagogue",
        },

        # Keywords in name that ALWAYS INCLUDE (even if type excluded)
        "include_name_keywords": [
            "museum",
            "muzeum",
            "musee",
            "museo",
            "military",
            "war",
            "army",
            "soviet",
            "red army",
            "cold war",
            "world war",
            "wwii",
            "ww2",
            "historical",
            "history",
            "memorial",
            "monument",
            "battle",
            "veteran",
            "bunker",
            "fortress",
            "tank",
            "aviation",
            "airforce",
            "navy",
            "marine",
            "soldier",
            "regiment",
            "brigade",
            "division",
            "militaria",
            "collectibles",
            "reenactment",
            "reconstruction",
            "living history",
            "historic site",
        ],

        # Keywords in name that ALWAYS EXCLUDE
        "exclude_name_keywords": [
            "restaurant",
            "cafe",
            "coffee",
            "pizza",
            "burger",
            "hotel",
            "hostel",
            "apartment",
            "travel agency",
            "real estate",
            "car wash",
            "gas station",
            "pharmacy",
            "supermarket",
            "grocery",
        ],

        # Minimum rating (0 = no filter)
        "min_rating": 0,
    }
}

# ============================================================================
# FILTERING LOGIC
# ============================================================================

def should_include_place(place: Dict, filters: Dict) -> tuple[bool, str]:
    """
    Determine if a place should be included based on filtering rules.

    Returns:
        (include: bool, reason: str)
    """
    name = place.get("name", "").lower()
    types = set(place.get("types", []))
    rating = place.get("rating", 0)

    # Check exclude name keywords first (highest priority)
    for keyword in filters["exclude_name_keywords"]:
        if keyword.lower() in name:
            return False, f"excluded_name_keyword: {keyword}"

    # Check include name keywords (override type filters)
    for keyword in filters["include_name_keywords"]:
        if keyword.lower() in name:
            return True, f"included_name_keyword: {keyword}"

    # Check exclude types
    if types & filters["exclude_types"]:
        excluded_type = list(types & filters["exclude_types"])[0]
        return False, f"excluded_type: {excluded_type}"

    # Check include types
    if types & filters["include_types"]:
        included_type = list(types & filters["include_types"])[0]
        # Check rating threshold
        if filters["min_rating"] > 0 and rating < filters["min_rating"]:
            return False, f"low_rating: {rating}"
        return True, f"included_type: {included_type}"

    # No matching criteria - exclude by default
    return False, "no_matching_criteria"

# ============================================================================
# LOAD AND FILTER
# ============================================================================

def load_and_filter_all_countries(config: Dict) -> Dict:
    """Load all country data and apply filters"""

    input_dir = Path(__file__).parent.parent / config["input_dir"]

    if not input_dir.exists():
        logger.error(f"Input directory not found: {input_dir}")
        return {}

    json_files = list(input_dir.glob("*.json"))
    logger.info(f"Found {len(json_files)} country files")

    all_places = []
    country_stats = defaultdict(lambda: {
        "total": 0,
        "filtered_in": 0,
        "filtered_out": 0,
        "reasons": defaultdict(int)
    })

    for json_file in json_files:
        country = json_file.stem.split("_")[0]  # Extract country name

        logger.info(f"Processing: {country}")

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Collect places from all keywords
        for keyword, places in data.items():
            for place in places:
                country_stats[country]["total"] += 1

                # Add metadata
                place["source_country"] = country
                place["source_keyword"] = keyword

                # Apply filter
                include, reason = should_include_place(place, config["filters"])

                if include:
                    all_places.append(place)
                    country_stats[country]["filtered_in"] += 1
                    country_stats[country]["reasons"][reason] += 1
                else:
                    country_stats[country]["filtered_out"] += 1
                    country_stats[country]["reasons"][reason] += 1

    logger.info(f"Total places after filtering: {len(all_places)}")

    return {
        "places": all_places,
        "stats": dict(country_stats)
    }

# ============================================================================
# DEDUPLICATION
# ============================================================================

def deduplicate_places(places: List[Dict]) -> List[Dict]:
    """Remove duplicates by place_id, keeping first occurrence"""

    seen_ids: Set[str] = set()
    unique_places = []
    duplicates_count = 0

    # Track keywords per place
    place_keywords = defaultdict(set)
    place_countries = defaultdict(set)

    for place in places:
        place_id = place.get("place_id")

        if not place_id:
            continue

        if place_id not in seen_ids:
            seen_ids.add(place_id)
            unique_places.append(place)
            place_keywords[place_id].add(place.get("source_keyword", ""))
            place_countries[place_id].add(place.get("source_country", ""))
        else:
            # Duplicate - add keyword and country to tracking
            place_keywords[place_id].add(place.get("source_keyword", ""))
            place_countries[place_id].add(place.get("source_country", ""))
            duplicates_count += 1

    # Add metadata to unique places
    for place in unique_places:
        place_id = place.get("place_id")
        place["found_in_keywords"] = ", ".join(sorted(place_keywords.get(place_id, [])))
        place["found_in_countries"] = ", ".join(sorted(place_countries.get(place_id, [])))

    logger.info(f"Unique places: {len(unique_places)}")
    logger.info(f"Duplicates removed: {duplicates_count}")

    return unique_places

# ============================================================================
# SAVE RESULTS
# ============================================================================

def save_filtered_results(data: Dict, config: Dict) -> Path:
    """Save filtered and deduplicated results"""

    output_dir = Path(__file__).parent.parent / config["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / config["output_filename"]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved filtered results: {output_path}")

    return output_path

def save_filter_report(data: Dict, unique_count: int, config: Dict) -> Path:
    """Generate comprehensive filter report"""

    output_dir = Path(__file__).parent.parent / config["output_dir"]

    total_raw = sum(stats["total"] for stats in data["stats"].values())
    total_filtered_in = sum(stats["filtered_in"] for stats in data["stats"].values())
    total_filtered_out = sum(stats["filtered_out"] for stats in data["stats"].values())

    report = {
        "summary": {
            "total_raw_places": total_raw,
            "total_after_filter": total_filtered_in,
            "total_filtered_out": total_filtered_out,
            "filter_rate": round((total_filtered_out / total_raw) * 100, 2),
            "unique_places_after_dedup": unique_count,
            "dedup_rate": round((1 - unique_count / total_filtered_in) * 100, 2),
        },
        "by_country": {}
    }

    # Per-country stats
    for country, stats in data["stats"].items():
        report["by_country"][country] = {
            "total_raw": stats["total"],
            "filtered_in": stats["filtered_in"],
            "filtered_out": stats["filtered_out"],
            "filter_rate": round((stats["filtered_out"] / stats["total"]) * 100, 2),
            "top_filter_reasons": dict(sorted(
                stats["reasons"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])
        }

    # Save report
    report_path = output_dir / "filter_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    logger.info(f"Filter report saved: {report_path}")

    return report_path

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""

    logger.info("=" * 80)
    logger.info("PRE-FILTER AND DEDUPLICATION")
    logger.info("=" * 80)

    # Load and filter
    logger.info("\nLoading and filtering places...")
    data = load_and_filter_all_countries(CONFIG)

    if not data["places"]:
        logger.error("No places passed filter")
        return

    # Deduplicate
    logger.info("\nDeduplicating places...")
    unique_places = deduplicate_places(data["places"])

    # Save results
    logger.info("\n" + "=" * 80)
    logger.info("SAVING RESULTS")
    logger.info("=" * 80)

    filtered_data = {
        "unique_places": unique_places,
        "count": len(unique_places),
    }

    output_path = save_filtered_results(filtered_data, CONFIG)
    report_path = save_filter_report(data, len(unique_places), CONFIG)

    # Final summary
    total_raw = sum(stats["total"] for stats in data["stats"].values())
    total_filtered = len(data["places"])

    logger.info("\n" + "=" * 80)
    logger.info("FILTERING COMPLETED")
    logger.info("=" * 80)
    logger.info(f"Total raw places: {total_raw}")
    logger.info(f"After filtering: {total_filtered}")
    logger.info(f"After deduplication: {len(unique_places)}")
    logger.info(f"Filter rate: {((total_raw - total_filtered) / total_raw) * 100:.1f}%")
    logger.info(f"Dedup rate: {((total_filtered - len(unique_places)) / total_filtered) * 100:.1f}%")
    logger.info("")
    logger.info(f"Filtered data: {output_path}")
    logger.info(f"Filter report: {report_path}")
    logger.info("=" * 80)
    logger.info("")
    logger.info("NEXT STEP: Review filter report and proceed to Step 2 (Place Details Enrichment)")
    logger.info(f"Estimated cost for Step 2: ${len(unique_places) * 0.023:.2f}")
    logger.info("")

if __name__ == "__main__":
    main()
