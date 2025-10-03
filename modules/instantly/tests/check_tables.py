#!/usr/bin/env python3
"""
Check all tables in Supabase and their relationships
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))
from lib.supabase_client import get_supabase

def check_table_exists(table_name: str):
    """Check if table exists and show sample data"""
    supabase = get_supabase()

    try:
        result = supabase.table(table_name).select('*').limit(1).execute()
        print(f"\n{table_name}:")
        print(f"  Status: EXISTS")
        print(f"  Rows: {len(result.data)}")
        if result.data:
            print(f"  Columns: {list(result.data[0].keys())}")
        return True
    except Exception as e:
        print(f"\n{table_name}:")
        print(f"  Status: DOES NOT EXIST or ERROR")
        print(f"  Error: {str(e)[:100]}")
        return False

def main():
    print("="*60)
    print("CHECKING SUPABASE TABLES")
    print("="*60)

    # Expected tables from migrations
    expected_tables = [
        'users',
        'instantly_campaigns_raw',
        'instantly_accounts_raw',
        'instantly_daily_analytics_raw',
        'instantly_emails_raw',
        'csv_imports_raw',
        'offers',
        'companies',
        'leads',
        'campaigns',
        'campaign_leads',
        'events'
    ]

    # Check for unexpected table
    unexpected_tables = ['email_accounts']

    print("\n--- EXPECTED TABLES ---")
    for table in expected_tables:
        check_table_exists(table)

    print("\n--- CHECKING FOR DUPLICATES/UNEXPECTED ---")
    for table in unexpected_tables:
        check_table_exists(table)

    print("\n" + "="*60)
    print("CHECKING FOREIGN KEYS AND RELATIONSHIPS")
    print("="*60)

    # Check data in key tables
    supabase = get_supabase()

    print("\ninstantly_campaigns_raw:")
    campaigns = supabase.table('instantly_campaigns_raw').select('instantly_campaign_id, campaign_name').execute()
    print(f"  Total: {len(campaigns.data)}")

    print("\ninstantly_accounts_raw:")
    accounts = supabase.table('instantly_accounts_raw').select('email, first_name, last_name').execute()
    print(f"  Total: {len(accounts.data)}")

    print("\ninstantly_daily_analytics_raw:")
    daily = supabase.table('instantly_daily_analytics_raw').select('analytics_date, sent, replies').execute()
    print(f"  Total: {len(daily.data)}")

    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)

    print("\n1. email_accounts table:")
    print("   - If empty and unused -> DELETE")
    print("   - We have instantly_accounts_raw for email accounts")

    print("\n2. Foreign Keys:")
    print("   - instantly_daily_analytics has optional campaign FK")
    print("   - Other RAW tables independent (no FKs by design)")

if __name__ == "__main__":
    main()
