-- Migration 004: Offers Table
-- Created: 2025-01-19
-- Purpose: Define what services/products we sell
-- Dependencies: 001_users_table.sql

CREATE TABLE IF NOT EXISTS offers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    offer_name TEXT NOT NULL,
    offer_description TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Auto-update updated_at
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

-- Seed data
INSERT INTO offers (offer_name, offer_description) VALUES (
    'AI Automation Services',
    'Custom AI automation solutions for business processes'
) ON CONFLICT DO NOTHING;
