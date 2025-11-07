-- Migration 007: Campaigns Table
-- Created: 2025-01-19
-- Purpose: Email/call campaigns
-- Dependencies: 004_offers.sql

CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Campaign identification
    campaign_name TEXT NOT NULL,
    campaign_description TEXT,

    -- Offer relationship
    offer_id UUID NOT NULL REFERENCES offers(id) ON DELETE RESTRICT,

    -- Campaign channels
    uses_email BOOLEAN DEFAULT true,
    uses_calls BOOLEAN DEFAULT false,
    uses_linkedin BOOLEAN DEFAULT false,

    -- Campaign status
    campaign_status TEXT NOT NULL DEFAULT 'draft',
    -- Values: draft, active, paused, completed, archived

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_campaigns_name ON campaigns(campaign_name);
CREATE INDEX idx_campaigns_status ON campaigns(campaign_status);
CREATE INDEX idx_campaigns_offer ON campaigns(offer_id);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_campaigns_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER campaigns_updated_at_trigger
    BEFORE UPDATE ON campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_campaigns_updated_at();
