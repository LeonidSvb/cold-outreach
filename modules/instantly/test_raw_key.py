#!/usr/bin/env python3
"""
Test with RAW base64 key (no decoding)
"""

import urllib.request
import json

def test_raw_key():
    # Use RAW base64 key exactly as in n8n
    raw_key = "YzZlYTFiZmQtNmZhYy00ZTQxLTkyNWMtNDYyODQ3N2UyOTU0Om94cnhsVkhYQ3p3Rg=="

    url = "https://api.instantly.ai/api/v2/campaigns/analytics"
    headers = {
        'Authorization': f'Bearer {raw_key}',
        'Content-Type': 'application/json'
    }

    print(f"Testing with RAW base64 key:")
    print(f"URL: {url}")
    print(f"Auth header: Bearer {raw_key}")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"\nSUCCESS! Status: {response.code}")
            print(f"Found {len(data)} campaigns:")

            for i, campaign in enumerate(data, 1):
                name = campaign.get('campaign_name', 'Unknown')
                status = campaign.get('campaign_status', 'Unknown')
                leads = campaign.get('leads_count', 0)
                sent = campaign.get('emails_sent_count', 0)
                replies = campaign.get('reply_count', 0)

                print(f"{i}. {name}")
                print(f"   Status: {status}, Leads: {leads}, Sent: {sent}, Replies: {replies}")

            return data

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_raw_key()