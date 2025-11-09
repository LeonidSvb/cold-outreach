#!/usr/bin/env python3
"""Test lukaskrivka/google-maps-with-contact-details actor"""

import os, sys, time, requests, json
from dotenv import load_dotenv

load_dotenv()

APIFY_KEY = os.getenv('APIFY_API_KEY')
ACTOR_ID = 'lukaskrivka/google-maps-with-contact-details'

# Test with a few companies
test_queries = [
    "60 Degrees Miami FL",
    "Direct Air Conditioning Miami FL",
    "Service Experts Miami FL"
]

print(f'Testing actor: {ACTOR_ID}')
print(f'Testing {len(test_queries)} companies\n')

actor_input = {
    "searchStringsArray": test_queries,
    "maxCrawledPlacesPerSearch": 1,
    "language": "en"
}

print('Actor input:')
print(json.dumps(actor_input, indent=2))
print()

# Start run
api_url = f'https://api.apify.com/v2/acts/{ACTOR_ID.replace("/", "~")}/runs'
params = {'token': APIFY_KEY}

print(f'API URL: {api_url}')

response = requests.post(
    api_url,
    json=actor_input,
    headers={'Content-Type': 'application/json'},
    params=params
)

if response.status_code != 201:
    print(f'ERROR: {response.status_code}')
    print(response.text)
    sys.exit(1)

run_id = response.json()['data']['id']
print(f'\nRun started: {run_id}')

# Wait for completion
status_url = f'https://api.apify.com/v2/actor-runs/{run_id}'

for _ in range(60):
    time.sleep(5)
    status_response = requests.get(status_url, params=params)
    status = status_response.json()['data']['status']
    print(f'  Status: {status}')

    if status in ['SUCCEEDED', 'FAILED', 'ABORTED', 'TIMED-OUT']:
        break

if status != 'SUCCEEDED':
    print(f'\nFAILED: {status}')
    sys.exit(1)

# Get results
dataset_id = status_response.json()['data']['defaultDatasetId']
dataset_url = f'https://api.apify.com/v2/datasets/{dataset_id}/items'

results_response = requests.get(dataset_url, params=params)
results = results_response.json()

print(f'\n{"="*70}')
print(f'RESULTS: {len(results)} places found')
print(f'{"="*70}\n')

for i, r in enumerate(results, 1):
    print(f'{i}. {r.get("title", "N/A")}')
    print(f'   Website: {r.get("website", "N/A")}')
    print(f'   Phone: {r.get("phone", "N/A")}')

    # Check all possible email fields
    email_fields = {}
    for key, value in r.items():
        if 'email' in key.lower() or 'contact' in key.lower():
            email_fields[key] = value

    if email_fields:
        print(f'   Contact fields found:')
        for key, value in email_fields.items():
            print(f'     {key}: {value}')
    else:
        print(f'   ❌ No email/contact fields')

    print()

print(f'\n{"="*70}')
print('SUMMARY:')
total_with_emails = sum(1 for r in results if any('email' in k.lower() for k in r.keys()))
print(f'Places with email fields: {total_with_emails}/{len(results)}')
print(f'{"="*70}')
