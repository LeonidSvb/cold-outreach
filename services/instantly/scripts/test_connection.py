#!/usr/bin/env python3
"""
Instantly API Connection Tester
Tests various authentication methods and endpoints
"""

import urllib.request
import urllib.parse
import json
import base64
import os
from datetime import datetime

def load_api_key():
    """Load API key from .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
    
    if not os.path.exists(env_path):
        print("❌ Error: .env file not found")
        return None
        
    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('INSTANTLY_API_KEY='):
                return line.split('=', 1)[1].strip()
    
    print("❌ Error: INSTANTLY_API_KEY not found in .env")
    return None

def test_auth_method(api_key, method_name, headers):
    """Test a specific authentication method"""
    url = "https://api.instantly.ai/api/v1/campaign/list"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print(f"✅ {method_name}: SUCCESS")
            return data
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else "No error details"
        print(f"❌ {method_name}: HTTP {e.code} - {e.reason}")
        print(f"   Error details: {error_body}")
        return None
    except Exception as e:
        print(f"❌ {method_name}: {e}")
        return None

def decode_api_key(api_key):
    """Try to decode the API key if it's base64 encoded"""
    try:
        decoded = base64.b64decode(api_key).decode('utf-8')
        print(f"🔍 API key appears to be base64 encoded")
        print(f"   Decoded: {decoded}")
        return decoded
    except:
        print(f"🔍 API key is not base64 encoded (or invalid base64)")
        return api_key

def main():
    print("=== Instantly API Connection Tester ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        return
    
    print(f"🔑 API Key (first 20 chars): {api_key[:20]}...")
    print(f"🔑 API Key length: {len(api_key)} characters")
    print()
    
    # Try to decode API key
    decoded_key = decode_api_key(api_key)
    print()
    
    # Test different authentication methods
    print("🧪 Testing authentication methods:")
    print()
    
    # Method 1: Bearer token (original key)
    headers1 = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    result1 = test_auth_method(api_key, "Method 1: Bearer (original key)", headers1)
    
    # Method 2: Bearer token (decoded key if different)
    if decoded_key != api_key:
        headers2 = {
            'Authorization': f'Bearer {decoded_key}',
            'Content-Type': 'application/json'
        }
        result2 = test_auth_method(decoded_key, "Method 2: Bearer (decoded key)", headers2)
    else:
        result2 = None
        print("⏭️  Method 2: Skipped (same as Method 1)")
    
    # Method 3: API Key header (original)
    headers3 = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    result3 = test_auth_method(api_key, "Method 3: X-API-Key (original)", headers3)
    
    # Method 4: API Key header (decoded)
    if decoded_key != api_key:
        headers4 = {
            'X-API-Key': decoded_key,
            'Content-Type': 'application/json'
        }
        result4 = test_auth_method(decoded_key, "Method 4: X-API-Key (decoded)", headers4)
    else:
        result4 = None
        print("⏭️  Method 4: Skipped (same as Method 3)")
    
    # Method 5: Basic Auth with original key
    basic_auth = base64.b64encode(f'{api_key}:'.encode()).decode()
    headers5 = {
        'Authorization': f'Basic {basic_auth}',
        'Content-Type': 'application/json'
    }
    result5 = test_auth_method(api_key, "Method 5: Basic Auth", headers5)
    
    print()
    print("=== Summary ===")
    
    successful_results = []
    if result1: successful_results.append(("Method 1", result1))
    if result2: successful_results.append(("Method 2", result2))
    if result3: successful_results.append(("Method 3", result3))
    if result4: successful_results.append(("Method 4", result4))
    if result5: successful_results.append(("Method 5", result5))
    
    if successful_results:
        print(f"✅ {len(successful_results)} authentication method(s) successful!")
        
        # Save the first successful result
        method_name, data = successful_results[0]
        
        outputs_dir = os.path.join(os.path.dirname(__file__), '..', 'outputs')
        os.makedirs(outputs_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = os.path.join(outputs_dir, f'test_connection_success_{timestamp}.json')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'successful_method': method_name,
                'timestamp': timestamp,
                'data': data
            }, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Results saved to: {filepath}")
        
        # Show campaign summary if available
        if 'campaigns' in data:
            campaigns = data['campaigns']
            print(f"🎯 Found {len(campaigns)} campaigns:")
            for i, campaign in enumerate(campaigns[:5], 1):  # Show first 5
                name = campaign.get('name', 'Unnamed')
                status = campaign.get('status', 'Unknown')
                print(f"   {i}. {name} ({status})")
            if len(campaigns) > 5:
                print(f"   ... and {len(campaigns) - 5} more")
        
    else:
        print("❌ All authentication methods failed")
        print("💡 Suggestions:")
        print("   1. Check if the API key in .env is correct")
        print("   2. Verify your Instantly account has API access enabled")
        print("   3. Check if there are any IP restrictions")
        print("   4. Try regenerating the API key in Instantly dashboard")

if __name__ == "__main__":
    main()