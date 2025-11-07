-- ============================================================================
-- INSTANTLY LEADS RAW
-- Migration: 012
-- Created: 2025-10-29
-- Purpose: Store raw lead data from Instantly API
-- ============================================================================

-- ============================================================================
-- INSTANTLY LEADS RAW TABLE
-- ============================================================================
-- Stores raw lead data from Instantly API
-- Source: POST /api/v2/leads/list endpoint

CREATE TABLE instantly_leads_raw (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Instantly IDs
    instantly_lead_id TEXT UNIQUE,
    instantly_campaign_id TEXT,

    -- Main fields for quick queries (extracted from JSON)
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    company_name TEXT,

    -- Lead status from Instantly
    lead_status TEXT,
    -- Common values: 'active', 'completed', 'paused', 'bounced', 'replied'

    -- Full raw JSON from Instantly (preserves ALL data)
    raw_json JSONB NOT NULL,

    -- Sync tracking
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_instantly_leads_email ON instantly_leads_raw(email);
CREATE INDEX idx_instantly_leads_campaign ON instantly_leads_raw(instantly_campaign_id);
CREATE INDEX idx_instantly_leads_status ON instantly_leads_raw(lead_status);
CREATE INDEX idx_instantly_leads_synced ON instantly_leads_raw(synced_at DESC);
CREATE INDEX idx_instantly_leads_name ON instantly_leads_raw(first_name, last_name);

-- Foreign key to campaigns (if campaign exists)
ALTER TABLE instantly_leads_raw
    ADD CONSTRAINT fk_instantly_leads_campaign
    FOREIGN KEY (instantly_campaign_id)
    REFERENCES instantly_campaigns_raw(instantly_campaign_id)
    ON DELETE SET NULL;

-- Trigger for updated_at
CREATE TRIGGER update_instantly_leads_raw_updated_at
    BEFORE UPDATE ON instantly_leads_raw
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE instantly_leads_raw IS 'Raw lead data from Instantly API - full historical data preserved';
COMMENT ON COLUMN instantly_leads_raw.instantly_lead_id IS 'Unique lead ID from Instantly (if provided by API)';
COMMENT ON COLUMN instantly_leads_raw.instantly_campaign_id IS 'Links to campaign this lead belongs to';
COMMENT ON COLUMN instantly_leads_raw.raw_json IS 'Complete JSON response from Instantly API - never modify manually';
COMMENT ON COLUMN instantly_leads_raw.synced_at IS 'When this record was last synced from Instantly API';

-- ============================================================================
-- MIGRATION COMPLETE - LEADS RAW LAYER
-- ============================================================================

-- Summary:
-- ✅ instantly_leads_raw table created
-- ✅ Key fields extracted for fast queries (email, name, company, status)
-- ✅ Full JSONB raw_json preservation
-- ✅ Indexes for performance
-- ✅ FK to campaigns table
-- ✅ Trigger for updated_at automation
