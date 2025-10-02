-- Migration 004: Offers Table
-- Created: 2025-01-19
-- Purpose: Define what services/products we sell to leads
-- Dependencies: 001_users_table.sql

-- ============================================================================
-- TABLE: offers
-- ============================================================================
-- What we sell to companies/leads
-- One offer can be used in multiple campaigns
-- Tracks pricing, description, target audience

CREATE TABLE IF NOT EXISTS offers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Offer details
    offer_name TEXT NOT NULL,
    offer_description TEXT,
    offer_type TEXT NOT NULL DEFAULT 'service',
    -- Values: service, product, consulting, subscription

    -- Pricing
    price_min DECIMAL(10, 2),  -- Minimum price (e.g., $1,000)
    price_max DECIMAL(10, 2),  -- Maximum price (e.g., $15,000)
    currency TEXT NOT NULL DEFAULT 'USD',

    -- Target audience
    target_industries TEXT[],  -- ['SaaS', 'E-commerce', 'B2B']
    target_company_size TEXT[],  -- ['1-10', '11-50', '51-200']
    target_job_titles TEXT[],  -- ['CEO', 'CTO', 'Founder']

    -- Messaging
    value_proposition TEXT,  -- Main selling point
    pain_points TEXT[],  -- Problems we solve
    key_features TEXT[],  -- What's included

    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Fast lookup by name
CREATE INDEX idx_offers_name ON offers(offer_name);

-- Query active offers only
CREATE INDEX idx_offers_active ON offers(is_active) WHERE is_active = true;

-- Query by creator (when multi-user)
CREATE INDEX idx_offers_creator ON offers(created_by);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_offers_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER offers_updated_at_trigger
    BEFORE UPDATE ON offers
    FOR EACH ROW
    EXECUTE FUNCTION update_offers_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

ALTER TABLE offers ENABLE ROW LEVEL SECURITY;

-- Users can see their own offers
CREATE POLICY offers_select_own ON offers
    FOR SELECT
    USING (created_by = auth.uid());

-- Users can create offers
CREATE POLICY offers_insert_own ON offers
    FOR INSERT
    WITH CHECK (created_by = auth.uid());

-- Users can update their own offers
CREATE POLICY offers_update_own ON offers
    FOR UPDATE
    USING (created_by = auth.uid());

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE offers IS 'Services/products we sell to leads';
COMMENT ON COLUMN offers.offer_type IS 'Type: service, product, consulting, subscription';
COMMENT ON COLUMN offers.target_industries IS 'Array of industry names';
COMMENT ON COLUMN offers.value_proposition IS 'Main selling point for outreach messages';

-- ============================================================================
-- SEED DATA (Example)
-- ============================================================================

INSERT INTO offers (
    offer_name,
    offer_description,
    offer_type,
    price_min,
    price_max,
    currency,
    target_industries,
    target_company_size,
    target_job_titles,
    value_proposition,
    pain_points,
    key_features,
    created_by
) VALUES (
    'AI Automation Services',
    'Custom AI automation solutions for business processes',
    'service',
    1000.00,
    15000.00,
    'USD',
    ARRAY['SaaS', 'E-commerce', 'B2B Services'],
    ARRAY['11-50', '51-200', '201-500'],
    ARRAY['CEO', 'CTO', 'Founder', 'VP Engineering'],
    'Automate repetitive tasks and scale operations without hiring',
    ARRAY['Manual data entry', 'Slow response times', 'High operational costs'],
    ARRAY['Custom AI workflows', 'API integrations', 'ROI tracking'],
    (SELECT id FROM users LIMIT 1)
) ON CONFLICT DO NOTHING;

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================

-- After running this migration, verify with:
-- SELECT id, offer_name, offer_type, price_min, price_max, is_active
-- FROM offers;
