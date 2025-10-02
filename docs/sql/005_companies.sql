-- Migration 005: Companies Table
-- Created: 2025-01-19
-- Purpose: Deduplicated company data (multiple leads can work at same company)
-- Dependencies: 003_csv_imports_raw.sql

-- ============================================================================
-- TABLE: companies
-- ============================================================================
-- Stores unique companies (not duplicated per lead)
-- 26% of leads share companies (proven by CSV analysis)
-- Links back to CSV import that discovered the company

CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Company identification
    company_name TEXT NOT NULL,
    company_domain TEXT UNIQUE,  -- UNIQUE: prevents duplicates
    website TEXT,

    -- Company details
    industry TEXT,
    company_size TEXT,  -- '1-10', '11-50', '51-200', etc.
    employee_count INTEGER,
    revenue_range TEXT,  -- '$1M-$10M', '$10M-$50M', etc.
    founded_year INTEGER,

    -- Location
    country TEXT,
    city TEXT,
    state TEXT,
    address TEXT,

    -- Contact info
    company_phone TEXT,
    company_linkedin TEXT,

    -- Technology stack (from Apollo/CSV)
    technologies TEXT[],  -- ['React', 'AWS', 'Salesforce']

    -- Apollo data (preserved from CSV)
    apollo_organization_id TEXT,
    apollo_data JSONB,  -- Full Apollo company data if available

    -- CSV source tracking
    first_seen_in_csv_id UUID REFERENCES csv_imports_raw(id),
    last_seen_in_csv_id UUID REFERENCES csv_imports_raw(id),
    csv_appearance_count INTEGER DEFAULT 1,  -- How many CSVs mentioned this company

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Fast lookup by domain (most common query)
CREATE INDEX idx_companies_domain ON companies(company_domain);

-- Search by name
CREATE INDEX idx_companies_name ON companies(company_name);

-- Filter by industry
CREATE INDEX idx_companies_industry ON companies(industry);

-- Filter by company size
CREATE INDEX idx_companies_size ON companies(company_size);

-- Query by Apollo ID
CREATE INDEX idx_companies_apollo_id ON companies(apollo_organization_id);

-- Track CSV sources
CREATE INDEX idx_companies_first_csv ON companies(first_seen_in_csv_id);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_companies_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER companies_updated_at_trigger
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_companies_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

-- All authenticated users can read companies
CREATE POLICY companies_select_all ON companies
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- All authenticated users can insert companies
CREATE POLICY companies_insert_authenticated ON companies
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- All authenticated users can update companies
CREATE POLICY companies_update_authenticated ON companies
    FOR UPDATE
    USING (auth.role() = 'authenticated');

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE companies IS 'Deduplicated company data - multiple leads can belong to same company';
COMMENT ON COLUMN companies.company_domain IS 'UNIQUE domain prevents duplicate companies';
COMMENT ON COLUMN companies.apollo_data IS 'Full Apollo company data preserved as JSONB';
COMMENT ON COLUMN companies.first_seen_in_csv_id IS 'CSV import that first discovered this company';
COMMENT ON COLUMN companies.csv_appearance_count IS 'How many different CSV files mentioned this company';

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================

-- After running this migration, verify with:
-- SELECT id, company_name, company_domain, industry, company_size
-- FROM companies
-- ORDER BY created_at DESC;

-- Check for duplicates (should return 0 rows):
-- SELECT company_domain, COUNT(*)
-- FROM companies
-- WHERE company_domain IS NOT NULL
-- GROUP BY company_domain
-- HAVING COUNT(*) > 1;
