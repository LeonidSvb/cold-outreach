-- Migration 009: Events Table (Multi-Source Timeline)
-- Created: 2025-01-19
-- Purpose: Unified event tracking from Instantly, VAPI, LinkedIn, manual actions
-- Dependencies: 006_leads.sql, 007_campaigns.sql, 008_campaign_leads.sql

-- ============================================================================
-- TABLE: events
-- ============================================================================
-- Unified timeline of all lead interactions across all channels
-- Tracks events from: Instantly (email), VAPI (calls), LinkedIn, manual
-- One lead can have many events across multiple campaigns

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Event identification
    event_source TEXT NOT NULL,
    -- Values: instantly, vapi, linkedin, manual, system
    event_type TEXT NOT NULL,
    -- Instantly: email_sent, email_opened, email_clicked, email_replied, email_bounced
    -- VAPI: call_initiated, call_answered, call_completed, call_voicemail, call_failed
    -- LinkedIn: connection_sent, connection_accepted, message_sent, message_replied
    -- Manual: note_added, status_changed, task_created

    -- Relationships
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    campaign_lead_id UUID REFERENCES campaign_leads(id) ON DELETE CASCADE,

    -- Event timing
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Email-specific fields (if event_source = 'instantly')
    email_subject TEXT,
    email_body TEXT,
    email_from TEXT,
    email_to TEXT,
    instantly_email_id TEXT,  -- Links to instantly_emails_raw if available

    -- Call-specific fields (if event_source = 'vapi')
    call_duration_seconds INTEGER,
    call_recording_url TEXT,
    call_transcript TEXT,
    call_outcome TEXT,  -- answered, no_answer, voicemail, busy, wrong_number
    vapi_call_id TEXT,

    -- LinkedIn-specific fields (if event_source = 'linkedin')
    linkedin_message_text TEXT,
    linkedin_profile_url TEXT,

    -- Manual event fields (if event_source = 'manual')
    note_text TEXT,
    performed_by UUID REFERENCES users(id),

    -- Metadata
    raw_data JSONB,  -- Full event data from source service
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Query events by lead (most common - show lead timeline)
CREATE INDEX idx_events_lead ON events(lead_id, event_timestamp DESC);

-- Query events by campaign
CREATE INDEX idx_events_campaign ON events(campaign_id, event_timestamp DESC);

-- Query by event source
CREATE INDEX idx_events_source ON events(event_source);

-- Query by event type
CREATE INDEX idx_events_type ON events(event_type);

-- Query by event source + type (specific workflows)
CREATE INDEX idx_events_source_type ON events(event_source, event_type);

-- Query recent events
CREATE INDEX idx_events_timestamp ON events(event_timestamp DESC);

-- Query by Instantly email ID
CREATE INDEX idx_events_instantly_id ON events(instantly_email_id)
    WHERE instantly_email_id IS NOT NULL;

-- Query by VAPI call ID
CREATE INDEX idx_events_vapi_id ON events(vapi_call_id)
    WHERE vapi_call_id IS NOT NULL;

-- Full-text search on email subject/body
CREATE INDEX idx_events_email_text ON events USING gin(
    to_tsvector('english', COALESCE(email_subject, '') || ' ' || COALESCE(email_body, ''))
) WHERE event_source = 'instantly';

-- Full-text search on call transcript
CREATE INDEX idx_events_call_transcript ON events USING gin(
    to_tsvector('english', call_transcript)
) WHERE event_source = 'vapi' AND call_transcript IS NOT NULL;

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- All authenticated users can read events
CREATE POLICY events_select_authenticated ON events
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- All authenticated users can insert events
CREATE POLICY events_insert_authenticated ON events
    FOR INSERT
    WITH CHECK (auth.role() = 'authenticated');

