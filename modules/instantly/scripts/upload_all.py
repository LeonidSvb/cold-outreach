#!/usr/bin/env python3
"""
Upload ALL Instantly data to Supabase
Campaigns + Accounts + Daily Analytics
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))
from lib.supabase_client import upsert_rows, query_table, get_supabase

# Import transformation modules
from sources import (
    load_from_json,
    extract_campaigns,
    extract_accounts,
    extract_daily_analytics
)
from transform import (
    transform_campaigns,
    transform_accounts,
    transform_daily_analytics,
    validate_transformed_data
)

def upload_campaigns(file_path: str):
    """Upload campaigns to Supabase"""
    print("\n=== CAMPAIGNS ===")

    result = load_from_json(file_path)
    campaigns = extract_campaigns(result['data'])
    transformed = transform_campaigns(campaigns)

    print(f"Extracted: {len(campaigns)}")

    validation = validate_transformed_data('instantly_campaigns_raw', transformed)
    if not validation['valid']:
        print(f"Validation FAILED: {validation['error']}")
        return False

    upload_result = upsert_rows(
        table='instantly_campaigns_raw',
        rows=transformed,
        on_conflict='instantly_campaign_id'
    )

    if upload_result['success']:
        print(f"Uploaded: {upload_result['upserted']} campaigns")
        return True
    else:
        print(f"Upload FAILED: {upload_result.get('error')}")
        return False

def upload_accounts(file_path: str):
    """Upload email accounts to Supabase"""
    print("\n=== EMAIL ACCOUNTS ===")

    result = load_from_json(file_path)
    accounts = extract_accounts(result['data'])

    if not accounts:
        print("No accounts found - SKIPPED")
        return True

    transformed = transform_accounts(accounts)
    print(f"Extracted: {len(accounts)}")

    validation = validate_transformed_data('instantly_accounts_raw', transformed)
    if not validation['valid']:
        print(f"Validation FAILED: {validation['error']}")
        return False

    upload_result = upsert_rows(
        table='instantly_accounts_raw',
        rows=transformed,
        on_conflict='email'
    )

    if upload_result['success']:
        print(f"Uploaded: {upload_result['upserted']} accounts")
        return True
    else:
        print(f"Upload FAILED: {upload_result.get('error')}")
        return False

def upload_daily_analytics(file_path: str):
    """Upload daily analytics to Supabase"""
    print("\n=== DAILY ANALYTICS ===")

    result = load_from_json(file_path)
    daily = extract_daily_analytics(result['data'])

    if not daily:
        print("No daily analytics found - SKIPPED")
        return True

    transformed = transform_daily_analytics(daily)
    print(f"Extracted: {len(daily)} records")

    validation = validate_transformed_data('instantly_daily_analytics_raw', transformed)
    if not validation['valid']:
        print(f"Validation FAILED: {validation['error']}")
        return False

    # Insert daily analytics (no upsert - unique constraint on date)
    try:
        supabase = get_supabase()

        # Delete existing records first to avoid conflicts
        supabase.table('instantly_daily_analytics_raw').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()

        # Insert new records
        response = supabase.table('instantly_daily_analytics_raw').insert(transformed).execute()
        print(f"Uploaded: {len(transformed)} daily records")
        return True
    except Exception as e:
        print(f"Upload FAILED: {str(e)}")
        return False

def verify_all():
    """Verify all data in Supabase"""
    print("\n" + "="*50)
    print("VERIFICATION")
    print("="*50)

    # Campaigns
    campaigns_result = query_table('instantly_campaigns_raw', limit=100)
    if campaigns_result['success']:
        print(f"\nCampaigns in DB: {len(campaigns_result['data'])}")
        for c in campaigns_result['data']:
            print(f"  - {c['campaign_name']}")

    # Accounts
    accounts_result = query_table('instantly_accounts_raw', limit=100)
    if accounts_result['success']:
        print(f"\nAccounts in DB: {len(accounts_result['data'])}")
        for a in accounts_result['data'][:5]:
            print(f"  - {a['email']} ({a['first_name']} {a['last_name']})")
        if len(accounts_result['data']) > 5:
            print(f"  ... and {len(accounts_result['data']) - 5} more")

    # Daily analytics
    try:
        supabase = get_supabase()
        daily_result = supabase.table('instantly_daily_analytics_raw').select('*').limit(100).execute()
        print(f"\nDaily analytics in DB: {len(daily_result.data)}")
        if daily_result.data:
            print(f"  Date range: {daily_result.data[0]['analytics_date']} to {daily_result.data[-1]['analytics_date']}")
    except Exception as e:
        print(f"  Error querying daily analytics: {str(e)}")

def main():
    print("="*50)
    print("UPLOAD ALL INSTANTLY DATA TO SUPABASE")
    print("="*50)

    file_path = str(Path(__file__).parent.parent / 'results/raw_data_20250921_125555.json')

    # Upload all data
    campaigns_ok = upload_campaigns(file_path)
    accounts_ok = upload_accounts(file_path)
    daily_ok = upload_daily_analytics(file_path)

    # Verify
    verify_all()

    # Summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Campaigns: {'SUCCESS' if campaigns_ok else 'FAILED'}")
    print(f"Accounts: {'SUCCESS' if accounts_ok else 'FAILED'}")
    print(f"Daily Analytics: {'SUCCESS' if daily_ok else 'FAILED'}")

    if all([campaigns_ok, accounts_ok, daily_ok]):
        print("\nALL DATA UPLOADED SUCCESSFULLY")
    else:
        print("\nSOME UPLOADS FAILED")

if __name__ == "__main__":
    main()
