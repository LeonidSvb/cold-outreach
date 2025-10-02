-- Migration 006: Leads Table
-- Created: 2025-01-19
-- Purpose: Store individual people to contact (linked to companies)
-- Dependencies: 005_companies.sql

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
    phone TEXT,

    -- Job information
    job_title TEXT,
    seniority TEXT,

    -- Company relationship
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Source tracking (flexible - can be CSV, API, manual, etc.)
    source_type TEXT,  -- 'csv', 'api', 'manual', 'linkedin', etc.
    source_id TEXT,  -- ID from source system (optional)
    raw_data JSONB,  -- Full data from any source preserved as JSONB

    -- Lead status
    lead_status TEXT DEFAULT 'new',
    -- Values: new, contacted, replied, converted, unqualified

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_company ON leads(company_id);
CREATE INDEX idx_leads_status ON leads(lead_status);
CREATE INDEX idx_leads_source_type ON leads(source_type);

-- Auto-update updated_at
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
