#!/usr/bin/env python3
"""
Test all possible authentication methods for Instantly API
"""

import urllib.request
import json
import base64
import ssl
import socket

def test_method(method_name, url, headers, data=None):
    """Test specific method"""
    print(f"\n--- Testing: {method_name} ---")
    print(f"URL: {url}")
    print(f"Headers: {headers}")

    try:
        if data:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
        else:
            req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = json.loads(response.read().decode())
            print(f"SUCCESS! Status: {response.code}")
            print(f"Response: {json.dumps(response_data, indent=2)[:300]}...")
            return True, response_data

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode()
        except:
            pass
        print(f"HTTP {e.code}: {e.reason}")
        print(f"Error: {error_body}")
        return False, error_body

    except Exception as e:
        print(f"Error: {e}")
        return False, str(e)

def main():
    api_key = "YzZlYTFiZmQtNmZhYy00ZTQxLTkyNWMtNDYyODQ3N2UyOTU0Om94cnhsVkhYQ3p3Rg=="
    decoded_key = base64.b64decode(api_key).decode('utf-8')

    print("=== TESTING ALL INSTANTLY API METHODS ===")
    print(f"API Key: {decoded_key}")

    # Different base URLs
    base_urls = [
        "https://api.instantly.ai/api/v1",
        "https://api.instantly.ai/api/v2",
        "https://app.instantly.ai/api/v1",
        "https://instantly.ai/api/v1"
    ]

    # Different endpoints
    endpoints = [
        "campaign/list",
        "campaigns",
        "accounts",
        "workspaces/current",
        "account/list"
    ]

    # Different auth methods
    auth_methods = [
        ("Bearer Token", {'Authorization': f'Bearer {decoded_key}'}),
        ("API Key Header", {'X-API-Key': decoded_key}),
        ("Basic Auth", {'Authorization': f'Basic {base64.b64encode(f"{decoded_key}:".encode()).decode()}'}),
        ("Custom Auth", {'instantly-api-key': decoded_key}),
    ]

    # Different User-Agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "PostmanRuntime/7.28.4",
        "curl/7.68.0",
        "Python/urllib",
        "Instantly-Client/1.0"
    ]

    successful_tests = []

    # Test combinations
    for base_url in base_urls:
        for endpoint in endpoints:
            for auth_name, auth_header in auth_methods:
                for ua in user_agents:

                    url = f"{base_url}/{endpoint}"
                    headers = {
                        'Content-Type': 'application/json',
                        'User-Agent': ua,
                        **auth_header
                    }

                    method_name = f"{base_url.split('/')[-1]} - {endpoint} - {auth_name} - {ua.split('/')[0]}"

                    success, response = test_method(method_name, url, headers)

                    if success:
                        successful_tests.append({
                            'method': method_name,
                            'url': url,
                            'headers': headers,
                            'response': response
                        })
                        print(f"\n*** FOUND WORKING METHOD! ***")
                        print(f"Method: {method_name}")
                        break

                if successful_tests:
                    break
            if successful_tests:
                break
        if successful_tests:
            break

    # Try with different HTTP methods
    if not successful_tests:
        print(f"\n=== TRYING POST METHODS ===")

        post_endpoints = [
            ("campaign/list", {}),
            ("campaigns/list", {}),
            ("accounts/list", {}),
        ]

        for endpoint, post_data in post_endpoints:
            url = f"https://api.instantly.ai/api/v1/{endpoint}"
            headers = {
                'Authorization': f'Bearer {decoded_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            success, response = test_method(f"POST {endpoint}", url, headers, post_data)
            if success:
                successful_tests.append({
                    'method': f"POST {endpoint}",
                    'url': url,
                    'headers': headers,
                    'response': response
                })
                break

    # Final results
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS")
    print(f"{'='*60}")

    if successful_tests:
        print(f"SUCCESS! Found {len(successful_tests)} working method(s):")
        for i, test in enumerate(successful_tests, 1):
            print(f"\n{i}. {test['method']}")
            print(f"   URL: {test['url']}")
            print(f"   Response preview: {str(test['response'])[:100]}...")
    else:
        print(f"FAILURE! No working methods found.")
        print(f"\nDETAILED PROBLEM ANALYSIS:")
        print(f"1. API Key format: {decoded_key[:50]}...")
        print(f"2. Key length: {len(decoded_key)} characters")
        print(f"3. Contains colon: {'Yes' if ':' in decoded_key else 'No'}")
        print(f"4. All tested combinations failed")
        print(f"5. Most common error: HTTP 401 Unauthorized")
        print(f"\nPOSSIBLE CAUSES:")
        print(f"- API key is deactivated in Instantly dashboard")
        print(f"- Account doesn't have API access enabled")
        print(f"- API key was regenerated and this one is old")
        print(f"- Account is suspended or has billing issues")
        print(f"- API endpoints have changed")
        print(f"\nRECOMMENDED ACTIONS:")
        print(f"1. Check Instantly dashboard -> Settings -> API")
        print(f"2. Verify account status and billing")
        print(f"3. Generate new API key")
        print(f"4. Contact Instantly support if issues persist")

if __name__ == "__main__":
    main()