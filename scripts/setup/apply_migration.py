#!/usr/bin/env python3
"""
=== APPLY SUPABASE MIGRATION ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
Applies SQL migration to Supabase database

USAGE:
python scripts/setup/apply_migration.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration_via_http():
    """
    Apply migration using Supabase Management API
    """
    import requests

    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    SUPABASE_ACCESS_TOKEN = os.getenv('SUPABASE_ACCESS_TOKEN')

    # Read SQL file
    sql_file = Path(__file__).parent / 'supabase_migration.sql'
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    print("Applying migration via Supabase REST API...")

    # Try using PostgREST to execute SQL
    # Note: This requires enabling pg_stat_statements or using a custom RPC function

    # Extract project reference from URL
    # https://hhbjftbomfuwnjkjnrke.supabase.co -> hhbjftbomfuwnjkjnrke
    project_ref = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')

    # Supabase REST API endpoint for SQL execution
    # We'll try using the management API if available

    headers = {
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'apikey': SUPABASE_SERVICE_KEY,
        'Content-Type': 'application/json'
    }

    # Split SQL into individual statements
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

    print(f"Found {len(statements)} SQL statements to execute...")

    # Note: Supabase doesn't expose direct SQL execution via REST API
    # We need to use psycopg2 or apply manually

    print("\n" + "=" * 60)
    print("IMPORTANT: Direct SQL execution not available via REST API")
    print("=" * 60)
    print("\nPlease apply migration manually:")
    print("\n1. Go to Supabase Dashboard:")
    print(f"   {SUPABASE_URL.replace('https://', 'https://app.supabase.com/project/')}")
    print("\n2. Navigate to: SQL Editor")
    print("\n3. Copy & paste content from:")
    print(f"   {sql_file.absolute()}")
    print("\n4. Click 'Run' to execute the migration")
    print("\n" + "=" * 60)

    return False

def apply_migration_via_postgres():
    """
    Apply migration using direct PostgreSQL connection
    Requires psycopg2 and database password
    """
    try:
        import psycopg2
    except ImportError:
        print("[X] psycopg2 not installed")
        print("\nInstall with: pip install psycopg2-binary")
        return False

    # Supabase PostgreSQL connection details
    # Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

    SUPABASE_URL = os.getenv('SUPABASE_URL')
    DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD')  # Need to add this to .env

    if not DB_PASSWORD:
        print("[X] SUPABASE_DB_PASSWORD not found in .env")
        print("\nTo use direct PostgreSQL connection:")
        print("1. Go to Supabase Dashboard > Settings > Database")
        print("2. Copy the database password")
        print("3. Add to .env: SUPABASE_DB_PASSWORD=your_password")
        return False

    # Extract project reference
    project_ref = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')

    # Connection string
    conn_string = f"postgresql://postgres:{DB_PASSWORD}@db.{project_ref}.supabase.co:5432/postgres"

    try:
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Read SQL file
        sql_file = Path(__file__).parent / 'supabase_migration.sql'
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        print("Executing migration...")
        cursor.execute(sql)
        conn.commit()

        print("[OK] Migration applied successfully!")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"[X] Error: {e}")
        return False

def main():
    """Main execution"""
    print("=" * 60)
    print("SUPABASE MIGRATION APPLICATION")
    print("=" * 60)
    print()

    # Try PostgreSQL connection first
    print("Method 1: Direct PostgreSQL connection")
    print("-" * 60)
    success = apply_migration_via_postgres()

    if not success:
        print("\nMethod 2: Manual application")
        print("-" * 60)
        apply_migration_via_http()

if __name__ == "__main__":
    main()
