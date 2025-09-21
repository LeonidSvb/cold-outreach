#!/usr/bin/env python3
"""
Simple test - get campaigns list
"""

import urllib.request
import json
import base64
import os

def test_campaigns():
    # Load API key
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')

    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('INSTANTLY_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break

    # Decode API key
    try:
        decoded_key = base64.b64decode(api_key).decode('utf-8')
        print(f"Decoded API key: {decoded_key}")
    except:
        decoded_key = api_key
        print(f"Using raw API key: {api_key}")

    # Test v1 campaigns endpoint
    url = "https://api.instantly.ai/api/v1/campaign/list"
    headers = {
        'Authorization': f'Bearer {decoded_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f"\nTesting: {url}")
    print(f"Headers: {headers}")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"\nSUCCESS!")
            print(f"Status: {response.code}")
            print(f"Response: {json.dumps(data, indent=2)}")
            return data

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode()
        except:
            pass
        print(f"\nFAILED!")
        print(f"HTTP {e.code}: {e.reason}")
        print(f"Error body: {error_body}")
        return None

    except Exception as e:
        print(f"\nERROR: {e}")
        return None

if __name__ == "__main__":
    test_campaigns()