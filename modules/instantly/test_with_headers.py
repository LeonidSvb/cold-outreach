#!/usr/bin/env python3
"""
Test Instantly API with enhanced headers to bypass Cloudflare
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

def test_with_headers(api_key, endpoint, method='GET', data=None):
    """Test endpoint with enhanced headers"""
    base_url = "https://api.instantly.ai/api/v2"
    url = f"{base_url}/{endpoint}"

    print(f"\nTesting: {endpoint}")
    print(f"URL: {url}")

    # Enhanced headers to bypass Cloudflare
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }

    try:
        if method == 'GET':
            req = urllib.request.Request(url, headers=headers)
        else:
            json_data = json.dumps(data).encode('utf-8') if data else None
            req = urllib.request.Request(url, data=json_data, headers=headers, method=method)

        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode())
            print(f"SUCCESS: {response.code}")
            print(f"Response: {json.dumps(response_data, indent=2)[:500]}...")
            return response_data

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode()
        except:
            pass
        print(f"FAILED: HTTP {e.code}: {e.reason}")
        if error_body:
            print(f"Error: {error_body}")
    except Exception as e:
        print(f"FAILED: {e}")

    return None

def main():
    """Main execution function"""
    print("=== INSTANTLY API TEST WITH ENHANCED HEADERS ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load API key
    api_key = load_api_key()
    if not api_key:
        return

    print(f"API Key (first 20 chars): {api_key[:20]}...")
    print(f"API Key length: {len(api_key)} characters")

    # Test different endpoints
    endpoints_to_test = [
        "workspaces/current",
        "campaigns",
        "accounts"
    ]

    for endpoint in endpoints_to_test:
        print(f"\n{'='*60}")
        result = test_with_headers(api_key, endpoint)
        if result:
            print(f"SUCCESS! Working endpoint found: {endpoint}")

            # Save the working response
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_dir = os.path.join(os.path.dirname(__file__), 'results')
            os.makedirs(results_dir, exist_ok=True)

            filepath = os.path.join(results_dir, f'instantly_enhanced_test_success_{timestamp}.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'success': True,
                    'working_endpoint': endpoint,
                    'timestamp': timestamp,
                    'response': result
                }, f, indent=2, ensure_ascii=False)

            print(f"Results saved to: {filepath}")
            break

    print(f"\nTest completed.")

if __name__ == "__main__":
    main()