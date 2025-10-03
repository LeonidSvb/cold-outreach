#!/usr/bin/env python3
"""
Instantly Sync Service
Production-ready orchestration service for Instantly → Supabase sync

Features:
- Syncs campaigns, accounts, daily analytics
- Incremental sync (upsert)
- Error handling & logging
- Returns detailed sync results
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add paths
backend_path = Path(__file__).parent.parent
modules_path = backend_path.parent / "modules" / "instantly" / "scripts"

sys.path.append(str(backend_path))
sys.path.append(str(modules_path))

# Backend imports
from lib.supabase_client import upsert_rows, query_table, get_supabase

# Instantly module imports
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

def sync_from_file(file_path: str, sync_options: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Sync Instantly data from JSON file to Supabase (Production-ready)

    Args:
        file_path: Path to JSON file (raw_data or dashboard_data)
        sync_options: Optional dict with:
            - sync_campaigns: bool (default True)
            - sync_accounts: bool (default True)
            - sync_daily: bool (default True)

    Returns:
        Dict with sync results:
        {
            "success": bool,
            "file_path": str,
            "campaigns": {"synced": int, "status": str},
            "accounts": {"synced": int, "status": str},
            "daily_analytics": {"synced": int, "status": str},
            "errors": []
        }

    Example:
        result = sync_from_file('modules/instantly/results/raw_data.json')
    """
    sync_options = sync_options or {}
    sync_campaigns_enabled = sync_options.get('sync_campaigns', True)
    sync_accounts_enabled = sync_options.get('sync_accounts', True)
    sync_daily_enabled = sync_options.get('sync_daily', True)

    results = {
        "success": True,
        "file_path": file_path,
        "campaigns": {"synced": 0, "status": "skipped"},
        "accounts": {"synced": 0, "status": "skipped"},
        "daily_analytics": {"synced": 0, "status": "skipped"},
        "errors": []
    }

    try:
        # Step 1: Sync Campaigns
        if sync_campaigns_enabled:
            campaigns_result = _upload_campaigns(file_path)
            results['campaigns'] = campaigns_result
            if not campaigns_result.get('success'):
                results['errors'].append(campaigns_result.get('error'))

        # Step 2: Sync Accounts
        if sync_accounts_enabled:
            accounts_result = _upload_accounts(file_path)
            results['accounts'] = accounts_result
            if not accounts_result.get('success'):
                results['errors'].append(accounts_result.get('error'))

        # Step 3: Sync Daily Analytics
        if sync_daily_enabled:
            daily_result = _upload_daily_analytics(file_path)
            results['daily_analytics'] = daily_result
            if not daily_result.get('success'):
                results['errors'].append(daily_result.get('error'))

        # Final status
        if results['errors']:
            results['success'] = False

        return results

    except Exception as e:
        results['success'] = False
        results['errors'].append(str(e))
        return results

def _upload_campaigns(file_path: str) -> Dict[str, Any]:
    """
    Internal: Upload campaigns to Supabase

    Returns:
        Dict with result: {"success": bool, "synced": int, "status": str, "error": str}
    """
    try:
        result = load_from_json(file_path)
        campaigns = extract_campaigns(result['data'])

        if not campaigns:
            return {"success": True, "synced": 0, "status": "no_data"}

        transformed = transform_campaigns(campaigns)

        validation = validate_transformed_data('instantly_campaigns_raw', transformed)
        if not validation['valid']:
            return {
                "success": False,
                "synced": 0,
                "status": "validation_error",
                "error": validation['error']
            }

        upload_result = upsert_rows(
            table='instantly_campaigns_raw',
            rows=transformed,
            on_conflict='instantly_campaign_id'
        )

        if upload_result['success']:
            return {
                "success": True,
                "synced": upload_result['upserted'],
                "status": "completed"
            }
        else:
            return {
                "success": False,
                "synced": 0,
                "status": "upload_error",
                "error": upload_result.get('error')
            }

    except Exception as e:
        return {
            "success": False,
            "synced": 0,
            "status": "error",
            "error": str(e)
        }

def _upload_accounts(file_path: str) -> Dict[str, Any]:
    """Internal: Upload email accounts to Supabase"""
    try:
        result = load_from_json(file_path)
        accounts = extract_accounts(result['data'])

        if not accounts:
            return {"success": True, "synced": 0, "status": "no_data"}

        transformed = transform_accounts(accounts)

        validation = validate_transformed_data('instantly_accounts_raw', transformed)
        if not validation['valid']:
            return {
                "success": False,
                "synced": 0,
                "status": "validation_error",
                "error": validation['error']
            }

        upload_result = upsert_rows(
            table='instantly_accounts_raw',
            rows=transformed,
            on_conflict='email'
        )

        if upload_result['success']:
            return {
                "success": True,
                "synced": upload_result['upserted'],
                "status": "completed"
            }
        else:
            return {
                "success": False,
                "synced": 0,
                "status": "upload_error",
                "error": upload_result.get('error')
            }

    except Exception as e:
        return {
            "success": False,
            "synced": 0,
            "status": "error",
            "error": str(e)
        }

def _upload_daily_analytics(file_path: str) -> Dict[str, Any]:
    """Internal: Upload daily analytics to Supabase"""
    try:
        result = load_from_json(file_path)
        daily = extract_daily_analytics(result['data'])

        if not daily:
            return {"success": True, "synced": 0, "status": "no_data"}

        transformed = transform_daily_analytics(daily)

        validation = validate_transformed_data('instantly_daily_analytics_raw', transformed)
        if not validation['valid']:
            return {
                "success": False,
                "synced": 0,
                "status": "validation_error",
                "error": validation['error']
            }

        # Insert daily analytics (delete old + insert new)
        supabase = get_supabase()

        # Delete existing records first
        supabase.table('instantly_daily_analytics_raw').delete().neq(
            'id', '00000000-0000-0000-0000-000000000000'
        ).execute()

        # Insert new records
        response = supabase.table('instantly_daily_analytics_raw').insert(transformed).execute()

        return {
            "success": True,
            "synced": len(transformed),
            "status": "completed"
        }

    except Exception as e:
        return {
            "success": False,
            "synced": 0,
            "status": "error",
            "error": str(e)
        }

# Test function (CLI usage)
if __name__ == "__main__":
    import json

    print("="*60)
    print("INSTANTLY SYNC SERVICE - TEST")
    print("="*60)

    # Default test file
    test_file = str(
        Path(__file__).parent.parent.parent /
        'modules/instantly/results/raw_data_20250921_125555.json'
    )

    print(f"\nSyncing from: {test_file}")

    # Run sync
    result = sync_from_file(test_file)

    # Print results
    print("\n" + "="*60)
    print("SYNC RESULTS")
    print("="*60)
    print(json.dumps(result, indent=2))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Overall: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Campaigns: {result['campaigns']['synced']} synced ({result['campaigns']['status']})")
    print(f"Accounts: {result['accounts']['synced']} synced ({result['accounts']['status']})")
    print(f"Daily: {result['daily_analytics']['synced']} synced ({result['daily_analytics']['status']})")

    if result['errors']:
        print(f"\nErrors: {result['errors']}")
    else:
        print("\nNo errors")
