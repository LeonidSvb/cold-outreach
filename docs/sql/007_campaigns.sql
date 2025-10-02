-- Migration 007: Campaigns Table
-- Created: 2025-01-19
-- Purpose: Email/call campaigns (not tied to Instantly - our own campaigns)
-- Dependencies: 004_offers.sql, 001_users_table.sql

-- ============================================================================
-- TABLE: campaigns
-- ============================================================================
-- Our internal campaigns that use Instantly/VAPI/etc as channels
-- One campaign can use multiple channels (email + calls)
-- Tracks what offer we're promoting to which audience

CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Campaign identification
    campaign_name TEXT NOT NULL,
    campaign_description TEXT,
    campaign_type TEXT NOT NULL DEFAULT 'outbound',
    -- Values: outbound, inbound, referral, event

    -- Offer relationship
    offer_id UUID NOT NULL REFERENCES offers(id) ON DELETE RESTRICT,

    -- Campaign channels
    uses_email BOOLEAN DEFAULT true,
    uses_calls BOOLEAN DEFAULT false,
    uses_linkedin BOOLEAN DEFAULT false,

    -- Instantly integration (optional)
    instantly_campaign_id TEXT,  -- Links to instantly_campaigns_raw if using Instantly
    instantly_campaign_name TEXT,

    -- VAPI integration (optional - future)
    vapi_campaign_id TEXT,

    -- Campaign timing
    starts_at TIMESTAMP WITH TIME ZONE,
    ends_at TIMESTAMP WITH TIME ZONE,

    -- Campaign settings
    daily_send_limit INTEGER DEFAULT 50,  -- Max leads to contact per day
    timezone TEXT DEFAULT 'UTC',

    -- Messaging
    email_subject_template TEXT,
    email_body_template TEXT,
    call_script_template TEXT,  -- For VAPI calls

    -- Campaign status
    campaign_status TEXT NOT NULL DEFAULT 'draft',
    -- Values: draft, active, paused, completed, archived

    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Fast lookup by name
CREATE INDEX idx_campaigns_name ON campaigns(campaign_name);

-- Query by status
CREATE INDEX idx_campaigns_status ON campaigns(campaign_status);

-- Query active campaigns only
CREATE INDEX idx_campaigns_active ON campaigns(campaign_status) WHERE campaign_status = 'active';

-- Query by offer
CREATE INDEX idx_campaigns_offer ON campaigns(offer_id);

-- Query by Instantly campaign
CREATE INDEX idx_campaigns_instantly_id ON campaigns(instantly_campaign_id);

-- Query by creator
CREATE INDEX idx_campaigns_creator ON campaigns(created_by);

-- Query campaigns by date range
CREATE INDEX idx_campaigns_dates ON campaigns(starts_at, ends_at);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
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

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

-- Users can see their own campaigns
CREATE POLICY campaigns_select_own ON campaigns
    FOR SELECT
    USING (created_by = auth.uid());

-- Users can create campaigns
CREATE POLICY campaigns_insert_own ON campaigns
    FOR INSERT
    WITH CHECK (created_by = auth.uid());

-- Users can update their own campaigns
CREATE POLICY campaigns_update_own ON campaigns
    FOR UPDATE
    USING (created_by = auth.uid());

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE campaigns IS 'Our internal campaigns - can use Instantly, VAPI, LinkedIn as channels';
COMMENT ON COLUMN campaigns.offer_id IS 'What we are selling in this campaign';
COMMENT ON COLUMN campaigns.instantly_campaign_id IS 'Optional: links to instantly_campaigns_raw table';
COMMENT ON COLUMN campaigns.campaign_type IS 'Type: outbound, inbound, referral, event';
COMMENT ON COLUMN campaigns.campaign_status IS 'Status: draft, active, paused, completed, archived';
COMMENT ON COLUMN campaigns.email_body_template IS 'Template with variables: {{first_name}}, {{company_name}}, etc.';

-- ============================================================================
-- SEED DATA (Example)
-- ============================================================================

INSERT INTO campaigns (
    campaign_name,
    campaign_description,
    campaign_type,
    offer_id,
    uses_email,
    uses_calls,
    campaign_status,
    email_subject_template,
    email_body_template,
    created_by
) VALUES (
    'Q1 2025 - AI Automation Outreach',
    'Cold outreach to SaaS companies for AI automation services',
    'outbound',
    (SELECT id FROM offers WHERE offer_name = 'AI Automation Services' LIMIT 1),
    true,
    true,
    'draft',
    'Automate {{pain_point}} at {{company_name}}',
    'Hi {{first_name}},

I noticed {{company_name}} is in {{industry}} - most companies in your space struggle with {{pain_point}}.

We have helped similar companies like {{competitor_example}} reduce operational costs by 40% through AI automation.

Would you be open to a 15-min call next week?

Best,
Leonid',
    (SELECT id FROM users LIMIT 1)
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- After running this migration, verify with:

-- 1. Check campaigns with offer details
-- SELECT
--     c.campaign_name,
--     c.campaign_status,
--     o.offer_name,
--     c.uses_email,
--     c.uses_calls
-- FROM campaigns c
-- JOIN offers o ON c.offer_id = o.id
-- ORDER BY c.created_at DESC;

-- 2. Check active campaigns
-- SELECT campaign_name, campaign_status, starts_at, ends_at
-- FROM campaigns
-- WHERE campaign_status = 'active'
-- ORDER BY starts_at;

-- 3. Check campaign channel usage
-- SELECT
--     uses_email,
--     uses_calls,
--     uses_linkedin,
--     COUNT(*) as campaign_count
-- FROM campaigns
-- GROUP BY uses_email, uses_calls, uses_linkedin;
