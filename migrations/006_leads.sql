-- Migration 006: Leads Table
-- Created: 2025-01-19
-- Purpose: Store individual people to contact (linked to companies)
-- Dependencies: 003_csv_imports_raw.sql, 005_companies.sql

-- ============================================================================
-- TABLE: leads
-- ============================================================================
-- Individual people to contact
-- Multiple leads can work at same company (company_id FK)
-- One lead belongs to exactly one company

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Personal information
    first_name TEXT NOT NULL,
    last_name TEXT,
    full_name TEXT GENERATED ALWAYS AS (
        CASE
            WHEN last_name IS NOT NULL THEN first_name || ' ' || last_name
            ELSE first_name
        END
    ) STORED,

    -- Contact information
    email TEXT NOT NULL,
    personal_email TEXT,
    phone TEXT,
    mobile_phone TEXT,

    -- Job information
    job_title TEXT,
    seniority TEXT,  -- 'C-Level', 'VP', 'Director', 'Manager', etc.
    department TEXT,  -- 'Engineering', 'Marketing', 'Sales', etc.

    -- Social profiles
    linkedin_url TEXT,
    twitter_url TEXT,
    facebook_url TEXT,

    -- Company relationship
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Apollo data (preserved from CSV)
    apollo_contact_id TEXT,
    apollo_data JSONB,  -- Full Apollo contact data if available

    -- CSV source tracking
    csv_import_id UUID REFERENCES csv_imports_raw(id),
    csv_row_number INTEGER,  -- Original row number in CSV for debugging

    -- Lead scoring
    lead_score INTEGER,  -- 0-100 (future: ML-based scoring)
    lead_status TEXT DEFAULT 'new',
    -- Values: new, qualified, contacted, replied, converted, unqualified

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Fast lookup by email (most common query)
CREATE INDEX idx_leads_email ON leads(email);

-- Query leads by company
CREATE INDEX idx_leads_company ON leads(company_id);

-- Filter by job title
CREATE INDEX idx_leads_job_title ON leads(job_title);

-- Filter by seniority
CREATE INDEX idx_leads_seniority ON leads(seniority);

-- Filter by status
CREATE INDEX idx_leads_status ON leads(lead_status);

-- Query by Apollo ID
CREATE INDEX idx_leads_apollo_id ON leads(apollo_contact_id);

-- Track CSV source
CREATE INDEX idx_leads_csv_import ON leads(csv_import_id);

-- Full-text search on name
CREATE INDEX idx_leads_full_name ON leads USING gin(to_tsvector('english', full_name));

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_leads_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER leads_updated_at_trigger
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_leads_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE leads ENABLE ROW LEVEL SECURITY;

-- All authenticated users can read leads
CREATE POLICY leads_select_all ON leads
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- All authenticated users can insert leads
CREATE POLICY leads_insert_authenticated ON leads
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- All authenticated users can update leads
CREATE POLICY leads_update_authenticated ON leads
    FOR UPDATE
    USING (auth.role() = 'authenticated');

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE leads IS 'Individual people to contact - linked to companies table';
COMMENT ON COLUMN leads.full_name IS 'Auto-generated from first_name + last_name';
COMMENT ON COLUMN leads.company_id IS 'FK to companies - one lead belongs to one company';
COMMENT ON COLUMN leads.apollo_data IS 'Full Apollo contact data preserved as JSONB';
COMMENT ON COLUMN leads.csv_import_id IS 'Links back to original CSV import';
COMMENT ON COLUMN leads.csv_row_number IS 'Original CSV row number for debugging import issues';
COMMENT ON COLUMN leads.lead_status IS 'Lifecycle: new, qualified, contacted, replied, converted, unqualified';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- After running this migration, verify with:

-- 1. Check leads with company info
-- SELECT
--     l.full_name,
--     l.email,
--     l.job_title,
--     c.company_name,
--     c.company_domain
-- FROM leads l
-- JOIN companies c ON l.company_id = c.id
-- ORDER BY l.created_at DESC
-- LIMIT 10;

-- 2. Find companies with multiple leads (26% of cases)
-- SELECT
--     c.company_name,
--     COUNT(l.id) as lead_count,
--     array_agg(l.full_name) as lead_names
-- FROM companies c
-- JOIN leads l ON l.company_id = c.id
-- GROUP BY c.id, c.company_name
-- HAVING COUNT(l.id) > 1
-- ORDER BY lead_count DESC;

-- 3. Check lead status distribution
-- SELECT lead_status, COUNT(*) as count
-- FROM leads
-- GROUP BY lead_status
-- ORDER BY count DESC;
