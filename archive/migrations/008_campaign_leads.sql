-- Migration 008: Campaign Leads (Many-to-Many)
-- Created: 2025-01-19
-- Purpose: Track which leads are in which campaigns + workflow status
-- Dependencies: 006_leads.sql, 007_campaigns.sql

CREATE TABLE IF NOT EXISTS campaign_leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Email workflow status
    email_status TEXT DEFAULT 'pending',
    -- Values: pending, sent, opened, replied, bounced, failed
    email_sent_at TIMESTAMP WITH TIME ZONE,
    email_replied_at TIMESTAMP WITH TIME ZONE,

    -- Call workflow status
    call_status TEXT DEFAULT 'not_scheduled',
    -- Values: not_scheduled, scheduled, completed, no_answer, voicemail
    call_scheduled_at TIMESTAMP WITH TIME ZONE,
    call_completed_at TIMESTAMP WITH TIME ZONE,

    -- Overall lead status in this campaign
    overall_status TEXT NOT NULL DEFAULT 'active',
    -- Values: active, replied, converted, disqualified

    -- Metadata
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_campaign_leads_campaign ON campaign_leads(campaign_id);
CREATE INDEX idx_campaign_leads_lead ON campaign_leads(lead_id);
CREATE UNIQUE INDEX idx_campaign_leads_unique ON campaign_leads(campaign_id, lead_id);
CREATE INDEX idx_campaign_leads_email_status ON campaign_leads(email_status);
CREATE INDEX idx_campaign_leads_call_status ON campaign_leads(call_status);
CREATE INDEX idx_campaign_leads_overall_status ON campaign_leads(overall_status);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_campaign_leads_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER campaign_leads_updated_at_trigger
    BEFORE UPDATE ON campaign_leads
    FOR EACH ROW
    EXECUTE FUNCTION update_campaign_leads_updated_at();
