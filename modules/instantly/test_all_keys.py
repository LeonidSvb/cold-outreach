#!/usr/bin/env python3
"""
Test all API keys from .env file
"""

import urllib.request
import json
import base64
import os

def decode_key(key):
    """Try to decode base64 key"""
    try:
        return base64.b64decode(key).decode('utf-8')
    except:
        return key

def test_instantly_key(key_name, api_key):
    """Test Instantly API key"""
    print(f"\n{'='*50}")
    print(f"TESTING: {key_name}")
    print(f"{'='*50}")

    decoded_key = decode_key(api_key)
    print(f"Original key: {api_key[:30]}...")
    print(f"Decoded key: {decoded_key[:30]}...")

    url = "https://api.instantly.ai/api/v1/campaign/list"
    headers = {
        'Authorization': f'Bearer {decoded_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"SUCCESS! Status: {response.code}")
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")
            return True, data

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode()
        except:
            pass
        print(f"FAILED! HTTP {e.code}: {e.reason}")
        print(f"Error: {error_body}")
        return False, None

    except Exception as e:
        print(f"ERROR: {e}")
        return False, None

def test_other_keys():
    """Test other API keys for verification"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')

    # Load all keys
    keys = {}
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#') and 'API_KEY' in line:
                key_name, value = line.split('=', 1)
                keys[key_name.strip()] = value.strip()

    print(f"Found API keys in .env:")
    for key_name, value in keys.items():
        print(f"  {key_name}: {value[:20]}...")

    # Test specifically Instantly keys
    instantly_keys = {k: v for k, v in keys.items() if 'INSTANTLY' in k}

    if not instantly_keys:
        print(f"\nNo Instantly API keys found!")
        return

    # Test each Instantly key
    for key_name, api_key in instantly_keys.items():
        success, data = test_instantly_key(key_name, api_key)
        if success:
            print(f"\n*** WORKING KEY FOUND: {key_name} ***")
            return key_name, api_key, data

    print(f"\nNo working Instantly keys found!")
    return None, None, None

if __name__ == "__main__":
    print("=== TESTING ALL API KEYS FROM .ENV ===")

    working_key, working_value, data = test_other_keys()

    if working_key:
        print(f"\n*** FINAL RESULT ***")
        print(f"Working key: {working_key}")
        print(f"Use this key for data collection!")
    else:
        print(f"\n*** NO WORKING KEYS ***")
        print(f"You need to get a new Instantly API key!")