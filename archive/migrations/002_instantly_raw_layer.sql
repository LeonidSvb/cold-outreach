-- ============================================================================
-- INSTANTLY RAW DATA LAYER
-- Migration: 002
-- Created: 2025-10-02
-- Purpose: Raw data storage from Instantly API for historical tracking
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. INSTANTLY CAMPAIGNS RAW
-- ============================================================================
-- Stores raw campaign data from Instantly API
-- Source: /api/v2/campaigns/analytics endpoint

CREATE TABLE instantly_campaigns_raw (
    -- Primary identification
    instantly_campaign_id TEXT PRIMARY KEY,

    -- Main fields for quick queries (extracted from JSON)
    campaign_name TEXT,
    campaign_status INTEGER, -- 2=active, -1=paused, -2=stopped, 3=completed

    -- Basic metrics (extracted for indexing)
    leads_count INTEGER DEFAULT 0,
    contacted_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    emails_sent_count INTEGER DEFAULT 0,

    -- Full raw JSON from Instantly (preserves ALL data)
    raw_json JSONB NOT NULL,

    -- Sync tracking
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_instantly_campaigns_name ON instantly_campaigns_raw(campaign_name);
CREATE INDEX idx_instantly_campaigns_status ON instantly_campaigns_raw(campaign_status);
CREATE INDEX idx_instantly_campaigns_synced ON instantly_campaigns_raw(synced_at DESC);

-- ============================================================================
-- 2. INSTANTLY ACCOUNTS RAW
-- ============================================================================
-- Stores raw email account data from Instantly API
-- Source: /api/v2/accounts endpoint

CREATE TABLE instantly_accounts_raw (
    -- Primary identification (email is unique in Instantly)
    email TEXT PRIMARY KEY,

    -- Main fields for quick queries
    first_name TEXT,
    last_name TEXT,
    account_status INTEGER, -- 1=active, -1=error
    warmup_status INTEGER,
    warmup_score INTEGER,

    -- Full raw JSON from Instantly
    raw_json JSONB NOT NULL,

    -- Sync tracking
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_instantly_accounts_status ON instantly_accounts_raw(account_status);
CREATE INDEX idx_instantly_accounts_warmup ON instantly_accounts_raw(warmup_score DESC);

-- ============================================================================
-- 3. INSTANTLY DAILY ANALYTICS RAW
-- ============================================================================
-- Stores raw daily analytics data from Instantly API
-- Source: /api/v2/campaigns/analytics/daily endpoint

CREATE TABLE instantly_daily_analytics_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Date identification
    analytics_date DATE NOT NULL,

    -- Optional: link to specific campaign (if available)
    instantly_campaign_id TEXT,

    -- Main metrics (extracted for quick queries)
    sent INTEGER DEFAULT 0,
    opened INTEGER DEFAULT 0,
    unique_opened INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    unique_replies INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    unique_clicks INTEGER DEFAULT 0,

    -- Full raw JSON from Instantly
    raw_json JSONB NOT NULL,

    -- Sync tracking
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint: one record per date (or per date+campaign if specified)
CREATE UNIQUE INDEX idx_instantly_daily_unique_global ON instantly_daily_analytics_raw(analytics_date)
    WHERE instantly_campaign_id IS NULL;

CREATE UNIQUE INDEX idx_instantly_daily_unique_campaign ON instantly_daily_analytics_raw(analytics_date, instantly_campaign_id)
    WHERE instantly_campaign_id IS NOT NULL;

-- Indexes for performance
CREATE INDEX idx_instantly_daily_date ON instantly_daily_analytics_raw(analytics_date DESC);
CREATE INDEX idx_instantly_daily_campaign ON instantly_daily_analytics_raw(instantly_campaign_id);

-- ============================================================================
-- 4. INSTANTLY EMAILS RAW (Future-ready)
-- ============================================================================
-- Stores raw email event data from Instantly API
-- Source: /api/v2/emails endpoint
-- NOTE: Currently empty in your data, but prepared for future

CREATE TABLE instantly_emails_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Instantly identification (if available)
    instantly_email_id TEXT UNIQUE,
    instantly_campaign_id TEXT,

    -- Main fields for quick queries
    email_address TEXT,
    event_type TEXT, -- sent, opened, replied, bounced, etc.
    event_date TIMESTAMP WITH TIME ZONE,

    -- Full raw JSON from Instantly
    raw_json JSONB NOT NULL,

    -- Sync tracking
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_instantly_emails_campaign ON instantly_emails_raw(instantly_campaign_id);
CREATE INDEX idx_instantly_emails_type ON instantly_emails_raw(event_type);
CREATE INDEX idx_instantly_emails_date ON instantly_emails_raw(event_date DESC);
CREATE INDEX idx_instantly_emails_address ON instantly_emails_raw(email_address);

-- ============================================================================
-- 5. TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_instantly_campaigns_raw_updated_at
    BEFORE UPDATE ON instantly_campaigns_raw
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_instantly_accounts_raw_updated_at
    BEFORE UPDATE ON instantly_accounts_raw
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. COMMENTS (Documentation)
-- ============================================================================

COMMENT ON TABLE instantly_campaigns_raw IS 'Raw campaign data from Instantly API - preserves full historical data';
COMMENT ON TABLE instantly_accounts_raw IS 'Raw email account data from Instantly API';
COMMENT ON TABLE instantly_daily_analytics_raw IS 'Raw daily analytics from Instantly API - aggregated metrics per day';
COMMENT ON TABLE instantly_emails_raw IS 'Raw email event data from Instantly API - individual email interactions';

COMMENT ON COLUMN instantly_campaigns_raw.raw_json IS 'Complete JSON response from Instantly API - never modify manually';
COMMENT ON COLUMN instantly_accounts_raw.raw_json IS 'Complete JSON response from Instantly API - never modify manually';
COMMENT ON COLUMN instantly_daily_analytics_raw.raw_json IS 'Complete JSON response from Instantly API - never modify manually';
COMMENT ON COLUMN instantly_emails_raw.raw_json IS 'Complete JSON response from Instantly API - never modify manually';

-- ============================================================================
-- MIGRATION COMPLETE - RAW LAYER
-- ============================================================================

-- Summary:
-- ✅ 4 raw data tables created
-- ✅ All tables have JSONB raw_json column (full data preservation)
-- ✅ Key fields extracted as columns for fast queries
-- ✅ Indexes added for performance
-- ✅ Triggers for updated_at automation
-- ✅ Unique constraints to prevent duplicates

-- Next steps:
-- 1. Test with sample data insert
-- 2. Create Python sync script (Instantly API → Supabase)
-- 3. Design normalized layer (campaigns, leads, events)
-- 4. Build transformation scripts (raw → normalized)

-- How to add new columns in the future:
-- ALTER TABLE instantly_campaigns_raw ADD COLUMN new_field_name TYPE;
-- This is safe and won't break existing data (JSONB preserves everything)
