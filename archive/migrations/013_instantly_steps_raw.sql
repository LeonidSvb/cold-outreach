-- ============================================================================
-- INSTANTLY STEPS RAW
-- Migration: 013
-- Created: 2025-10-29
-- Purpose: Store raw steps analytics data from Instantly API
-- ============================================================================

-- ============================================================================
-- INSTANTLY STEPS RAW TABLE
-- ============================================================================
-- Stores raw steps analytics data from Instantly API
-- Source: GET /api/v2/campaigns/analytics/steps?campaign_id={id} endpoint

CREATE TABLE instantly_steps_raw (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Campaign relationship
    instantly_campaign_id TEXT NOT NULL,

    -- Step identification (extracted from JSON)
    step_number INTEGER,
    step_name TEXT,
    step_type TEXT,
    -- Common types: 'email', 'follow_up', 'delay', 'conditional'

    -- Step metrics (extracted for quick queries)
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_replied INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,

    -- Full raw JSON from Instantly (preserves ALL data)
    raw_json JSONB NOT NULL,

    -- Sync tracking
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_instantly_steps_campaign ON instantly_steps_raw(instantly_campaign_id);
CREATE INDEX idx_instantly_steps_number ON instantly_steps_raw(step_number);
CREATE INDEX idx_instantly_steps_synced ON instantly_steps_raw(synced_at DESC);

-- Unique constraint: one record per campaign+step combination
CREATE UNIQUE INDEX idx_instantly_steps_unique ON instantly_steps_raw(instantly_campaign_id, step_number)
    WHERE step_number IS NOT NULL;

-- Foreign key to campaigns
ALTER TABLE instantly_steps_raw
    ADD CONSTRAINT fk_instantly_steps_campaign
    FOREIGN KEY (instantly_campaign_id)
    REFERENCES instantly_campaigns_raw(instantly_campaign_id)
    ON DELETE CASCADE;

-- Trigger for updated_at
CREATE TRIGGER update_instantly_steps_raw_updated_at
    BEFORE UPDATE ON instantly_steps_raw
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE instantly_steps_raw IS 'Raw steps analytics from Instantly API - tracks performance of each email sequence step';
COMMENT ON COLUMN instantly_steps_raw.instantly_campaign_id IS 'Campaign this step belongs to';
COMMENT ON COLUMN instantly_steps_raw.step_number IS 'Sequential step number in the campaign (1, 2, 3, etc.)';
COMMENT ON COLUMN instantly_steps_raw.raw_json IS 'Complete JSON response from Instantly API - never modify manually';

-- ============================================================================
-- MIGRATION COMPLETE - STEPS RAW LAYER
-- ============================================================================

-- Summary:
-- ✅ instantly_steps_raw table created
-- ✅ Key metrics extracted for fast queries
-- ✅ Full JSONB raw_json preservation
-- ✅ Indexes for performance
-- ✅ FK to campaigns table with CASCADE delete
-- ✅ Unique constraint to prevent duplicate steps
-- ✅ Trigger for updated_at automation
