#!/usr/bin/env python3
"""
Migrate data from csv_imports_raw to leads table
Handles phone formatting and preserves full CSV data
"""

import json
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.supabase_client import get_supabase
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)


def format_phone(phone_raw):
    """
    Convert phone to international format
    14154046407.0 -> +14154046407
    """
    if not phone_raw or phone_raw == '':
        return None

    # Remove all non-digits
    digits = re.sub(r'[^0-9]', '', str(phone_raw))

    if not digits:
        return None

    # Add + prefix for international format
    return f'+{digits}'


def migrate_csv_to_leads():
    """
    Main migration function
    """
    logger.info("CSV to leads migration started")
    supabase = get_supabase()

    # Get CSV data
    print("Fetching CSV data from csv_imports_raw...")
    response = supabase.table('csv_imports_raw').select('*').order('uploaded_at', desc=True).limit(1).execute()

    if not response.data:
        print("ERROR: No CSV data found")
        logger.error("No CSV data found in csv_imports_raw")
        return

    csv_import = response.data[0]
    raw_data_str = csv_import['raw_data']
    logger.info("CSV data fetched", csv_id=csv_import.get('id'))

    # Parse JSON string
    print("Parsing CSV rows...")
    if isinstance(raw_data_str, str):
        csv_rows = json.loads(raw_data_str)
    else:
        csv_rows = raw_data_str

    print(f"Found {len(csv_rows)} rows")

    # Prepare leads data
    leads_data = []
    for row in csv_rows:
        if not row.get('email'):
            continue

        lead = {
            'first_name': row.get('first_name') or '',
            'last_name': row.get('last_name') or '',
            'email': row.get('email'),
            'phone': format_phone(row.get('phone')),
            'linkedin_url': row.get('linkedin_url'),
            'job_title': row.get('title'),
            'seniority': row.get('seniority'),
            'headline': row.get('headline'),
            'company_name': row.get('company_name'),
            'company_website': row.get('company_url'),
            'company_linkedin': row.get('company_linkedin_url'),
            'city': row.get('city'),
            'state': row.get('state'),
            'country': row.get('country'),
            'email_status': row.get('email_status'),
            'raw_data': row,
            'source_type': 'csv_upload'
        }

        leads_data.append(lead)

    # Batch insert
    print(f"Inserting {len(leads_data)} leads...")
    batch_size = 500
    total_inserted = 0

    for i in range(0, len(leads_data), batch_size):
        batch = leads_data[i:i+batch_size]
        try:
            result = supabase.table('leads').upsert(batch, on_conflict='email').execute()
            total_inserted += len(batch)
            print(f"Inserted batch {i//batch_size + 1}: {len(batch)} records (total: {total_inserted})")
        except Exception as e:
            print(f"ERROR in batch {i//batch_size + 1}: {e}")

    print(f"\nMigration complete!")
    print(f"Total leads inserted: {total_inserted}")
    logger.info("Migration completed", total_inserted=total_inserted)

    # Verify
    count_result = supabase.table('leads').select('id', count='exact').execute()
    print(f"Total leads in database: {count_result.count}")
    logger.info("Migration verified", total_in_db=count_result.count)


if __name__ == '__main__':
    try:
        migrate_csv_to_leads()
    except Exception as e:
        logger.error("Migration failed", error=e)
        raise
