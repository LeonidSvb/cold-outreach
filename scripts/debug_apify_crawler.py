#!/usr/bin/env python3
import os, sys, requests, re, time, json
from dotenv import load_dotenv

load_dotenv()

APIFY_KEY = os.getenv('APIFY_API_KEY')

# Test one URL manually
url = 'https://www.directac123.com/'

actor_input = {
    'startUrls': [{'url': url}],
    'crawlerType': 'playwright:firefox',
    'maxCrawlDepth': 2,
    'maxCrawlPages': 5,
    'htmlTransformer': 'readableText',
    'removeCookieWarnings': True,
    'clickElementsCssSelector': 'a[href*="contact"], button:contains("contact"), a:contains("Contact")',
    'waitForDynamicContent': 3000,
    'maxScrollHeightPixels': 5000,
    'expandClickableElements': True,
    'saveHtml': False,
    'saveMarkdown': True
}

print(f'Testing: {url}')
print(f'Starting crawler...')

# Start run
api_url = 'https://api.apify.com/v2/acts/apify~website-content-crawler/runs'
params = {'token': APIFY_KEY}

response = requests.post(api_url, json=actor_input, headers={'Content-Type': 'application/json'}, params=params)

if response.status_code != 201:
    print(f'ERROR: {response.status_code}')
    print(response.text)
    sys.exit(1)

run_id = response.json()['data']['id']
print(f'Run ID: {run_id}')

# Wait for completion
status_url = f'https://api.apify.com/v2/actor-runs/{run_id}'

for i in range(60):
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
pages = results_response.json()

print(f'\nGot {len(pages)} pages')

for i, page in enumerate(pages[:2], 1):
    print(f'\n--- PAGE {i}: {page.get("url", "")} ---')
    text = page.get('text', '')
    markdown = page.get('markdown', '')

    print(f'Text length: {len(text)}')
    print(f'Markdown length: {len(markdown)}')
    print(f'\nFirst 500 chars of TEXT:')
    print(text[:500])
    print(f'\nFirst 500 chars of MARKDOWN:')
    print(markdown[:500])

    # Try to find emails
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails_text = re.findall(email_pattern, text)
    emails_markdown = re.findall(email_pattern, markdown)

    print(f'\nEmails found in text: {emails_text}')
    print(f'Emails found in markdown: {emails_markdown}')
