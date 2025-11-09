#!/usr/bin/env python3
"""Quick test of Google Maps Scraper with place URLs"""

import os, sys, time, requests, csv
from dotenv import load_dotenv

load_dotenv()

APIFY_KEY = os.getenv('APIFY_API_KEY')
ACTOR_ID = "nwua9Gu5YrADL7ZDj"

# Read one place ID
with open('data/temp/problem_sites_placeids.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    sites = list(reader)

test_site = sites[0]
place_id = test_site['placeId']
title = test_site['title']

print(f"Testing: {title}")
print(f"Place ID: {place_id}")

# Try different URL formats
url_formats = [
    f"https://www.google.com/maps/search/?api=1&query=Google&query_place_id={place_id}",
    f"https://maps.google.com/?q=place_id:{place_id}",
    f"https://www.google.com/maps/place/?q=place_id:{place_id}"
]

for i, url in enumerate(url_formats, 1):
    print(f"\n--- Test {i}: {url[:80]}... ---")

    actor_input = {
        "startUrls": [url],
        "maxCrawledPlacesPerSearch": 1,
        "language": "en",
        "scrapeCompanyContactsInfo": True,
        "maxImages": 0,
        "maxReviews": 0
    }

    # Start run
    api_url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs"
    params = {"token": APIFY_KEY}

    response = requests.post(api_url, json=actor_input, headers={"Content-Type": "application/json"}, params=params)

    if response.status_code != 201:
        print(f"ERROR: {response.status_code}")
        continue

    run_id = response.json()["data"]["id"]
    print(f"Run ID: {run_id}")

    # Wait
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"

    for _ in range(30):
        time.sleep(5)
        status_response = requests.get(status_url, params=params)
        status = status_response.json()["data"]["status"]

        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break

    print(f"Status: {status}")

    if status == "SUCCEEDED":
        dataset_id = status_response.json()["data"]["defaultDatasetId"]
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"

        results_response = requests.get(dataset_url, params=params)
        results = results_response.json()

        print(f"Results: {len(results)} places")

        if results:
            r = results[0]
            print(f"  Title: {r.get('title', '')}")
            print(f"  Website: {r.get('website', '')}")
            print(f"  Email: {r.get('email', 'N/A')}")
            print(f"  Company contacts: {r.get('companyContactsInfo', {})}")
            print(f"SUCCESS! Found data")
            break
    else:
        print(f"FAILED")

    time.sleep(2)
