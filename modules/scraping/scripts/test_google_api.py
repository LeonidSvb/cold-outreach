#!/usr/bin/env python3
"""
Quick test script to verify Google Places API is working
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

print(f"Testing Google Places API...")
print(f"API Key: {API_KEY[:20]}..." if API_KEY else "No API key found")
print()

# Test 1: Try new Places API
print("Test 1: New Places API (v1)")
url = "https://places.googleapis.com/v1/places:searchText"
headers = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': API_KEY,
    'X-Goog-FieldMask': 'places.id,places.displayName'
}
payload = {
    "textQuery": "real estate Bali",
    "maxResultCount": 5,
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*70 + "\n")

# Test 2: Try legacy Places API Text Search
print("Test 2: Legacy Places API (Text Search)")
url2 = "https://maps.googleapis.com/maps/api/place/textsearch/json"
params = {
    'query': 'real estate agency in Bali',
    'key': API_KEY,
    'location': '-8.4095,115.1889',
    'radius': 50000,
}

try:
    response2 = requests.get(url2, params=params, timeout=10)
    print(f"Status: {response2.status_code}")
    data = response2.json()
    print(f"Status field: {data.get('status')}")
    print(f"Results count: {len(data.get('results', []))}")

    if data.get('results'):
        print(f"\nFirst result:")
        first = data['results'][0]
        print(f"  Name: {first.get('name')}")
        print(f"  Address: {first.get('formatted_address')}")
        print(f"  Rating: {first.get('rating')}")
    else:
        print(f"Error message: {data.get('error_message')}")

except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*70 + "\n")
print("If Test 2 works, we should use Legacy Places API instead of New API")
