#!/usr/bin/env python3
"""
Instantly API Router
FastAPI endpoints for Instantly data synchronization
"""

import sys
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

# Add paths
backend_path = Path(__file__).parent.parent
modules_path = backend_path.parent / "modules" / "instantly" / "scripts"

sys.path.append(str(backend_path))
sys.path.append(str(modules_path))

# Import services
from services.instantly_sync import sync_from_file
from universal_collector import InstantlyUniversalCollector

router = APIRouter(prefix="/api/instantly", tags=["instantly"])

# Response Models
class SyncResponse(BaseModel):
    success: bool
    campaigns_synced: int
    accounts_synced: int
    daily_synced: int
    errors: list
    message: str

class StatusResponse(BaseModel):
    last_sync: Optional[str]
    status: str
    db_stats: dict
    instantly_stats: dict

class PreviewSummary(BaseModel):
    new: int
    updates: int
    duplicates: int

class DuplicateItem(BaseModel):
    type: str
    identifier: str
    action: str

class PreviewResponse(BaseModel):
    valid: bool
    summary: dict
    duplicates: list
    errors: list

@router.post("/preview-upload", response_model=PreviewResponse)
async def preview_upload(file: UploadFile = File(...)):
    """
    Preview what will be uploaded (DRY RUN - no DB writes)

    Returns summary with new/update/duplicate counts and duplicate details
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files accepted")

    try:
        import json
        from lib.supabase_client import query_table

        # Read file content
        content = await file.read()
        data = json.loads(content)

        # Extract data using instantly module functions
        from sources import extract_campaigns, extract_accounts, extract_daily_analytics
        from transform import transform_campaigns, transform_accounts, transform_daily_analytics

        campaigns = extract_campaigns(data)
        accounts = extract_accounts(data)
        daily = extract_daily_analytics(data)

        # Transform data
        transformed_campaigns = transform_campaigns(campaigns) if campaigns else []
        transformed_accounts = transform_accounts(accounts) if accounts else []
        transformed_daily = transform_daily_analytics(daily) if daily else []

        # Get existing data from DB
        existing_campaigns = query_table('instantly_campaigns_raw', limit=1000)
        existing_accounts = query_table('instantly_accounts_raw', limit=1000)
        existing_daily = query_table('instantly_daily_analytics_raw', limit=1000)

        existing_campaign_ids = {c['instantly_campaign_id'] for c in existing_campaigns.get('data', [])}
        existing_account_emails = {a['email'] for a in existing_accounts.get('data', [])}
        existing_daily_keys = {d.get('analytics_date') for d in existing_daily.get('data', []) if d.get('analytics_date')}

        # Analyze campaigns
        campaigns_new = sum(1 for c in transformed_campaigns if c['instantly_campaign_id'] not in existing_campaign_ids)
        campaigns_updates = len(transformed_campaigns) - campaigns_new
        campaigns_duplicates = []

        for c in transformed_campaigns:
            if c['instantly_campaign_id'] in existing_campaign_ids:
                campaigns_duplicates.append({
                    "type": "campaign",
                    "identifier": c['name'],
                    "action": "will_update"
                })

        # Analyze accounts
        accounts_new = sum(1 for a in transformed_accounts if a['email'] not in existing_account_emails)
        accounts_updates = len(transformed_accounts) - accounts_new
        accounts_duplicates = []

        for a in transformed_accounts:
            if a['email'] in existing_account_emails:
                accounts_duplicates.append({
                    "type": "account",
                    "identifier": a['email'],
                    "action": "will_update"
                })

        # Analyze daily analytics
        daily_new = sum(1 for d in transformed_daily if d.get('analytics_date') not in existing_daily_keys)
        daily_updates = len(transformed_daily) - daily_new

        # Combine all duplicates
        all_duplicates = campaigns_duplicates + accounts_duplicates

        return PreviewResponse(
            valid=True,
            summary={
                "campaigns": {
                    "new": campaigns_new,
                    "updates": campaigns_updates,
                    "duplicates": len(campaigns_duplicates),
                    "total": len(transformed_campaigns)
                },
                "accounts": {
                    "new": accounts_new,
                    "updates": accounts_updates,
                    "duplicates": len(accounts_duplicates),
                    "total": len(transformed_accounts)
                },
                "daily_analytics": {
                    "new": daily_new,
                    "updates": daily_updates,
                    "duplicates": 0,
                    "total": len(transformed_daily)
                }
            },
            duplicates=all_duplicates[:10],  # Show first 10 duplicates
            errors=[]
        )

    except Exception as e:
        return PreviewResponse(
            valid=False,
            summary={},
            duplicates=[],
            errors=[str(e)]
        )

@router.post("/sync-from-file", response_model=SyncResponse)
async def sync_json_file(file: UploadFile = File(...)):
    """
    Upload JSON file and sync to Supabase

    Accepts: raw_data or dashboard_data JSON format from Instantly
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files accepted")

    try:
        # Create uploads directory
        uploads_dir = Path("uploads/instantly")
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded file temporarily
        temp_file = uploads_dir / file.filename

        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        # Sync using service
        result = sync_from_file(str(temp_file), sync_options={
            'sync_campaigns': True,
            'sync_accounts': True,
            'sync_daily': True
        })

        # Clean up temp file
        temp_file.unlink()

        return SyncResponse(
            success=result['success'],
            campaigns_synced=result['campaigns'].get('synced', 0),
            accounts_synced=result['accounts'].get('synced', 0),
            daily_synced=result['daily_analytics'].get('synced', 0),
            errors=result.get('errors', []),
            message="Sync completed successfully" if result['success'] else "Sync failed"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync-from-api", response_model=SyncResponse)
async def sync_from_api():
    """
    Sync directly from Instantly API (real-time sync)

    Fetches latest data from Instantly API and syncs to Supabase
    """
    try:
        # Step 1: Collect from Instantly API
        collector = InstantlyUniversalCollector()
        collector.collect_all_data()

        # Get the generated file path
        results_dir = Path(__file__).parent.parent.parent / "modules" / "instantly" / "results"
        json_files = sorted(results_dir.glob("dashboard_data_*.json"), reverse=True)

        if not json_files:
            raise HTTPException(
                status_code=500,
                detail="Failed to collect data from Instantly API"
            )

        latest_file = json_files[0]

        # Step 2: Sync to Supabase
        result = sync_from_file(str(latest_file), sync_options={
            'sync_campaigns': True,
            'sync_accounts': True,
            'sync_daily': True
        })

        return SyncResponse(
            success=result['success'],
            campaigns_synced=result['campaigns'].get('synced', 0),
            accounts_synced=result['accounts'].get('synced', 0),
            daily_synced=result['daily_analytics'].get('synced', 0),
            errors=result.get('errors', []),
            message="API sync completed successfully" if result['success'] else "API sync failed"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=StatusResponse)
async def get_sync_status():
    """
    Get current sync status and statistics
    """
    try:
        from lib.supabase_client import query_table

        # Query database stats
        campaigns = query_table('instantly_campaigns_raw', limit=1000)
        accounts = query_table('instantly_accounts_raw', limit=1000)
        daily = query_table('instantly_daily_analytics_raw', limit=1000)

        return StatusResponse(
            last_sync="2 hours ago",  # TODO: Get from database
            status="healthy",
            db_stats={
                "campaigns": campaigns.get('count', 0),
                "accounts": accounts.get('count', 0),
                "daily_analytics": daily.get('count', 0)
            },
            instantly_stats={
                "total_campaigns": 4,  # TODO: Get from API
                "active_accounts": 5
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
