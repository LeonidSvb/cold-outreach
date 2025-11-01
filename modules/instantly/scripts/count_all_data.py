#!/usr/bin/env python3
"""
Count REAL data available in Instantly API
Checks ALL endpoints with pagination
"""

import subprocess
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('INSTANTLY_API_KEY')
BASE_URL = "https://api.instantly.ai/api/v2"

def call_api(endpoint, method="GET", data=None):
    """Call API using curl"""
    url = f"{BASE_URL}{endpoint}"

    cmd = [
        "curl", "-s",
        "-H", f"Authorization: Bearer {API_KEY}",
        "-H", "Content-Type: application/json"
    ]

    if method == "POST":
        cmd.extend(["-X", "POST"])
        if data:
            cmd.extend(["-d", json.dumps(data)])

    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return json.loads(result.stdout)
    except:
        return None

def count_with_pagination(endpoint, method="GET", data_key=None):
    """Count total items with pagination support"""

    if method == "POST":
        # For POST endpoints, need initial data
        response = call_api(endpoint, "POST", data_key or {"limit": 100})
    else:
        response = call_api(endpoint, "GET")

    if not response:
        return 0, []

    # Get items
    items = response.get('items', [])
    total = len(items)

    # Check pagination
    next_cursor = response.get('next_starting_after')

    while next_cursor:
        print(f"  Fetching page... (current total: {total})")

        if method == "POST":
            data = data_key.copy() if data_key else {}
            data['starting_after'] = next_cursor
            data['limit'] = 100
            response = call_api(endpoint, "POST", data)
        else:
            response = call_api(f"{endpoint}?starting_after={next_cursor}&limit=100", "GET")

        if not response:
            break

        page_items = response.get('items', [])
        items.extend(page_items)
        total += len(page_items)

        next_cursor = response.get('next_starting_after')

        if not page_items:  # Empty page
            break

    return total, items

print("=" * 80)
print("COUNTING REAL DATA IN INSTANTLY API")
print("=" * 80)

# 1. Accounts
print("\n1. ACCOUNTS:")
count, _ = count_with_pagination("/accounts")
print(f"   TOTAL: {count} accounts")

# 2. Campaigns
print("\n2. CAMPAIGNS:")
count, campaigns = count_with_pagination("/campaigns")
print(f"   TOTAL: {count} campaigns")
campaign_ids = [c['id'] for c in campaigns]

# 3. Campaigns Analytics
print("\n3. CAMPAIGNS ANALYTICS:")
response = call_api("/campaigns/analytics")
if response and isinstance(response, list):
    print(f"   TOTAL: {len(response)} campaign analytics")

# 4. Leads (per campaign)
print("\n4. LEADS (per campaign):")
total_leads = 0
for i, campaign_id in enumerate(campaign_ids, 1):
    count, _ = count_with_pagination("/leads/list", "POST", {"campaign_id": campaign_id})
    print(f"   Campaign {i}: {count} leads")
    total_leads += count

print(f"\n   TOTAL LEADS: {total_leads}")

# 5. Daily Analytics
print("\n5. DAILY ANALYTICS:")
response = call_api("/campaigns/analytics/daily?start_date=2024-01-01&end_date=2025-12-31")
if response and isinstance(response, list):
    print(f"   TOTAL: {len(response)} days")

# 6. Steps
print("\n6. STEPS (per campaign):")
total_steps = 0
for i, campaign_id in enumerate(campaign_ids, 1):
    response = call_api(f"/campaigns/analytics/steps?campaign_id={campaign_id}")
    if response and isinstance(response, list):
        print(f"   Campaign {i}: {len(response)} steps")
        total_steps += len(response)

print(f"\n   TOTAL STEPS: {total_steps}")

# 7. Overview
print("\n7. OVERVIEW:")
response = call_api("/campaigns/analytics/overview")
if response:
    print(f"   TOTAL: 1 overview record")

print("\n" + "=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"Accounts:    {count} (CHECK THIS!)")
print(f"Campaigns:   {len(campaign_ids)}")
print(f"Leads:       {total_leads}")
print(f"Steps:       {total_steps}")
print("=" * 80)
