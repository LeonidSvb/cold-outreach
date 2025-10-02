-- ============================================================================
-- Supabase Database Schema for Cold Outreach Platform
-- Version: 1.0.0
-- Created: 2025-10-02
-- Purpose: First Campaign Launch - Complete database foundation
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USERS TABLE (Single-user mode for now, multi-user ready)
-- ============================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    organization TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default user for single-user mode
INSERT INTO users (email, full_name, organization) VALUES
    ('leonid@example.com', 'Leonid Shvorob', 'SystemHustle')
ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- 2. OFFERS TABLE (Services we sell)
-- ============================================================================
CREATE TABLE offers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Offer details
    name TEXT NOT NULL,
    description TEXT,
    target_audience TEXT,

    -- Pricing
    price_min INTEGER,
    price_max INTEGER,
    currency TEXT DEFAULT 'USD',

    -- Offer content (for icebreakers/emails)
    short_pitch TEXT, -- 1-2 sentences
    value_proposition TEXT,
    call_to_action TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sample offers
INSERT INTO offers (user_id, name, description, target_audience, price_min, price_max, short_pitch, value_proposition, call_to_action) VALUES
    (
        (SELECT id FROM users LIMIT 1),
        'AI Automation for Service Businesses',
        'Complete AI automation system for lead generation and client communication',
        'Service businesses, consultants, coaches with 10-50 employees',
        1000,
        5000,
        'We build AI systems that handle your lead generation and client communication automatically.',
        'Save 20+ hours per week on repetitive tasks while converting 3x more leads into clients.',
        'Book a 15-minute demo to see how AI can automate your business'
    ),
    (
        (SELECT id FROM users LIMIT 1),
        'Cold Outreach System',
        'Done-for-you cold email system generating qualified leads',
        'B2B companies looking to scale outbound sales',
        2000,
        10000,
        'We launch and manage cold email campaigns that book meetings with your ideal clients.',
        'Generate 10-30 qualified sales calls per month without hiring a sales team.',
        'Let us show you our proven cold outreach playbook'
    )
ON CONFLICT DO NOTHING;

-- ============================================================================
-- 3. LEADS TABLE (Contacts from CSV imports)
-- ============================================================================
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Personal info
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,
    email TEXT NOT NULL,
    email_status TEXT, -- verified, unavailable, etc.

    -- Professional info
    title TEXT,
    seniority TEXT,
    headline TEXT,

    -- Company info
    company_name TEXT,
    company_url TEXT,
    company_domain TEXT,
    company_linkedin_url TEXT,
    estimated_num_employees INTEGER,

    -- Industry & keywords
    industry TEXT,
    secondary_industries JSONB,
    industries JSONB,
    functions JSONB,
    departments JSONB,
    keywords JSONB,

    -- Contact info
    phone_number TEXT,
    sanitized_phone_number TEXT,
    linkedin_url TEXT,

    -- Location
    country TEXT,
    state TEXT,
    city TEXT,

    -- Apollo metadata
    is_likely_to_engage BOOLEAN,

    -- Enrichment data (from scraping, AI analysis)
    website_content TEXT,
    website_summary TEXT,
    personalization_data JSONB,

    -- Icebreaker
    icebreaker TEXT,
    icebreaker_style TEXT,
    icebreaker_generated_at TIMESTAMP WITH TIME ZONE,

    -- Status tracking
    lead_status TEXT DEFAULT 'imported', -- imported, enriched, ready, contacted, replied, bounced

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint on email per user
    UNIQUE(user_id, email)
);

-- Indexes for performance
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_company_domain ON leads(company_domain);
CREATE INDEX idx_leads_status ON leads(lead_status);
CREATE INDEX idx_leads_user_id ON leads(user_id);

