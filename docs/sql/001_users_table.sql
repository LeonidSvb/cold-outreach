-- ============================================================================
-- USERS TABLE
-- Migration: 001
-- Created: 2025-10-02
-- Purpose: Single-user mode (multi-user ready for future)
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- USERS TABLE
-- ============================================================================
-- Currently single-user, but designed for multi-user expansion

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Basic info
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,

    -- Organization (optional)
    organization TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for email lookups
CREATE INDEX idx_users_email ON users(email);

-- Trigger for updated_at
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

-- ============================================================================
-- INSERT DEFAULT USER (Single-user mode)
-- ============================================================================

INSERT INTO users (email, full_name, organization) VALUES
    ('leonid@systemhustle.com', 'Leonid Shvorob', 'SystemHustle')
ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- ROW LEVEL SECURITY (Prepared for multi-user)
-- ============================================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Single-user mode: allow all for now
CREATE POLICY "Allow all for authenticated users" ON users
    FOR ALL USING (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'Users table - currently single-user mode, multi-user ready';
COMMENT ON COLUMN users.email IS 'User email - unique identifier';
COMMENT ON COLUMN users.organization IS 'Optional organization name';

-- ============================================================================
-- MIGRATION COMPLETE - USERS TABLE
-- ============================================================================

-- Summary:
-- ✅ Users table created
-- ✅ Default user inserted (leonid@systemhustle.com)
-- ✅ RLS enabled (prepared for Supabase Auth)
-- ✅ Updated_at trigger configured

-- Next steps:
-- 1. Run migration 002 (Instantly raw layer)
-- 2. All future tables will have user_id FK to this table