-- Users can update their own manual events
CREATE POLICY events_update_own_manual ON events
    FOR UPDATE
    USING (event_source = 'manual' AND performed_by = auth.uid());

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE events IS 'Unified timeline of all lead interactions across all channels (Instantly, VAPI, LinkedIn, manual)';
COMMENT ON COLUMN events.event_source IS 'Source: instantly, vapi, linkedin, manual, system';
COMMENT ON COLUMN events.event_type IS 'Type depends on source - email_sent, call_completed, connection_accepted, note_added, etc.';
COMMENT ON COLUMN events.raw_data IS 'Full event data from source service preserved as JSONB';
COMMENT ON COLUMN events.instantly_email_id IS 'Links to instantly_emails_raw table if available';
COMMENT ON COLUMN events.vapi_call_id IS 'VAPI call identifier for call events';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Get lead timeline with all events chronologically
CREATE OR REPLACE FUNCTION get_lead_timeline(p_lead_id UUID)
RETURNS TABLE (
    event_id UUID,
    event_source TEXT,
    event_type TEXT,
    event_timestamp TIMESTAMP WITH TIME ZONE,
    event_summary TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.event_source,
        e.event_type,
        e.event_timestamp,
        CASE
            WHEN e.event_source = 'instantly' THEN
                COALESCE(e.email_subject, e.event_type)
            WHEN e.event_source = 'vapi' THEN
                e.event_type || ' - ' || COALESCE(e.call_outcome, 'unknown')
            WHEN e.event_source = 'linkedin' THEN
                e.event_type
            WHEN e.event_source = 'manual' THEN
                COALESCE(e.note_text, e.event_type)
            ELSE e.event_type
        END as event_summary
    FROM events e
    WHERE e.lead_id = p_lead_id
    ORDER BY e.event_timestamp DESC;
END;
$$ LANGUAGE plpgsql;

-- Get campaign event stats
CREATE OR REPLACE FUNCTION get_campaign_event_stats(p_campaign_id UUID)
RETURNS TABLE (
    event_source TEXT,
    event_type TEXT,
    event_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.event_source,
        e.event_type,
        COUNT(*) as event_count
    FROM events e
    WHERE e.campaign_id = p_campaign_id
    GROUP BY e.event_source, e.event_type
    ORDER BY event_count DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- After running this migration, verify with:

-- 1. Check event distribution by source
-- SELECT
--     event_source,
--     COUNT(*) as event_count,
--     MIN(event_timestamp) as first_event,
--     MAX(event_timestamp) as last_event
-- FROM events
-- GROUP BY event_source
-- ORDER BY event_count DESC;

-- 2. Check email workflow events
-- SELECT
--     event_type,
--     COUNT(*) as count
-- FROM events
-- WHERE event_source = 'instantly'
-- GROUP BY event_type
-- ORDER BY count DESC;

-- 3. Get lead timeline (example)
-- SELECT * FROM get_lead_timeline(
--     (SELECT id FROM leads LIMIT 1)
-- );

-- 4. Check recent events across all sources
-- SELECT
--     e.event_timestamp,
--     e.event_source,
--     e.event_type,
--     l.full_name as lead_name,
--     l.email as lead_email,
--     c.campaign_name
-- FROM events e
-- JOIN leads l ON e.lead_id = l.id
-- LEFT JOIN campaigns c ON e.campaign_id = c.id
-- ORDER BY e.event_timestamp DESC
-- LIMIT 20;

-- 5. Find leads with no events (need attention)
-- SELECT
--     l.full_name,
--     l.email,
--     l.job_title,
--     l.lead_status,
--     l.created_at
-- FROM leads l
-- WHERE NOT EXISTS (
--     SELECT 1 FROM events e WHERE e.lead_id = l.id
-- )
-- ORDER BY l.created_at DESC;

-- 6. Call workflow analysis (VAPI events)
-- SELECT
--     call_outcome,
--     COUNT(*) as call_count,
--     AVG(call_duration_seconds) as avg_duration_sec,
--     SUM(call_duration_seconds) as total_duration_sec
-- FROM events
-- WHERE event_source = 'vapi' AND event_type = 'call_completed'
-- GROUP BY call_outcome
-- ORDER BY call_count DESC;