-- ============================================================================
-- 4. BATCHES TABLE (Groups of leads for campaigns)
-- ============================================================================
CREATE TABLE batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Batch info
    name TEXT NOT NULL,
    description TEXT,

    -- Segmentation criteria
    segment_criteria JSONB, -- Company size, industry, location, etc.

    -- Stats
    total_leads INTEGER DEFAULT 0,

    -- Status
    batch_status TEXT DEFAULT 'draft', -- draft, ready, assigned_to_campaign

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Junction table for batch membership
CREATE TABLE batch_leads (
    batch_id UUID REFERENCES batches(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    PRIMARY KEY (batch_id, lead_id)
);

-- ============================================================================
-- 5. EMAIL ACCOUNTS TABLE (Sender accounts)
-- ============================================================================
CREATE TABLE email_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Account details
    email TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,

    -- Provider info
    provider TEXT, -- gmail, outlook, custom
    provider_code INTEGER,

    -- Instantly integration
    instantly_account_id TEXT UNIQUE,

    -- Domain tracking
    tracking_domain_name TEXT,
    tracking_domain_status TEXT,

    -- Warmup
    warmup_status INTEGER, -- 1=active, 0=inactive
    warmup_score INTEGER DEFAULT 0,
    warmup_pool_id TEXT,

    -- Sending limits
    daily_limit INTEGER DEFAULT 30,
    sending_gap INTEGER DEFAULT 10, -- seconds between emails

    -- Status
    account_status INTEGER, -- 1=active, -1=error
    is_managed_account BOOLEAN DEFAULT FALSE,
    status_message JSONB,

    -- Timestamps
    timestamp_created TIMESTAMP WITH TIME ZONE,
    timestamp_updated TIMESTAMP WITH TIME ZONE,
    timestamp_warmup_start TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- 6. CAMPAIGNS TABLE (Outreach campaigns)
-- ============================================================================
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    offer_id UUID REFERENCES offers(id) ON DELETE SET NULL,
    batch_id UUID REFERENCES batches(id) ON DELETE SET NULL,

    -- Campaign details
    name TEXT NOT NULL,
    description TEXT,

    -- Instantly integration
    instantly_campaign_id TEXT UNIQUE,

    -- Email sequence
    email_sequence JSONB, -- Array of email templates with delays

    -- Status
    campaign_status INTEGER, -- 2=active, -1=paused, -2=stopped, 3=completed
    is_evergreen BOOLEAN DEFAULT FALSE,

    -- Analytics
    leads_count INTEGER DEFAULT 0,
    contacted_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    link_click_count INTEGER DEFAULT 0,
    bounced_count INTEGER DEFAULT 0,
    unsubscribed_count INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    emails_sent_count INTEGER DEFAULT 0,

    -- Opportunities
    total_opportunities INTEGER DEFAULT 0,
    total_opportunity_value INTEGER DEFAULT 0,

    -- Enhanced analytics (calculated)
    formal_reply_rate NUMERIC(5,2),
    estimated_real_replies INTEGER,
    real_reply_rate NUMERIC(5,2),
    positive_reply_rate NUMERIC(5,2),
    bounce_rate NUMERIC(5,2),
    opportunity_rate NUMERIC(5,2),

    -- Schedule
    start_date DATE,
    end_date DATE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Instantly sync
    last_synced_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- 7. EVENTS TABLE (All campaign actions and responses)
-- ============================================================================
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    email_account_id UUID REFERENCES email_accounts(id) ON DELETE SET NULL,

    -- Event details
    event_type TEXT NOT NULL, -- sent, opened, replied, bounced, clicked, unsubscribed
    event_date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Email details
    email_subject TEXT,
    email_body TEXT,
    sequence_step INTEGER, -- Which email in the sequence (1, 2, 3, etc.)

    -- Response data (for replies)
    response_text TEXT,
    response_sentiment TEXT, -- positive, neutral, negative, out_of_office, auto_reply

    -- Instantly integration
    instantly_event_id TEXT UNIQUE,

    -- Metadata
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_events_campaign_id ON events(campaign_id);
CREATE INDEX idx_events_lead_id ON events(lead_id);
CREATE INDEX idx_events_event_type ON events(event_type);
CREATE INDEX idx_events_event_date ON events(event_date);

-- ============================================================================
-- 8. DAILY ANALYTICS TABLE (Aggregated daily stats)
-- ============================================================================
CREATE TABLE daily_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,

    -- Date
    analytics_date DATE NOT NULL,

    -- Metrics
    sent INTEGER DEFAULT 0,
    opened INTEGER DEFAULT 0,
    unique_opened INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    unique_replies INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    unique_clicks INTEGER DEFAULT 0,
    bounced INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique per campaign per day
    UNIQUE(campaign_id, analytics_date)
);

-- ============================================================================
-- 9. TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_offers_updated_at BEFORE UPDATE ON offers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_batches_updated_at BEFORE UPDATE ON batches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_accounts_updated_at BEFORE UPDATE ON email_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_daily_analytics_updated_at BEFORE UPDATE ON daily_analytics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 10. ROW LEVEL SECURITY (RLS) - Prepared for multi-user mode
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE offers ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_analytics ENABLE ROW LEVEL SECURITY;

-- Single-user mode: Allow all operations for now
-- (Will be updated when adding Supabase Auth)

CREATE POLICY "Allow all for authenticated users" ON users
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON offers
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON leads
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON batches
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON batch_leads
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON email_accounts
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON campaigns
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON events
    FOR ALL USING (true);

CREATE POLICY "Allow all for authenticated users" ON daily_analytics
    FOR ALL USING (true);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Summary of tables created:
-- 1. users (1 default user)
-- 2. offers (2 sample offers)
-- 3. leads (ready for CSV import)
-- 4. batches (lead segmentation)
-- 5. batch_leads (junction table)
-- 6. email_accounts (sender accounts from Instantly)
-- 7. campaigns (outreach campaigns)
-- 8. events (all email events)
-- 9. daily_analytics (aggregated stats)

-- Next steps:
-- 1. Execute this SQL in your Supabase project
-- 2. Verify tables are created
-- 3. Test with sample lead insert
-- 4. Build Python scripts for data import
-- 5. Connect backend to Supabase
