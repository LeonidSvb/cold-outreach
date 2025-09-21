#!/usr/bin/env python3
"""
Simple Instantly API Connection Test
No emojis, no external dependencies
"""

import urllib.request
import urllib.parse
import json
import base64
import os
from datetime import datetime

def load_api_key():
    """Load API key from .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')

    if not os.path.exists(env_path):
        print("Error: .env file not found")
        return None

    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('INSTANTLY_API_KEY='):
                api_key = line.split('=', 1)[1].strip()

                # Try to decode if base64 encoded
                try:
                    decoded = base64.b64decode(api_key).decode('utf-8')
                    print(f"API key decoded from base64")
                    return decoded
                except:
                    print(f"Using API key as-is")
                    return api_key

    print("Error: INSTANTLY_API_KEY not found in .env")
    return None

def test_endpoint(api_key, endpoint, method='GET', data=None):
    """Test a specific endpoint"""
    base_url_v1 = "https://api.instantly.ai/api/v1"
    base_url_v2 = "https://api.instantly.ai/api/v2"

    # Test both v1 and v2
    for version, base_url in [("v1", base_url_v1), ("v2", base_url_v2)]:
        url = f"{base_url}/{endpoint}"

        print(f"\nTesting {version}: {endpoint}")

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        try:
            if method == 'GET':
                req = urllib.request.Request(url, headers=headers)
            else:
                json_data = json.dumps(data).encode('utf-8') if data else None
                req = urllib.request.Request(url, data=json_data, headers=headers, method=method)

            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode())
                print(f"SUCCESS: {version} - {response.code}")
                print(f"Response: {json.dumps(response_data, indent=2)[:500]}...")
                return version, response_data

        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode()
            except:
                pass
            print(f"FAILED: {version} - HTTP {e.code}: {e.reason}")
            if error_body:
                print(f"Error: {error_body}")
        except Exception as e:
            print(f"FAILED: {version} - {e}")

    return None, None

def main():
    """Main execution function"""
    print("=== INSTANTLY API CONNECTION TEST ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load API key
    api_key = load_api_key()
    if not api_key:
        return

    print(f"API Key (first 20 chars): {api_key[:20]}...")
    print(f"API Key length: {len(api_key)} characters")
    print()

    # Test different endpoints in order of simplicity
    endpoints_to_test = [
        "campaigns",
        "campaign/list",
        "accounts",
        "workspaces/current"
    ]

    working_version = None
    working_endpoint = None

    for endpoint in endpoints_to_test:
        print(f"\n{'='*50}")
        print(f"TESTING ENDPOINT: {endpoint}")
        print(f"{'='*50}")

        version, response = test_endpoint(api_key, endpoint)
        if version and response:
            working_version = version
            working_endpoint = endpoint
            print(f"\nFOUND WORKING ENDPOINT!")
            print(f"Version: {version}")
            print(f"Endpoint: {endpoint}")

            # Save the working response
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_dir = os.path.join(os.path.dirname(__file__), 'results')
            os.makedirs(results_dir, exist_ok=True)

            filepath = os.path.join(results_dir, f'instantly_test_success_{timestamp}.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'success': True,
                    'working_version': version,
                    'working_endpoint': endpoint,
                    'timestamp': timestamp,
                    'response': response
                }, f, indent=2, ensure_ascii=False)

            print(f"Results saved to: {filepath}")
            break

    if not working_version:
        print(f"\nNO WORKING ENDPOINTS FOUND")
        print(f"All endpoints failed. Possible issues:")
        print(f"1. API key is invalid or expired")
        print(f"2. Account doesn't have API access")
        print(f"3. IP is blocked or rate limited")
        print(f"4. Cloudflare protection is blocking requests")

    print(f"\nTest completed.")

if __name__ == "__main__":
    main()