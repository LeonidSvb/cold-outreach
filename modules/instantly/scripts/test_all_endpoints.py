#!/usr/bin/env python3
"""
Test ALL Instantly API v2 Endpoints

Tests each endpoint individually and saves raw responses for analysis
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('INSTANTLY_API_KEY')
BASE_URL = "https://api.instantly.ai/api/v2"
RESULTS_DIR = Path(__file__).parent.parent / "results" / "endpoint_tests"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def call_api(endpoint, method="GET", data=None, description=""):
    """Call API using curl and save response"""

    print(f"\n{'=' * 80}")
    print(f"Testing: {description}")
    print(f"Endpoint: {method} {endpoint}")
    print('=' * 80)

    url = f"{BASE_URL}{endpoint}"

    cmd = [
        "curl", "-s", "-w", "\nHTTP_STATUS:%{http_code}",
        "-H", f"Authorization: Bearer {API_KEY}",
        "-H", "Content-Type: application/json"
    ]

    if method == "POST":
        cmd.extend(["-X", "POST"])
        if data:
            cmd.extend(["-d", json.dumps(data)])
            print(f"POST Data: {json.dumps(data, indent=2)}")

    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        output = result.stdout
        if "HTTP_STATUS:" in output:
            response_body, status_line = output.rsplit("HTTP_STATUS:", 1)
            status_code = int(status_line.strip())
        else:
            response_body = output
            status_code = result.returncode

        print(f"Status Code: {status_code}")

        # Try to parse as JSON
        try:
            response_json = json.loads(response_body)
            print(f"Response Type: JSON")

            # Print sample
            if isinstance(response_json, list):
                print(f"Array Length: {len(response_json)}")
                if len(response_json) > 0:
                    print(f"First Item Keys: {list(response_json[0].keys())}")
            elif isinstance(response_json, dict):
                print(f"Object Keys: {list(response_json.keys())}")

            # Save to file
            filename = description.replace(' ', '_').replace('/', '_').lower() + '.json'
            filepath = RESULTS_DIR / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'endpoint': endpoint,
                    'method': method,
                    'post_data': data,
                    'status_code': status_code,
                    'timestamp': datetime.now().isoformat(),
                    'response': response_json
                }, f, indent=2, ensure_ascii=False)

            print(f"Saved: {filepath.name}")

            return {'success': True, 'data': response_json, 'status': status_code}

        except json.JSONDecodeError:
            print(f"Response Type: Not JSON")
            print(f"Raw Response: {response_body[:500]}")

            return {'success': False, 'error': 'Not JSON', 'raw': response_body}

    except subprocess.TimeoutExpired:
        print("ERROR: Request timeout (60s)")
        return {'success': False, 'error': 'Timeout'}
    except Exception as e:
        print(f"ERROR: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """Test all endpoints"""

    print("\n" + "=" * 80)
    print("INSTANTLY API V2 - ENDPOINT TESTING")
    print("=" * 80)
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Results: {RESULTS_DIR}")
    print()

    # Test 1: Campaigns Analytics (all campaigns)
    call_api("/campaigns/analytics", "GET", description="Campaigns Analytics")

    # Test 2: Get campaign IDs for further testing
    campaigns_result = call_api("/campaigns/analytics", "GET", description="Get Campaign IDs")

    campaign_ids = []
    if campaigns_result['success'] and isinstance(campaigns_result['data'], list):
        campaign_ids = [c['campaign_id'] for c in campaigns_result['data'] if 'campaign_id' in c]
        print(f"\nFound {len(campaign_ids)} campaigns")

    # Test 3: Accounts
    call_api("/accounts", "GET", description="Email Accounts")

    # Test 4: Overview
    call_api("/campaigns/analytics/overview", "GET", description="Analytics Overview")

    # Test 5: Daily Analytics (last 90 days)
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    call_api(f"/campaigns/analytics/daily?start_date={start_date}&end_date={end_date}",
             "GET", description=f"Daily Analytics ({start_date} to {end_date})")

    # Test 6: Emails (limit 500)
    call_api("/emails?limit=500", "GET", description="Emails (limit 500)")

    # Test 7: Emails with pagination (if needed)
    call_api("/emails?limit=1000", "GET", description="Emails (limit 1000)")

    # Test 8-11: Per-campaign endpoints
    for i, campaign_id in enumerate(campaign_ids[:4], 1):  # Test first 4 campaigns

        # Campaign detailed analytics
        call_api(f"/campaigns/analytics?id={campaign_id}",
                "GET", description=f"Campaign {i} Detailed Analytics")

        # Campaign steps
        call_api(f"/campaigns/analytics/steps?campaign_id={campaign_id}",
                "GET", description=f"Campaign {i} Steps Analytics")

        # Campaign daily analytics
        call_api(f"/campaigns/analytics/daily?campaign_id={campaign_id}&start_date={start_date}&end_date={end_date}",
                "GET", description=f"Campaign {i} Daily Analytics")

        # Campaign LEADS (POST request!)
        call_api("/leads/list", "POST",
                data={"campaign_id": campaign_id, "limit": 1000},
                description=f"Campaign {i} Leads (POST)")

    # Test 12: Try to get all leads (if endpoint exists)
    call_api("/leads/list", "POST",
            data={"limit": 5000},
            description="All Leads (no campaign filter)")

    # Test 13: Try /leads endpoint (might be 404, but test anyway)
    call_api("/leads", "GET", description="Leads GET (might be 404)")

    # Test 14: Try /campaigns endpoint (list all campaigns)
    call_api("/campaigns", "GET", description="Campaigns List")

    # Summary
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    print(f"Results saved to: {RESULTS_DIR}")
    print("\nNext steps:")
    print("1. Review JSON files in endpoint_tests/")
    print("2. Identify which endpoints have data")
    print("3. Update database schema based on actual responses")
    print()

if __name__ == "__main__":
    main()
