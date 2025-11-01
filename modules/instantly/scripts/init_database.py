#!/usr/bin/env python3
"""
=== INSTANTLY DATABASE INITIALIZATION ===
Version: 1.0.0 | Created: 2025-11-01

PURPOSE:
Initialize SQLite database for Instantly raw data storage

FEATURES:
- Creates instantly.db file
- Applies complete schema migration
- Verifies all tables created successfully
- Shows database statistics

USAGE:
1. Run: python init_database.py
2. Database created at: data/instantly.db
3. Open with DB Browser for SQLite to explore

TABLES CREATED:
1. instantly_campaigns_raw - Campaign analytics
2. instantly_leads_raw - Lead data
3. instantly_steps_raw - Step analytics
4. instantly_accounts_raw - Email accounts
5. instantly_emails_raw - Email details
6. instantly_daily_analytics_raw - Daily metrics
7. instantly_overview_raw - Account overview
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path for logger
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "instantly.db"
MIGRATION_PATH = PROJECT_ROOT / "migrations" / "sqlite_instantly_init.sql"

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)

def print_step(text):
    """Print step indicator"""
    print(f"\n>>> {text}")

def print_success(text):
    """Print success message"""
    print(f"  SUCCESS: {text}")

def print_error(text):
    """Print error message"""
    print(f"  ERROR: {text}")

def create_database():
    """Create and initialize SQLite database"""

    print_header("INSTANTLY DATABASE INITIALIZATION")

    # Step 1: Create data directory if not exists
    print_step("Creating data directory...")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print_success(f"Directory ready: {DB_PATH.parent}")

    # Step 2: Check if database already exists
    force_recreate = len(sys.argv) > 1 and sys.argv[1] == '--force'

    if DB_PATH.exists():
        print_step("Existing database found")
        if force_recreate:
            print("  Force recreate enabled - deleting old database...")
            DB_PATH.unlink()
            print_success("Old database deleted")
        else:
            response = input("  Database already exists. Recreate? (yes/no): ")
            if response.lower() != 'yes':
                print("  Aborted. Existing database preserved.")
                return False
            DB_PATH.unlink()
            print_success("Old database deleted")

    # Step 3: Read migration SQL
    print_step("Reading migration file...")
    if not MIGRATION_PATH.exists():
        print_error(f"Migration file not found: {MIGRATION_PATH}")
        return False

    migration_sql = MIGRATION_PATH.read_text(encoding='utf-8')
    print_success(f"Migration loaded: {len(migration_sql)} characters")

    # Step 4: Create database and apply migration
    print_step("Creating database and applying schema...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Execute migration (SQLite can handle multiple statements)
        cursor.executescript(migration_sql)
        conn.commit()

        print_success(f"Database created: {DB_PATH}")

    except sqlite3.Error as e:
        print_error(f"Database creation failed: {e}")
        return False

    # Step 5: Verify tables created
    print_step("Verifying tables...")

    expected_tables = [
        'instantly_campaigns_raw',
        'instantly_leads_raw',
        'instantly_steps_raw',
        'instantly_accounts_raw',
        'instantly_emails_raw',
        'instantly_daily_analytics_raw',
        'instantly_overview_raw'
    ]

    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)

    actual_tables = [row[0] for row in cursor.fetchall()]

    print("\n  Tables created:")
    for table in expected_tables:
        if table in actual_tables:
            print(f"    [OK] {table}")
        else:
            print(f"    [FAIL] {table} - MISSING!")

    # Step 6: Show database info
    print_step("Database information")

    # Get database size
    db_size = DB_PATH.stat().st_size
    print(f"  Database size: {db_size:,} bytes")

    # Get SQLite version
    cursor.execute("SELECT sqlite_version()")
    sqlite_version = cursor.fetchone()[0]
    print(f"  SQLite version: {sqlite_version}")

    # Get table count
    print(f"  Tables created: {len(actual_tables)}")

    # Close connection
    conn.close()

    # Step 7: Success summary
    print_header("INITIALIZATION COMPLETE")
    print(f"""
  Database Location: {DB_PATH}
  Tables: {len(expected_tables)}
  Status: Ready for data collection

  Next Steps:
  1. Run data collection script: python collect_instantly_data.py
  2. Or open with DB Browser for SQLite to explore

  Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

    return True

def show_existing_stats():
    """Show statistics for existing database"""

    if not DB_PATH.exists():
        print("No database found. Run initialization first.")
        return

    print_header("EXISTING DATABASE STATISTICS")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = [
        'instantly_campaigns_raw',
        'instantly_leads_raw',
        'instantly_steps_raw',
        'instantly_accounts_raw',
        'instantly_emails_raw',
        'instantly_daily_analytics_raw',
        'instantly_overview_raw'
    ]

    print("\n  Table                          Records    Last Synced")
    print("  " + "-" * 70)

    for table in tables:
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]

        # Get last sync time
        cursor.execute(f"SELECT MAX(synced_at) FROM {table}")
        last_sync = cursor.fetchone()[0] or "Never"

        print(f"  {table:30} {count:8}    {last_sync}")

    # Get database size
    db_size = DB_PATH.stat().st_size / 1024 / 1024  # Convert to MB
    print(f"\n  Database size: {db_size:.2f} MB")

    conn.close()

def main():
    """Main entry point"""

    # Check if showing stats
    if len(sys.argv) > 1 and sys.argv[1] == '--stats':
        show_existing_stats()
        return

    # Initialize database
    success = create_database()

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
