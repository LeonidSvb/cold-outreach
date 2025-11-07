-- Migration 005: Companies Table
-- Created: 2025-01-19
-- Purpose: Deduplicated company data (multiple leads can work at same company)
-- Dependencies: None (universal - can be populated from any source)

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

    -- Location
    country TEXT,
    city TEXT,
    state TEXT,

    -- Contact info
    company_phone TEXT,
    company_linkedin TEXT,

    -- Source tracking (flexible - can be CSV, API, manual, etc.)
    source_type TEXT,  -- 'csv', 'api', 'manual', 'linkedin', etc.
    source_id TEXT,  -- ID from source system (optional)
    raw_data JSONB,  -- Full data from any source preserved as JSONB

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookup by domain (most common query)
CREATE INDEX idx_companies_domain ON companies(company_domain);

-- Index for company name search
CREATE INDEX idx_companies_name ON companies(company_name);

-- Index by source type (to query companies from specific source)
CREATE INDEX idx_companies_source_type ON companies(source_type);

-- Auto-update updated_at
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
