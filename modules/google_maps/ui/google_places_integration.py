"""
Google Places API Integration for Streamlit UI
"""

import requests
import time
from typing import List, Dict
import os


def search_places(
    api_key: str,
    query: str,
    location: str,
    max_results: int = 60,
    min_rating: float = 0.0,
    min_reviews: int = 0,
    max_reviews: int = 10000
) -> List[Dict]:
    """
    Search for places using Google Places API (New)

    Args:
        api_key: Google Maps API key
        query: Search query (e.g., "real estate agency")
        location: Location (e.g., "Denpasar, Bali, Indonesia")
        max_results: Maximum results to return
        min_rating: Minimum rating filter
        min_reviews: Minimum review count
        max_reviews: Maximum review count

    Returns:
        List of business dictionaries
    """

    results = []

    # Places API (New) Text Search
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.internationalPhoneNumber,places.websiteUri,places.rating,places.userRatingCount,places.googleMapsUri"
    }

    body = {
        "textQuery": f"{query} in {location}",
        "maxResultCount": min(max_results, 20)  # API limit is 20 per request
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=30)
        response.raise_for_status()

        data = response.json()

        if "places" in data:
            for place in data["places"]:
                # Extract data
                name = place.get("displayName", {}).get("text", "N/A")
                address = place.get("formattedAddress", "N/A")
                phone = place.get("internationalPhoneNumber", "N/A")
                website = place.get("websiteUri", "N/A")
                rating = place.get("rating", 0.0)
                reviews = place.get("userRatingCount", 0)
                maps_url = place.get("googleMapsUri", "N/A")

                # Apply filters
                if rating < min_rating:
                    continue
                if reviews < min_reviews or reviews > max_reviews:
                    continue

                results.append({
                    "Name": name,
                    "Phone": phone,
                    "Rating": rating,
                    "Reviews": reviews,
                    "Address": address,
                    "Website": website,
                    "Google Maps": maps_url
                })

        return results

    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")


def search_multiple_locations(
    api_key: str,
    query: str,
    locations: List[str],
    **kwargs
) -> Dict:
    """
    Search multiple locations and combine results

    Returns:
        {
            "results": List[Dict],
            "stats": Dict with counts per location
        }
    """

    all_results = []
    stats = {}

    for location in locations:
        try:
            results = search_places(
                api_key=api_key,
                query=query,
                location=location,
                **kwargs
            )

            all_results.extend(results)
            stats[location] = len(results)

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            stats[location] = f"Error: {str(e)}"

    return {
        "results": all_results,
        "stats": stats
    }
