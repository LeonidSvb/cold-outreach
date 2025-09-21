#!/usr/bin/env python3
"""
Quick test of single company upload with curl
"""

import json
import csv
import subprocess
from pathlib import Path

def test_single_upload():
    """Test uploading a single company"""
    print("=== TESTING SINGLE COMPANY UPLOAD ===")

    # Load API key
    env_path = Path(__file__).parent.parent.parent / ".env"
    api_key = None

    with open(env_path, 'r') as f:
        for line in f:
            if line.startswith('INSTANTLY_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break

    if not api_key:
        print("No API key found")
        return

    print(f"API Key: {api_key[:20]}...")

    # Test connection first
    print("\nTesting connection...")
    cmd = [
        'curl', '-s',
        '-H', f'Authorization: Bearer {api_key}',
        '-H', 'Content-Type: application/json',
        'https://api.instantly.ai/api/v2/campaigns/analytics'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode == 0:
        campaigns = json.loads(result.stdout)
        print(f"Connection successful! Found {len(campaigns)} campaigns")
    else:
        print(f"Connection failed: {result.stderr}")
        return

    # Test creating a single lead
    print("\nCreating test lead...")

    lead_data = {
        "email": "info@testcompany123.com",
        "first_name": "Test",
        "last_name": "User",
        "company_name": "Test Company 123",
        "website": "https://testcompany123.com",
        "country": "Canada",
        "status": "lead"
    }

    cmd = [
        'curl', '-s', '-X', 'POST',
        '-H', f'Authorization: Bearer {api_key}',
        '-H', 'Content-Type: application/json',
        '-d', json.dumps(lead_data),
        'https://api.instantly.ai/api/v2/leads'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

    if result.returncode == 0:
        response = json.loads(result.stdout)
        if 'id' in response:
            print(f"Lead created successfully! ID: {response['id']}")
        else:
            print(f"Unexpected response: {response}")
    else:
        print(f"Lead creation failed: {result.stderr}")

    print("\nTest completed!")

if __name__ == "__main__":
    test_single_upload()