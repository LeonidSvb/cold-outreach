-- Migration 011: Create Prompts Table with Versioning
-- Created: 2025-10-04
-- Purpose: Store AI prompts with version history for column transformations

-- Create prompts table
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

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_prompts_parent ON prompts(parent_id);
CREATE INDEX IF NOT EXISTS idx_prompts_name_version ON prompts(name, version DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_user ON prompts(user_id);

-- Insert default prompts from existing scripts
INSERT INTO prompts (name, description, prompt_text, version, change_comment) VALUES
(
  'Icebreaker Generator',
  'Generates personalized email openers for B2B cold outreach',
  'Create a personalized 2-3 sentence email opener for this lead:

Name: {first_name} {last_name}
Title: {job_title}
Company: {company_name}
City: {city}

Create an opener that:
1. References something specific about their company or location
2. Shows genuine research and interest
3. Creates curiosity about our solution

Return only the opener text, no additional formatting.',
  1,
  'Initial version from openai_mass_processor.py'
),
(
  'City Abbreviator',
  'Converts full city names to common abbreviations',
  'Convert the following city name to its common abbreviation:

City: {city}

Rules:
- San Francisco → SF
- Los Angeles → LA
- New York → NYC
- Chicago → Chi
- For cities without common abbreviations, return the first 3-4 letters

Return only the abbreviation, nothing else.',
  1,
  'Initial version for city normalization'
),
(
  'Company Name Normalizer',
  'Normalizes formal company names to short colloquial forms',
  'Normalize this company name to a short, colloquial form:

Company: {company_name}

Rules:
- Remove suffixes: Inc., LLC, Ltd., Corporation, Co., etc.
- Handle abbreviations in parentheses: "Company (ABC)" → "ABC"
- Convert to title case: "COMPANY NAME" → "Company Name"
- Keep well-known brand names intact: "Google Inc." → "Google"

Return only the normalized company name, nothing else.',
  1,
  'Initial version from csv_column_transformer.py'
);
