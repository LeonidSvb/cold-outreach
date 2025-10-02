-- Migration 009: Events Table (Multi-Source Timeline)
-- Created: 2025-01-19
-- Purpose: Unified event tracking from Instantly, VAPI, LinkedIn, manual actions
-- Dependencies: 006_leads.sql, 007_campaigns.sql, 008_campaign_leads.sql

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event identification
    event_source TEXT NOT NULL,
    -- Values: instantly, vapi, linkedin, manual
    event_type TEXT NOT NULL,
    -- Instantly: email_sent, email_opened, email_replied, email_bounced
    -- VAPI: call_initiated, call_completed, call_voicemail, call_failed
    -- LinkedIn: connection_sent, connection_accepted, message_sent, message_replied
    -- Manual: note_added, status_changed

    -- Relationships
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    campaign_lead_id UUID REFERENCES campaign_leads(id) ON DELETE CASCADE,

    -- Event timing
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Email fields (if event_source = 'instantly')
    email_subject TEXT,
    email_body TEXT,

    -- Call fields (if event_source = 'vapi')
    call_duration_seconds INTEGER,
    call_recording_url TEXT,
    call_outcome TEXT,

    -- LinkedIn fields (if event_source = 'linkedin')
    linkedin_message_text TEXT,

    -- Manual event fields (if event_source = 'manual')
    note_text TEXT,

    -- Full event data from source
    raw_data JSONB,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_events_lead ON events(lead_id, event_timestamp DESC);
CREATE INDEX idx_events_campaign ON events(campaign_id, event_timestamp DESC);
CREATE INDEX idx_events_source ON events(event_source);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_source_type ON events(event_source, event_type);
