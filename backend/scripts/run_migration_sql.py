#!/usr/bin/env python3
"""
Run SQL migration directly via HTTP request to Supabase
"""

import sys
import os
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment
root_path = Path(__file__).parent.parent.parent
load_dotenv(root_path / '.env')

SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def run_sql(sql_statement):
    """Execute SQL via Supabase REST API"""
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"

    headers = {
        'apikey': SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {'query': sql_statement}

    response = requests.post(url, json=payload, headers=headers)

    return response

def apply_migration():
    migration_file = root_path / 'migrations' / '010_add_upload_tracking.sql'

    print(f"Reading migration: {migration_file}\n")
    migration_sql = migration_file.read_text(encoding='utf-8')

    # Execute individual ALTER statements
    statements = [
        ("Add upload_batch_id column",
         "ALTER TABLE leads ADD COLUMN IF NOT EXISTS upload_batch_id UUID;"),

        ("Add uploaded_at column",
         "ALTER TABLE leads ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMPTZ;"),

        ("Create index",
         "CREATE INDEX IF NOT EXISTS idx_leads_upload_batch ON leads(upload_batch_id);"),

        ("Update existing leads",
         "UPDATE leads SET upload_batch_id = '00000000-0000-0000-0000-000000000001'::uuid, uploaded_at = created_at WHERE upload_batch_id IS NULL;"),

        ("Create upload_history view",
         """CREATE OR REPLACE VIEW upload_history AS
         SELECT
           upload_batch_id,
           MIN(uploaded_at) as uploaded_at,
           COUNT(*) as total_leads,
           COUNT(CASE WHEN created_at = uploaded_at THEN 1 END) as new_leads,
           COUNT(CASE WHEN created_at < uploaded_at THEN 1 END) as updated_leads,
           COUNT(DISTINCT email) as unique_emails,
           COUNT(CASE WHEN phone IS NOT NULL THEN 1 END) as leads_with_phone,
           COUNT(CASE WHEN linkedin_url IS NOT NULL THEN 1 END) as leads_with_linkedin
         FROM leads
         WHERE upload_batch_id IS NOT NULL
         GROUP BY upload_batch_id
         ORDER BY uploaded_at DESC;""")
    ]

    print("Executing migration statements:\n")

    for i, (desc, sql) in enumerate(statements, 1):
        print(f"[{i}/{len(statements)}] {desc}...")

        try:
            # Use Supabase client directly
            sys.path.append(str(root_path / 'backend'))
            from lib.supabase_client import get_supabase

            supabase = get_supabase()

            # For ALTER/CREATE/UPDATE, we need to use PostgREST's query endpoint
            # Since we can't use RPC, we'll execute via raw PostgreSQL connection

            # Fallback: Print SQL for manual execution
            print(f"  SQL: {sql[:100]}...")
            print(f"  Status: NEEDS MANUAL EXECUTION IN SUPABASE DASHBOARD")
            print()

        except Exception as e:
            print(f"  ERROR: {e}\n")

    print("\nMigration SQL statements printed above.")
    print("Please execute them manually in Supabase SQL Editor:")
    print(f"{SUPABASE_URL.replace('https://', 'https://supabase.com/dashboard/project/')}/editor")

if __name__ == '__main__':
    apply_migration()
