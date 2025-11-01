-- ============================================================================
-- COMBINED INITIALIZATION FOR OUTREACH ENGINE
-- Created: 2025-10-29
-- Purpose: Complete database setup with raw Instantly data layer
-- ============================================================================

-- ============================================================================
-- MIGRATION 001: USERS TABLE
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    organization TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Trigger function for updated_at (used by multiple tables)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default user
INSERT INTO users (email, full_name, organization) VALUES
    ('leonid@systemhustle.com', 'Leonid Shvorob', 'SystemHustle')
ON CONFLICT (email) DO NOTHING;

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all for authenticated users" ON users
    FOR ALL USING (true);

COMMENT ON TABLE users IS 'Users table - currently single-user mode, multi-user ready';

-- ============================================================================
-- MIGRATION 002: INSTANTLY RAW DATA LAYER
-- ============================================================================

-- 1. CAMPAIGNS RAW
CREATE TABLE instantly_campaigns_raw (
    instantly_campaign_id TEXT PRIMARY KEY,
    campaign_name TEXT,
    campaign_status INTEGER,
    leads_count INTEGER DEFAULT 0,
    contacted_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    emails_sent_count INTEGER DEFAULT 0,
    raw_json JSONB NOT NULL,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_instantly_campaigns_name ON instantly_campaigns_raw(campaign_name);
CREATE INDEX idx_instantly_campaigns_status ON instantly_campaigns_raw(campaign_status);
CREATE INDEX idx_instantly_campaigns_synced ON instantly_campaigns_raw(synced_at DESC);

CREATE TRIGGER update_instantly_campaigns_raw_updated_at
    BEFORE UPDATE ON instantly_campaigns_raw
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE instantly_campaigns_raw IS 'Raw campaign data from Instantly API';

-- 2. ACCOUNTS RAW
CREATE TABLE instantly_accounts_raw (
    email TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    account_status INTEGER,
    warmup_status INTEGER,
    warmup_score INTEGER,
    raw_json JSONB NOT NULL,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_instantly_accounts_status ON instantly_accounts_raw(account_status);
CREATE INDEX idx_instantly_accounts_warmup ON instantly_accounts_raw(warmup_score DESC);

CREATE TRIGGER update_instantly_accounts_raw_updated_at
    BEFORE UPDATE ON instantly_accounts_raw
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE instantly_accounts_raw IS 'Raw email account data from Instantly API';

-- 3. DAILY ANALYTICS RAW
CREATE TABLE instantly_daily_analytics_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analytics_date DATE NOT NULL,
    instantly_campaign_id TEXT,
    sent INTEGER DEFAULT 0,
    opened INTEGER DEFAULT 0,
    unique_opened INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    unique_replies INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    unique_clicks INTEGER DEFAULT 0,
    raw_json JSONB NOT NULL,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_instantly_daily_unique_global ON instantly_daily_analytics_raw(analytics_date)
    WHERE instantly_campaign_id IS NULL;

CREATE UNIQUE INDEX idx_instantly_daily_unique_campaign ON instantly_daily_analytics_raw(analytics_date, instantly_campaign_id)
    WHERE instantly_campaign_id IS NOT NULL;

CREATE INDEX idx_instantly_daily_date ON instantly_daily_analytics_raw(analytics_date DESC);
CREATE INDEX idx_instantly_daily_campaign ON instantly_daily_analytics_raw(instantly_campaign_id);

COMMENT ON TABLE instantly_daily_analytics_raw IS 'Raw daily analytics from Instantly API';

-- 4. EMAILS RAW
CREATE TABLE instantly_emails_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instantly_email_id TEXT UNIQUE,
    instantly_campaign_id TEXT,
    email_address TEXT,
    event_type TEXT,
    event_date TIMESTAMP WITH TIME ZONE,
    raw_json JSONB NOT NULL,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_instantly_emails_campaign ON instantly_emails_raw(instantly_campaign_id);
CREATE INDEX idx_instantly_emails_type ON instantly_emails_raw(event_type);
CREATE INDEX idx_instantly_emails_date ON instantly_emails_raw(event_date DESC);
CREATE INDEX idx_instantly_emails_address ON instantly_emails_raw(email_address);

COMMENT ON TABLE instantly_emails_raw IS 'Raw email event data from Instantly API';

-- ============================================================================
-- MIGRATION 012: INSTANTLY LEADS RAW
-- ============================================================================

CREATE TABLE instantly_leads_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instantly_lead_id TEXT UNIQUE,
    instantly_campaign_id TEXT,
    email TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    company_name TEXT,
    lead_status TEXT,
    raw_json JSONB NOT NULL,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_instantly_leads_email ON instantly_leads_raw(email);
CREATE INDEX idx_instantly_leads_campaign ON instantly_leads_raw(instantly_campaign_id);
CREATE INDEX idx_instantly_leads_status ON instantly_leads_raw(lead_status);
CREATE INDEX idx_instantly_leads_synced ON instantly_leads_raw(synced_at DESC);
CREATE INDEX idx_instantly_leads_name ON instantly_leads_raw(first_name, last_name);

ALTER TABLE instantly_leads_raw
    ADD CONSTRAINT fk_instantly_leads_campaign
    FOREIGN KEY (instantly_campaign_id)
    REFERENCES instantly_campaigns_raw(instantly_campaign_id)
    ON DELETE SET NULL;

CREATE TRIGGER update_instantly_leads_raw_updated_at
    BEFORE UPDATE ON instantly_leads_raw
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE instantly_leads_raw IS 'Raw lead data from Instantly API';

-- ============================================================================
-- MIGRATION 013: INSTANTLY STEPS RAW
-- ============================================================================

CREATE TABLE instantly_steps_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instantly_campaign_id TEXT NOT NULL,
    step_number INTEGER,
    step_name TEXT,
    step_type TEXT,
    emails_sent INTEGER DEFAULT 0,
    emails_opened INTEGER DEFAULT 0,
    emails_replied INTEGER DEFAULT 0,
    emails_bounced INTEGER DEFAULT 0,
    emails_clicked INTEGER DEFAULT 0,
    raw_json JSONB NOT NULL,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_instantly_steps_campaign ON instantly_steps_raw(instantly_campaign_id);
CREATE INDEX idx_instantly_steps_number ON instantly_steps_raw(step_number);
CREATE INDEX idx_instantly_steps_synced ON instantly_steps_raw(synced_at DESC);

CREATE UNIQUE INDEX idx_instantly_steps_unique ON instantly_steps_raw(instantly_campaign_id, step_number)
    WHERE step_number IS NOT NULL;

ALTER TABLE instantly_steps_raw
    ADD CONSTRAINT fk_instantly_steps_campaign
    FOREIGN KEY (instantly_campaign_id)
    REFERENCES instantly_campaigns_raw(instantly_campaign_id)
    ON DELETE CASCADE;

CREATE TRIGGER update_instantly_steps_raw_updated_at
    BEFORE UPDATE ON instantly_steps_raw
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE instantly_steps_raw IS 'Raw steps analytics from Instantly API';

-- ============================================================================
-- INITIALIZATION COMPLETE
-- ============================================================================

-- Summary:
-- ✅ Users table created with default user
-- ✅ 6 Instantly raw data tables created:
--    - instantly_campaigns_raw
--    - instantly_accounts_raw
--    - instantly_daily_analytics_raw
--    - instantly_emails_raw
--    - instantly_leads_raw (NEW!)
--    - instantly_steps_raw (NEW!)
-- ✅ All tables have JSONB raw_json for full data preservation
-- ✅ Indexes for performance
-- ✅ Foreign keys for referential integrity
-- ✅ Triggers for updated_at automation
-- ✅ Comments for documentation

-- Next steps:
-- 1. Create Python sync script (Instantly API → Supabase)
-- 2. Design views when needed (no premature optimization)
-- 3. Monitor query performance and add indexes as needed
