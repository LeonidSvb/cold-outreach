#!/usr/bin/env python3
"""
=== INSTANTLY API CONNECTION TESTER ===
Quick test script to verify API key and campaign access

USAGE:
1. Set API_KEY and CAMPAIGN_ID below
2. Run: python test_instantly_connection.py
3. Check if connection works before bulk upload
"""

import requests
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from logger.universal_logger import get_logger

logger = get_logger(__name__)

# ============================================================================
# CONFIGURATION - SET YOUR CREDENTIALS HERE
# ============================================================================

API_KEY = ""  # Your Instantly API key
CAMPAIGN_ID = ""  # Your campaign ID

# ============================================================================

def test_api_connection():
    """Test Instantly API connection"""

    if not API_KEY:
        print("\n❌ ERROR: API_KEY not set")
        print("Please set API_KEY in the script")
        return False

    print("\n" + "="*60)
    print("TESTING INSTANTLY API CONNECTION")
    print("="*60)

    # Test 1: Get workspace info
    print("\n[1/3] Testing API key...")
    try:
        response = requests.get(
            "https://api.instantly.ai/api/v2/workspace",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        response.raise_for_status()
        workspace = response.json()
        print(f"✅ API key valid")
        print(f"   Workspace: {workspace.get('name', 'N/A')}")
    except Exception as e:
        print(f"❌ API key test failed: {str(e)}")
        return False

    # Test 2: Get campaign info (if campaign_id provided)
    if CAMPAIGN_ID:
        print("\n[2/3] Testing campaign access...")
        try:
            response = requests.get(
                f"https://api.instantly.ai/api/v2/campaign/{CAMPAIGN_ID}",
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=30
            )
            response.raise_for_status()
            campaign = response.json()
            print(f"✅ Campaign found")
            print(f"   Name: {campaign.get('name', 'N/A')}")
            print(f"   Status: {campaign.get('status', 'N/A')}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"❌ Campaign not found - check CAMPAIGN_ID")
            else:
                print(f"❌ Campaign access failed: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ Campaign test failed: {str(e)}")
            return False
    else:
        print("\n[2/3] Skipping campaign test (CAMPAIGN_ID not set)")

    # Test 3: List campaigns
    print("\n[3/3] Fetching available campaigns...")
    try:
        response = requests.get(
            "https://api.instantly.ai/api/v2/campaign/list",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )
        response.raise_for_status()
        campaigns = response.json()

        if isinstance(campaigns, list) and campaigns:
            print(f"✅ Found {len(campaigns)} campaigns:")
            for i, camp in enumerate(campaigns[:5], 1):
                print(f"   {i}. {camp.get('name', 'N/A')} (ID: {camp.get('id', 'N/A')})")
            if len(campaigns) > 5:
                print(f"   ... and {len(campaigns) - 5} more")
        else:
            print("⚠️  No campaigns found in workspace")
    except Exception as e:
        print(f"⚠️  Could not list campaigns: {str(e)}")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    print("\nYou're ready to upload leads!")
    print("\nNext step:")
    print("1. Copy your CAMPAIGN_ID from the list above")
    print("2. Set it in upload_csv_to_campaign.py")
    print("3. Run the upload script")
    print("="*60 + "\n")

    return True


if __name__ == "__main__":
    success = test_api_connection()
    sys.exit(0 if success else 1)
