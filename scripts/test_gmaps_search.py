#!/usr/bin/env python3
import os, sys, time, requests, csv, json
from dotenv import load_dotenv

load_dotenv()

APIFY_KEY = os.getenv('APIFY_API_KEY')
ACTOR_ID = 'nwua9Gu5YrADL7ZDj'

# Get problem sites
with open('data/temp/test_hvac.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    sites = list(reader)

# Take first site
site = sites[0]
title = site['title']
city = site['city']
search_query = f'{title} {city}'

print(f'Testing Google Maps Scraper with search query')
print(f'Query: {search_query}')
print()

actor_input = {
    'searchStringsArray': [search_query],
    'maxCrawledPlacesPerSearch': 1,
    'language': 'en',
    'scrapeCompanyContactsInfo': True,
    'maxImages': 0,
    'maxReviews': 0
}

print('Actor input:')
print(json.dumps(actor_input, indent=2))
print()

api_url = f'https://api.apify.com/v2/acts/{ACTOR_ID}/runs'
params = {'token': APIFY_KEY}

response = requests.post(api_url, json=actor_input, headers={'Content-Type': 'application/json'}, params=params)

if response.status_code != 201:
    print(f'ERROR: {response.status_code}')
    print(response.text)
    sys.exit(1)

run_id = response.json()['data']['id']
print(f'Run started: {run_id}')

# Wait
status_url = f'https://api.apify.com/v2/actor-runs/{run_id}'

for _ in range(30):
    time.sleep(5)
    status_response = requests.get(status_url, params=params)
    status = status_response.json()['data']['status']
    print(f'  Status: {status}')

    if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
        break

if status != 'SUCCEEDED':
    print(f'FAILED: {status}')
    sys.exit(1)

# Get results
dataset_id = status_response.json()['data']['defaultDatasetId']
dataset_url = f'https://api.apify.com/v2/datasets/{dataset_id}/items'

results_response = requests.get(dataset_url, params=params)
results = results_response.json()

print(f'\nResults: {len(results)} places\n')

if results:
    r = results[0]
    print(f'SUCCESS!')
    print(f'Title: {r.get("title", "")}')
    print(f'Website: {r.get("website", "")}')
    print(f'Phone: {r.get("phone", "")}')
    print(f'Email field: {r.get("email", "N/A")}')
    print(f'\nAll fields in result ({len(r)} fields):')
    for key in sorted(r.keys()):
        value = r[key]
        if isinstance(value, (str, int, float)):
            print(f'  {key}: {value}')
        elif isinstance(value, dict):
            print(f'  {key}: {{dict with {len(value)} keys}}')
        elif isinstance(value, list):
            print(f'  {key}: [list with {len(value)} items]')
        else:
            print(f'  {key}: {type(value)}')
else:
    print('No results')
