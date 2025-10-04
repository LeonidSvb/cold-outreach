#!/usr/bin/env python3
"""
Apply migration 010: Add upload tracking to leads table
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from lib.supabase_client import get_supabase

def apply_migration():
    supabase = get_supabase()

    migration_file = Path(__file__).parent.parent.parent / 'migrations' / '010_add_upload_tracking.sql'

    print(f"Reading migration from: {migration_file}")
    migration_sql = migration_file.read_text(encoding='utf-8')

    # Execute entire migration as single block
    print("\nExecuting migration...\n")

    try:
        # Try executing the entire migration
        result = supabase.postgrest.rpc('query', {'sql': migration_sql}).execute()
        print("SUCCESS: Migration applied")

    except Exception as e:
        print(f"ERROR: {e}")
        print("\nTrying manual execution via ALTER statements...")

        # Manual execution
        statements = [
            "ALTER TABLE leads ADD COLUMN upload_batch_id UUID",
            "ALTER TABLE leads ADD COLUMN uploaded_at TIMESTAMPTZ",
            "CREATE INDEX idx_leads_upload_batch ON leads(upload_batch_id)",
            "UPDATE leads SET upload_batch_id = '00000000-0000-0000-0000-000000000001'::uuid, uploaded_at = created_at WHERE upload_batch_id IS NULL"
        ]

        for stmt in statements:
            try:
                print(f"Executing: {stmt[:60]}...")
                supabase.postgrest.rpc('query', {'sql': stmt}).execute()
                print("  OK")
            except Exception as e2:
                if 'already exists' in str(e2).lower():
                    print("  SKIP (already exists)")
                else:
                    print(f"  FAILED: {e2}")

    print("\nMigration completed!")

if __name__ == '__main__':
    apply_migration()
