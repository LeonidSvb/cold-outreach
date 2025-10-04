#!/usr/bin/env python3
"""
Run SQL Migration Script
Applies migration files to Supabase database
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.supabase_client import get_supabase
from modules.logging.shared.universal_logger import get_logger

logger = get_logger(__name__)


def run_migration(migration_file: str):
    """Execute SQL migration file"""
    migration_path = Path(__file__).parent.parent.parent / "migrations" / migration_file

    if not migration_path.exists():
        print(f"ERROR: Migration file not found: {migration_path}")
        return False

    print(f"Reading migration: {migration_file}")
    with open(migration_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    print("Connecting to Supabase...")
    supabase = get_supabase()

    print("Executing migration...")
    try:
        # Execute SQL via RPC function
        result = supabase.rpc('exec_sql', {'query': sql}).execute()
        print(f"SUCCESS: Migration applied")
        print(f"Result: {result.data}")
        return True
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print("\nTrying alternative approach - direct table creation...")

        # Alternative: Execute via postgrest (may not work for all operations)
        # This will fail gracefully if exec_sql RPC doesn't exist
        print("Please execute this SQL manually in Supabase Studio:")
        print("\n" + "="*60)
        print(sql)
        print("="*60)
        return False


if __name__ == "__main__":
    logger.info("Migration runner started")
    try:
        migration_file = "011_create_prompts_table.sql"
        if len(sys.argv) > 1:
            migration_file = sys.argv[1]

        success = run_migration(migration_file)
        logger.info("Migration completed", success=success)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error("Migration runner failed", error=e)
        raise
