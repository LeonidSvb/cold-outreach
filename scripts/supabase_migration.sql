-- =============================================
-- SUPABASE MIGRATION: Leads & Contact History
-- Created: 2025-11-06
-- Version: 1.0.0
-- =============================================

-- =============================================
-- LEADS TABLE (Master Data)
-- =============================================
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- IDENTIFIERS (for deduplication)
    email TEXT,
    phone_number TEXT,

    -- At least one contact method required
    CHECK (email IS NOT NULL OR phone_number IS NOT NULL),

    -- CONTACT INFO
    first_name TEXT,
    last_name TEXT,
    full_name TEXT,

    -- COMPANY INFO
    company_name TEXT,
    company_domain TEXT,
    company_url TEXT,
    company_linkedin_url TEXT,
    estimated_num_employees INTEGER,

    -- PROFESSIONAL
    title TEXT,
    linkedin_url TEXT,
    headline TEXT,
    seniority TEXT,

    -- LOCATION
    country TEXT,
    state TEXT,
    city TEXT,

    -- CATEGORIZATION
    industry TEXT,

    -- FLEXIBLE STORAGE (all other CSV fields)
    extra_data JSONB DEFAULT '{}',

    -- SOURCE TRACKING
    original_source TEXT,
    sources JSONB DEFAULT '[]',

    -- STATUS
    email_status TEXT,
    phone_status TEXT,

    -- CONTACT RESTRICTIONS
    do_not_email BOOLEAN DEFAULT false,
    do_not_call BOOLEAN DEFAULT false,

    -- METADATA
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_enriched_at TIMESTAMPTZ
);

-- Unique indexes for deduplication
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_email
    ON leads(email) WHERE email IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_phone
    ON leads(phone_number) WHERE phone_number IS NOT NULL;

-- Search indexes
CREATE INDEX IF NOT EXISTS idx_leads_company
    ON leads(company_domain);

CREATE INDEX IF NOT EXISTS idx_leads_name
    ON leads(full_name);

CREATE INDEX IF NOT EXISTS idx_leads_extra
    ON leads USING GIN(extra_data);

CREATE INDEX IF NOT EXISTS idx_leads_sources
    ON leads USING GIN(sources);

CREATE INDEX IF NOT EXISTS idx_leads_created
    ON leads(created_at DESC);

-- =============================================
-- CONTACT HISTORY TABLE (Tracking)
-- =============================================
CREATE TABLE IF NOT EXISTS contact_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,

    -- CONTACT INFO
    channel TEXT NOT NULL CHECK (channel IN ('email', 'voice', 'linkedin', 'other')),
    contact_type TEXT NOT NULL,

    -- CAMPAIGN/OFFER
    campaign TEXT,
    offer TEXT,

    -- DETAILS (flexible storage)
    details JSONB DEFAULT '{}',

    -- RESULT
    result TEXT,

    -- TIMING
    contacted_at TIMESTAMPTZ DEFAULT now(),

    -- METADATA
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_contact_history_lead
    ON contact_history(lead_id);

CREATE INDEX IF NOT EXISTS idx_contact_history_channel
    ON contact_history(channel);

CREATE INDEX IF NOT EXISTS idx_contact_history_date
    ON contact_history(contacted_at DESC);

CREATE INDEX IF NOT EXISTS idx_contact_history_campaign
    ON contact_history(campaign);

CREATE INDEX IF NOT EXISTS idx_contact_history_offer
    ON contact_history(offer);

CREATE INDEX IF NOT EXISTS idx_contact_history_details
    ON contact_history USING GIN(details);

-- =============================================
-- HELPER FUNCTIONS
-- =============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for leads table
DROP TRIGGER IF EXISTS update_leads_updated_at ON leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- HELPER VIEWS (Optional - for analytics)
-- =============================================

-- View: Recent contacts per lead
CREATE OR REPLACE VIEW lead_contact_summary AS
SELECT
    l.id,
    l.email,
    l.full_name,
    l.company_name,
    COUNT(ch.id) as total_contacts,
    MAX(ch.contacted_at) as last_contacted,
    COUNT(CASE WHEN ch.channel = 'email' THEN 1 END) as email_contacts,
    COUNT(CASE WHEN ch.channel = 'voice' THEN 1 END) as voice_contacts,
    COUNT(CASE WHEN ch.result IN ('replied', 'meeting_booked') THEN 1 END) as positive_responses
FROM leads l
LEFT JOIN contact_history ch ON l.id = ch.lead_id
GROUP BY l.id, l.email, l.full_name, l.company_name;

-- =============================================
-- SAMPLE QUERIES (for reference)
-- =============================================

-- Find leads not contacted in last 30 days
-- SELECT * FROM leads l
-- WHERE id NOT IN (
--     SELECT lead_id FROM contact_history
--     WHERE contacted_at > NOW() - INTERVAL '30 days'
-- );

-- Find leads contacted with specific offer
-- SELECT l.*, ch.contacted_at, ch.result
-- FROM leads l
-- JOIN contact_history ch ON l.id = ch.lead_id
-- WHERE ch.offer = 'AI Cold Calling Agents';

-- Campaign performance
-- SELECT
--     campaign,
--     COUNT(*) as total_contacts,
--     COUNT(CASE WHEN result = 'replied' THEN 1 END) as replies,
--     ROUND(100.0 * COUNT(CASE WHEN result = 'replied' THEN 1 END) / COUNT(*), 2) as reply_rate
-- FROM contact_history
-- GROUP BY campaign;
