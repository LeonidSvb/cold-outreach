#!/usr/bin/env python3
"""
Upload full CSV to Supabase leads table
Handles 1,691 leads with proper phone formatting
"""

import pandas as pd
import json
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from lib.supabase_client import get_supabase
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)


def format_phone(phone_raw):
    """Convert phone to international format"""
    if pd.isna(phone_raw) or phone_raw == '':
        return None

    digits = re.sub(r'[^0-9]', '', str(phone_raw))
    if not digits:
        return None

    return f'+{digits}'


def upload_csv():
    """Main upload function"""
    csv_path = r'C:\Users\79818\Downloads\ppc US - Canada, 11-20 _ 4 Sep   - Us - founders (1).csv'

    logger.info("CSV upload started", csv_path=csv_path)
    df = pd.read_csv(csv_path)
    logger.info("CSV loaded", total_rows=len(df))

    # Clear existing test data
    supabase = get_supabase()
    logger.debug("Clearing test data")
    supabase.table('leads').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()

    # Prepare leads data
    leads = []
    for idx, row in df.iterrows():
        if pd.isna(row.get('email')):
            continue

        lead = {
            'first_name': str(row.get('first_name', '')),
            'last_name': str(row.get('last_name', '')) if not pd.isna(row.get('last_name')) else None,
            'email': str(row.get('email')),
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
            'source_type': 'csv_upload'
        }
        leads.append(lead)

    print(f"Prepared {len(leads)} leads")

    # Batch insert
    batch_size = 500
    total_inserted = 0

    for i in range(0, len(leads), batch_size):
        batch = leads[i:i+batch_size]
        try:
            supabase.table('leads').upsert(batch, on_conflict='email').execute()
            total_inserted += len(batch)
            print(f"Batch {i//batch_size + 1}: {len(batch)} records (total: {total_inserted}/{len(leads)})")
        except Exception as e:
            print(f"ERROR in batch {i//batch_size + 1}: {e}")

    print(f"\nUpload complete! Total: {total_inserted} leads")

    # Verify
    count = supabase.table('leads').select('id', count='exact').execute()
    print(f"Database count: {count.count}")

    # Stats via MCP
    print("\nDone!")


if __name__ == '__main__':
    upload_csv()
