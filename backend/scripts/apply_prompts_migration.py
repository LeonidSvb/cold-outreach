#!/usr/bin/env python3
"""
Apply Prompts Table Migration
Creates prompts table with default prompts in Supabase
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.append(str(backend_path))

from lib.supabase_client import get_supabase


def apply_migration():
    """Create prompts table and insert default prompts"""
    print("Connecting to Supabase...")
    supabase = get_supabase()

    # Step 1: Create table
    print("\nStep 1: Creating prompts table...")
    try:
        # Check if table exists
        existing = supabase.table('prompts').select('id').limit(1).execute()
        print("Table already exists, skipping creation")
    except Exception:
        print("Table does not exist, creating via backend endpoint...")
        print("ERROR: Cannot create table directly via Supabase SDK")
        print("\nPlease execute this SQL in Supabase Studio SQL Editor:")
        print("="*80)
        print("""
CREATE TABLE IF NOT EXISTS prompts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT DEFAULT '1',
  name TEXT NOT NULL,
  description TEXT,
  prompt_text TEXT NOT NULL,
  version INTEGER DEFAULT 1,
  parent_id UUID REFERENCES prompts(id),
  change_comment TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_prompts_parent ON prompts(parent_id);
CREATE INDEX IF NOT EXISTS idx_prompts_name_version ON prompts(name, version DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_user ON prompts(user_id);
        """)
        print("="*80)
        print("\nAfter executing the SQL, press Enter to continue with inserting default prompts...")
        input()

    # Step 2: Insert default prompts
    print("\nStep 2: Inserting default prompts...")

    prompts = [
        {
            "name": "Icebreaker Generator",
            "description": "Generates personalized email openers for B2B cold outreach",
            "prompt_text": """Create a personalized 2-3 sentence email opener for this lead:

Name: {first_name} {last_name}
Title: {job_title}
Company: {company_name}
City: {city}

Create an opener that:
1. References something specific about their company or location
2. Shows genuine research and interest
3. Creates curiosity about our solution

Return only the opener text, no additional formatting.""",
            "version": 1,
            "change_comment": "Initial version from openai_mass_processor.py"
        },
        {
            "name": "City Abbreviator",
            "description": "Converts full city names to common abbreviations",
            "prompt_text": """Convert the following city name to its common abbreviation:

City: {city}

Rules:
- San Francisco -> SF
- Los Angeles -> LA
- New York -> NYC
- Chicago -> Chi
- For cities without common abbreviations, return the first 3-4 letters

Return only the abbreviation, nothing else.""",
            "version": 1,
            "change_comment": "Initial version for city normalization"
        },
        {
            "name": "Company Name Normalizer",
            "description": "Normalizes formal company names to short colloquial forms",
            "prompt_text": """Normalize this company name to a short, colloquial form:

Company: {company_name}

Rules:
- Remove suffixes: Inc., LLC, Ltd., Corporation, Co., etc.
- Handle abbreviations in parentheses: "Company (ABC)" -> "ABC"
- Convert to title case: "COMPANY NAME" -> "Company Name"
- Keep well-known brand names intact: "Google Inc." -> "Google"

Return only the normalized company name, nothing else.""",
            "version": 1,
            "change_comment": "Initial version from csv_column_transformer.py"
        }
    ]

    for prompt in prompts:
        try:
            # Check if prompt already exists
            existing = supabase.table('prompts').select('id').eq('name', prompt['name']).execute()

            if existing.data:
                print(f"  - {prompt['name']}: Already exists, skipping")
            else:
                supabase.table('prompts').insert(prompt).execute()
                print(f"  - {prompt['name']}: Inserted successfully")
        except Exception as e:
            print(f"  - {prompt['name']}: ERROR - {str(e)}")

    print("\nMigration completed!")
    print("Verifying prompts...")

    # Verify
    all_prompts = supabase.table('prompts').select('name, version').execute()
    print(f"\nTotal prompts in database: {len(all_prompts.data)}")
    for p in all_prompts.data:
        print(f"  - {p['name']} (v{p['version']})")


if __name__ == "__main__":
    apply_migration()
