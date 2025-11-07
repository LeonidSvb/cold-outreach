#!/usr/bin/env python3
"""
=== SUPABASE TABLE CREATION ===
Version: 1.0.0 | Created: 2025-11-06

PURPOSE:
Creates leads and contact_history tables in Supabase via API

FEATURES:
- Two-layer architecture (leads + contact_history)
- Auto-deduplication by email/phone
- Multi-channel tracking (email, voice, linkedin)
- Flexible JSONB storage for extra fields

USAGE:
python scripts/setup/create_supabase_tables.py
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def get_supabase_client() -> Client:
    """Get Supabase client with service role key"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")

    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def create_tables(supabase: Client):
    """Create leads and contact_history tables"""

    print("Creating Supabase tables...")

    # SQL for creating tables
    sql = """
    -- =============================================
    -- LEADS TABLE (Master Data)
    -- =============================================
    CREATE TABLE IF NOT EXISTS leads (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

        -- IDENTIFIERS (for deduplication)
        email TEXT,
        phone_number TEXT,

        -- At least one contact method required
        CHECK (email IS NOT NULL OR phone_number IS NOT NULL),

        -- CONTACT INFO
        first_name TEXT,
        last_name TEXT,
        full_name TEXT,

        -- COMPANY INFO
        company_name TEXT,
        company_domain TEXT,
        company_url TEXT,
        company_linkedin_url TEXT,
        estimated_num_employees INTEGER,

        -- PROFESSIONAL
        title TEXT,
        linkedin_url TEXT,
        headline TEXT,
        seniority TEXT,

        -- LOCATION
        country TEXT,
        state TEXT,
        city TEXT,

        -- CATEGORIZATION
        industry TEXT,

        -- FLEXIBLE STORAGE (all other CSV fields)
        extra_data JSONB DEFAULT '{{}}',

        -- SOURCE TRACKING
        original_source TEXT,
        sources JSONB DEFAULT '[]',

        -- STATUS
        email_status TEXT,
        phone_status TEXT,

        -- CONTACT RESTRICTIONS
        do_not_email BOOLEAN DEFAULT false,
        do_not_call BOOLEAN DEFAULT false,

        -- METADATA
        created_at TIMESTAMPTZ DEFAULT now(),
        updated_at TIMESTAMPTZ DEFAULT now(),
        last_enriched_at TIMESTAMPTZ
    );

    -- Unique indexes for deduplication
    CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_email
        ON leads(email) WHERE email IS NOT NULL;

    CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_phone
        ON leads(phone_number) WHERE phone_number IS NOT NULL;

    -- Search indexes
    CREATE INDEX IF NOT EXISTS idx_leads_company
        ON leads(company_domain);

    CREATE INDEX IF NOT EXISTS idx_leads_name
        ON leads(full_name);

    CREATE INDEX IF NOT EXISTS idx_leads_extra
        ON leads USING GIN(extra_data);

    CREATE INDEX IF NOT EXISTS idx_leads_sources
        ON leads USING GIN(sources);

    CREATE INDEX IF NOT EXISTS idx_leads_created
        ON leads(created_at DESC);

    -- =============================================
    -- CONTACT HISTORY TABLE (Tracking)
    -- =============================================
    CREATE TABLE IF NOT EXISTS contact_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,

        -- CONTACT INFO
        channel TEXT NOT NULL CHECK (channel IN ('email', 'voice', 'linkedin', 'other')),
        contact_type TEXT NOT NULL,

        -- CAMPAIGN/OFFER
        campaign TEXT,
        offer TEXT,

        -- DETAILS (flexible storage)
        details JSONB DEFAULT '{{}}',

        -- RESULT
        result TEXT,

        -- TIMING
        contacted_at TIMESTAMPTZ DEFAULT now(),

        -- METADATA
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- Indexes for fast queries
    CREATE INDEX IF NOT EXISTS idx_contact_history_lead
        ON contact_history(lead_id);

    CREATE INDEX IF NOT EXISTS idx_contact_history_channel
        ON contact_history(channel);

    CREATE INDEX IF NOT EXISTS idx_contact_history_date
        ON contact_history(contacted_at DESC);

    CREATE INDEX IF NOT EXISTS idx_contact_history_campaign
        ON contact_history(campaign);

    CREATE INDEX IF NOT EXISTS idx_contact_history_offer
        ON contact_history(offer);

    CREATE INDEX IF NOT EXISTS idx_contact_history_details
        ON contact_history USING GIN(details);

    -- =============================================
    -- HELPER FUNCTIONS
    -- =============================================

    -- Auto-update updated_at timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = now();
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    -- Trigger for leads table
    DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
    CREATE TRIGGER update_leads_updated_at
        BEFORE UPDATE ON leads
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """

    try:
        # Execute SQL via Supabase RPC
        # Note: Supabase doesn't have direct SQL execution via Python client
        # We need to use the PostgREST API or execute via psycopg2

        print("SQL commands prepared. Executing via Supabase...")

        # Using raw SQL execution
        response = supabase.postgrest.rpc('exec_sql', {'query': sql}).execute()

        print("✓ Tables created successfully!")
        return True

    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        print("\nNote: Supabase Python client doesn't support direct SQL execution.")
        print("Please use one of these methods instead:")
        print("\n1. Copy SQL from the migration file and run in Supabase Dashboard")
        print("2. Use psycopg2 to connect directly to Postgres")
        print("3. Use Supabase CLI: supabase db push")
        return False

def main():
    """Main execution"""
    try:
        print("=" * 50)
        print("SUPABASE TABLE CREATION")
        print("=" * 50)

        # Get Supabase client
        supabase = get_supabase_client()
        print(f"✓ Connected to Supabase: {SUPABASE_URL}")

        # Create tables
        success = create_tables(supabase)

        if success:
            print("\n" + "=" * 50)
            print("SUCCESS!")
            print("=" * 50)
            print("\nTables created:")
            print("  1. leads (master data)")
            print("  2. contact_history (tracking)")
        else:
            print("\n" + "=" * 50)
            print("ALTERNATIVE METHOD NEEDED")
            print("=" * 50)
            print("\nSee: scripts/setup/supabase_migration.sql")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
