-- Migration 008: Campaign Leads (Many-to-Many)
-- Created: 2025-01-19
-- Purpose: Track which leads are in which campaigns + workflow status
-- Dependencies: 006_leads.sql, 007_campaigns.sql

-- ============================================================================
-- TABLE: campaign_leads
-- ============================================================================
-- Many-to-Many relationship between campaigns and leads
-- Tracks workflow: Email sent → No reply → Call via VAPI
-- One lead can be in multiple campaigns (different offers/timing)

CREATE TABLE IF NOT EXISTS campaign_leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Relationships
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

    -- Email workflow status
    email_status TEXT DEFAULT 'pending',
    -- Values: pending, sent, opened, clicked, replied, bounced, unsubscribed, failed
    email_sent_at TIMESTAMP WITH TIME ZONE,
    email_opened_at TIMESTAMP WITH TIME ZONE,
    email_replied_at TIMESTAMP WITH TIME ZONE,

    -- Call workflow status
    call_status TEXT DEFAULT 'not_scheduled',
    -- Values: not_scheduled, scheduled, completed, no_answer, voicemail, wrong_number, do_not_call
    call_scheduled_at TIMESTAMP WITH TIME ZONE,
    call_completed_at TIMESTAMP WITH TIME ZONE,
    call_duration_seconds INTEGER,

    -- LinkedIn workflow status (future)
    linkedin_status TEXT DEFAULT 'not_started',
    -- Values: not_started, connection_sent, connected, message_sent, replied

    -- Overall lead status in this campaign
    overall_status TEXT NOT NULL DEFAULT 'active',
    -- Values: active, replied, converted, disqualified, bounced, unsubscribed

    -- Engagement scoring
    engagement_score INTEGER DEFAULT 0,  -- 0-100 based on opens, clicks, replies
    last_activity_at TIMESTAMP WITH TIME ZONE,

    -- Sequence tracking
    sequence_step INTEGER DEFAULT 1,  -- Which email in sequence (1, 2, 3...)
    next_followup_at TIMESTAMP WITH TIME ZONE,

    -- Metadata
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Query leads in a campaign
CREATE INDEX idx_campaign_leads_campaign ON campaign_leads(campaign_id);

-- Query campaigns a lead is in
CREATE INDEX idx_campaign_leads_lead ON campaign_leads(lead_id);

-- UNIQUE constraint: one lead can only be in a campaign once
CREATE UNIQUE INDEX idx_campaign_leads_unique ON campaign_leads(campaign_id, lead_id);

-- Query by email status
CREATE INDEX idx_campaign_leads_email_status ON campaign_leads(email_status);

-- Query by call status
CREATE INDEX idx_campaign_leads_call_status ON campaign_leads(call_status);

-- Query by overall status
CREATE INDEX idx_campaign_leads_overall_status ON campaign_leads(overall_status);

-- Query leads needing followup
CREATE INDEX idx_campaign_leads_next_followup ON campaign_leads(next_followup_at)
    WHERE next_followup_at IS NOT NULL AND overall_status = 'active';

-- Query by last activity
CREATE INDEX idx_campaign_leads_last_activity ON campaign_leads(last_activity_at DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
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

-- Auto-update last_activity_at when email/call status changes
CREATE OR REPLACE FUNCTION update_campaign_leads_last_activity()
RETURNS TRIGGER AS $$
BEGIN
    IF (NEW.email_status <> OLD.email_status) OR
       (NEW.call_status <> OLD.call_status) OR
       (NEW.linkedin_status <> OLD.linkedin_status) THEN
        NEW.last_activity_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER campaign_leads_last_activity_trigger
    BEFORE UPDATE ON campaign_leads
    FOR EACH ROW
    EXECUTE FUNCTION update_campaign_leads_last_activity();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE campaign_leads ENABLE ROW LEVEL SECURITY;

-- Users can see campaign_leads for their own campaigns
CREATE POLICY campaign_leads_select_own_campaigns ON campaign_leads
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = campaign_leads.campaign_id
            AND campaigns.created_by = auth.uid()
        )
    );

-- Users can insert campaign_leads for their own campaigns
CREATE POLICY campaign_leads_insert_own_campaigns ON campaign_leads
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = campaign_leads.campaign_id
            AND campaigns.created_by = auth.uid()
        )
    );

-- Users can update campaign_leads for their own campaigns
CREATE POLICY campaign_leads_update_own_campaigns ON campaign_leads
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = campaign_leads.campaign_id
            AND campaigns.created_by = auth.uid()
        )
    );

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE campaign_leads IS 'Many-to-Many relationship: tracks which leads are in which campaigns with workflow status';
COMMENT ON COLUMN campaign_leads.email_status IS 'Email workflow: pending, sent, opened, clicked, replied, bounced, unsubscribed, failed';
COMMENT ON COLUMN campaign_leads.call_status IS 'Call workflow: not_scheduled, scheduled, completed, no_answer, voicemail, wrong_number, do_not_call';
COMMENT ON COLUMN campaign_leads.overall_status IS 'Lead status in campaign: active, replied, converted, disqualified, bounced, unsubscribed';
COMMENT ON COLUMN campaign_leads.sequence_step IS 'Which email in sequence (1=initial, 2=first followup, 3=second followup, etc.)';
COMMENT ON COLUMN campaign_leads.engagement_score IS 'Calculated score 0-100 based on opens, clicks, replies';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- After running this migration, verify with:

-- 1. Check campaign leads with full details
-- SELECT
--     c.campaign_name,
--     l.full_name,
--     l.email,
--     cl.email_status,
--     cl.call_status,
--     cl.overall_status,
--     cl.sequence_step
-- FROM campaign_leads cl
-- JOIN campaigns c ON cl.campaign_id = c.id
-- JOIN leads l ON cl.lead_id = l.id
-- ORDER BY cl.added_at DESC
-- LIMIT 10;

-- 2. Check email workflow funnel
-- SELECT
--     email_status,
--     COUNT(*) as count,
--     ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
-- FROM campaign_leads
-- GROUP BY email_status
-- ORDER BY count DESC;

-- 3. Find leads ready for follow-up calls (email sent, no reply)
-- SELECT
--     l.full_name,
--     l.email,
--     c.campaign_name,
--     cl.email_status,
--     cl.call_status,
--     cl.email_sent_at
-- FROM campaign_leads cl
-- JOIN leads l ON cl.lead_id = l.id
-- JOIN campaigns c ON cl.campaign_id = c.id
-- WHERE cl.email_status IN ('sent', 'opened')
--   AND cl.email_replied_at IS NULL
--   AND cl.call_status = 'not_scheduled'
--   AND cl.email_sent_at < NOW() - INTERVAL '3 days'
-- ORDER BY cl.email_sent_at ASC;

-- 4. Check engagement scores distribution
-- SELECT
--     CASE
--         WHEN engagement_score >= 80 THEN 'High (80-100)'
--         WHEN engagement_score >= 50 THEN 'Medium (50-79)'
--         WHEN engagement_score >= 20 THEN 'Low (20-49)'
--         ELSE 'Very Low (0-19)'
--     END as engagement_level,
--     COUNT(*) as lead_count
-- FROM campaign_leads
-- GROUP BY engagement_level
-- ORDER BY MIN(engagement_score) DESC;
