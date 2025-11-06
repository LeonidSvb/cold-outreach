#!/usr/bin/env python3
"""
=== IMPORT LEADS TO SUPABASE ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
Imports leads from CSV to Supabase with auto-deduplication

FEATURES:
- Auto-detects CSV structure
- Deduplicates by email OR phone
- Merges data if duplicate found
- Tracks sources (Apollo, Instantly, manual)
- Flexible JSONB storage for extra fields

USAGE:
python scripts/data_import/import_leads_to_supabase.py path/to/leads.csv [source_name]

EXAMPLES:
python scripts/data_import/import_leads_to_supabase.py data.csv apollo
python scripts/data_import/import_leads_to_supabase.py leads.csv instantly
"""

import os
import sys
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase package not installed")
    print("Install with: pip install supabase")
    sys.exit(1)

# Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Core field mapping
CORE_FIELDS = {
    'email': 'email',
    'phone_number': 'phone_number',
    'sanitized_phone_number': 'phone_number',
    'first_name': 'first_name',
    'last_name': 'last_name',
    'full_name': 'full_name',
    'company_name': 'company_name',
    'company_domain': 'company_domain',
    'company_url': 'company_url',
    'company_linkedin_url': 'company_linkedin_url',
    'estimated_num_employees': 'estimated_num_employees',
    'title': 'title',
    'linkedin_url': 'linkedin_url',
    'headline': 'headline',
    'seniority': 'seniority',
    'country': 'country',
    'state': 'state',
    'city': 'city',
    'industry': 'industry',
    'email_status': 'email_status',
}

STATS = {
    'total_rows': 0,
    'new_leads': 0,
    'updated_leads': 0,
    'skipped': 0,
    'errors': 0
}

