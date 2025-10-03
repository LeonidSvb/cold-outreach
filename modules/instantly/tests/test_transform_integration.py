#!/usr/bin/env python3
"""
Integration test for Instantly data transformation
Tests with real data from raw_data_20250921_125555.json
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / 'scripts'))

from sources import load_from_json, extract_campaigns, extract_accounts, extract_daily_analytics
from transform import transform_campaigns, transform_accounts, transform_daily_analytics, validate_transformed_data

def test_campaigns_transformation():
    """Test campaign transformation with real data"""
    print("=== Testing Campaigns Transformation ===")

    # Load real data
    result = load_from_json(str(Path(__file__).parent.parent / 'results/raw_data_20250921_125555.json'))
    print(f"Data type: {result['data_type']}")

    # Extract campaigns
    campaigns = extract_campaigns(result['data'])
    print(f"Campaigns extracted: {len(campaigns)}")

    # Transform
    transformed = transform_campaigns(campaigns)
    print(f"Campaigns transformed: {len(transformed)}")

    # Validate
    validation = validate_transformed_data('instantly_campaigns_raw', transformed)
    print(f"Validation: {validation}")

    # Show sample
    if transformed:
        sample = transformed[0]
        print(f"\nSample campaign:")
        print(f"  ID: {sample['instantly_campaign_id']}")
        print(f"  Name: {sample['campaign_name']}")
        print(f"  Status: {sample['campaign_status']}")
        print(f"  Leads: {sample['leads_count']}")
        print(f"  Raw JSON keys: {list(sample['raw_json'].keys())[:5]}...")

    return validation['valid']

def test_accounts_transformation():
    """Test accounts transformation with real data"""
    print("\n=== Testing Accounts Transformation ===")

    # Load real data
    result = load_from_json(str(Path(__file__).parent.parent / 'results/raw_data_20250921_125555.json'))

    # Extract accounts
    accounts = extract_accounts(result['data'])
    print(f"Accounts extracted: {len(accounts)}")

    if not accounts:
        print("No accounts in test data - SKIPPED")
        return True

    # Transform
    transformed = transform_accounts(accounts)
    print(f"Accounts transformed: {len(transformed)}")

    # Validate
    validation = validate_transformed_data('instantly_accounts_raw', transformed)
    print(f"Validation: {validation}")

    # Show sample
    if transformed:
        sample = transformed[0]
        print(f"\nSample account:")
        print(f"  Email: {sample['email']}")
        print(f"  Name: {sample['first_name']} {sample['last_name']}")
        print(f"  Status: {sample['account_status']}")

    return validation['valid']

def test_daily_analytics_transformation():
    """Test daily analytics transformation with real data"""
    print("\n=== Testing Daily Analytics Transformation ===")

    # Load real data
    result = load_from_json(str(Path(__file__).parent.parent / 'results/raw_data_20250921_125555.json'))

    # Extract daily analytics
    daily = extract_daily_analytics(result['data'])
    print(f"Daily records extracted: {len(daily)}")

    if not daily:
        print("No daily analytics in test data - SKIPPED")
        return True

    # Transform
    transformed = transform_daily_analytics(daily)
    print(f"Daily records transformed: {len(transformed)}")

    # Validate
    validation = validate_transformed_data('instantly_daily_analytics_raw', transformed)
    print(f"Validation: {validation}")

    # Show sample
    if transformed:
        sample = transformed[0]
        print(f"\nSample daily record:")
        print(f"  Date: {sample['analytics_date']}")
        print(f"  Sent: {sample['sent']}")
        print(f"  Opened: {sample['opened']}")
        print(f"  Replies: {sample['replies']}")

    return validation['valid']

if __name__ == "__main__":
    print("Integration Test - Instantly Transformation Module\n")

    try:
        # Run all tests
        campaigns_ok = test_campaigns_transformation()
        accounts_ok = test_accounts_transformation()
        daily_ok = test_daily_analytics_transformation()

        # Summary
        print("\n" + "="*50)
        print("INTEGRATION TEST SUMMARY")
        print("="*50)
        print(f"Campaigns: {'PASS' if campaigns_ok else 'FAIL'}")
        print(f"Accounts: {'PASS' if accounts_ok else 'FAIL'}")
        print(f"Daily Analytics: {'PASS' if daily_ok else 'FAIL'}")

        if all([campaigns_ok, accounts_ok, daily_ok]):
            print("\nALL TESTS PASSED")
        else:
            print("\nSOME TESTS FAILED")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
