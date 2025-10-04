#!/usr/bin/env python3
"""
CSV Upload Router
Handles CSV upload to leads table with batch tracking
"""

import sys
import os
import json
import re
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from lib.supabase_client import get_supabase

router = APIRouter(prefix="/api/csv", tags=["csv"])

# Response Models
class UploadResponse(BaseModel):
    success: bool
    upload_batch_id: str
    total_rows: int
    new_leads: int
    updated_leads: int
    message: str
    errors: List[str]

class Lead(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: Optional[str]
    phone: Optional[str]
    company_name: Optional[str]
    job_title: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    linkedin_url: Optional[str]
    uploaded_at: Optional[str]
    upload_batch_id: Optional[str]

class LeadsResponse(BaseModel):
    success: bool
    leads: List[Lead]
    total: int
    upload_batch_id: Optional[str]

class UploadHistoryItem(BaseModel):
    upload_batch_id: str
    uploaded_at: str
    total_leads: int
    new_leads: int
    updated_leads: int
    unique_emails: int
    leads_with_phone: int
    leads_with_linkedin: int

class UploadHistoryResponse(BaseModel):
    success: bool
    history: List[UploadHistoryItem]


def format_phone(phone_raw):
    """Convert phone to international format"""
    if pd.isna(phone_raw) or phone_raw == '':
        return None

    digits = re.sub(r'[^0-9]', '', str(phone_raw))
    if not digits:
        return None

    return f'+{digits}'


@router.post("/upload", response_model=UploadResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload CSV file and insert leads into database

    Returns upload statistics and batch ID
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files accepted")

    try:
        # Generate batch ID
        batch_id = str(uuid.uuid4())

        # Read CSV
        content = await file.read()
        from io import BytesIO
        df = pd.read_csv(BytesIO(content))

        total_rows = len(df)
        print(f"Read CSV: {total_rows} rows")

        # Get existing emails for duplicate detection
        supabase = get_supabase()
        existing = supabase.table('leads').select('email').execute()
        existing_emails = {lead['email'] for lead in existing.data}

        # Prepare leads data
        leads = []
        new_count = 0
        update_count = 0

        for idx, row in df.iterrows():
            if pd.isna(row.get('email')):
                continue

            email = str(row.get('email'))
            is_new = email not in existing_emails

            if is_new:
                new_count += 1
            else:
                update_count += 1

            lead = {
                'first_name': str(row.get('first_name', '')),
                'last_name': str(row.get('last_name', '')) if not pd.isna(row.get('last_name')) else None,
                'email': email,
                'phone': format_phone(row.get('phone_number')),
                'linkedin_url': str(row.get('linkedin_url')) if not pd.isna(row.get('linkedin_url')) else None,
                'job_title': str(row.get('title')) if not pd.isna(row.get('title')) else None,
                'seniority': str(row.get('seniority')) if not pd.isna(row.get('seniority')) else None,
                'headline': str(row.get('headline')) if not pd.isna(row.get('headline')) else None,
                'company_name': str(row.get('company_name')) if not pd.isna(row.get('company_name')) else None,
                'company_website': str(row.get('company_url')) if not pd.isna(row.get('company_url')) else None,
                'company_linkedin': str(row.get('company_linkedin_url')) if not pd.isna(row.get('company_linkedin_url')) else None,
                'city': str(row.get('city')) if not pd.isna(row.get('city')) else None,
                'state': str(row.get('state')) if not pd.isna(row.get('state')) else None,
                'country': str(row.get('country')) if not pd.isna(row.get('country')) else None,
                'email_status': str(row.get('email_status')) if not pd.isna(row.get('email_status')) else None,
                'raw_data': json.loads(row.to_json()),
                'source_type': 'csv_upload',
                'upload_batch_id': batch_id,
                'uploaded_at': 'NOW()'
            }
            leads.append(lead)

        print(f"Prepared {len(leads)} leads (new: {new_count}, updates: {update_count})")

        # Batch insert
        batch_size = 500
        total_inserted = 0
        errors = []

        for i in range(0, len(leads), batch_size):
            batch = leads[i:i+batch_size]
            try:
                supabase.table('leads').upsert(batch, on_conflict='email').execute()
                total_inserted += len(batch)
                print(f"Batch {i//batch_size + 1}: {len(batch)} records")
            except Exception as e:
                error_msg = f"Batch {i//batch_size + 1} failed: {str(e)}"
                print(f"ERROR: {error_msg}")
                errors.append(error_msg)

        return UploadResponse(
            success=True,
            upload_batch_id=batch_id,
            total_rows=total_rows,
            new_leads=new_count,
            updated_leads=update_count,
            message=f"Successfully uploaded {total_inserted} leads",
            errors=errors
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leads", response_model=LeadsResponse)
async def get_leads(
    limit: int = Query(100, ge=1, le=1000),
    upload_batch_id: Optional[str] = None
):
    """
    Get leads from database

    Optionally filter by upload_batch_id
    """
    try:
        supabase = get_supabase()

        query = supabase.table('leads').select('*').limit(limit)

        if upload_batch_id:
            query = query.eq('upload_batch_id', upload_batch_id)

        result = query.execute()

        return LeadsResponse(
            success=True,
            leads=result.data,
            total=len(result.data),
            upload_batch_id=upload_batch_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=UploadHistoryResponse)
async def get_upload_history():
    """
    Get upload history from upload_history view
    """
    try:
        supabase = get_supabase()

        result = supabase.table('upload_history').select('*').execute()

        return UploadHistoryResponse(
            success=True,
            history=result.data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