def get_supabase_client() -> Client:
    """Get Supabase client"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")

    return create_client(SUPABASE_URL, SUPABASE_KEY)

def normalize_csv_row(row: Dict) -> Dict:
    """
    Normalize CSV row to match Supabase schema
    """
    lead = {}
    extra_data = {}

    # Map core fields
    for csv_field, db_field in CORE_FIELDS.items():
        if csv_field in row and row[csv_field]:
            value = row[csv_field].strip()
            if value:
                # Convert numeric fields
                if db_field == 'estimated_num_employees' and value.isdigit():
                    lead[db_field] = int(value)
                else:
                    lead[db_field] = value

    # Handle full_name if missing
    if 'full_name' not in lead and ('first_name' in lead or 'last_name' in lead):
        first = lead.get('first_name', '')
        last = lead.get('last_name', '')
        lead['full_name'] = f"{first} {last}".strip()

    # All other fields go to extra_data
    for key, value in row.items():
        if key not in CORE_FIELDS and value and value.strip():
            # Skip weird columns
            if key in ['company_name+', 'loction+', '']:
                continue
            extra_data[key] = value.strip()

    if extra_data:
        lead['extra_data'] = extra_data

    return lead

def find_existing_lead(supabase: Client, email: Optional[str], phone: Optional[str]) -> Optional[Dict]:
    """
    Find existing lead by email OR phone
    """
    if not email and not phone:
        return None

    try:
        # Search by email first
        if email:
            result = supabase.table('leads').select('*').eq('email', email).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]

        # Then by phone
        if phone:
            result = supabase.table('leads').select('*').eq('phone_number', phone).execute()
            if result.data and len(result.data) > 0:
                return result.data[0]

        return None

    except Exception as e:
        print(f"Error searching for lead: {e}")
        return None

def merge_lead_data(existing: Dict, new_data: Dict, source: str) -> Dict:
    """
    Merge new data into existing lead
    Strategy: prefer newer/richer data
    """
    updated = existing.copy()

    # Update core fields if new data is richer
    for field, value in new_data.items():
        if field in ['extra_data', 'sources']:
            continue

        # Update if field was empty or new value is longer
        if not updated.get(field) or (value and len(str(value)) > len(str(updated.get(field, '')))):
            updated[field] = value

    # Merge extra_data
    existing_extra = existing.get('extra_data', {})
    new_extra = new_data.get('extra_data', {})
    updated['extra_data'] = {**existing_extra, **new_extra}

    # Track sources
    existing_sources = existing.get('sources', [])
    source_tag = f"{source}_{datetime.now().strftime('%Y%m%d')}"

    if source_tag not in existing_sources:
        existing_sources.append(source_tag)

    updated['sources'] = existing_sources
    updated['updated_at'] = datetime.now().isoformat()

    return updated

def insert_lead(supabase: Client, lead_data: Dict, source: str) -> bool:
    """
    Insert new lead into Supabase
    """
    try:
        # Add metadata
        lead_data['original_source'] = source
        lead_data['sources'] = [f"{source}_{datetime.now().strftime('%Y%m%d')}"]
        lead_data['created_at'] = datetime.now().isoformat()
        lead_data['updated_at'] = datetime.now().isoformat()

        result = supabase.table('leads').insert(lead_data).execute()

        if result.data:
            STATS['new_leads'] += 1
            return True
        else:
            STATS['errors'] += 1
            return False

    except Exception as e:
        print(f"Error inserting lead: {e}")
        STATS['errors'] += 1
        return False

def update_lead(supabase: Client, lead_id: str, updated_data: Dict) -> bool:
    """
    Update existing lead
    """
    try:
        # Remove id from update data
        update_payload = {k: v for k, v in updated_data.items() if k != 'id'}

        result = supabase.table('leads').update(update_payload).eq('id', lead_id).execute()

        if result.data:
            STATS['updated_leads'] += 1
            return True
        else:
            STATS['errors'] += 1
            return False

    except Exception as e:
        print(f"Error updating lead: {e}")
        STATS['errors'] += 1
        return False

def import_csv(file_path: str, source: str = 'manual'):
    """
    Import CSV file to Supabase
    """
    print("=" * 70)
    print("IMPORT LEADS TO SUPABASE")
    print("=" * 70)
    print(f"\nFile: {file_path}")
    print(f"Source: {source}")
    print()

    # Check file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return

    # Get Supabase client
    try:
        supabase = get_supabase_client()
        print(f"Connected to Supabase: {SUPABASE_URL}")
        print()
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        return

    # Read CSV
    print("Reading CSV...")

    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, start=1):
            STATS['total_rows'] += 1

            # Skip rows without email AND phone
            if not row.get('email') and not row.get('phone_number'):
                STATS['skipped'] += 1
                continue

            # Normalize row
            lead_data = normalize_csv_row(row)

            # Find existing
            existing = find_existing_lead(
                supabase,
                lead_data.get('email'),
                lead_data.get('phone_number')
            )

            if existing:
                # Update existing
                merged = merge_lead_data(existing, lead_data, source)
                success = update_lead(supabase, existing['id'], merged)

                if success:
                    print(f"[{idx}] Updated: {lead_data.get('email', lead_data.get('phone_number'))}")
            else:
                # Insert new
                success = insert_lead(supabase, lead_data, source)

                if success:
                    print(f"[{idx}] Inserted: {lead_data.get('email', lead_data.get('phone_number'))}")

            # Progress indicator
            if idx % 50 == 0:
                print(f"\n--- Processed {idx} rows ---\n")

    # Summary
    print()
    print("=" * 70)
    print("IMPORT SUMMARY")
    print("=" * 70)
    print(f"Total rows:      {STATS['total_rows']}")
    print(f"New leads:       {STATS['new_leads']}")
    print(f"Updated leads:   {STATS['updated_leads']}")
    print(f"Skipped:         {STATS['skipped']}")
    print(f"Errors:          {STATS['errors']}")
    print("=" * 70)

def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python import_leads_to_supabase.py <csv_file> [source]")
        print("\nExamples:")
        print("  python import_leads_to_supabase.py data.csv apollo")
        print("  python import_leads_to_supabase.py leads.csv instantly")
        sys.exit(1)

    csv_file = sys.argv[1]
    source = sys.argv[2] if len(sys.argv) > 2 else 'manual'

    import_csv(csv_file, source)

if __name__ == "__main__":
    main()
